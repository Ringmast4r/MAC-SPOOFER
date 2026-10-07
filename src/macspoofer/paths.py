from pathlib import Path
import os
from . import BUNDLE

DATA = Path(os.environ.get('MACSPOOFER_DATA', str(Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'NetWorksLab' / 'MACSpoofer')))
DATA.mkdir(parents=True, exist_ok=True)
ROOT = DATA
