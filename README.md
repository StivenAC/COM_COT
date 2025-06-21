
# 🧾 SIIAPP COTM - Sistema Integrado de Información de Aplicaciones (Cotizaciones y Módulos)

**SIIAPP COTM** es una aplicación de escritorio desarrollada en Python para la gestión de cotizaciones comerciales en entornos empresariales. Ofrece autenticación con Active Directory, control de acceso basado en roles y gestión de datos mediante SQL Server.

## 📌 Características principales

- Interfaz moderna con pestañas (CustomTkinter)
- Autenticación segura con Active Directory (LDAP)
- Acceso basado en roles definidos por grupo o usuario
- Control de flujo de cotizaciones (estados y fechas)
- Exportación de datos a Excel
- Cifrado seguro de credenciales (Fernet)
- Empaquetado como aplicación ejecutable para Windows

---

## 🧱 Arquitectura del Sistema

```mermaid
graph TD;
    A[Usuario] --> B[LoginFrame (Autenticación)]
    B --> C{Active Directory}
    C -->|LDAP| D[SERVER2.GBLAB.LOCAL]
    B --> E[App]
    E --> F[MyTabView (Interfaz de Negocio)]
    F --> G[Funciones: load, create, edit, export]
    G --> H[(SQL Server: COM_Cot, COM_Proy)]
```

### Componentes principales

| Clase         | Descripción                                  |
|---------------|----------------------------------------------|
| `App`         | Orquestador principal de la aplicación       |
| `LoginFrame`  | Interfaz de autenticación con AD             |
| `MyTabView`   | Gestión tabulada de cotizaciones             |

---

## ⚙️ Instalación

### Requisitos

- Python 3.10+
- SQL Server (con base de datos SIIAPP configurada)
- Active Directory
- Windows OS

### Clonar repositorio

```bash
git clone https://github.com/tuusuario/siiapp-cotm.git
cd siiapp-cotm
```

### Crear entorno virtual e instalar dependencias

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🔐 Configuración

Edita el archivo `.env` con tus variables:

```ini
# Conexiones a bases de datos
DB1_HOST=localhost
DB1_USER=usuario1
DB1_PASS=clave1
DB1_NAME=SIIAPP

DB2_HOST=localhost
DB2_USER=usuario2
DB2_PASS=clave2
DB2_NAME=SIIAPP

# Configuración de Active Directory
AD_DOMAIN=GBLAB.LOCAL
AD_SERVER=SERVER2.GBLAB.LOCAL

# Acceso por grupo o usuario
ALLOWED_GROUPS=SISTEMAS,DESARROLLOS,PRODUCCION
ALLOWED_USERS=JORGE.PINEDA,adj

# Clave para cifrado Fernet
ENCRYPTION_KEY=GENERAR_TU_LLAVE
```

---

## ▶️ Ejecución

```bash
python COT.py
```

O bien ejecuta el archivo empaquetado:

```bash
./dist/SIIAPP_COTM_APP.exe
```

---

## 📊 Estructura de Datos

### Tablas principales

**COM_Cot**  
Contiene registros de cotizaciones.

Campos: `ID`, `DATE_REP`, `TRANS_STATE`, `COT_STATE`, `COT_ID`, `C_NAME`, `COM_RESP`

**COM_Proy**  
Datos asociados a proyectos cotizados.

---

## 🔄 Flujo de Estados de Cotización

1. **NUEVA**
2. **ENVIADO AL COMERCIAL**
3. **ENVIADO AL CLIENTE**
4. **ATRASADO** (automático tras 3 días sin avance)

---

## 📤 Exportación

Los usuarios autorizados pueden exportar datos a Excel directamente desde la pestaña de "Costo Comercial".

---

## 📦 Distribución

La aplicación puede ser distribuida como ejecutable standalone con PyInstaller:

```bash
pyinstaller --onefile --windowed COT.py
```

Los recursos se manejan desde `Assets/` o `_internal/`, y se ajustan automáticamente usando `sys._MEIPASS`.

---

## 🛡️ Seguridad

- Autenticación empresarial vía Active Directory.
- Control de acceso por grupo/usuario.
- Cifrado de credenciales con Fernet.
- Variables sensibles en `.env`.

---

## 📁 Estructura del Proyecto

```
siiapp-cotm/
│
├── Assets/                # Íconos, temas y recursos gráficos
├── COT.py                 # Código fuente principal
├── .env                   # Configuración del entorno
├── credentials.txt        # Archivo encriptado con credenciales
├── requirements.txt       # Librerías necesarias
└── README.md              # Este documento
```

---

## 👥 Autores y Créditos

Desarrollado por el equipo de TI de [Nombre de la empresa].

Colaboradores:
- Jorge Pineda
- adj
- Departamento de Desarrollo

---

## 📄 Licencia

Este proyecto es propiedad de [Tu Empresa]. Uso interno. Todos los derechos reservados.

---
