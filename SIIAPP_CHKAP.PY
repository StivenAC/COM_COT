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

logging.basicConfig(filename="auth.log", level=logging.INFO)

# Check if .env file exists in the current directory
env_file_path = ".env" if os.path.isfile(".env") else "_internal/.env"

# Load .env file
load_dotenv(env_file_path)

# AD settings
AD_SERVER = os.getenv("AD_SERVER")
AD_DOMAIN = os.getenv("AD_DOMAIN")
AD_USER = os.getenv("AD_USER")
AD_PASSWORD = os.getenv("AD_PASSWORD")
ALLOWED_GROUPS = os.getenv("ALLOWED_GROUPS")
ALLOWED_USERS = os.getenv("ALLOWED_USERS")
ACCESS_CONFIG = os.getenv("ACCESS_CONFIG", {})
# Retrieve the encryption key from the .env file
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
fernet = Fernet(ENCRYPTION_KEY)

# Ensure the encryption key is loaded
if ENCRYPTION_KEY is None:
    raise ValueError("No encryption key found in environment variables.")

class FilterableCombobox(ctk.CTkFrame):
    def __init__(self, parent, values, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.values = values
        self.filtered_values = values

        self.entry = ctk.CTkEntry(self)
        self.entry.pack(fill="x", expand=True)

        self.listbox = tk.Listbox(self, height=5)
        self.listbox.pack(fill="x", expand=True)
        self.listbox.bind("<ButtonRelease-1>", self._on_select)

        self.entry.bind("<KeyRelease>", self._filter_values)

        self._update_listbox()

    def _update_listbox(self):
        """Update the Listbox with current filtered values."""
        self.listbox.delete(0, tk.END)
        for value in self.filtered_values:
            self.listbox.insert(tk.END, value)

    def _filter_values(self, event=None):
        """Filter values based on entry content."""
        search_term = self.entry.get().lower()
        self.filtered_values = [
            value for value in self.values if search_term in value.lower()
        ]
        self._update_listbox()

    def _on_select(self, event=None):
        """Set the selected value in the Entry field."""
        selection = self.listbox.get(self.listbox.curselection())
        self.entry.delete(0, tk.END)
        self.entry.insert(0, selection)
        self.listbox.pack_forget()  # Hide the Listbox after selection

    def get(self):
        """Return the current value of the Entry."""
        return self.entry.get()

    def set(self, value):
        """Set the value of the Entry."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
class MyTabView(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Tab configurations
        self.tab_configs = {
            "Desarrollo": {
                "load_func": self.load_data_Desarrollo,
                "create_func": self.create_record_Desarrollo,
                "edit_func": self.edit_record_Desarrollo,
            },
            "Bodega": {
                "load_func": self.load_data_Bodega,
                "create_func": self.create_record_Bodega,
                "edit_func": self.edit_record_Bodega,
            },
            "Calidad": {
                "load_func": self.load_data_Calidad,
                "create_func": self.create_record_Calidad,
                "edit_func": self.edit_record_Calidad,
            },
            "Produccion": {
                "load_func": self.load_data_Produccion,
                "create_func": self.create_record_Produccion,
                "edit_func": self.edit_record_Produccion,
            },
        }

        # Create tabs and frames
        self.frames = {}
        for tab_name, config in self.tab_configs.items():
            self.add(tab_name)
            self.frames[tab_name] = MyFrame(
                master=self.tab(tab_name),
                load_data_func=config["load_func"],
                create_record_func=config.get("create_func"),
                edit_record_func=config.get("edit_func"),
            )
            self.frames[tab_name].pack(fill="both", expand=True)

    def load_data_Desarrollo(self, frame):
        cursor = None
        conn = None
        try:
            conn_str = (
                f"DRIVER={os.getenv('DB1_DRIVER')};"
                f"SERVER={os.getenv('DB1_SERVER')};"
                f"DATABASE={os.getenv('DB1_DATABASE')};"
                f"UID={os.getenv('DB1_UID')};"
                f"PWD={os.getenv('DB1_PWD')}"
            )
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            query = """SELECT
            SIIAPP_Des.N_control
            ,SIIAPP_Des.Fecha_Soli
            ,SIIAPP_Des.N_cotizacion
            ,SIIAPP_Des.PT
            ,SIIAPP_Des.Producto
            ,SIIAPP_Des.Cliente
            ,SIIAPP_Des.Notif_Sanitaria
            FROM dbo.SIIAPP_Des
            """
            cursor.execute(query)
            data = cursor.fetchall()
            headers = [
                "Numero de control",
                "Fecha de solicitud",
                "Numero Cotizacion",
                "PT",
                "Producto",
                "Cliente",
                "Notificacion Sanitaria",
            ]
            frame.sheet.headers(headers)

            # Convert data to list of lists with string values
            formatted_data = [[str(value) if value is not None else "" for value in row] for row in data]
            frame.original_data = formatted_data
            frame.sheet.set_sheet_data(formatted_data)
        except pyodbc.Error as e:
            print(f"An error occurred while loading Desarrollo data: {str(e)}", file=sys.stderr)
            messagebox.showerror(title="Error", message=f"No se pudo cargar los datos: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Placeholder methods for create and edit
    def create_record_Desarrollo(self, frame):
        crear_dialog = ctk.CTkToplevel(self)
        crear_dialog.title("Crear Nuevo Registro - Desarrollo")
        crear_dialog.geometry("400x500")

        # Campos basados en la consulta SELECT
        campos = [
            "Numero de control",
            "Fecha de solicitud (yy-mm-dd)",
            "Numero Cotizacion",
            "PT",
            "Producto",
            "Cliente",
            "Notificacion Sanitaria",
        ]

        # Diccionario para guardar entradas
        entries = {}

        # Crear entradas para cada campo
        for campo in campos:
            frame_campo = ctk.CTkFrame(crear_dialog)
            frame_campo.pack(pady=5, padx=20, fill="x")

            label = ctk.CTkLabel(frame_campo, text=campo, width=150, anchor="w")
            label.pack(side="left", padx=(0, 10))

            entry = ctk.CTkEntry(frame_campo, width=300)
            entry.pack(side="left", expand=True, fill="x")
            entries[campo] = entry

        def guardar():
            """Guardar el nuevo registro"""
            try:
                # Preparar conexión a la base de datos
                conn_str = (
                    f"DRIVER={os.getenv('DB1_DRIVER')};"
                    f"SERVER={os.getenv('DB1_SERVER')};"
                    f"DATABASE={os.getenv('DB1_DATABASE')};"
                    f"UID={os.getenv('DB1_UID')};"
                    f"PWD={os.getenv('DB1_PWD')}"
                )
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()

                # Preparar consulta de inserción
                query = """
                INSERT INTO dbo.SIIAPP_Des (
                    N_control, 
                    Fecha_Soli, 
                    N_cotizacion, 
                    PT, 
                    Producto, 
                    Cliente,
                    Notif_Sanitaria
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """

                # Recoger valores
                valores = [entries[campo].get() for campo in campos]
                valores = [texto.upper() for texto in valores]
                # Ejecutar inserción
                cursor.execute(query, valores)
                conn.commit()

                messagebox.showinfo(title="Éxito", message="Registro creado correctamente")
                crear_dialog.destroy()
                frame.load_data()

            except Exception as e:
                messagebox.showerror(title="Error", message=f"No se pudo crear el registro: {str(e)}", icon="cancel")
            finally:
                if "conn" in locals():
                    conn.close()

        # Botón de guardar
        guardar_btn = ctk.CTkButton(crear_dialog, text="Guardar", command=guardar)
        guardar_btn.pack(pady=20)

    def edit_record_Desarrollo(self, frame):
        try:
            selected_rows = frame.sheet.get_selected_rows()

            if not selected_rows:
                messagebox.showerror(title="Error", message="Seleccione un registro para editar")
                return

            # Get the data of the selected row from filtered or original data
            selected_data = next(iter(selected_rows))
            row_data = frame.sheet.get_row_data(selected_data)
            N_control = row_data[0]  # Assuming N_control is in the first column (index 0)

            if not N_control:
                messagebox.showerror("Error", "No se pudo obtener el N_control del registro seleccionado.")
                logging.error("El N_control es nulo o no válido.")
                return

            logging.info(f"N_control seleccionado: {N_control}")

            # Create edit dialog window
            editar_dialog = ctk.CTkToplevel(frame)
            editar_dialog.title("Editar Registro")
            editar_dialog.geometry("400x500")

            # Fields (excluding N_control)
            campos = ["Numero Cotizacion", "PT", "Producto", "Cliente", "Notificacion Sanitaria"]

            # Dictionary to store entry widgets
            entries = {}
            # Create the scrollable frame
            scrollable_frame = ScrollableFrame(editar_dialog)
            scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)

            # Create a frame for the input fields
            input_frame = ctk.CTkFrame(scrollable_frame)
            input_frame.pack(fill="x", expand=True)
            # Create input fields for each column
            for i, campo in enumerate(campos, start=2):
                field_frame = ctk.CTkFrame(input_frame)
                field_frame.pack(pady=5, padx=20, fill="x")

                label = ctk.CTkLabel(field_frame, text=campo, width=150, anchor="w")
                label.pack(side="left", padx=(0, 10))

                entry = ctk.CTkEntry(field_frame, width=300)
                entry.pack(side="left", expand=True, fill="x")

                # Pre-fill current value from row_data
                valor_actual = row_data[i]
                entry.insert(0, valor_actual)

                entries[campo] = entry

            def actualizar():
                """Update the selected record"""
                try:
                    logging.info(f"Inicio de actualización para N_control: {N_control}")
                    conn_str = (
                        f"DRIVER={os.getenv('DB1_DRIVER')};"
                        f"SERVER={os.getenv('DB1_SERVER')};"
                        f"DATABASE={os.getenv('DB1_DATABASE')};"
                        f"UID={os.getenv('DB1_UID')};"
                        f"PWD={os.getenv('DB1_PWD')}"
                    )
                    conn = pyodbc.connect(conn_str)
                    cursor = conn.cursor()

                    # Prepare update query
                    query = """
                        UPDATE dbo.SIIAPP_Des
                        SET 
                            N_cotizacion = ?, 
                            PT = ?, 
                            Producto = ?, 
                            Cliente = ?,
                            Notif_Sanitaria = ?
                        WHERE N_control = ?
                    """
                    # Collect values
                    valores = [entries[campo].get() for campo in campos] + [N_control]
                    valores = [texto.upper() for texto in valores]

                    # Execute update
                    cursor.execute(query, valores)
                    conn.commit()

                    logging.info(f"Registro {N_control} actualizado exitosamente.")
                    messagebox.showinfo("Éxito", "Registro actualizado correctamente")
                    editar_dialog.destroy()

                    # Refresh data in the frame
                    frame.load_data()

                except Exception as e:
                    logging.error(f"Error al actualizar registro {N_control}: {e}")
                    messagebox.showerror("Error", f"No se pudo actualizar el registro: {str(e)}")
                finally:
                    if "conn" in locals():
                        conn.close()

            # Update button
            actualizar_btn = ctk.CTkButton(input_frame, text="Actualizar", command=actualizar)
            actualizar_btn.pack(pady=20)

        except Exception as e:
            logging.error(f"Error en el proceso de edición: {e}")
            messagebox.showerror("Error", f"Ocurrió un problema al intentar editar el registro: {str(e)}")

    def load_data_Bodega(self, frame):
        cursor = None  # Initialize cursor with None
        conn = None  # Initialize conn with None
        try:
            conn_str = (
                f"DRIVER={os.getenv('DB1_DRIVER')};"
                f"SERVER={os.getenv('DB1_SERVER')};"
                f"DATABASE={os.getenv('DB1_DATABASE')};"
                f"UID={os.getenv('DB1_UID')};"
                f"PWD={os.getenv('DB1_PWD')}"
            )
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            query = """SELECT
                    SIIAPP_Bod.N_Control
                    ,SIIAPP_Des.Fecha_Soli
                    ,SIIAPP_Bod.Bottle_Cod
                    ,SIIAPP_Bod.Envase
                    ,SIIAPP_Bod.Bottle_Sum
                    ,SIIAPP_Bod.Bottle_Color
                    ,SIIAPP_Bod.Bottle_Material
                    ,SIIAPP_Bod.Bottle_ML
                    ,SIIAPP_Bod.Cap_Cod
                    ,SIIAPP_Bod.Tapa
                    ,SIIAPP_Bod.Cap_Sum
                    ,SIIAPP_Bod.Cap_Color
                    ,SIIAPP_Bod.Cap_Material
                    ,SIIAPP_Bod.Foil_Cod
                    ,SIIAPP_Bod.Foil
                    ,SIIAPP_Bod.Foil_Type
                    ,SIIAPP_Bod.FB_Cod
                    ,SIIAPP_Bod.Funda_Banda
                    ,SIIAPP_Bod.Ubicacion_Termoduc
                    ,SIIAPP_Bod.Etiq_Cod
                    ,SIIAPP_Bod.Etiqueta
                    ,SIIAPP_Bod.Box_Cod
                    ,SIIAPP_Bod.Box_Folding
                    ,SIIAPP_Bod.Box_Sum
                    FROM dbo.SIIAPP_Bod
                    INNER JOIN dbo.SIIAPP_Des
                    ON SIIAPP_Bod.N_Control = SIIAPP_Des.N_control
                    """
            cursor.execute(query)
            data = cursor.fetchall()
            headers = [
                "Numero Control",
                "Fecha Solicitud",
                "Codigo Envase",
                "Envase",
                "Suministra Envase",
                "Color Envase",
                "Material Envase",
                "Capacidad Envase",
                "Codigo Tapa",
                "Tapa",
                "Suministra Tapa",
                "Color Tapa",
                "Material Tapa",
                "Codigo Foil",
                "Foil",
                "Tipo Foil",
                "Codigo Banda",
                "Banda",
                "Ubicacion Banda",
                "Codigo Etiqueta",
                "Etiqueta",
                "Codigo Plegadiza",
                "Caja Plegadiza",
                "Suministra Caja",
            ]
            frame.sheet.headers(headers)

            # Convert data to list of lists with string values
            formatted_data = [[str(value) if value is not None else "" for value in row] for row in data]

            frame.original_data = formatted_data
            frame.sheet.set_sheet_data(formatted_data)

        except pyodbc.Error as e:
            print(f"An error occurred while loading Bodega data: {str(e)}", file=sys.stderr)
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Placeholder methods for create and edit
    def create_record_Bodega(self, frame):
        # crear_dialog = ctk.CTkToplevel(self)
        crear_dialog.title("Crear Nuevo Registro - Desarrollo")
        crear_dialog.geometry("400x500")

        # Campos basados en la consulta SELECT
        campos = [
            "N_Control",
            "Bottle_Cod",
            "Envase",
            "Bottle_Sum",
            "Bottle_Color",
            "Bottle_Material",
            "Bottle_ML",
            "Cap_Cod",
            "Tapa",
            "Cap_Sum",
            "Cap_Color",
            "Cap_Material",
            "Foil_Cod",
            "Foil",
            "Foil_Type",
            "FB_Cod",
            "Funda_Banda",
            "Ubicacion_Termoduc",
            "Etiq_Cod",
            "Etiqueta",
            "Box_Cod",
            "Box_Folding",
            "Box_Sum",
        ]

        # Diccionario para guardar entradas
        entries = {}

        # Crear entradas para cada campo
        for campo in campos:
            frame_campo = ctk.CTkFrame(crear_dialog)
            frame_campo.pack(pady=5, padx=20, fill="x")

            label = ctk.CTkLabel(frame_campo, text=campo, width=150, anchor="w")
            label.pack(side="left", padx=(0, 10))

            entry = ctk.CTkEntry(frame_campo, width=300)
            entry.pack(side="left", expand=True, fill="x")
            entries[campo] = entry

        def guardar():
            """Guardar el nuevo registro"""
            try:
                # Preparar conexión a la base de datos
                conn_str = (
                    f"DRIVER={os.getenv('DB1_DRIVER')};"
                    f"SERVER={os.getenv('DB1_SERVER')};"
                    f"DATABASE={os.getenv('DB1_DATABASE')};"
                    f"UID={os.getenv('DB1_UID')};"
                    f"PWD={os.getenv('DB1_PWD')}"
                )
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()

                # SQL Insert statement
                query = """
                INSERT INTO dbo.SIIAPP_Bod (
                    N_Control,
                    Bottle_Cod,
                    Envase,
                    Bottle_Sum,
                    Bottle_Color,
                    Bottle_Material,
                    Bottle_ML,
                    Cap_Cod,
                    Tapa,
                    Cap_Sum,
                    Cap_Color,
                    Cap_Material,
                    Foil_Cod,
                    Foil,
                    Foil_Type,
                    FB_Cod,
                    Funda_Banda,
                    Ubicacion_Termoduc,
                    Etiq_Cod,
                    Etiqueta,
                    Box_Cod,
                    Box_Folding,
                    Box_Sum
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                # Recoger valores
                valores = [entries[campo].get() for campo in campos]

                # Ejecutar inserción
                cursor.execute(query, valores)
                conn.commit()

                messagebox.showinfo(title="Éxito", message="Registro creado correctamente")
                crear_dialog.destroy()
                frame.load_data()

            except Exception as e:
                messagebox.showerror(title="Error", message=f"No se pudo crear el registro: {str(e)}", icon="cancel")
            finally:
                if "conn" in locals():
                    conn.close()

        # Botón de guardar
        guardar_btn = ctk.CTkButton(crear_dialog, text="Guardar", command=guardar)
        guardar_btn.pack(pady=20)

    def edit_record_Bodega(self, frame):
        try:
            selected_rows = frame.sheet.get_selected_rows()

            if not selected_rows:
                messagebox.showerror(title="Error", message="Seleccione un registro para editar")
                return

            # Get the data of the selected row from filtered or original data
            selected_data = next(iter(selected_rows))
            row_data = frame.sheet.get_row_data(selected_data)
            N_control = row_data[0]  # Assuming N_control is in the first column (index 0)

            if not N_control:
                messagebox.showerror("Error", "No se pudo obtener el N_control del registro seleccionado.")
                logging.error("El N_control es nulo o no válido.")
                return

            logging.info(f"N_control seleccionado: {N_control}")

            # Create edit dialog window
            editar_dialog = ctk.CTkToplevel(frame)
            editar_dialog.title("Editar Registro")
            editar_dialog.geometry("400x500")

            # Fields (excluding N_control)
            campos = [
                "Codigo Envase", "Envase", "Suministra Envase", "Color Envase", "Material Envase", "Capacidad Envase",
                "Codigo Tapa", "Tapa", "Suministra Tapa", "Color Tapa", "Material Tapa",
                "Codigo Foil", "Foil", "Tipo Foil",
                "Codigo Banda", "Banda", "Ubicacion Banda",
                "Codigo Etiqueta", "Etiqueta",
                "Codigo Plegadiza", "Caja Plegadiza", "Suministra Caja",
            ]

            # Dictionary to store entry/combobox widgets
            entries = {}

            # Function to fetch item data from database
            def fetch_item_data():
                try:
                    conn_str = (
                        f"DRIVER={os.getenv('DB2_DRIVER')};"
                        f"SERVER={os.getenv('DB2_SERVER')};"
                        f"DATABASE={os.getenv('DB2_DATABASE')};"
                        f"UID={os.getenv('DB2_UID')};"
                        f"PWD={os.getenv('DB2_PWD')}"
                    )
                    conn = pyodbc.connect(conn_str)
                    cursor = conn.cursor()

                    # Query to fetch item codes and descriptions
                    query = """
                    SELECT in_items.itecodigo AS [Codigo item], 
                        in_items.itedesccort AS [Descripcion item] 
                    FROM dbo.in_items 
                    WHERE in_items.itecompania = '01' AND 
                        (in_items.itecodigo LIKE 'ME%')
                    """
                    cursor.execute(query)
                    return cursor.fetchall()
                except Exception as e:
                    logging.error(f"Error fetching item data: {e}")
                    messagebox.showerror("Error", f"No se pudieron cargar los datos de elementos: {str(e)}")
                    return []
                finally:
                    if 'conn' in locals():
                        conn.close()

            # Fetch item data once
            item_data = fetch_item_data()
            item_dict = {row[0]: row[1] for row in item_data}
            item_codes = list(item_dict.keys())

            # Create scrollable frame
            scrollable_frame = ScrollableFrame(editar_dialog)
            scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)

            # Create input frame
            input_frame = ctk.CTkFrame(scrollable_frame)
            input_frame.pack(fill="x", expand=True)
            
            # Fetch item data once
            item_data = fetch_item_data()

            # Create a dictionary for Codigo and Descripcion
            item_dict = {row[0]: row[1] for row in item_data}
            item_codes = list(item_dict.keys())

            # Create a combined list for combobox display
            item_combined_list = [f"{codigo} - {descripcion}" for codigo, descripcion in item_dict.items()]

            # Specific fields to use the combined list
            special_fields = ["Envase", "Tapa", "Foil", "Banda", "Etiqueta", "Caja Plegadiza"]

            # Create input fields for each column
            for i, campo in enumerate(campos, start=2):
                field_frame = ctk.CTkFrame(input_frame)
                field_frame.pack(pady=5, padx=20, fill="x")

                label = ctk.CTkLabel(field_frame, text=campo, width=150, anchor="w")
                label.pack(side="left", padx=(0, 10))

                if campo in special_fields:
                    # Create combobox for special fields
                    combobox = ctk.CTkComboBox(field_frame, width=300, values=item_combined_list)
                    combobox.pack(side="left", expand=True, fill="x")

                    # Pre-fill current value from row_data
                    valor_actual = row_data[i] if i < len(row_data) else ""
                    if valor_actual and valor_actual in item_dict:
                        combobox.set(f"{valor_actual} - {item_dict[valor_actual]}")
                    else:
                        combobox.set("")  # Default to an empty value if no valid value exists

                    # Add filtering functionality
                    def on_combobox_input(event, combobox=combobox):
                        input_text = combobox.get().lower()
                        filtered_values = [
                            f"{codigo} - {descripcion}"
                            for codigo, descripcion in item_dict.items()
                            if input_text in codigo.lower() or input_text in descripcion.lower()
                        ]
                        combobox.configure(values=filtered_values)

                    combobox.bind("<KeyRelease>", on_combobox_input)

                    # Store combobox in entries
                    entries[campo] = combobox

                elif campo.startswith("Codigo"):
                    # Create combobox for Codigo fields
                    combobox = ctk.CTkComboBox(field_frame, width=300, values=item_codes)
                    combobox.pack(side="left", expand=True, fill="x")

                    # Pre-fill current value from row_data
                    valor_actual = row_data[i] if i < len(row_data) else ""
                    if valor_actual and valor_actual in item_codes:
                        combobox.set(valor_actual)
                    else:
                        combobox.set("")  # Default to an empty value if no valid value exists

                    # Store combobox in entries
                    entries[campo] = combobox

                else:
                    # Regular entry for non-Codigo and non-special fields
                    entry = ctk.CTkEntry(field_frame, width=300)
                    entry.pack(side="left", expand=True, fill="x")

                    # Pre-fill current value from row_data
                    valor_actual = row_data[i] if i < len(row_data) else ""
                    entry.insert(0, valor_actual)

                    entries[campo] = entry

            def actualizar():
                """Update the selected record"""
                try:
                    logging.info(f"Inicio de actualización para N_control: {N_control}")
                    conn_str = (
                        f"DRIVER={os.getenv('DB1_DRIVER')};"
                        f"SERVER={os.getenv('DB1_SERVER')};"
                        f"DATABASE={os.getenv('DB1_DATABASE')};"
                        f"UID={os.getenv('DB1_UID')};"
                        f"PWD={os.getenv('DB1_PWD')}"
                    )
                    conn = pyodbc.connect(conn_str)
                    cursor = conn.cursor()

                    # Prepare update query (same as before)
                    query = """
                    UPDATE dbo.SIIAPP_Bod SET
                        Bottle_Cod = ?,
                        Envase = ?,
                        Bottle_Sum = ?,
                        Bottle_Color = ?,
                        Bottle_Material = ?,
                        Bottle_ML = ?,
                        Cap_Cod = ?,
                        Tapa = ?,
                        Cap_Sum = ?,
                        Cap_Color = ?,
                        Cap_Material = ?,
                        Foil_Cod = ?,
                        Foil = ?,
                        Foil_Type = ?,
                        FB_Cod = ?,
                        Funda_Banda = ?,
                        Ubicacion_Termoduc = ?,
                        Etiq_Cod = ?,
                        Etiqueta = ?,
                        Box_Cod = ?,
                        Box_Folding = ?,
                        Box_Sum = ?
                    WHERE N_Control = ?
                    """
                    # Ensure the order of fields matches the database columns
                    ordered_campos = [
                        "Codigo Envase", "Envase", "Suministra Envase", "Color Envase", "Material Envase", "Capacidad Envase",
                        "Codigo Tapa", "Tapa", "Suministra Tapa", "Color Tapa", "Material Tapa",
                        "Codigo Foil", "Foil", "Tipo Foil",
                        "Codigo Banda", "Banda", "Ubicacion Banda",
                        "Codigo Etiqueta", "Etiqueta",
                        "Codigo Plegadiza", "Caja Plegadiza", "Suministra Caja"
                    ]

                    # Collect values in the correct order
                    valores = []
                    for campo in ordered_campos:
                        if campo in entries:
                            valores.append(entries[campo].get())
                        else:
                            valores.append("")  # Default to empty string if the field is not present

                    valores.append(N_control)  # Add N_control at the end
                    valores = [texto.upper() for texto in valores]  # Convert all values to uppercase

                    # Execute update query
                    cursor.execute(query, valores)
                    conn.commit()

                    logging.info(f"Registro {N_control} actualizado exitosamente.")
                    messagebox.showinfo("Éxito", "Registro actualizado correctamente")
                    editar_dialog.destroy()

                    # Refresh data in the frame
                    frame.load_data()

                except Exception as e:
                    logging.error(f"Error al actualizar registro {N_control}: {e}")
                    messagebox.showerror("Error", f"No se pudo actualizar el registro: {str(e)}")
                finally:
                    if "conn" in locals():
                        conn.close()

            # Update button
            actualizar_btn = ctk.CTkButton(input_frame, text="Actualizar", command=actualizar)
            actualizar_btn.pack(pady=20)

        except Exception as e:
            logging.error(f"Error en el proceso de edición: {e}")
            messagebox.showerror("Error", f"Ocurrió un problema al intentar editar el registro: {str(e)}")

    def load_data_Calidad(self, frame):
        cursor = None
        conn = None
        try:
            conn_str = (
                f"DRIVER={os.getenv('DB1_DRIVER')};"
                f"SERVER={os.getenv('DB1_SERVER')};"
                f"DATABASE={os.getenv('DB1_DATABASE')};"
                f"UID={os.getenv('DB1_UID')};"
                f"PWD={os.getenv('DB1_PWD')}"
            )
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            query = """SELECT
            SIIAPP_Cal.N_Control
            ,SIIAPP_Des.Fecha_Soli
            ,SIIAPP_Cal.Mesofilos
            ,SIIAPP_Cal.E_Coli
            ,SIIAPP_Cal.S_Aureus
            ,SIIAPP_Cal.P_Aureoginosa
            ,SIIAPP_Cal.Moho_Levadura
            ,SIIAPP_Cal.Micro_Obs
            ,SIIAPP_Cal.Cumple_Microbiologia
            ,SIIAPP_Cal.Densidad
            ,SIIAPP_Cal.Ph
            ,SIIAPP_Cal.Contenido
            ,SIIAPP_Cal.Color
            ,SIIAPP_Cal.Textura
            ,SIIAPP_Cal.Olor
            ,SIIAPP_Cal.Viscosidad
            ,SIIAPP_Cal.Rpm
            ,SIIAPP_Cal.Aguja
            ,SIIAPP_Cal.Torque
            ,SIIAPP_Cal.Apt_Container
            ,SIIAPP_Cal.Cont_Obs
            ,SIIAPP_Cal.Diligenciado
            FROM dbo.SIIAPP_Cal
            INNER JOIN dbo.SIIAPP_Des
            ON SIIAPP_Cal.N_Control = SIIAPP_Des.N_control
            """
            cursor.execute(query)
            data = cursor.fetchall()
            headers = [
                "Numero Control",
                "Fecha Solicitud",
                "Mesofilos",
                "E Coli",
                "S Aureus",
                "P Aureoginosa",
                "Moho y Levaduras",
                "Observaciones Microbiologia",
                "Cumple Microbiologia",
                "Densidad",
                "Ph",
                "Contenido",
                "Color",
                "Textura",
                "Olor",
                "Viscosidad",
                "Rpm",
                "Aguja",
                "Torque",
                "Apto para Contenedor",
                "Observaciones",
                "Diligenciado",
            ]
            frame.sheet.headers(headers)

            # Convert data to list of lists with string values
            formatted_data = [[str(value) if value is not None else "" for value in row] for row in data]

            frame.original_data = formatted_data
            frame.sheet.set_sheet_data(formatted_data)

        except pyodbc.Error as e:
            print(f"An error occurred while loading Calidad data: {str(e)}", file=sys.stderr)
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Placeholder methods for create and edit
    def create_record_Calidad(self, frame):
        # crear_dialog = ctk.CTkToplevel(self)
        crear_dialog.title("Crear Nuevo Registro - Desarrollo")
        crear_dialog.geometry("400x500")

        # Campos basados en la consulta SELECT
        campos = [
            "N_Control",
            "Mesofilos",
            "E_Coli",
            "S_Aureus",
            "P_Aureoginosa",
            "Moho_Levadura",
            "Micro_Obs",
            "Cumple_Microbiologia",
            "Densidad",
            "Ph",
            "Contenido",
            "Color",
            "Textura",
            "Olor",
            "Viscosidad",
            "Rpm",
            "Aguja",
            "Torque",
            "Apt_Container",
            "Cont_Obs",
            "Diligenciado",
        ]

        # Diccionario para guardar entradas
        entries = {}

        # Crear entradas para cada campo
        for campo in campos:
            frame_campo = ctk.CTkFrame(crear_dialog)
            frame_campo.pack(pady=5, padx=20, fill="x")

            label = ctk.CTkLabel(frame_campo, text=campo, width=150, anchor="w")
            label.pack(side="left", padx=(0, 10))

            entry = ctk.CTkEntry(frame_campo, width=300)
            entry.pack(side="left", expand=True, fill="x")
            entries[campo] = entry

        def guardar():
            """Guardar el nuevo registro"""
            try:
                # Preparar conexión a la base de datos
                conn_str = (
                    f"DRIVER={os.getenv('DB1_DRIVER')};"
                    f"SERVER={os.getenv('DB1_SERVER')};"
                    f"DATABASE={os.getenv('DB1_DATABASE')};"
                    f"UID={os.getenv('DB1_UID')};"
                    f"PWD={os.getenv('DB1_PWD')}"
                )
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()

                # SQL Insert statement
                query = """
                INSERT INTO dbo.SIIAPP_Cal (
                    N_Control,
                    Mesofilos,
                    E_Coli,
                    S_Aureus,
                    P_Aureoginosa,
                    Moho_Levadura,
                    Micro_Obs,
                    Cumple_Microbiologia,
                    Densidad,
                    Ph,
                    Contenido,
                    Color,
                    Textura,
                    Olor,
                    Viscosidad,
                    Rpm,
                    Aguja,
                    Torque,
                    Apt_Container,
                    Cont_Obs,
                    Diligenciado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """

                # Recoger valores
                valores = [entries[campo].get() for campo in campos]

                # Ejecutar inserción
                cursor.execute(query, valores)
                conn.commit()

                messagebox.showinfo(title="Éxito", message="Registro creado correctamente")
                crear_dialog.destroy()
                frame.load_data()

            except Exception as e:
                messagebox.showerror(title="Error", message=f"No se pudo crear el registro: {str(e)}", icon="cancel")
            finally:
                if "conn" in locals():
                    conn.close()

        # Botón de guardar
        guardar_btn = ctk.CTkButton(crear_dialog, text="Guardar", command=guardar)
        guardar_btn.pack(pady=20)

    def edit_record_Calidad(self, frame):
        try:
            selected_rows = frame.sheet.get_selected_rows()

            if not selected_rows:
                messagebox.showerror(title="Error", message="Seleccione un registro para editar")
                return

            # Get the data of the selected row from filtered or original data
            selected_data = next(iter(selected_rows))
            row_data = frame.sheet.get_row_data(selected_data)
            N_control = row_data[0]  # Assuming N_control is in the first column (index 0)

            if not N_control:
                messagebox.showerror("Error", "No se pudo obtener el N_control del registro seleccionado.")
                logging.error("El N_control es nulo o no válido.")
                return

            logging.info(f"N_control seleccionado: {N_control}")

            # Create edit dialog window
            editar_dialog = ctk.CTkToplevel(frame)
            editar_dialog.title("Editar Registro")
            editar_dialog.geometry("400x500")

            # Fields (excluding N_control)
            campos = [
                "Mesofilos",
                "E Coli",
                "S Aureus",
                "P Aureoginosa",
                "Moho y Levaduras",
                "Observaciones Microbiologia",
                "Cumple Microbiologia",
                "Densidad",
                "Ph",
                "Contenido",
                "Color",
                "Textura",
                "Olor",
                "Viscosidad",
                "Rpm",
                "Aguja",
                "Torque",
                "Apto para Contenedor",
                "Observaciones",
                "Diligenciado",
            ]

            # Dictionary to store entry widgets
            entries = {}

            # Your existing code for creating input fields
            # Create the scrollable frame
            scrollable_frame = ScrollableFrame(editar_dialog)
            scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)

            # Create a frame for the input fields
            input_frame = ctk.CTkFrame(scrollable_frame)
            input_frame.pack(fill="x", expand=True)
            # Create input fields for each column
            for i, campo in enumerate(campos, start=2):
                field_frame = ctk.CTkFrame(input_frame)
                field_frame.pack(pady=5, padx=20, fill="x")

                label = ctk.CTkLabel(field_frame, text=campo, width=150, anchor="w")
                label.pack(side="left", padx=(0, 10))

                entry = ctk.CTkEntry(field_frame, width=300)
                entry.pack(side="left", expand=True, fill="x")

                # Pre-fill current value from row_data
                valor_actual = row_data[i]
                entry.insert(0, valor_actual)

                entries[campo] = entry

            def actualizar():
                """Update the selected record"""
                try:
                    logging.info(f"Inicio de actualización para N_control: {N_control}")
                    conn_str = (
                        f"DRIVER={os.getenv('DB1_DRIVER')};"
                        f"SERVER={os.getenv('DB1_SERVER')};"
                        f"DATABASE={os.getenv('DB1_DATABASE')};"
                        f"UID={os.getenv('DB1_UID')};"
                        f"PWD={os.getenv('DB1_PWD')}"
                    )
                    conn = pyodbc.connect(conn_str)
                    cursor = conn.cursor()

                    # Prepare update query
                    query = """
                    UPDATE dbo.SIIAPP_Cal SET
                        Mesofilos = ?,
                        E_Coli = ?,
                        S_Aureus = ?,
                        P_Aureoginosa = ?,
                        Moho_Levadura = ?,
                        Micro_Obs = ?,
                        Cumple_Microbiologia = ?,
                        Densidad = ?,
                        Ph = ?,
                        Contenido = ?,
                        Color = ?,
                        Textura = ?,
                        Olor = ?,
                        Viscosidad = ?,
                        Rpm = ?,
                        Aguja = ?,
                        Torque = ?,
                        Apt_Container = ?,
                        Cont_Obs = ?,
                        Diligenciado = ?
                    WHERE N_Control = ?;
                    """
                    # Collect values
                    valores = [entries[campo].get() for campo in campos] + [N_control]
                    valores = [texto.upper() for texto in valores]

                    # Execute update
                    cursor.execute(query, valores)
                    conn.commit()

                    logging.info(f"Registro {N_control} actualizado exitosamente.")
                    messagebox.showinfo("Éxito", "Registro actualizado correctamente")
                    editar_dialog.destroy()

                    # Refresh data in the frame
                    frame.load_data()

                except Exception as e:
                    logging.error(f"Error al actualizar registro {N_control}: {e}")
                    messagebox.showerror("Error", f"No se pudo actualizar el registro: {str(e)}")
                finally:
                    if "conn" in locals():
                        conn.close()

            # Update button
            actualizar_btn = ctk.CTkButton(input_frame, text="Actualizar", command=actualizar)
            actualizar_btn.pack(pady=20)

        except Exception as e:
            logging.error(f"Error en el proceso de edición: {e}")
            messagebox.showerror("Error", f"Ocurrió un problema al intentar editar el registro: {str(e)}")

    def load_data_Produccion(self, frame):
        cursor = None
        conn = None
        try:
            conn_str = (
                f"DRIVER={os.getenv('DB1_DRIVER')};"
                f"SERVER={os.getenv('DB1_SERVER')};"
                f"DATABASE={os.getenv('DB1_DATABASE')};"
                f"UID={os.getenv('DB1_UID')};"
                f"PWD={os.getenv('DB1_PWD')}"
            )
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            query = """SELECT
            SIIAPP_Prod.N_Control
            ,SIIAPP_Des.Fecha_Soli
            ,SIIAPP_Prod.Cod_Caja
            ,SIIAPP_Prod.Caja_Embalaje
            ,SIIAPP_Prod.FB_Dimensiones_Adec
            ,SIIAPP_Prod.FB_Tunel_Temp
            ,SIIAPP_Prod.FB_Tunel_Speed
            ,SIIAPP_Prod.FB_Test_Tool
            ,SIIAPP_Prod.FB_obs
            ,SIIAPP_Prod.SCE_Temp
            ,SIIAPP_Prod.SCE_Temp_Time
            ,SIIAPP_Prod.SCE_Obs
            ,SIIAPP_Prod.SCE_Hermt
            ,SIIAPP_Prod.Ubi_Lote
            ,SIIAPP_Prod.Etiqueta_Manual
            ,SIIAPP_Prod.Diligenciado
            FROM dbo.SIIAPP_Prod
            INNER JOIN dbo.SIIAPP_Des
            ON SIIAPP_Prod.N_Control = SIIAPP_Des.N_control
            """
            cursor.execute(query)
            data = cursor.fetchall()
            headers = [
                "Numero Control",
                "Fecha Solicitud",
                "Codigo Caja",
                "Caja Embalaje",
                "Banda Dimensiones",
                "Banda Temperatura Tunel",
                "Banda Velocidad Tunel",
                "Herramienta Usada para Prueba",
                "Observaciones Funda",
                "Temperatura Sellado Colapsible",
                "Tiempo de Calentamiento",
                "Observaciones Sellado",
                "Hermeticidad",
                "Ubicacion Lote",
                "Etiqueta Manual",
                "Diligenciado",
            ]
            frame.sheet.headers(headers)

            # Convert data to list of lists with string values
            formatted_data = [[str(value) if value is not None else "" for value in row] for row in data]

            frame.original_data = formatted_data
            frame.sheet.set_sheet_data(formatted_data)

        except pyodbc.Error as e:
            print(f"An error occurred while loading Produccion data: {str(e)}", file=sys.stderr)
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Placeholder methods for create and edit
    def create_record_Produccion(self, frame):
        #  crear_dialog = ctk.CTkToplevel(self)
        crear_dialog.title("Crear Nuevo Registro - Desarrollo")
        crear_dialog.geometry("400x500")

        # Campos basados en la consulta SELECT
        campos = [
            "N_Control",
            "Cod_Caja",
            "Caja_Embalaje",
            "FB_Dimensiones_Adec",
            "FB_Tunel_Temp",
            "FB_Tunel_Speed",
            "FB_Test_Tool",
            "FB_obs",
            "SCE_Temp",
            "SCE_Temp_Time",
            "SCE_Obs",
            "SCE_Hermt",
            "Ubi_Lote",
            "Etiqueta_Manual",
            "Diligenciado",
        ]

        # Diccionario para guardar entradas
        entries = {}

        # Crear entradas para cada campo
        for campo in campos:
            frame_campo = ctk.CTkFrame(crear_dialog)
            frame_campo.pack(pady=5, padx=20, fill="x")

            label = ctk.CTkLabel(frame_campo, text=campo, width=150, anchor="w")
            label.pack(side="left", padx=(0, 10))

            entry = ctk.CTkEntry(frame_campo, width=300)
            entry.pack(side="left", expand=True, fill="x")
            entries[campo] = entry

        def guardar():
            """Guardar el nuevo registro"""
            try:
                # Preparar conexión a la base de datos
                conn_str = (
                    f"DRIVER={os.getenv('DB1_DRIVER')};"
                    f"SERVER={os.getenv('DB1_SERVER')};"
                    f"DATABASE={os.getenv('DB1_DATABASE')};"
                    f"UID={os.getenv('DB1_UID')};"
                    f"PWD={os.getenv('DB1_PWD')}"
                )
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()

                # Preparar consulta de inserción
                query = """
                INSERT INTO dbo.SIIAPP_Prod (
                N_Control,
                Cod_Caja,
                Caja_Embalaje,
                FB_Dimensiones_Adec,
                FB_Tunel_Temp,
                FB_Tunel_Speed,
                FB_Test_Tool,
                FB_obs,
                SCE_Temp,
                SCE_Temp_Time,
                SCE_Obs,
                SCE_Hermt,
                Ubi_Lote,
                Etiqueta_Manual,
                Diligenciado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """

                # Recoger valores
                valores = [entries[campo].get() for campo in campos]

                # Ejecutar inserción
                cursor.execute(query, valores)
                conn.commit()

                messagebox.showinfo(title="Éxito", message="Registro creado correctamente")
                crear_dialog.destroy()
                frame.load_data()

            except Exception as e:
                messagebox.showerror(title="Error", message=f"No se pudo crear el registro: {str(e)}", icon="cancel")
            finally:
                if "conn" in locals():
                    conn.close()

        # Botón de guardar
        guardar_btn = ctk.CTkButton(crear_dialog, text="Guardar", command=guardar)
        guardar_btn.pack(pady=20)

    def edit_record_Produccion(self, frame):
        try:
            selected_rows = frame.sheet.get_selected_rows()

            if not selected_rows:
                messagebox.showerror(title="Error", message="Seleccione un registro para editar")
                return

            # Get the data of the selected row from filtered or original data
            selected_data = next(iter(selected_rows))
            row_data = frame.sheet.get_row_data(selected_data)
            N_control = row_data[0]  # Assuming N_control is in the first column (index 0)

            if not N_control:
                messagebox.showerror("Error", "No se pudo obtener el N_control del registro seleccionado.")
                logging.error("El N_control es nulo o no válido.")
                return

            logging.info(f"N_control seleccionado: {N_control}")

            # Create edit dialog window
            editar_dialog = ctk.CTkToplevel(frame)
            editar_dialog.title("Editar Registro")
            editar_dialog.geometry("400x500")

            # Fields (excluding N_control)
            campos = [
                "Codigo Caja",
                "Caja Embalaje",
                "Banda Dimensiones",
                "Banda Temperatura Tunel",
                "Banda Velocidad Tunel",
                "Herramienta Usada para Prueba",
                "Observaciones Funda",
                "Temperatura Sellado Colapsible",
                "Tiempo de Calentamiento",
                "Observaciones Sellado",
                "Hermeticidad",
                "Ubicacion Lote",
                "Etiqueta Manual",
                "Diligenciado",
            ]

            # Dictionary to store entry widgets
            entries = {}
            # Create the scrollable frame
            scrollable_frame = ScrollableFrame(editar_dialog)
            scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)

            # Create a frame for the input fields
            input_frame = ctk.CTkFrame(scrollable_frame)
            input_frame.pack(fill="x", expand=True)
            # Create input fields for each column
            for i, campo in enumerate(campos, start=2):
                field_frame = ctk.CTkFrame(input_frame)
                field_frame.pack(pady=5, padx=20, fill="x")

                label = ctk.CTkLabel(field_frame, text=campo, width=150, anchor="w")
                label.pack(side="left", padx=(0, 10))

                entry = ctk.CTkEntry(field_frame, width=300)
                entry.pack(side="left", expand=True, fill="x")

                # Pre-fill current value from row_data
                valor_actual = row_data[i]
                entry.insert(0, valor_actual)

                entries[campo] = entry

            def actualizar():
                """Update the selected record"""
                try:
                    logging.info(f"Inicio de actualización para N_control: {N_control}")
                    conn_str = (
                        f"DRIVER={os.getenv('DB1_DRIVER')};"
                        f"SERVER={os.getenv('DB1_SERVER')};"
                        f"DATABASE={os.getenv('DB1_DATABASE')};"
                        f"UID={os.getenv('DB1_UID')};"
                        f"PWD={os.getenv('DB1_PWD')}"
                    )
                    conn = pyodbc.connect(conn_str)
                    cursor = conn.cursor()

                    # Prepare update query
                    query = """
                        UPDATE dbo.SIIAPP_Prod SET
                        Cod_Caja = ?,
                        Caja_Embalaje = ?,
                        FB_Dimensiones_Adec = ?,
                        FB_Tunel_Temp = ?,
                        FB_Tunel_Speed = ?,
                        FB_Test_Tool = ?,
                        FB_obs = ?,
                        SCE_Temp = ?,
                        SCE_Temp_Time = ?,
                        SCE_Obs = ?,
                        SCE_Hermt = ?,
                        Ubi_Lote = ?,
                        Etiqueta_Manual = ?,
                        Diligenciado = ?
                    WHERE N_Control = ?;
                    """
                    # Collect values
                    valores = [entries[campo].get() for campo in campos] + [N_control]
                    valores = [texto.upper() for texto in valores]

                    # Execute update
                    cursor.execute(query, valores)
                    conn.commit()

                    logging.info(f"Registro {N_control} actualizado exitosamente.")
                    messagebox.showinfo("Éxito", "Registro actualizado correctamente")
                    editar_dialog.destroy()

                    # Refresh data in the frame
                    frame.load_data()

                except Exception as e:
                    logging.error(f"Error al actualizar registro {N_control}: {e}")
                    messagebox.showerror("Error", f"No se pudo actualizar el registro: {str(e)}")
                finally:
                    if "conn" in locals():
                        conn.close()

            # Update button
            actualizar_btn = ctk.CTkButton(input_frame, text="Actualizar", command=actualizar)
            actualizar_btn.pack(pady=20)

        except Exception as e:
            logging.error(f"Error en el proceso de edición: {e}")
            messagebox.showerror("Error", f"Ocurrió un problema al intentar editar el registro: {str(e)}")


class ScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)


class MyFrame(ctk.CTkFrame):
    def __init__(self, master, load_data_func, create_record_func=None, edit_record_func=None, **kwargs):
        super().__init__(master, **kwargs)

        # Store data management functions
        self.load_data_func = load_data_func
        self.create_record_func = create_record_func
        self.edit_record_func = edit_record_func

        # Original and filtered data storage
        self.original_data = []
        self.filtered_data = []

        # Create sheet
        self.sheet = Sheet(self)
        self.sheet.pack(fill="both", expand=True)

        # Enable row selection
        self.sheet.enable_bindings(
            (
                "single_select",
                "row_select",
                "arrowkeys",
                "column_width_resize",
                "row_width_resize",
                "double_click_row_resize",
                "column_select",
            )
        )

        # Create buttons
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(fill="x", padx=10, pady=5)

        self.create_record_button = ctk.CTkButton(
            self.button_frame, text="Crear Registro", command=self.handle_create_record
        )
        self.create_record_button.pack(side="left", padx=5)

        self.edit_record_button = ctk.CTkButton(
            self.button_frame, text="Editar Registro", command=self.handle_edit_record
        )
        self.edit_record_button.pack(side="left", padx=5)

        self.reload_button = ctk.CTkButton(self.button_frame, text="Refrescar", command=self.reload_data)
        self.reload_button.pack(side="left", padx=5)

        # Initial data load
        self.load_data()

    def handle_create_record(self):
        """Handle record creation with custom function"""
        if self.create_record_func:
            self.create_record_func(self)
        else:
            self.show_default_create_dialog()

    def handle_edit_record(self):
        """Handle record editing with custom function"""

        if self.edit_record_func:
            self.edit_record_func(self)
        else:
            self.show_default_edit_dialog()

    def show_default_create_dialog(self):
        """Default create record dialog"""
        create_window = ctk.CTkToplevel(self)
        create_window.title("Crear Nuevo Registro")
        create_window.geometry("400x300")

    def show_default_edit_dialog(self, record_data):
        """Default edit record dialog"""
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Editar Registro")
        edit_window.geometry("400x300")

    def reload_data(self):
        # Clear existing data
        self.sheet.set_sheet_data([])

        # Load updated data from the database
        self.load_data()

    def load_data(self):
        """Initial data loading"""
        self.load_data_func(self)

    def filter_data(self, event):
        search_text = self.filter_entry.get().lower()
        if search_text:
            self.filtered_data = [
                row
                for row in self.original_data
                if search_text in str(row[1]).lower() or  # Search by "# OP"
                # Search by "CODIGO ITEM"
                search_text in str(row[2]).lower() or
                # Search by "NIT PROVEEDOR"
                search_text in str(row[4]).lower() or
                # Search by "DESCRIPCION ITEM"
                search_text in str(row[3]).lower() or
                # Search by "DESCRIPCION PROVEEDOR"
                search_text in str(row[5]).lower()
            ]
            self.sheet.set_sheet_data(self.filtered_data)
            # Update column widths after filtering
            for i, width in enumerate(self.column_widths):
                if all(row[i] == "" for row in self.filtered_data):
                    self.sheet.column_width(column=i, width=0)
                else:
                    self.sheet.column_width(column=i, width=width)
        else:
            self.filtered_data = self.original_data
            self.sheet.set_sheet_data(self.filtered_data)
            # Update column widths after filtering
            for i, width in enumerate(self.column_widths):
                if all(row[i] == "" for row in self.filtered_data):
                    self.sheet.column_width(column=i, width=0)
                else:
                    self.sheet.column_width(column=i, width=width)

    def reload_data(self):
        # Clear existing data
        self.sheet.set_sheet_data([])

        # Load updated data from the database
        self.load_data()


