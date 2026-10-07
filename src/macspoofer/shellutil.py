"""Windows app identity: AppUserModelID, window icon, shortcuts, Start Menu."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from macspoofer import __app_id__, __app_name__
from macspoofer.log import write_log
from macspoofer.paths import BUNDLE
from macspoofer.paths import ROOT as HOME

WINDOW_TITLE = "MAC // Spoofer"
EXE_NAME = "MAC_Spoofer.exe"


def icon_file() -> Path:
    """The app icon: the Net // Works globe. EXE file, window, taskbar, alt-tab."""
    cands = [
        BUNDLE / "assets" / "app.ico",
        Path(__file__).resolve().parents[2] / "assets" / "app.ico",
    ]
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        cands[0:0] = [exe.parent / "assets" / "app.ico", exe.parent / "app.ico"]
    for p in cands:
        if p.is_file():
            return p
    return Path()


def shortcut_icon_file() -> Path:
    """Blade (Sin City 14): Desktop shortcut, Start Menu shortcut and the tray icon.

    A shortcut needs a path that outlives the process, so a one-file EXE that has
    no assets/ folder next to it keeps a copy of its bundled icon in %LOCALAPPDATA%.
    """
    cands = [Path(__file__).resolve().parents[2] / "assets" / "shortcut-blade.ico"]
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        cands[0:0] = [exe.parent / "assets" / "shortcut-blade.ico", exe.parent / "shortcut-blade.ico"]
    for p in cands:
        if p.is_file():
            return p
    bundled = BUNDLE / "assets" / "shortcut-blade.ico"
    if not bundled.is_file():
        return Path()
    keep = HOME / "shortcut-blade.ico"
    try:
        if not keep.is_file() or keep.stat().st_size != bundled.stat().st_size:
            keep.parent.mkdir(parents=True, exist_ok=True)
            keep.write_bytes(bundled.read_bytes())
        return keep
    except OSError:
        return bundled


MUTEX_NAME = "Local\\Ringmast4r.MACSpoofer.Single"
SHOW_EVENT_NAME = "Local\\Ringmast4r.MACSpoofer.Show"
ERROR_ALREADY_EXISTS = 183
EVENT_MODIFY_STATE = 0x0002
ASFW_ANY = 0xFFFFFFFF
_mutex_handle = None
_show_event = None


def _kernel32():
    import ctypes
    from ctypes import wintypes

    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    k.CreateMutexW.restype = wintypes.HANDLE
    k.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    k.CreateEventW.restype = wintypes.HANDLE
    k.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    k.OpenEventW.restype = wintypes.HANDLE
    k.SetEvent.argtypes = [wintypes.HANDLE]
    k.SetEvent.restype = wintypes.BOOL
    k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k.WaitForSingleObject.restype = wintypes.DWORD
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    k.CloseHandle.restype = wintypes.BOOL
    return k


def claim_single_instance(wait_s: float = 15.0) -> bool:
    """True when this process is the only one, and it then owns the app: the mutex plus a named
    'show' event that every later launch signals. Otherwise the click is handed to the running
    instance, which shows its own window through its own code (a hidden-to-tray window included),
    and False is returned so this process exits without a window or a tray icon."""
    global _mutex_handle, _show_event
    try:
        import ctypes
        import time

        k = _kernel32()
        handle = k.CreateMutexW(None, False, MUTEX_NAME)
        err = ctypes.get_last_error()
        if handle and err != ERROR_ALREADY_EXISTS:
            _mutex_handle = handle
            _show_event = k.CreateEventW(None, False, False, SHOW_EVENT_NAME)  # auto-reset, unsignalled
            return True
        deadline = time.time() + wait_s
        while time.time() < deadline:  # the running instance may still be starting
            ev = k.OpenEventW(EVENT_MODIFY_STATE, False, SHOW_EVENT_NAME)
            if ev:
                try:
                    try:  # this process got the user's click, so it may lend its foreground right
                        ctypes.windll.user32.AllowSetForegroundWindow(ASFW_ANY)
                    except Exception:
                        pass
                    if k.SetEvent(ev):
                        write_log("second launch: handed over to the running instance")
                        return False
                finally:
                    k.CloseHandle(ev)
            elif restore_existing():  # a copy built before the show event existed
                write_log("second launch: restored the running instance")
                return False
            time.sleep(0.3)
        write_log("second launch: instance running but not answering; exiting")
        return False
    except Exception as e:
        write_log("single-instance check failed: " + str(e))
        raise RuntimeError("Single-instance lock could not be acquired") from e


