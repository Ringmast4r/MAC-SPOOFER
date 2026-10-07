"""Notification-area icon (Windows).

No dependency: Shell_NotifyIcon on a hidden window with its own message loop in a
daemon thread. The icon is keyed by (hWnd, uID), NOT by a GUID: the shell binds a
NIF_GUID to the first executable path that registers it, so a dev run from
python.exe (or a moved EXE) makes every later NIM_ADD fail with no error text.
A second instance never starts (window.restore_existing), so nothing stacks.
Answers the TaskbarCreated broadcast so the icon comes back after explorer.exe
restarts.

It carries Brim (Sin City 17), the same icon as the Desktop and Start Menu
shortcuts (assets/coldcase/SOURCE.txt). Left click opens the window, right click
gives Open / Exit.
"""
from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes
from pathlib import Path

from macspoofer import __app_name__
from macspoofer.log import write_log

CLASS_NAME = "Ringmast4r.MACSpoofer.Tray"
TRAY_ID = 1

WM_NULL = 0x0000
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_APP = 0x8000
WM_LBUTTONUP = 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP = 0x0205

NIF_MESSAGE = 0x01
NIF_ICON = 0x02
NIF_TIP = 0x04
NIF_INFO = 0x10
NIF_SHOWTIP = 0x80
NIM_ADD = 0x00
NIM_MODIFY = 0x01
NIM_DELETE = 0x02
NIIF_USER = 0x04
NIIF_LARGE_ICON = 0x20

WS_POPUP = 0x80000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010
SM_CXSMICON = 49
SM_CXICON = 11
MSGFLT_ALLOW = 1
CLASS_ALREADY_EXISTS = 1410

MF_STRING = 0x0000
MF_SEPARATOR = 0x0800
TPM_RIGHTBUTTON = 0x0002
TPM_BOTTOMALIGN = 0x0020
TPM_NONOTIFY = 0x0080
TPM_RETURNCMD = 0x0100
ID_OPEN = 1001
ID_EXIT = 1002

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_user32 = ctypes.WinDLL("user32", use_last_error=True)
_shell32 = ctypes.WinDLL("shell32", use_last_error=True)

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
)


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]


class NOTIFYICONDATAW(ctypes.Structure):
    class _Version(ctypes.Union):
        _fields_ = [("uTimeout", wintypes.UINT), ("uVersion", wintypes.UINT)]

    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("version_or_timeout", _Version),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", GUID),
        ("hBalloonIcon", wintypes.HICON),
    ]
    _anonymous_ = ["version_or_timeout"]


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]


def _proto() -> None:
    k, u, s = _kernel32, _user32, _shell32
    k.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    k.GetModuleHandleW.restype = wintypes.HINSTANCE
    u.RegisterClassExW.argtypes = [ctypes.c_void_p]
    u.RegisterClassExW.restype = wintypes.ATOM
    u.CreateWindowExW.argtypes = [
        wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID,
    ]
    u.CreateWindowExW.restype = wintypes.HWND
    u.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    u.DefWindowProcW.restype = ctypes.c_ssize_t
    u.DestroyWindow.argtypes = [wintypes.HWND]
    u.DestroyWindow.restype = wintypes.BOOL
    u.DestroyIcon.argtypes = [wintypes.HICON]
    u.DestroyIcon.restype = wintypes.BOOL
    u.LoadImageW.argtypes = [
        wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT
    ]
    u.LoadImageW.restype = wintypes.HANDLE
    u.GetSystemMetrics.argtypes = [ctypes.c_int]
    u.GetSystemMetrics.restype = ctypes.c_int
    u.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
    u.RegisterWindowMessageW.restype = wintypes.UINT
    u.ChangeWindowMessageFilterEx.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.DWORD, ctypes.c_void_p]
    u.ChangeWindowMessageFilterEx.restype = wintypes.BOOL
    u.SetForegroundWindow.argtypes = [wintypes.HWND]
    u.SetForegroundWindow.restype = wintypes.BOOL
    u.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    u.PostMessageW.restype = wintypes.BOOL
    u.PostQuitMessage.argtypes = [ctypes.c_int]
    u.PostQuitMessage.restype = None
    u.GetMessageW.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.UINT]
    u.GetMessageW.restype = ctypes.c_int
    u.TranslateMessage.argtypes = [ctypes.c_void_p]
    u.TranslateMessage.restype = wintypes.BOOL
    u.DispatchMessageW.argtypes = [ctypes.c_void_p]
    u.DispatchMessageW.restype = ctypes.c_ssize_t
    u.CreatePopupMenu.argtypes = []
    u.CreatePopupMenu.restype = wintypes.HMENU
    u.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
    u.AppendMenuW.restype = wintypes.BOOL
    u.DestroyMenu.argtypes = [wintypes.HMENU]
    u.DestroyMenu.restype = wintypes.BOOL
    u.TrackPopupMenu.argtypes = [
        wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND, ctypes.c_void_p
    ]
    u.TrackPopupMenu.restype = ctypes.c_int
    u.GetCursorPos.argtypes = [ctypes.c_void_p]
    u.GetCursorPos.restype = wintypes.BOOL
    s.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.c_void_p]
    s.Shell_NotifyIconW.restype = wintypes.BOOL


_proto()


