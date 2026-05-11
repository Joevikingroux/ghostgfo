# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for GhostCFOAgent.exe
#
# Build command (run from the agent/ directory):
#   pyinstaller build.spec
#
# Output: dist/GhostCFOAgent.exe (single-file, no console window shown to end-users)

from PyInstaller.utils.hooks import collect_all, collect_submodules

# PyInstaller's pyi_rth_pkgres runtime hook imports pkg_resources which pulls in
# the full setuptools/jaraco/more_itertools tree. Collect everything up front so
# we don't chase individual ModuleNotFoundError crashes one at a time.
_extra_datas    = []
_extra_binaries = []
_extra_hidden   = []

for _pkg in (
    'pkg_resources',
    'jaraco',
    'jaraco.text',
    'jaraco.functools',
    'jaraco.context',
    'jaraco.collections',
    'more_itertools',
    'importlib_resources',
    'importlib_metadata',
    'zipp',
):
    try:
        _d, _b, _h = collect_all(_pkg)
        _extra_datas    += _d
        _extra_binaries += _b
        _extra_hidden   += _h
    except Exception:
        pass

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[] + _extra_binaries,
    datas=[
        ('assets/ghostcfo.ico', 'assets'),
    ] + _extra_datas,
    hiddenimports=[
        # cryptography backends
        'cryptography.hazmat.primitives.ciphers.aead',
        'cryptography.hazmat.backends.openssl',
        # pyodbc
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
        # tkinter (status window)
        'tkinter',
        'tkinter.ttk',
        'tkinter.font',
        '_tkinter',
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
        'status_window',
    ] + _extra_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon='assets/ghostcfo.ico',
)
