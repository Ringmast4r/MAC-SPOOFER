# Build wrapper for the canonical portable specification.
from pathlib import Path
root=Path(SPECPATH)
SPECPATH=str(root/"packager")
exec((root/"packager/MAC_Spoofer.spec").read_text())
