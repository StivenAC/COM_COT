import os
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
import logging
import json

def get_user_access(user_groups):
    """
    Matches the user's group memberships against the ACCESS_CONFIG environment variable.
    Returns the corresponding access configuration if found.
    """
    try:
        access_config = json.loads(os.getenv("ACCESS_CONFIG"))
    except json.JSONDecodeError:
        logging.error("ACCESS_CONFIG environment variable is not a valid JSON.")
        return None

    # Iterate through configured groups to find a match
    for group, config in access_config.items():
        if any(group in user_group for user_group in user_groups):
            logging.info(f"Access granted: matched group '{group}'.")
            return config

    logging.warning("No matching group found in ACCESS_CONFIG.")
    return None

def authenticate_user(username, password):
    """
    Authenticates a user against an Active Directory server using NTLM.
    Returns True if user is in ALLOWED_USERS.
    Returns access configuration if the user's group matches ACCESS_CONFIG.
    Returns False if authentication fails or no match is found.
    """
    server = Server(os.getenv("AD_SERVER"), get_info=ALL)
    user = f"{os.getenv('AD_DOMAIN')}\\{username}"

    try:
        # Attempt LDAP bind (authentication)
        conn = Connection(
            server,
            user=user,
            password=password,
            authentication=NTLM,
            auto_bind=True
        )
        logging.info(f"LDAP bind successful for {username}.")

        # Define search base using domain
        search_base = f"DC={os.getenv('AD_DOMAIN').replace('.', ',DC=')}"

        # Check for direct user access via ALLOWED_USERS
        allowed_users = os.getenv("ALLOWED_USERS", "").split(",")
        if username in allowed_users:
            return True

        # Perform LDAP search to find user and group memberships
        conn.search(
            search_base,
            f"(sAMAccountName={username})",
            attributes=["distinguishedName", "memberOf"]
        )

        if not conn.entries:
            logging.warning(f"LDAP search failed: user '{username}' not found.")
            return False

        # Get user's group memberships
        user_groups = conn.entries[0].memberOf.values if conn.entries[0].memberOf else []

        # Determine access config from group membership
        user_access = get_user_access(user_groups)
        if user_access:
            return user_access

        logging.warning(f"Access denied: no matching groups for user '{username}'.")
        return False

    except Exception as e:
        logging.error(f"LDAP authentication error for user '{username}': {e}")
        return False
