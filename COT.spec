# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['COT.py'],
    pathex=['./modules'],
    binaries=[],
    datas=[('.env', '.'), ('Assets/icon_2.ico', 'Assets'),('themes/red.json', 'themes')],
    hiddenimports=['modules.login','modules.extra_functions','modules.f_combobox','modules.gui_frame','modules.query','modules.holyday','tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'customtkinter',
    'pyodbc',
    'tksheet',
    'dotenv',
    'ldap3',
    'ldap3.server',
    'ldap3.connection',
    'ldap3.ALL',
    'ldap3.SUBTREE',
    'ldap3.NTLM',
    'logging',
    'cryptography.fernet',
    'cryptography.fernet.Fernet',
    'cryptography.fernet.InvalidToken',
    'datetime'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SIIAPP_COTM_APP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Assets/icon.ico',  
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SIIAPP_COTM_APP',
)
