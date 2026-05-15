# PyInstaller spec — run: pyinstaller ckpt.spec --clean
# Produces a single binary in dist/ckpt

block_cipher = None

a = Analysis(
    ["ckpt/__main__.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[
        "click",
        "rich",
        "rich.console",
        "rich.table",
        "rich.text",
        "rich.box",
        "rich.status",
        "rich.spinner",
    ],
    excludes=[
        "tkinter",
        "unittest",
        "email",
        "http",
        "urllib",
        "xml",
        "pydoc",
        "doctest",
        "difflib",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="ckpt",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=True,
    onefile=True,
)