def on_show_request(callback) -> None:
    """In the running instance: call back (on a daemon thread) each time another launch asks."""
    if not _show_event:
        return
    import threading

    def loop() -> None:
        k = _kernel32()
        while k.WaitForSingleObject(_show_event, 0xFFFFFFFF) == 0:  # WAIT_OBJECT_0
            write_log("another launch asked for the window")
            try:
                callback()
            except Exception as e:
                write_log("show on request failed: " + str(e))

    threading.Thread(target=loop, name="mac-show", daemon=True).start()


def bring_to_front() -> None:
    try:
        import ctypes
        from ctypes import wintypes

        hwnd = find_app_window()
        if not hwnd:
            return
        user32 = ctypes.windll.user32
        user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                        ctypes.c_int, ctypes.c_int, wintypes.UINT]
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        if user32.GetForegroundWindow() != hwnd:
            # Windows kept focus elsewhere (it only lends it to a launch that follows a real click):
            # still lift the window above everything once, so the click visibly brings it back
            flags = 0x0001 | 0x0002 | 0x0040  # SWP_NOSIZE | SWP_NOMOVE | SWP_SHOWWINDOW
            user32.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, flags)  # HWND_TOPMOST
            user32.SetWindowPos(hwnd, wintypes.HWND(-2), 0, 0, 0, 0, flags)  # HWND_NOTOPMOST
    except Exception as e:
        write_log("bring to front failed: " + str(e))


def set_process_appid() -> None:
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(__app_id__)
    except Exception as e:
        write_log("appid process failed: " + str(e))


def find_app_window(title: str = WINDOW_TITLE) -> int:
    """Our own top-level window, or 0. FindWindowW(None, title) is not enough: a File Explorer
    window open on a folder called "MAC // Spoofer" has exactly this title, and matching it
    made a fresh launch 'restore' Explorer and exit. Accept only pywebview's WinForms class or a
    window owned by our EXE / python."""
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        found = []
        me = Path(sys.executable).name.lower()

        def check(hwnd, _lp):
            length = user32.GetWindowTextLengthW(hwnd)
            if length != len(title):
                return True
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if buf.value != title:
                return True
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls, 256)
            if cls.value.startswith("WindowsForms10"):
                found.append(hwnd)
                return False
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            h = kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
            if h:
                try:
                    size = wintypes.DWORD(1024)
                    path = ctypes.create_unicode_buffer(1024)
                    if kernel32.QueryFullProcessImageNameW(h, 0, path, ctypes.byref(size)):
                        exe = Path(path.value).name.lower()
                        if exe in (EXE_NAME.lower(), me, "python.exe", "pythonw.exe"):
                            found.append(hwnd)
                            return False
                finally:
                    kernel32.CloseHandle(h)
            return True

        proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(proto(check), 0)
        return int(found[0]) if found else 0
    except Exception as e:
        write_log("find_app_window failed: " + str(e))
        return 0


def restore_existing() -> bool:
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = find_app_window()
        if not hwnd:
            return False
        user32.ShowWindow(hwnd, 9)
        user32.SetForegroundWindow(hwnd)
        write_log("restored existing window")
        return True
    except Exception:
        return False


_window_icon_handle = None

