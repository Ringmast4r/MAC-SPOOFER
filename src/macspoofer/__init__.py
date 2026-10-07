from pathlib import Path
import sys

BUNDLE = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[2]))
__version__ = (BUNDLE / 'VERSION').read_text().strip()
__app_name__ = 'MAC Spoofer'
__app_id__ = 'Ringmast4r.MACSpoofer'
