# -*- mode: python ; coding: utf-8 -*-
import shutil
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None

streamlit_datas, streamlit_binaries, streamlit_hiddenimports = collect_all("streamlit")
altair_datas, altair_binaries, altair_hiddenimports = collect_all("altair")

datas = [
    ("app.py", "."),
    ("db.py", "."),
    ("pages", "pages"),
    (".streamlit/config.toml", ".streamlit"),
] + streamlit_datas + altair_datas

binaries = streamlit_binaries + altair_binaries
hiddenimports = streamlit_hiddenimports + altair_hiddenimports

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Bookstore",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Bookstore",
)

dist_dir = Path("dist") / "Bookstore"
readme_src = Path("packaging") / "README.md"
readme_dst = dist_dir / "README.md"
config_src = Path(".streamlit") / "config.toml"
config_dst_dir = dist_dir / ".streamlit"
config_dst = config_dst_dir / "config.toml"
if readme_src.is_file():
    shutil.copy2(readme_src, readme_dst)
if config_src.is_file():
    config_dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config_src, config_dst)