class Tray:
    """The only tray icon this program adds. Runs its own thread; callbacks fire on it."""

    def __init__(self, icon_path: Path | str, on_open, on_exit, tip: str = __app_name__) -> None:
        self._icon_path = str(icon_path or "")
        self._on_open = on_open
        self._on_exit = on_exit
        self._tip = (tip or __app_name__)[:127]
        self._taskbar_created = 0
        self._wndproc = WNDPROC(self._proc)
        self._hwnd = None
        self._hicon = None
        self._hbig = None
        self._added = False
        self._ready = threading.Event()
        self.error = ""
        self._thread = threading.Thread(target=self._run, name="mac-tray", daemon=True)
        self._thread.start()
        self._ready.wait(5)

    @property
    def ok(self) -> bool:
        return bool(self._added)

    # -- lifecycle -------------------------------------------------------------

    def _run(self) -> None:
        try:
            self._taskbar_created = _user32.RegisterWindowMessageW("TaskbarCreated")
            self._hwnd = self._create_window()
            self._hicon = self._load_icon(_user32.GetSystemMetrics(SM_CXSMICON) or 16)
            self._hbig = self._load_icon(_user32.GetSystemMetrics(SM_CXICON) or 32)
            self._added = self._notify(NIM_ADD, NIF_MESSAGE | NIF_ICON | NIF_TIP | NIF_SHOWTIP)
            if not self._added:
                self.error = "Shell_NotifyIcon add failed (winerror %s)" % ctypes.get_last_error()
        except Exception as e:  # never take the app down over a tray icon
            self.error = str(e)
            write_log("tray failed: " + self.error)
        finally:
            self._ready.set()
        if not self._hwnd:
            return
        msg = wintypes.MSG()
        while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            _user32.TranslateMessage(ctypes.byref(msg))
            _user32.DispatchMessageW(ctypes.byref(msg))
        self._notify(NIM_DELETE, 0)
        self._added = False
        for h in (self._hicon, self._hbig):
            if h:
                _user32.DestroyIcon(h)
        self._hicon = self._hbig = None

    def close(self) -> None:
        if self._hwnd:
            _user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)
            self._thread.join(3)

    def balloon(self, title: str, text: str) -> None:
        """One shell notification. With the AppUserModelID + Start Menu shortcut this
        arrives as a real toast with the app's name; without them it is a balloon."""
        if not self._added:
            return
        data = self._data(NIF_INFO | NIF_ICON | NIF_TIP | NIF_SHOWTIP)
        data.szInfoTitle = (title or "")[:63]
        data.szInfo = (text or "")[:255]
        data.dwInfoFlags = NIIF_USER | NIIF_LARGE_ICON
        data.hBalloonIcon = self._hbig or self._hicon
        _shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(data))

    # -- win32 -----------------------------------------------------------------

    def _create_window(self):
        module = _kernel32.GetModuleHandleW(None)
        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.lpfnWndProc = self._wndproc
        wc.hInstance = module
        wc.lpszClassName = CLASS_NAME
        atom = _user32.RegisterClassExW(ctypes.byref(wc))
        err = ctypes.get_last_error()
        if not atom and err not in (0, CLASS_ALREADY_EXISTS):
            raise ctypes.WinError(err)
        hwnd = _user32.CreateWindowExW(
            WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE, CLASS_NAME, "MACSpoofer.Tray", WS_POPUP,
            0, 0, 0, 0, None, None, module, None,
        )
        if not hwnd:
            raise ctypes.WinError(ctypes.get_last_error())
        if self._taskbar_created:
            _user32.ChangeWindowMessageFilterEx(hwnd, self._taskbar_created, MSGFLT_ALLOW, None)
        return hwnd

    def _load_icon(self, size: int):
        if not self._icon_path:
            return None
        handle = _user32.LoadImageW(None, self._icon_path, IMAGE_ICON, size, size, LR_LOADFROMFILE)
        return handle or None

    def _data(self, flags: int) -> NOTIFYICONDATAW:
        data = NOTIFYICONDATAW()
        data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        data.hWnd = self._hwnd
        data.uID = TRAY_ID
        data.uFlags = flags
        data.uCallbackMessage = WM_APP
        data.hIcon = self._hicon
        data.szTip = self._tip
        return data

    def _notify(self, code: int, flags: int) -> bool:
        if not self._hwnd:
            return False
        data = self._data(flags)
        return bool(_shell32.Shell_NotifyIconW(code, ctypes.byref(data)))

    def _menu(self) -> None:
        menu = _user32.CreatePopupMenu()
        if not menu:
            return
        _user32.AppendMenuW(menu, MF_STRING, ID_OPEN, "Open " + __app_name__)
        _user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        _user32.AppendMenuW(menu, MF_STRING, ID_EXIT, "Exit")
        pt = wintypes.POINT()
        _user32.GetCursorPos(ctypes.byref(pt))
        _user32.SetForegroundWindow(self._hwnd)  # so the menu closes on a click elsewhere
        cmd = _user32.TrackPopupMenu(
            menu, TPM_RIGHTBUTTON | TPM_BOTTOMALIGN | TPM_NONOTIFY | TPM_RETURNCMD,
            pt.x, pt.y, 0, self._hwnd, None,
        )
        _user32.PostMessageW(self._hwnd, WM_NULL, 0, 0)
        _user32.DestroyMenu(menu)
        if cmd == ID_OPEN:
            self._call(self._on_open)
        elif cmd == ID_EXIT:
            self._call(self._on_exit)

    def _call(self, fn) -> None:
        if fn is None:
            return
        try:
            fn()
        except Exception as e:
            write_log("tray action failed: " + str(e))

    def _proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_APP:
            if lparam == WM_RBUTTONUP:
                self._menu()
            elif lparam in (WM_LBUTTONUP, WM_LBUTTONDBLCLK):
                self._call(self._on_open)
            return 0
        if self._taskbar_created and msg == self._taskbar_created:
            self._added = self._notify(NIM_ADD, NIF_MESSAGE | NIF_ICON | NIF_TIP | NIF_SHOWTIP)
            return 0
        if msg == WM_DESTROY:
            _user32.PostQuitMessage(0)
            return 0
        return _user32.DefWindowProcW(hwnd, msg, wparam, lparam)
