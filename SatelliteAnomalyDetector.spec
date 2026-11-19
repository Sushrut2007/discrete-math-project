# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_submodules
from pathlib import Path
import os

project_root = Path('.').resolve()

# Collect Streamlit assets and metadata
streamlit_datas = collect_data_files('streamlit')
streamlit_meta = copy_metadata('streamlit')

# Additional project data
project_datas = [
    ('app', 'app'),
    ('src', 'src'),
    ('data', 'data'),
] + streamlit_datas + streamlit_meta

hidden_imports = [
    'streamlit',
    'streamlit.web.cli',
    'streamlit.runtime.scriptrunner.magic_expressions',
    'altair',
    'pandas',
    'numpy',
    'scipy',
    'scipy.spatial',
    'scipy.spatial.transform',
    'sklearn',
    'sklearn.cluster',
    'sklearn.ensemble',
    'sklearn.neighbors',
    'sklearn.preprocessing',
    'plotly',
    'requests',
    'seaborn',
    'matplotlib',
] + collect_submodules('streamlit') + collect_submodules('sklearn')

a = Analysis(
    ['run_app.py'],
    pathex=['.'],
    binaries=[],
    datas=project_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SatelliteAnomalyDetector',
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SatelliteAnomalyDetector',
)
