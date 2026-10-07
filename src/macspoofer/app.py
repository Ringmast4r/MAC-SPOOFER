import ctypes
import json
import os
import subprocess
import sys
import threading
from . import BUNDLE
from .paths import DATA
from .log import write_log

class Desktop:
    def __init__(self, service):
        self._service = service
        self._window = None
        self._tray = None
        self._exiting = False

    def quit(self):
        if self._service.busy: raise ValueError('Wait for the adapter operation to finish before exiting.')
        self._exiting = True
        watchdog = threading.Timer(6, lambda: os._exit(0))
        watchdog.daemon = True
        watchdog.start()
        def close():
            if self._tray: self._tray.close()
            self._window.destroy()
        threading.Timer(0.3,close).start()
        return {'ok':True}

    def repo(self):
        import webbrowser
        webbrowser.open('https://github.com/Ringmast4r/MAC-SPOOFER')
        return {'ok':True}

    def elevate(self):
        if self._service.busy: raise ValueError('Wait for the current operation.')
        args = [] if getattr(sys,'frozen',False) else [str(BUNDLE / 'mac_spoofer_gui.py')]
        args += ['--wait-for-exit',str(os.getpid())]
        code = ctypes.windll.shell32.ShellExecuteW(None,'runas',sys.executable,subprocess.list2cmdline(args),str(BUNDLE),1)
        if code <= 32: raise RuntimeError('Administrator restart was cancelled or could not start. This window remains available.')
        return self.quit()

def wait_for_previous():
    if '--wait-for-exit' not in sys.argv: return
    pid = int(sys.argv[sys.argv.index('--wait-for-exit')+1])
    k = ctypes.WinDLL('kernel32',use_last_error=True)
    from ctypes import wintypes
    k.OpenProcess.argtypes = [wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    k.OpenProcess.restype = wintypes.HANDLE
    k.WaitForSingleObject.argtypes = [wintypes.HANDLE,wintypes.DWORD]
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = k.OpenProcess(0x100000,False,pid)
    if handle:
        result = k.WaitForSingleObject(handle,30000)
        k.CloseHandle(handle)
        if result != 0: raise RuntimeError('The previous app instance did not exit.')

def main():
    from .service import Service
    from .server import start_server
    if '--serve' in sys.argv:
        service = Service(preview=True)
        server,url = start_server(service,port=0)
        (DATA / 'preview.json').write_text(json.dumps({'url':url,'pid':os.getpid()}))
        threading.Event().wait()
        return
    wait_for_previous()
    from .shellutil import claim_single_instance, set_process_appid
    if not claim_single_instance(): return
    set_process_appid()
    from .window import run_window
    run_window(Service())
