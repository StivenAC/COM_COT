import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import openpyxl.workbook
import pyodbc
from tksheet import Sheet
import sys
import os
import json
from dotenv import load_dotenv
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
from cryptography.fernet import Fernet, InvalidToken
import logging
import modules.gui_frame as gf
import modules.extra_functions as ef
import modules.f_combobox as f_combobox
import modules.login as lg
import modules.query as qry
from datetime import datetime as dt
from datetime import timedelta
import modules.holiday as hd
import openpyxl
from pathlib import Path


if hasattr(sys, "_MEIPASS"):
    icon_path = os.path.join(sys._MEIPASS, "Assets", "icon_2.ico")
    theme_path = os.path.join(sys._MEIPASS, "themes", "red.json")
else:
    icon_path = os.path.join(os.path.dirname(__file__), "Assets", "icon_2.ico")
    theme_path = os.path.join(os.path.dirname(__file__), "themes", "red.json")

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme(theme_path)

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

class MyTabView(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Tab configurations
        self.tab_configs = {
            "Costo Comercial": {
                "load_func": self.load_data_Cotizacion,
                "create_func": self.create_record_Cotizacion,
                "edit_func": self.edit_record_Cotizacion,
                "export_func": self.export_data_cot,
            },  
          #  "Proyectos": {
           #     "load_func": self.load_data_Proyectos,
            #    "create_func": self.create_record_Proyectos,
             #  "edit_func": self.edit_record_Proyectos,
         #   },  
        }
        # Create tabs and frames
        self.frames = {}
        for tab_name, config in self.tab_configs.items():
            self.add(tab_name)
            self.frames[tab_name] = gf.MyFrame(
                master=self.tab(tab_name),
                load_data_func=config["load_func"],
                create_record_func=config.get("create_func"),
                edit_record_func=config.get("edit_func"),
                export_data_func=config.get("export_func")
            )
            self.frames[tab_name].pack(fill="both", expand=True)
    def load_data_Cotizacion(self, frame):
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
            
            cursor.execute("SELECT ID, DATE_REP, TRANS_STATE,COT_STATE,DELIV_DAYS FROM SIIAPP.dbo.COM_Cot WHERE DATE_REP IS NOT NULL")
            rows = cursor.fetchall()

            id_list = []
            diferencia_dias_list = []

            fecha_actual = dt.now()

            for row in rows:
                id_valor = row[0]
                fecha_campo1 = row[1]
                estado_actual = row[2]
                enviado=row[3]
 
                if fecha_campo1 is not None:  #
                    diferencia_dias = (fecha_actual - fecha_campo1).days
                else:
                    diferencia_dias = None
                dias_a_restar = 0
                for i in range(diferencia_dias + 1):
                    fecha_iterada = fecha_campo1 + timedelta(days=i)
                    if fecha_iterada.strftime("%Y-%m-%d") in hd.fechas_especiales:
                        dias_a_restar += 1
                
                # Ajustar la diferencia de días
                diferencia_dias -= dias_a_restar
               
                diferencia_dias_list.append(diferencia_dias)
                if estado_actual == "CERRADO":
                    continue
                else:
                    if diferencia_dias is not None and diferencia_dias > 3:
                        cursor.execute("""
                            UPDATE SIIAPP.dbo.COM_Cot 
                            SET TRANS_STATE = ? 
                            WHERE ID = ?
                        """, ("ATRASADO", id_valor))

                    if enviado=="ANULADA":
                        cursor.execute("""
                            UPDATE SIIAPP.dbo.COM_Cot 
                            SET TRANS_STATE = ?
                            WHERE ID = ?
                        """, ("CERRADO",id_valor))

                    if enviado =="ENVIADO AL COMERCIAL" :
                     cursor.execute("""
                            UPDATE SIIAPP.dbo.COM_Cot 
                            SET TRANS_STATE = ?,
                            DATE_DELIV = ?,
                            DELIV_DAYS=?
                            WHERE ID = ?
                        """, ("CERRADO", fecha_actual, diferencia_dias,id_valor))
                        
            conn.commit()
            cursor.execute(qry.load_query_des)
            
            data = cursor.fetchall()

            headers = [
                "Numero de Registro",
                "Fecha de Recepcion",
                "Mes de recepcion",
                "Numero Cotizacion",
                "Prioridad",
                "Nombre Cliente",
                "Marca",
                "Comercial Responsable",
                "Elaborado Por",
                "Relacion",
                "Cantidad Productos",
                "Compañia",
                "Estado Transitorio Cotizacion",
                "Estado Cotizacion",
                "Fecha de Entrega",
                "Tiempo de Entrega (dias)",
                "Fecha Envio Cliente",
                "Respuesta Cliente",
                "Observacion",
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
    def create_record_Cotizacion(self, frame):
        crear_dialog = ctk.CTkToplevel(self)
        crear_dialog.title("Crear Nuevo Registro - Desarrollo")
        crear_dialog.after(201, lambda :crear_dialog.iconbitmap(icon_path))
        crear_dialog.geometry("400x500")

        # Campos basados en la consulta SELECT
        campos = [
                "Consecutivo Cotizacion",
                "Prioridad",
                "Nombre Cliente",
                "Marca",
                "Comercial Responsable",
                "Elaborado Por",
                "Relacion",
                "Cantidad Productos",
                "Compañia",      
        ]
        # Diccionario para guardar entradas
        entries = {}
        scrollable_frame = ef.ScrollableFrame(crear_dialog)
        scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)

        input_frame = ctk.CTkFrame(scrollable_frame)
        input_frame.pack(fill="x", expand=True)
        # Crear entradas para cada campo
        for i, campo in enumerate(campos):
                field_frame = ctk.CTkFrame(input_frame)
                field_frame.pack(pady=5, padx=20, fill="x")

                label = ctk.CTkLabel(field_frame, text=campo, width=150, anchor="w")
                label.pack(side="left", padx=(0, 10))
                dictionary= { "Comercial Responsable": ["","MATEO ALARCON", "ALEXANDRA SUAREZ","ELIZABETH MONTOYA","STELLA RESTREPO","JORGE ALARCON"],
                            "Compañia": ["","GB LAB", "COBES"],
                            "Estado Cotizacion": ["","NUEVA COTIZACION", "ENVIADO AL COMERCIAL", "ENVIADO AL CLIENTE", "ANULADA"],
                            "Prioridad": ["","VERDE", "AMARILLO", "ROJO"],
                            "Elaborado Por": ["","COSTOS", "COTIZADOR"],
                            "Relacion": ["","CLIENTE", "PROSPECTO"]}
                if campo in dictionary:
                    options = dictionary[campo]
                    combo = ctk.CTkComboBox(field_frame, values=options, width=300)
                    combo.pack(side="left", expand=True, fill="x")
                    entries[campo] = combo  # Agregar el ComboBox al diccionario
                else:
                    entry = ctk.CTkEntry(field_frame, width=300)
                    entry.pack(side="left", expand=True, fill="x")
                    entries[campo] = entry  # Mantener los Entry en el diccionario
                    
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

                # Recoger valores
                valores = [entries[campo].get() for campo in campos]
                valores = [texto.upper() for texto in valores]
                
                # Ejecutar inserción
                cursor.execute(qry.create_query_des, valores)
                conn.commit()

                messagebox.showinfo(title="Éxito", message="Registro creado correctamente")
                crear_dialog.destroy()
                frame.load_data()

            except Exception as e:
                #print("Claves en entries:", entries.keys())

                messagebox.showerror(title="Error", message=f"No se pudo crear el registro: {str(e)}", icon="error")
            finally:
                if "conn" in locals():
                    conn.close()

        # Botón de guardar
        guardar_btn = ctk.CTkButton(crear_dialog, text="Guardar", command=guardar)
        guardar_btn.pack(pady=20)

    def edit_record_Cotizacion(self, frame):
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
            editar_dialog.after(201, lambda :editar_dialog.iconbitmap(icon_path))
            editar_dialog.geometry("400x500")

            # Fields (excluding N_control)
            campos = [
                 "Consecutivo Cotizacion",
                "Prioridad",
                "Nombre Cliente",
                "Marca",
                "Comercial Responsable",
                "Elaborado Por",
                "Relacion",
                "Cantidad Productos",
                "Compañia", 
                "Estado Cotizacion",
                 "Respuesta Cliente",
                 "Observacion",
                ]
            campo_to_value = {
                "Consecutivo Cotizacion": row_data[3],  # ""
                "Prioridad": row_data[4],  # "ROJO"
                "Nombre Cliente": row_data[5],  # ""
                "Marca": row_data[6],  # ""
                "Comercial Responsable": row_data[7],  # ""
                "Elaborado Por": row_data[8],  # ""
                "Relacion": row_data[9],  # ""
                "Cantidad Productos": row_data[10],  # ""
                "Compañia": row_data[11],  # ""
                "Estado Cotizacion": row_data[13],  # "NUEVA COTIZACION"
                "Respuesta Cliente": row_data[17],  # ""
                "Observacion": row_data[18],  # ""
                 }
            dictionary = {
                "Comercial Responsable": ["", "MATEO ALARCON", "ALEXANDRA SUAREZ", "ELIZABETH MONTOYA", "STELLA RESTREPO", "JORGE ALARCON"],
                "Compañia": ["", "GB LAB", "COBES"],
                "Estado Cotizacion": ["", "ENVIADO AL COMERCIAL", "ENVIADO AL CLIENTE", "ANULADA"],
                "Prioridad": ["", "VERDE", "AMARILLO", "ROJO"],
                "Elaborado Por": ["", "COSTOS", "COTIZADOR"],
                "Respuesta Cliente": ["", "APROBADA", "RECHAZADA","RECOTIZACION"],
                 }
                      
            # Dictionary to store entry widgets
            entries = {}
            # Create the scrollable frame
            scrollable_frame = ef.ScrollableFrame(editar_dialog)
            scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)

            # Create a frame for the input fields
            input_frame = ctk.CTkFrame(scrollable_frame)
            input_frame.pack(fill="x", expand=True)
            # Create input fields for each column
            for campo in campos:
                field_frame = ctk.CTkFrame(input_frame)
                field_frame.pack(pady=5, padx=20, fill="x")

                label = ctk.CTkLabel(field_frame, text=campo, width=150, anchor="w")
                label.pack(side="left", padx=(0, 10))

                if campo in dictionary:
                    # Crear un ComboBox para campos con opciones predefinidas
                    options = dictionary[campo]
                    combo = ctk.CTkComboBox(field_frame, values=options, width=300)
                    combo.pack(side="left", expand=True, fill="x")
                    combo.set(campo_to_value[campo])  # Asignar valor manualmente
                    entries[campo] = combo
                else:
                    # Crear un Entry para campos sin opciones predefinidas
                    entry = ctk.CTkEntry(field_frame, width=300)
                    entry.pack(side="left", expand=True, fill="x")
                    entry.insert(0, campo_to_value[campo])  # Asignar valor manualmente
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
                        UPDATE SIIAPP.dbo.COM_Cot
                        SET 
                            COT_ID = ?, 
                            PRIO = ?, 
                            C_NAME = ?, 
                            BRAND = ?,
                            COM_RESP = ?,
                            MADE_BY = ?, 
                            RELATION = ?, 
                            QUANT_PROD = ?,
                            COMPANY = ?,
                            COT_STATE = ?,
                            CLIENT_RESPON = ?,
                            OBS = ?
                        WHERE ID = ?
                    """
                    # Collect values
                    valores = [entries[campo].get() for campo in campos] + [N_control]
                    valores = [texto.upper() for texto in valores]
                    # Verificar si se va a actualizar COT_STATE con "ENVIADO AL COMERCIAL"
                    if row_data[13]=="NUEVA COTIZACION":
                        if valores[9]=="ENVIADO AL CLIENTE":
                            messagebox.showinfo("Accion Cancelada", "No se puede realizar esta accion.")
                            return

                    if valores[9] == "ENVIADO AL COMERCIAL":
                        response = messagebox.askyesno("Confirmación", "¿Esta seguro de cambiar el estado?", icon="warning")
                        
                        if not response:  # 
                            messagebox.showinfo("Accion Cancelada", "No se actualizaron registros")
                            return  # exit the function without update the database

                    # Execute update
                    cursor.execute(query, valores)
                    cursor.execute("SELECT COT_STATE FROM SIIAPP.dbo.COM_Cot WHERE ID = ?", (N_control,))
                    cot_state = cursor.fetchone()
                  
                    if cot_state and cot_state[0]  == 'ENVIADO AL CLIENTE':
                      fecha_actual = dt.now()
                      cursor.execute("UPDATE SIIAPP.dbo.COM_Cot SET DATE_CLIENT_SEND = ? WHERE ID = ?",(fecha_actual, N_control))
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
    def load_data_Proyectos(self, frame):
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
            
            cursor.execute(qry.load_query_proy)
            data = cursor.fetchall()
               
            conn.commit() 

            headers = [
                "Numero de Registro",
                "Estado Cotización",
                "Tipo de Proyecto",
                "Fecha Ingreso",
                "Razon Social",
                "Pais",
                "Tipo de Cliente",
                "Comercial",
                "Producto",
                "NSOC",
                "Cantidad",
                "Valor Unitario",
                "Valor Total",
                "Desarrollo",
                "Codigo Cotizacion",
                "Codigo Muestra",
                "Estado Fial Proyecto",
                "Responsable",   
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
    def create_record_Proyectos(self, frame):
       return
    def edit_record_Proyectos(self, frame):
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
            editar_dialog.after(201, lambda :editar_dialog.iconbitmap(icon_path))
            editar_dialog.geometry("400x500")

            # Fields (excluding N_control)
            campos = [
                
                 "Pais",
                "Tipo de Cliente",
                "Producto",
                "NSOC",
                "Cantidad",
                "Valor Unitario",
                "Desarrollo",
                "Codigo Muestra",
                "Estado Final Proyecto",
                "Responsable",
                ]
            
            campo_to_value = {
                "Pais": row_data[5],  # "NS-22"
                "Tipo de Cliente": row_data[6],  # "ROJO"
                "Producto": row_data[8],  # ""
                "NSOC": row_data[9],  # ""
                "Cantidad": row_data[10],  # ""
                "Valor Unitario": row_data[11],  # ""
                "Desarrollo": row_data[13],  # ""
                "Codigo Muestra": row_data[15],  # ""
                "Estado Final Proyecto": row_data[16],  # ""
                "Responsable": row_data[17],  # ""
                # ""
                 }
            dictionary = {
                "Comercial Responsable": ["", "MATEO ALARCON", "ALEXANDRA SUAREZ", "ELIZABETH MONTOYA", "CAROLINA VEGA", "STELLA RESTREPO", "JORGE ALARCON"],
                "Compañia": ["", "GB LAB", "COBES"],
                "Estado Cotizacion": ["", "NUEVA COTIZACION", "ENVIADO AL COMERCIAL", "ENVIADO AL CLIENTE", "ANULADA"],
                "Prioridad": ["", "VERDE", "AMARILLO", "ROJO"],
                "Elaborado Por": ["", "COSTOS", "COTIZADOR"],
                "Respuesta Cliente": ["", "APROBADA", "RECHAZADA,","RECOTIZACION"],
                 }

            # Dictionary to store entry widgets
            entries = {}
            # Create the scrollable frame
            scrollable_frame = ef.ScrollableFrame(editar_dialog)
            scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)

            # Create a frame for the input fields
            input_frame = ctk.CTkFrame(scrollable_frame)
            input_frame.pack(fill="x", expand=True)
            # Create input fields for each column
            for campo in campos:
                field_frame = ctk.CTkFrame(input_frame)
                field_frame.pack(pady=5, padx=20, fill="x")

                label = ctk.CTkLabel(field_frame, text=campo, width=150, anchor="w")
                label.pack(side="left", padx=(0, 10))

                if campo in dictionary:
                    # Crear un ComboBox para campos con opciones predefinidas
                    options = dictionary[campo]
                    combo = ctk.CTkComboBox(field_frame, values=options, width=300)
                    combo.pack(side="left", expand=True, fill="x")
                    combo.set(campo_to_value[campo])  # Asignar valor manualmente
                    entries[campo] = combo
                else:
                    # Crear un Entry para campos sin opciones predefinidas
                    entry = ctk.CTkEntry(field_frame, width=300)
                    entry.pack(side="left", expand=True, fill="x")
                    entry.insert(0, campo_to_value[campo])  # Asignar valor manualmente
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
                        UPDATE SIIAPP.dbo.COM_Proy
                        SET 
                            COUNTRY = ?, 
                            CLIENT_TYPE = ?, 
                            PRODUCT = ?, 
                            NSOC = ?,
                            QUANT = ?,
                            UNIT_PRICE = ?, 
                            DEVELOP = ?, 
                            SAMPLE_COD = ?,
                            FINAL_STATE = ?,
                            RESPONSIBLE = ?
                        WHERE ID = ?
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

    def export_data_cot(self, frame):
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
            
            cursor.execute(qry.load_query_des)
            data = cursor.fetchall()
            creators = []
            for row in data:
                creators.append(row)
          
            excel_book=openpyxl.Workbook()
            sheet=excel_book.active
            sheet['A1'] = "NUMERO DE REGISTRO"
            sheet['B1'] = "FECHA DE RECEPCIÓN"
            sheet['C1'] = "MES DE RECEPCIÓN"
            sheet['D1'] = "NUMERO COTIZACIÓN"
            sheet['E1'] = "PRIORIDAD"
            sheet['F1'] = "NOMBRE CLIENTE"
            sheet['G1'] = "MARCA"
            sheet['H1'] = "COMERCIAL RESPONSABLE"
            sheet['I1'] = "ELABORADO POR"
            sheet['J1'] = "RELACION"
            sheet['K1'] = "CANTIDAD PRODUCTO"
            sheet['L1'] = "COMPAÑIA"
            sheet['M1'] = "ESTADO TRANSITORIO COTIZACIÓN"
            sheet['N1'] = "ESTADO COTIZACIÓN"
            sheet['O1'] = "FECHA DE ENTREGA"
            sheet['P1'] = "FECHA DE ENTREGA (DÍAS)"
            sheet['Q1'] = "FECHA ENVÍO CLIENTE"
            sheet['R1'] = "RESPUESTA CLIENTE"
            sheet['S1'] = "OBSERVACION"
            for index, row in enumerate(creators):
                sheet[f'A{index+2}'] = row[0]
                sheet[f'B{index+2}'] = row[1]
                sheet[f'C{index+2}'] = row[2]
                sheet[f'D{index+2}'] = row[3]
                sheet[f'E{index+2}'] = row[4]
                sheet[f'F{index+2}'] = row[5]
                sheet[f'G{index+2}'] = row[6]
                sheet[f'H{index+2}'] = row[7]
                sheet[f'I{index+2}'] = row[8]
                sheet[f'J{index+2}'] = row[9]
                sheet[f'K{index+2}'] = row[10]
                sheet[f'L{index+2}'] = row[11]
                sheet[f'M{index+2}'] = row[12]
                sheet[f'N{index+2}'] = row[13]
                sheet[f'O{index+2}'] = row[14]
                sheet[f'P{index+2}'] = row[15]
                sheet[f'Q{index+2}'] = row[16]
                sheet[f'R{index+2}'] = row[17]
                sheet[f'S{index+2}'] = row[18]

            downloads_path = str(Path.home() / "Downloads")
            file_path = os.path.join(downloads_path, "data_cot_export.xlsx")
            excel_book.save(file_path)
            
            messagebox.showinfo(title="Éxito", message=f"Datos exportados correctamente")

        except pyodbc.Error as e:
            print(f"An error occurred while loading Desarrollo data: {str(e)}", file=sys.stderr)
            messagebox.showerror(title="Error", message=f"No se pudo cargar los datos: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
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
        self.user_access = lg.authenticate_user(username, password)

        if lg.authenticate_user(username, password):
            messagebox.showinfo("Login Exitoso", "Bienvenido!")
            self.save_credentials()  # Save credentials before showing the app frame
            self.master.show_app_frame(self.user_access)
        else:
            messagebox.showerror("Login Fallido", "Credenciales invalidas o acceso denegado.")

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
app.title("Cotizaciones")
app.iconbitmap(icon_path)
app.mainloop()