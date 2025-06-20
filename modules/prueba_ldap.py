from ldap3 import Server, Connection, NTLM

# Datos de prueba
server = Server('SERVER2.GBLAB.LOCAL')
user = 'GBLAB\\adj'
password = 'Genericos03*'

try:
    conn = Connection(server, user=user, password=password, authentication=NTLM, auto_bind=True)
    print("✅ Login correcto")
except Exception as e:
    print("❌ Login fallido:", e)
