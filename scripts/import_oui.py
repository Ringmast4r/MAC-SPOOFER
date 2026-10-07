"""Build the offline catalog from a local OUI Master JSON snapshot."""
import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
args = p.parse_args()
raw = args.source.read_bytes()
records = json.loads(raw)
target = root / 'data' / 'oui.sqlite3'
temporary = target.with_suffix('.new')
temporary.unlink(missing_ok=True)
db = sqlite3.connect(temporary)
db.executescript('CREATE TABLE prefixes(prefix TEXT PRIMARY KEY,vendor TEXT,registry TEXT,country TEXT,status TEXT,sources TEXT); CREATE INDEX vendor_idx ON prefixes(vendor); CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);')
rows = []
for key, v in records.items():
    prefix = key.replace(':', '').upper()
    if len(prefix) not in (6,7,9):
        raise ValueError('Unrecognized prefix: ' + key)
    int(prefix, 16)
    rows.append((prefix,v.get('manufacturer') or 'Unknown',v.get('registry') or '',v.get('country') or '',v.get('status') or 'current',json.dumps(v.get('sources') or [])))
db.executemany('INSERT INTO prefixes VALUES (?,?,?,?,?,?)', rows)
meta = {'records': str(len(rows)), 'vendors': str(len({r[1] for r in rows})),
        'source': 'Ringmast4r/OUI-Master-Database / LISTS/master_oui.json',
        'source_sha256': hashlib.sha256(raw).hexdigest(),
        'snapshot_utc': datetime.fromtimestamp(args.source.stat().st_mtime, timezone.utc).isoformat(),
        'built_utc': datetime.now(timezone.utc).isoformat()}
db.executemany('INSERT INTO metadata VALUES (?,?)', meta.items())
db.commit()
db.close()
temporary.replace(target)
(root / 'data' / 'provenance.json').write_text(json.dumps(meta, indent=2)+'\n', encoding='utf-8')
print(json.dumps(meta, indent=2))