class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.username_entry = ctk.CTkEntry(self, placeholder_text="Nombre de usuario")
        self.username_entry.pack(pady=10)
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*")
        self.password_entry.pack(pady=10)
        self.remember_var = tk.BooleanVar()  # Variable to track the checkbox state
        self.remember_checkbox = ctk.CTkCheckBox(self, text="Recordar mis credenciales", variable=self.remember_var)
        self.remember_checkbox.pack(pady=5)
        self.login_button = ctk.CTkButton(self, text="Login", command=self.authenticate)
        self.login_button.pack(pady=10)

        self.user_access = None
        # Load saved credentials if available
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

        if authenticate_user(username, password):
            messagebox.showinfo("Login Exitoso", "Bienvenido!")
            self.save_credentials()  # Save credentials before showing the app frame
            self.master.show_app_frame(self.user_access)
        else:
            messagebox.showerror("Login Fallido", "Credenciales invalidas o acceso denegado.")


def get_user_access(user_groups):
    """
    Determine the user's access configuration based on group memberships.
    """
    try:
        access_config = json.loads(os.getenv("ACCESS_CONFIG"))
    except json.JSONDecodeError:
        logging.error("Invalid JSON format in ACCESS_CONFIG environment variable.")
        return None

    # Match user groups with those in ACCESS_CONFIG
    for group, config in access_config.items():
        if any(group in user_group for user_group in user_groups):
            logging.info(f"Access granted based on group: {group}")
            return config

    logging.warning("No matching group found in ACCESS_CONFIG.")
    return None


