# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for GhostCFOAgent.exe
#
# Build command (run from the agent/ directory):
#   pyinstaller build.spec
#
# Output: dist/GhostCFOAgent.exe (single-file, no console window shown to end-users)

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Pillow image plugins needed for tray icon rendering
        ('assets/ghostcfo.ico', 'assets'),
    ],
    hiddenimports=[
        # cryptography backends
        'cryptography.hazmat.primitives.ciphers.aead',
        'cryptography.hazmat.backends.openssl',
        # pyodbc — driver detection happens at runtime
        'pyodbc',
        # httpx transports
        'httpx._transports.default',
        # click
        'click',
        # pystray + Pillow for tray icon
        'pystray',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL._imagingtk',
        # agent submodules
        'connector',
        'connector.evolution_db',
        'connector.queries',
        'sync',
        'sync.encryptor',
        'sync.extractor',
        'sync.uploader',
        'service',
        'service.installer',
        'service.scheduler',
        'tray',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # keep the .exe lean — these are not needed at runtime
        'tkinter', 'unittest', 'email', 'html', 'http.server',
        'xml', 'xmlrpc', 'pydoc', 'doctest', 'difflib',
        'setuptools', 'pip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GhostCFOAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,            # Compress with UPX if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # No console window for the service mode
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows-specific: embed version info and icon
    version='version_info.txt',    # optional — create separately for code-signing
    icon='assets/ghostcfo.ico',
)