def apply_window_icon(title: str = WINDOW_TITLE) -> None:
    global _window_icon_handle
    import ctypes
    from ctypes import wintypes
    ico = icon_file()
    if not ico.is_file(): return
    user32 = ctypes.windll.user32
    hwnd = find_app_window(title)
    if not hwnd: return
    user32.LoadImageW.argtypes = [wintypes.HINSTANCE,wintypes.LPCWSTR,wintypes.UINT,ctypes.c_int,ctypes.c_int,wintypes.UINT]
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.SendMessageW.argtypes = [wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
    user32.SendMessageW.restype = wintypes.LPARAM
    if not _window_icon_handle:
        _window_icon_handle = user32.LoadImageW(None,str(ico),1,0,0,0x0010|0x0040)
    if _window_icon_handle:
        user32.SendMessageW(hwnd,0x0080,1,_window_icon_handle)
        user32.SendMessageW(hwnd,0x0080,0,_window_icon_handle)


def stamp_shortcut(lnk: Path, exe: Path, workdir: Path, ico: Path) -> None:
    """Write a .lnk that carries the same AppUserModelID as the process (taskbar grouping)."""
    lnk.parent.mkdir(parents=True, exist_ok=True)
    ps = r"""
$ErrorActionPreference = 'Stop'
$lnk = [string]$env:MAC_LNK
$exe = [string]$env:MAC_EXE
$wd  = [string]$env:MAC_WD
$ico = [string]$env:MAC_ICO
$app = [string]$env:MAC_APPID
$sh = New-Object -ComObject WScript.Shell
$s = $sh.CreateShortcut($lnk)
$s.TargetPath = $exe
$s.WorkingDirectory = $wd
$s.WindowStyle = 1
$s.Description = 'Inspect and change local network adapter addresses. Built by Net Works Lab LLC.'
if (Test-Path -LiteralPath $ico) { $s.IconLocation = "$ico,0" } else { $s.IconLocation = "$exe,0" }
$s.Save()

$code = @'
using System;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;

[ComImport, Guid("00021401-0000-0000-C000-000000000046")]
public class CShellLink {}

[ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown),
 Guid("0000010b-0000-0000-C000-000000000046")]
public interface IPersistFile {
  void GetClassID(out Guid pClassID);
  [PreserveSig] int IsDirty();
  void Load([MarshalAs(UnmanagedType.LPWStr)] string pszFileName, uint dwMode);
  void Save([MarshalAs(UnmanagedType.LPWStr)] string pszFileName, [MarshalAs(UnmanagedType.Bool)] bool fRemember);
  void SaveCompleted([MarshalAs(UnmanagedType.LPWStr)] string pszFileName);
  void GetCurFile(out IntPtr ppszFileName);
}

[StructLayout(LayoutKind.Sequential, Pack = 4)]
public struct PROPERTYKEY { public Guid fmtid; public UInt32 pid; }

[StructLayout(LayoutKind.Explicit)]
public struct PROPVARIANT {
  [FieldOffset(0)] public ushort vt;
  [FieldOffset(8)] public IntPtr pointerValue;
}

[ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown),
 Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")]
public interface IPropertyStore {
  void GetCount(out uint cProps);
  void GetAt(uint iProp, out PROPERTYKEY pkey);
  void GetValue(ref PROPERTYKEY key, out PROPVARIANT pv);
  void SetValue(ref PROPERTYKEY key, ref PROPVARIANT pv);
  void Commit();
}

public static class AppIdStamp {
  public static void Apply(string lnk, string appId) {
    var sl = (IPersistFile)new CShellLink();
    sl.Load(lnk, 2);
    var ps = (IPropertyStore)sl;
    var key = new PROPERTYKEY();
    key.fmtid = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3");
    key.pid = 5;
    var pv = new PROPVARIANT();
    pv.vt = 31;
    pv.pointerValue = Marshal.StringToCoTaskMemUni(appId);
    ps.SetValue(ref key, ref pv);
    ps.Commit();
    sl.Save(lnk, true);
    Marshal.FreeCoTaskMem(pv.pointerValue);
  }
}
'@
Add-Type -TypeDefinition $code -Language CSharp -ErrorAction Stop
[AppIdStamp]::Apply($lnk, $app)
"""
    env = os.environ.copy()
    env["MAC_LNK"] = str(lnk)
    env["MAC_EXE"] = str(exe)
    env["MAC_WD"] = str(workdir)
    env["MAC_ICO"] = str(ico)
    env["MAC_APPID"] = __app_id__
    r = subprocess.run(
        ["powershell", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-Command", ps],
        capture_output=True,
        text=True,
        timeout=45,
        env=env,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if r.returncode != 0:
        write_log("stamp shortcut failed: " + (r.stderr or r.stdout or "exit %s" % r.returncode)[-500:])
    else:
        write_log("stamped shortcut " + str(lnk))


def install_shortcuts(exe: Path | None = None) -> list[Path]:
    if exe is None:
        exe = Path(sys.executable).resolve() if getattr(sys, "frozen", False) else (
            Path(__file__).resolve().parents[2] / EXE_NAME
        )
    if not exe.is_file():
        return []
    ico = shortcut_icon_file()  # Blade, not the app's globe
    if not ico.is_file():
        ico = icon_file()
    if not ico.is_file():
        ico = exe
    workdir = exe.parent
    desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
    start = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    made: list[Path] = []
    for folder in (desktop, start):
        if not folder.is_dir():
            continue
        lnk = folder / f"{__app_name__}.lnk"
        try:
            stamp_shortcut(lnk, exe, workdir, ico)
            made.append(lnk)
        except Exception as e:
            write_log("shortcut " + str(lnk) + " failed: " + str(e))

    return made

