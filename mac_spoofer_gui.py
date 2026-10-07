"""Native desktop entry point; historical Tkinter source is in legacy/."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
if __name__ == '__main__':
    try:
        from macspoofer.app import main
        main()
    except Exception:
        import traceback
        details=traceback.format_exc()
        from macspoofer.log import write_log
        write_log(details)
        if '--serve' in sys.argv: raise
        import ctypes
        ctypes.windll.user32.MessageBoxW(None,details[-1800:],'MAC // Spoofer could not start',0x10)
