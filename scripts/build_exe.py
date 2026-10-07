"""Build MAC_Spoofer.exe into dist/ and copy it to the desktop folder, then re-stamp the
Desktop, Start Menu and folder shortcuts (Blade icon, the app's AppUserModelID).
Stops a running copy first or the copy gets Permission denied."""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXE_NAME = "MAC_Spoofer.exe"
PORT = 8802
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _running() -> bool:
    out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {EXE_NAME}", "/NH"],
                         capture_output=True, text=True, creationflags=NO_WINDOW).stdout
    return EXE_NAME.lower() in out.lower()


def stop_running_copy() -> None:
    """Ask a running copy to quit through its own Exit path first, so it takes its tray icon
    with it; a forced kill leaves a dead icon in the tray until the mouse passes over it."""
    if not _running():
        return
    import re, json
    base = f"http://127.0.0.1:{PORT}/"
    try:
        html = urllib.request.urlopen(base, timeout=4).read().decode()
        token = re.search(r'name="mac-session" content="([^"]+)', html)[1]
        headers = {"Content-Type":"application/json", "X-MAC-Token":token}
        state = json.load(urllib.request.urlopen(urllib.request.Request(base+'api/state',headers=headers)))
        if state['busy']: raise RuntimeError('An adapter operation is active. Build staged; install after it completes.')
        req = urllib.request.Request(base+'api/quit', data=b'{}', method='POST', headers=headers)
        urllib.request.urlopen(req, timeout=4).read()
        for _ in range(40):
            if not _running(): return
            time.sleep(.25)
    except Exception as exc:
        raise RuntimeError('Could not close the current copy cleanly; staged build retained. '+str(exc)) from exc
    raise RuntimeError('Current copy did not exit; staged build retained.')


def main() -> int:
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage', action='store_true')
    parser.add_argument('--install-only', action='store_true')
    args=parser.parse_args()
    subprocess.run([sys.executable,str(ROOT/'scripts/make_icon.py')],check=True)
    version=(ROOT/'VERSION').read_text().strip()
    numbers=tuple(int(v) for v in version.split('.'))+(0,)
    resource = f"VSVersionInfo(ffi=FixedFileInfo(filevers={numbers},prodvers={numbers},mask=0x3f,flags=0x0,OS=0x40004,fileType=0x1,subtype=0x0,date=(0,0)),kids=[StringFileInfo([StringTable('040904B0',[StringStruct('CompanyName','Net Works Lab LLC'),StringStruct('FileDescription','MAC // Spoofer'),StringStruct('FileVersion','{version}'),StringStruct('ProductName','MAC // Spoofer'),StringStruct('ProductVersion','{version}'),StringStruct('OriginalFilename','MAC_Spoofer.exe'),StringStruct('LegalCopyright','Copyright 2026 Net Works Lab LLC')])]),VarFileInfo([VarStruct('Translation',[1033,1200])])])"
    (ROOT/'build/version-resource.txt').write_text(resource,encoding='utf-8')
    spec = ROOT / "packager" / "MAC_Spoofer.spec"
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm",
           "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build"), str(spec)]
    print(" ".join(cmd))
    rc = 0 if args.install_only else subprocess.call(cmd, cwd=ROOT)
    if rc != 0:
        return rc
    if args.stage: return 0
    stop_running_copy()
    src = ROOT / "dist" / EXE_NAME
    dst = ROOT / EXE_NAME
    if src.is_file():
        shutil.copy2(src, dst)
        print("copied", dst)
        sys.path.insert(0, str(ROOT / "src"))
        sys.path.insert(0, str(ROOT.parent))
        from macspoofer import __app_name__
        from macspoofer.shellutil import install_shortcuts, shortcut_icon_file, stamp_shortcut

        for p in install_shortcuts(dst):
            print("shortcut", p)
        local = ROOT / f"{__app_name__}.lnk"  # the copy that lives next to the EXE
        stamp_shortcut(local, dst, ROOT, shortcut_icon_file())
        print("shortcut", local)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
