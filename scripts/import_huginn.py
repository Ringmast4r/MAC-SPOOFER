"""Build a bounded offline intelligence index from a local Huginn-Muninn checkout.

Source databases are opened read-only. Only MAC labels overlapping the bundled
registered OUI prefixes are retained; no full device MAC observations are copied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def option55(value):
    value = str(value or '').strip()
    parts = value.split(',')
    if not value or len(parts) > 255 or any(not re.fullmatch(r'\s*\d{1,3}\s*', p) or int(p) > 255 for p in parts):
        return None
    return ','.join(str(int(p)) for p in parts)

@contextmanager
def connect(path):
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try: yield db
    finally: db.close()

def build(source):
    target = ROOT/'data/huginn.sqlite3'
    temporary = target.with_suffix('.building')
    if temporary.exists(): temporary.unlink()
    hashes = []
    def recorded(path):
        with path.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
        hashes.append({'path':path.relative_to(source).as_posix(),'sha256':digest})
        return connect(path)
    with connect(ROOT/'data/oui.sqlite3') as oui:
        allowed = sorted({r[0][:6] for r in oui.execute('SELECT prefix FROM prefixes') if not int(r[0][:2],16)&3})
    meta = {'source':'Ringmast4r/Huginn-Muninn', 'source_url':'https://github.com/Ringmast4r/Huginn-Muninn',
            'built_utc':datetime.now(timezone.utc).isoformat(), 'signature_source_rows':0,
            'ignored_signatures':0, 'invalid_signatures':0, 'mac_source_rows':0, 'association_source_rows':0,
            'satori_source_profiles':0}
    with sqlite3.connect(temporary) as out:
        out.executescript('''
        CREATE TABLE signatures (value TEXT PRIMARY KEY, updated_at TEXT) WITHOUT ROWID;
        CREATE TABLE labels (prefix TEXT, vendor TEXT, PRIMARY KEY(prefix,vendor)) WITHOUT ROWID;
        CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT, vendor TEXT, device_type TEXT,
                               os_name TEXT, updated_at TEXT, source TEXT);
        CREATE TABLE rules (id INTEGER PRIMARY KEY, profile_id INTEGER, signature TEXT,
                            packet_type TEXT, weight TEXT, conditions TEXT, source TEXT);
        CREATE INDEX rule_sequence ON rules(signature);
        CREATE INDEX rule_profile ON rules(profile_id);
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT);
        ''')
        for path in sorted((source/'DHCP_Signatures/sqlite').glob('*.db')):
            batch=[]
            with recorded(path) as db:
                for row in db.execute('SELECT value,updated_at,ignored FROM dhcp_signature'):
                    meta['signature_source_rows']+=1
                    value=option55(row['value'])
                    if row['ignored'] in (1,'1'):
                        meta['ignored_signatures']+=1
                        continue
                    if not value:
                        meta['invalid_signatures']+=1
                        continue
                    batch.append((value,row['updated_at']))
                    if len(batch)==5000:
                        out.executemany('INSERT OR IGNORE INTO signatures VALUES (?,?)',batch);batch=[]
            out.executemany('INSERT OR IGNORE INTO signatures VALUES (?,?)',batch)
        for path in sorted((source/'MAC_Vendors/sqlite').glob('*.db')):
            with recorded(path) as db:
                meta['mac_source_rows']+=db.execute('SELECT COUNT(*) FROM mac_vendor').fetchone()[0]
                db.execute('CREATE TEMP TABLE allowed(prefix TEXT PRIMARY KEY) WITHOUT ROWID')
                db.executemany('INSERT INTO allowed VALUES (?)',[(p,) for p in allowed])
                rows=db.execute('SELECT DISTINCT upper(mac),name FROM mac_vendor WHERE upper(mac) IN (SELECT prefix FROM allowed) AND name IS NOT NULL')
                out.executemany('INSERT OR IGNORE INTO labels VALUES (?,?)',((r[0],str(r[1]).strip()) for r in rows if str(r[1]).strip()))
        path=source/'Satori_Fingerprints/sqlite/dhcp.db'
        with recorded(path) as db:
            for row in db.execute('SELECT * FROM fingerprint'):
                meta['satori_source_profiles']+=1
                tests=json.loads(row['tests'] or '[]')
                rules=[(test,option55(test.get('dhcpoption55'))) for test in tests if test.get('matchtype')=='exact']
                rules=[(test,sig) for test,sig in rules if sig]
                if not rules: continue
                pid=out.execute('INSERT INTO profiles(name,vendor,device_type,os_name,updated_at,source) VALUES (?,?,?,?,?,?)',
                    (row['name'],row['device_vendor'],row['device_type'],row['os_name'],row['last_updated'],'Satori')).lastrowid
                for test,sig in rules:
                    conditions={k:v for k,v in test.items() if k not in ('weight','matchtype','dhcpoption55','dhcptype')}
                    out.execute('INSERT INTO rules(profile_id,signature,packet_type,weight,conditions,source) VALUES (?,?,?,?,?,?)',
                        (pid,sig,test.get('dhcptype','Any'),str(test.get('weight','')),json.dumps(conditions),'Satori exact Option 55 rule'))
        path=source/'Combinations/sqlite/dhcp_combinations.db'
        profiles={}
        with recorded(path) as db:
            for row in db.execute('SELECT * FROM dhcp_combination'):
                meta['association_source_rows']+=1
                sig=option55(row['dhcp_option55'])
                if not sig: continue
                key=(row['satori_name'],row['device_vendor'],row['device_type'])
                if key not in profiles:
                    profiles[key]=out.execute('INSERT INTO profiles(name,vendor,device_type,os_name,updated_at,source) VALUES (?,?,?,?,?,?)',
                        (*key,'','','Huginn-Muninn combinations')).lastrowid
                out.execute('INSERT INTO rules(profile_id,signature,packet_type,weight,conditions,source) VALUES (?,?,?,?,?,?)',
                    (profiles[key],sig,'Not recorded','','{}','Huginn-Muninn association'))
        for table in ('signatures','labels','profiles','rules'):
            meta[table]=out.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
        meta['label_prefixes']=out.execute('SELECT COUNT(DISTINCT prefix) FROM labels').fetchone()[0]
        meta['duplicate_signatures']=meta['signature_source_rows']-meta['ignored_signatures']-meta['invalid_signatures']-meta['signatures']
        assert meta['signatures']>300000 and meta['rules']>500 and meta['labels']>10000, meta
        out.executemany('INSERT INTO metadata VALUES (?,?)',[(k,json.dumps(v)) for k,v in meta.items()])
        out.commit()
        out.execute('VACUUM')
        assert out.execute('PRAGMA quick_check').fetchone()[0]=='ok'
    out.close()  # sqlite's transaction context does not close the Windows file handle.
    temporary.replace(target)
    manifest={**meta,'source_files':hashes,
        'selection':'Non-ignored valid Option 55 sequences; exact Satori and combination associations; MAC corpus labels restricted to registered OUI parent prefixes.',
        'limitations':'Option 55 alone is not full device identification. Conditional rule fields and packet types remain visible. Weights are not probabilities. Source rows are not observed device counts.'}
    (ROOT/'data/huginn-provenance.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(meta,indent=2))
    print('Offline index bytes:',target.stat().st_size)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    build(parser.parse_args().source.resolve())
