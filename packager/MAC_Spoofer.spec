from pathlib import Path
from PyInstaller.utils.hooks import collect_all
root = Path(SPECPATH).resolve().parent
datas, binaries, hidden = [], [], []
for package in ('webview','pythonnet','clr_loader'):
    d,b,h = collect_all(package)
    datas += d; binaries += b; hidden += h
a = Analysis([str(root/'mac_spoofer_gui.py')], pathex=[str(root/'src')],
    binaries=binaries, datas=datas+[(str(root/'public'),'public'),(str(root/'assets'),'assets'),
    (str(root/'data'),'data'),(str(root/'VERSION'),'.')],
    hiddenimports=hidden+['macspoofer.app','macspoofer.window','macspoofer.tray','macspoofer.shellutil','sqlite3'],
    excludes=['pytest','playwright'],noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz,a.scripts,a.binaries,a.datas,[],name='MAC_Spoofer',console=False,
    upx=False,icon=str(root/'assets/app.ico'),version=str(root/'build/version-resource.txt'))
