import customtkinter as ctk
from tksheet import Sheet
import modules.query as qry

class MyFrame(ctk.CTkFrame):
    def __init__(self, master, load_data_func, create_record_func=None, edit_record_func=None, export_data_func=None, **kwargs):
        super().__init__(master, **kwargs)

        # Store data management functions
        self.load_data_func = load_data_func
        self.create_record_func = create_record_func
        self.edit_record_func = edit_record_func
        self.export_data_func = export_data_func

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
            ))

        # Create buttons
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(fill="x", padx=10, pady=5)

        # Create filter entry
        self.filter_type_combo = ctk.CTkComboBox(
            self.button_frame,
            values=["Número de Registro", "Fecha", "Encargado"],
            width=180
        )
        self.filter_type_combo.pack(side="left", padx=(10, 5))

        self.filter_entry = ctk.CTkEntry(
            self.button_frame, placeholder_text="Buscar por Número de Registro, Fecha o Encargado")
        self.filter_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.filter_entry.bind("<Return>", self.filter_data)

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
        self.export_button = ctk.CTkButton(self.button_frame, text="Exportar", command=self.export_data)
        self.export_button.pack(side="left", padx=5)

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
        filter_option = self.filter_type_combo.get()

        if search_text:
            if filter_option == "Número de Registro":
                column_index = 0
            elif filter_option == "Fecha":
                column_index = 15
            elif filter_option == "Encargado":
                column_index = 7  # Adjust according to your actual table column for 'Encargado'
            else:
                column_index = 0

            self.filtered_data = [
                row for row in self.original_data
                if (search_text in str(row[column_index]).lower()
                    if search_text.strip() != "" else str(row[column_index]).strip() == "")
            ]
            self.sheet.set_sheet_data(self.filtered_data)
        else:
            self.filtered_data = self.original_data
            self.sheet.set_sheet_data(self.filtered_data)

    def export_data(self):
        self.export_data_func(self)