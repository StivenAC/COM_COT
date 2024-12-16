import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import pyodbc
from tksheet import Sheet
import sys
import os
import json
from dotenv import load_dotenv
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
from cryptography.fernet import Fernet, InvalidToken
import logging

logging.basicConfig(filename='auth.log', level=logging.INFO)

# Check if .env file exists in the current directory
env_file_path = '.env' if os.path.isfile('.env') else '_internal/.env'

# Load .env file
load_dotenv(env_file_path)

# AD settings
AD_SERVER = os.getenv('AD_SERVER')
AD_DOMAIN = os.getenv('AD_DOMAIN')
AD_USER = os.getenv('AD_USER')
AD_PASSWORD = os.getenv('AD_PASSWORD')
ALLOWED_GROUPS = os.getenv('ALLOWED_GROUPS')
ALLOWED_USERS = os.getenv('ALLOWED_USERS')
ACCESS_CONFIG = os.getenv('ACCESS_CONFIG', {})
# Retrieve the encryption key from the .env file
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
fernet = Fernet(ENCRYPTION_KEY)

# Ensure the encryption key is loaded
if ENCRYPTION_KEY is None:
    raise ValueError("No encryption key found in environment variables.")

class MyTabView(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Create tabs
        self.add("Desarrollo")
        self.add("Abastecimiento")
        self.add("Calidad")
        
        # Add widgets to tabs
        self.my_frame1 = MyFrame(master=self.tab("Desarrollo"), load_data_func=self.load_data_oc)
        self.my_frame1.pack(fill="both", expand=True)
        self.my_frame2 = MyFrame(master=self.tab("Abastecimiento"), load_data_func=self.load_data_noc)
        self.my_frame2.pack(fill="both", expand=True)
        
    def load_data_oc(self, frame):
        # Aquí iría tu lógica de carga de datos
        pass

    def load_data_noc(self, frame):
        # Aquí iría tu lógica de carga de datos
        pass

class ScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

class MyFrame(ctk.CTkFrame):
    def __init__(self, master, load_data_func, **kwargs):
        super().__init__(master, **kwargs)
        self.load_data_func = load_data_func

        # Configuración de la hoja
        self.sheet = Sheet(self)
        self.sheet.pack(fill="both", expand=True)

        # Configurar encabezados
        headers = [
            "UUID",
            "N_control",
            "Producto", 
            "N_cotizacion", 
            "Notificacion_Sanitaria",
            "Densidad", 
            "Ph", 
            "Contenido", 
            "Color", 
            "Textura", 
            "Olor", 
            "Diligenciado"
        ]
        self.sheet.headers(headers)

        # Habilitar selección de filas
        self.sheet.enable_bindings(("single_select", "row_select", "arrowkeys"))

        # Marco para botones
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(padx=10, pady=10, fill="x")

        # Botones
        self.create_child_button = ctk.CTkButton(
            self.button_frame, 
            text="Crear Registro", 
            command=self.crear_registro
        )
        self.create_child_button.pack(side="left", padx=5)

        self.edit_child_button = ctk.CTkButton(
            self.button_frame, 
            text="Editar Registro", 
            command=self.editar_registro
        )
        self.edit_child_button.pack(side="left", padx=5)

        self.hot_reload_button = ctk.CTkButton(
            self.button_frame, 
            text="Refrescar", 
            command=self.refrescar_datos
        )
        self.hot_reload_button.pack(side="left", padx=5)

        # Configurar logging
        logging.basicConfig(level=logging.INFO, 
                             format='%(asctime)s - %(levelname)s - %(message)s',
                             filename='app.log')
        self.logger = logging.getLogger(__name__)

        # Cargar datos iniciales
        self.refrescar_datos()

    def get_db_connection(self):
        """Método para obtener conexión a la base de datos"""
        try:
            # Cargar variables de entorno para conexión
            server = os.getenv('DB1_SERVER')
            database = os.getenv('DB1_DATABASE')
            username = os.getenv('DB1_UID')
            password = os.getenv('DB1_PWD')
            driver = os.getenv('DB_DRIVER', '{SQL Server}')

            # Cadena de conexión
            conn_str = (
                f'DRIVER={driver};'
                f'SERVER={server};'
                f'DATABASE={database};'
                f'UID={username};'
                f'PWD={password}'
            )
            
            # Establecer conexión
            conn = pyodbc.connect(conn_str)
            return conn
        except Exception as e:
            self.logger.error(f"Error de conexión a base de datos: {e}")
            messagebox.showerror("Error de Conexión", str(e))
            return None

    def crear_registro(self):
        """Método para crear un nuevo registro"""
        # Diálogo de creación de registro
        crear_dialog = ctk.CTkToplevel(self)
        crear_dialog.title("Crear Nuevo Registro")
        crear_dialog.geometry("500x700")

        # Campos (excluyendo UUID que es autoincremental)
        campos = [
            "N_control", "Producto", "N_cotizacion", "Notificacion_Sanitaria", 
            "Densidad", "Ph", "Contenido", "Color", "Textura", "Olor", "Diligenciado"
        ]

        # Diccionario para guardar entradas
        entries = {}

        # Crear entradas para cada campo
        for campo in campos:
            frame = ctk.CTkFrame(crear_dialog)
            frame.pack(pady=5, padx=20, fill="x")
            
            label = ctk.CTkLabel(frame, text=campo, width=150, anchor="w")
            label.pack(side="left", padx=(0, 10))
            
            entry = ctk.CTkEntry(frame, width=300)
            entry.pack(side="left", expand=True, fill="x")
            entries[campo] = entry

        def guardar():
            """Guardar el nuevo registro"""
            try:
                conn = self.get_db_connection()
                if not conn:
                    return

                cursor = conn.cursor()
                
                # Preparar consulta
                query = '''
                INSERT INTO SIIAPP.dbo.Test_Muestras (
                    N_control, Producto, N_cotizacion, Notificacion_Sanitaria, 
                    Densidad, Ph, Contenido, Color, Textura, Olor, Diligenciado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                
                # Recoger valores
                valores = [entries[campo].get() for campo in campos]
                
                # Ejecutar inserción
                cursor.execute(query, valores)
                conn.commit()
                
                self.logger.info("Registro creado exitosamente")
                messagebox.showinfo("Éxito", "Registro creado correctamente")
                crear_dialog.destroy()
                self.refrescar_datos()
                
            except Exception as e:
                self.logger.error(f"Error al crear registro: {e}")
                messagebox.showerror("Error", f"No se pudo crear el registro: {str(e)}")
            finally:
                if conn:
                    conn.close()

        # Botón de guardar
        guardar_btn = ctk.CTkButton(crear_dialog, text="Guardar", command=guardar)
        guardar_btn.pack(pady=20)

    def editar_registro(self):
     """Método para editar un registro existente"""
     try:
        logging.info("Inicio del proceso de edición.")
        
        # Obtener fila seleccionada
        selected_rows = self.sheet.get_currently_selected()
        logging.info(f"selected_rows: {selected_rows} (tipo: {type(selected_rows)})")

        # Validar que se haya seleccionado al menos una fila
        if not selected_rows:
            messagebox.showwarning("Advertencia", "Seleccione un registro para editar")
            logging.warning("No se seleccionó ninguna fila para editar.")
            return

        # Obtener la primera fila seleccionada
        selected_row = next(iter(selected_rows))
        row_data = self.sheet.get_row_data(selected_row)
        uuid = row_data[0]  # Asumiendo que el UUID está en el índice 0

        if not uuid:
            messagebox.showerror("Error", "No se pudo obtener el UUID del registro seleccionado.")
            logging.error("El UUID es nulo o no válido.")
            return

        logging.info(f"UUID seleccionado: {uuid}")

        # Crear ventana de diálogo de edición
        editar_dialog = ctk.CTkToplevel(self)
        editar_dialog.title("Editar Registro")
        editar_dialog.geometry("500x700")

        # Campos (excluyendo UUID)
        campos = [
            "N_control", "Producto", "N_cotizacion", "Notificacion_Sanitaria", 
            "Densidad", "Ph", "Contenido", "Color", "Textura", "Olor", "Diligenciado"
        ]

        # Diccionario para guardar entradas
        entries = {}

        # Crear entradas para cada campo
        for i, campo in enumerate(campos, start=1):
            frame = ctk.CTkFrame(editar_dialog)
            frame.pack(pady=5, padx=20, fill="x")

            label = ctk.CTkLabel(frame, text=campo, width=150, anchor="w")
            label.pack(side="left", padx=(0, 10))

            entry = ctk.CTkEntry(frame, width=300)
            entry.pack(side="left", expand=True, fill="x")

            # Obtener valor actual del campo
            valor_actual = row_data[i]
            entry.insert(0, valor_actual)

            entries[campo] = entry

        def actualizar():
            """Actualizar el registro seleccionado"""
            try:
                logging.info(f"Inicio de actualización para UUID: {uuid}")
                conn = self.get_db_connection()
                if not conn:
                    logging.error("No se pudo establecer conexión a la base de datos.")
                    return

                cursor = conn.cursor()

                # Preparar consulta de actualización
                query = '''
                UPDATE SIIAPP.dbo.Test_Muestras SET
                    N_control = ?, Producto = ?, N_cotizacion = ?, 
                    Notificacion_Sanitaria = ?, Densidad = ?, Ph = ?, 
                    Contenido = ?, Color = ?, Textura = ?, Olor = ?, 
                    Diligenciado = ?
                WHERE UUID = ?
                '''

                # Recoger valores
                valores = [entries[campo].get() for campo in campos] + [uuid]

                # Ejecutar actualización
                cursor.execute(query, valores)
                conn.commit()

                logging.info(f"Registro {uuid} actualizado exitosamente.")
                messagebox.showinfo("Éxito", "Registro actualizado correctamente")
                editar_dialog.destroy()
                self.refrescar_datos()

            except Exception as e:
                logging.error(f"Error al actualizar registro {uuid}: {e}")
                messagebox.showerror("Error", f"No se pudo actualizar el registro: {str(e)}")
            finally:
                if conn:
                    conn.close()

        # Botón de actualizar
        actualizar_btn = ctk.CTkButton(editar_dialog, text="Actualizar", command=actualizar)
        actualizar_btn.pack(pady=20)

     except Exception as e:
        logging.error(f"Error en el proceso de edición: {e}")
        messagebox.showerror("Error", f"Ocurrió un problema al intentar editar el registro: {str(e)}")

    def refrescar_datos(self):
        """Método para refrescar datos de la tabla"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return

            cursor = conn.cursor()
            
            # Consulta para obtener todos los registros
            query = '''
            SELECT 
                UUID, N_control, Producto, N_cotizacion, Notificacion_Sanitaria, 
                Densidad, Ph, Contenido, Color, Textura, Olor, Diligenciado
            FROM SIIAPP.dbo.Test_Muestras
            '''
            
            cursor.execute(query)
            datos = cursor.fetchall()
            
            # Limpiar datos actuales
            self.sheet.set_sheet_data([])
            
            self.sheet.set_sheet_data(datos)
            
            self.logger.info("Datos actualizados correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al refrescar datos: {e}")
            messagebox.showerror("Error", f"No se pudieron cargar los datos: {str(e)}")
        finally:
            if conn:
                conn.close()

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.username_entry = ctk.CTkEntry(self, placeholder_text="Nombre de usuario")
        self.username_entry.pack(pady=10)
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*")
        self.password_entry.pack(pady=10)
        self.remember_var = tk.BooleanVar()
        self.remember_checkbox = ctk.CTkCheckBox(self, text="Recordar mis credenciales", variable=self.remember_var)
        self.remember_checkbox.pack(pady=5)
        self.login_button = ctk.CTkButton(self, text="Login", command=self.authenticate)
        self.login_button.pack(pady=10)

        self.user_access = None  # Store user access configuration
        self.load_credentials()    
    
    def save_credentials(self):
        if self.remember_var.get():
            encrypted_username = fernet.encrypt(self.username_entry.get().encode())
            encrypted_password = fernet.encrypt(self.password_entry.get().encode())
            with open("credentials.txt", "wb") as f:
                f.write(encrypted_username + b"," + encrypted_password)

    def load_credentials(self):
        try:
            with open("credentials.txt", "rb") as f:
                data = f.read()
                encrypted_username, encrypted_password = data.split(b",")
                self.username = fernet.decrypt(encrypted_username).decode()
                self.password = fernet.decrypt(encrypted_password).decode()
                self.username_entry.insert(0, self.username)
                self.password_entry.insert(0, self.password)
        except FileNotFoundError:
            pass
        except (ValueError, InvalidToken):
            messagebox.showerror("Error", "Unable to decrypt credentials. Please enter the correct password.")
    
    def authenticate(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Store user access configuration
        self.user_access = authenticate_user(username, password)

        if self.user_access:
            messagebox.showinfo("Login Exitoso", "Bienvenido!")
            self.save_credentials()
            self.master.show_app_frame(self.user_access)
        else:
            messagebox.showerror("Login Fallido", "Credenciales invalidas o acceso denegado.")

def get_user_access(username):
    try:
        access_config = json.loads(ACCESS_CONFIG)
    except json.JSONDecodeError:
        logging.error("Invalid JSON format in ACCESS_CONFIG environment variable.")
        return None

    # Check if the username exists in the access configuration
    return access_config.get(username)

def authenticate_user(username, password):
    server = Server(os.getenv('AD_SERVER'), get_info=ALL)
    user = f'{os.getenv("AD_DOMAIN")}\\{username}'

    try:
        conn = Connection(server, user=user, password=password,
                          authentication='NTLM', auto_bind=True)
        logging.info(f"LDAP bind successful for {username}.")
        
         # Fetch user access from the .env file
        user_access = get_user_access(username)
        if user_access:
            return user_access

        # Check if user is in allowed users
        allowed_users = os.getenv('ALLOWED_USERS').split(',')
        if username in allowed_users:
            return True

        # Search base is set to the root of the domain
        search_base = f'DC={AD_DOMAIN.replace(".", ",DC=")}'

        conn.search(
            search_base,
            f'(sAMAccountName={username})',
            attributes=['memberOf'],
            search_scope=SUBTREE
        )

        if not conn.entries:
            logging.warning(f"User {username} not found in LDAP search.")
            return False

        user_groups = [entry.memberOf.values if isinstance(entry.memberOf, list) else [
            entry.memberOf] for entry in conn.entries]
        user_groups = [item for sublist in user_groups for item in sublist]

        allowed_groups = os.getenv('ALLOWED_GROUPS').split(',')

        for group in allowed_groups:
            if any(group in str(user_group) for user_group in user_groups):
                return True

    except Exception as e:
        logging.error(f"LDAP error for {username}: {e}")

        logging.warning(f"Access denied for {username}.")
    return False

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1000x600")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.login_frame = LoginFrame(master=self)
        self.login_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

    def show_app_frame(self, user_access=None):
        # Destroy login frame
        self.login_frame.destroy()
        self.geometry("1000x600")
        
        # Create tab view
        self.my_frame = MyTabView(master=self)
        self.my_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Disable tabs based on access configuration
        if user_access and 'disabled_tabs' in user_access:
            for tab in user_access['disabled_tabs']:
                self.my_frame._segmented_button._buttons_dict[tab].configure(state=ctk.DISABLED)
app = App()
app.title("SIIAPP Desarrollo")
app.mainloop()