def authenticate_user(username, password):
    server = Server(os.getenv("AD_SERVER"), get_info=ALL)
    user = f'{os.getenv("AD_DOMAIN")}\\{username}'

    try:
        # Attempt LDAP bind with provided credentials
        conn = Connection(server, user=user, password=password, authentication="NTLM", auto_bind=True)
        logging.info(f"LDAP bind successful for {username}.")

        # Search base for LDAP
        search_base = f"DC={os.getenv('AD_DOMAIN').replace('.', ',DC=')}"

        # Check if user is in allowed users
        allowed_users = os.getenv("ALLOWED_USERS").split(",")
        if username in allowed_users:
            return True

        # Search for the user's DN and group memberships
        conn.search(search_base, f"(sAMAccountName={username})", attributes=["distinguishedName", "memberOf"])

        if not conn.entries:
            logging.warning(f"User {username} not found in LDAP search.")
            return False

        # Retrieve user's group memberships
        user_groups = conn.entries[0].memberOf.values if conn.entries[0].memberOf else []

        # Determine access based on group memberships
        user_access = get_user_access(user_groups)
        if user_access:
            return user_access

        logging.warning(f"Access denied for {username}. No matching group configuration.")
        return False

    except Exception as e:
        logging.error(f"LDAP error for {username}: {e}")
        return False


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1000x600")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.login_frame = LoginFrame(master=self)
        self.login_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

    def show_app_frame(self, user_access):
        # Replace the login frame with the main app frame
        self.login_frame.destroy()
        self.geometry("1000x600")
        self.my_frame = MyTabView(master=self)
        self.my_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Disable tabs and set active tab based on access configuration
        if user_access:
            # Disable tabs
            if "disabled_tabs" in user_access:
                logging.info(f"Disabling tabs: {user_access['disabled_tabs']}")
                for tab in user_access["disabled_tabs"]:
                    if tab in self.my_frame._segmented_button._buttons_dict:
                        self.my_frame._segmented_button._buttons_dict[tab].configure(state=ctk.DISABLED)
                    else:
                        logging.warning(f"Tab '{tab}' not found in segmented button dictionary.")

            # Set active tab
            if "active_tab" in user_access:
                active_tab = user_access.get("active_tab")
                if active_tab and active_tab in self.my_frame.tab_configs:
                    # For your custom TabView, use .set() method
                    self.my_frame.set(active_tab)
                    logging.info(f"Set active tab to: {active_tab}")
                else:
                    logging.warning(f"Could not set active tab: {active_tab}")
app = App()
app.title("Checklist Aprobaciones")
app.mainloop()