"""Offline address guidance and evidence-limited Huginn-Muninn lookups."""
import json
import re
import sqlite3
from contextlib import contextmanager
from . import BUNDLE
from .oui import normalize

def option55(value):
    parts=str(value or '').strip().split(',')
    if len(parts)>255 or any(not re.fullmatch(r'\s*\d{1,3}\s*', p) or int(p)>255 for p in parts):
        raise ValueError('Enter 1–255 DHCP option numbers from 0 to 255, separated by commas. Order matters.')
    return ','.join(str(int(p)) for p in parts)

class Intelligence:
    def __init__(self, path=None):
        self.path=path or BUNDLE/'data/huginn.sqlite3'
        try:
            with self.connect() as db:
                self.meta={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
            self.meta['available']=True
        except (OSError,sqlite3.Error,ValueError):
            self.meta={'available':False,'error':'Offline Huginn-Muninn index unavailable.'}

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path.resolve().as_uri()+'?mode=ro',uri=True,timeout=3)
        db.row_factory=sqlite3.Row
        try: yield db
        finally: db.close()

    def require(self):
        if not self.meta['available']: raise ValueError(self.meta['error'])

    def labels(self, value):
        mac=normalize(value)
        if not self.meta['available'] or int(mac[:2],16)&3: return []
        with self.connect() as db:
            return [r[0] for r in db.execute('SELECT vendor FROM labels WHERE prefix=? ORDER BY vendor LIMIT 12',(mac.replace(':','')[:6],))]

    def dhcp(self, value):
        self.require()
        value=option55(value)
        with self.connect() as db:
            known=db.execute('SELECT updated_at FROM signatures WHERE value=?',(value,)).fetchone()
            count=db.execute('SELECT COUNT(*) FROM rules WHERE signature=?',(value,)).fetchone()[0]
            rows=db.execute('''SELECT p.name,p.vendor,p.device_type,p.updated_at,r.packet_type,
                r.weight,r.conditions,r.source FROM rules r JOIN profiles p ON p.id=r.profile_id
                WHERE r.signature=? ORDER BY p.name,r.source,r.packet_type LIMIT 60''',(value,)).fetchall()
        matches=[{**dict(row),'conditions':json.loads(row['conditions'])} for row in rows]
        return {'query':value,'known_signature':bool(known),'catalog_updated_at':known[0] if known else None,
                'matches':matches,'total_rules':count,'truncated':count>len(matches),
                'scope':'Exact Option 55 sequence only. Packet type and other rule conditions are not checked.',
                'note':'A sequence can match several device families. Corpus weights are not probabilities. No match does not establish anonymity.'}

    def profiles(self, query='', limit=40):
        self.require()
        query=str(query).strip()[:100]
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
        with self.connect() as db:
            rows=db.execute('''SELECT p.*,COUNT(r.id) AS rules FROM profiles p
                JOIN rules r ON r.profile_id=p.id
                WHERE p.name LIKE ? ESCAPE '\\' OR p.vendor LIKE ? ESCAPE '\\' OR p.device_type LIKE ? ESCAPE '\\'
                GROUP BY p.id ORDER BY p.name,p.source LIMIT ?''',('%'+escaped+'%',)*3+(limit,)).fetchall()
        return [dict(row) for row in rows]

    def profile(self, profile_id):
        self.require()
        try: profile_id=int(profile_id)
        except (TypeError,ValueError): raise ValueError('Select a fingerprint reference.')
        with self.connect() as db:
            row=db.execute('SELECT * FROM profiles WHERE id=?',(profile_id,)).fetchone()
            if not row: raise ValueError('Fingerprint reference not found.')
            total=db.execute('SELECT COUNT(*) FROM rules WHERE profile_id=?',(profile_id,)).fetchone()[0]
            rules=db.execute('SELECT signature,packet_type,weight,conditions,source FROM rules WHERE profile_id=? ORDER BY id LIMIT 20',(profile_id,)).fetchall()
        return {**dict(row),'total_rules':total,'truncated':total>len(rules),
                'rules':[{**dict(r),'conditions':json.loads(r['conditions'])} for r in rules]}

    def advice(self, info, adapter=None, adapters=()):
        mac=info['mac']
        local=info['local']
        issues=[]
        if not info['usable']:
            title='This address cannot identify an adapter.';tone='warning'
        elif local:
            title='Local unicast: the recommended format for a private address.';tone='good'
        else:
            title='Registered-style address: useful for testing, not extra anonymity.';tone='note'
            issues.append('An exact vendor prefix can be rejected by a driver. Compatible local preserves the old app’s conversion, but no longer identifies that vendor.')
        if adapter and mac==adapter.get('permanent'):
            title='This is the adapter’s reported hardware address.';tone='warning'
            issues.append('Using the hardware address preserves its stable link-layer identifier.')
        collisions=[a['name'] for a in adapters if a.get('id')!=(adapter or {}).get('id') and a.get('mac')==mac]
        if collisions:
            tone='warning';title='Another adapter on this computer already reports this address.'
            issues.append('Duplicate: '+', '.join(collisions)+'. Generate a different address to avoid a local collision.')
        if adapter and not adapter.get('physical',True):
            issues.append('This is a virtual adapter. Changing it does not necessarily change the physical Wi-Fi or Ethernet address.')
        if info.get('convention'):
            issues.append('This address resembles the '+info['convention']+' convention. That resemblance does not establish a runtime or improve privacy.')
        return {'mac':mac,'title':title,'tone':tone,'issues':issues,
                'registered_owner':info['match']['vendor'] if info.get('match') else None,
                'corpus_labels':self.labels(mac),'corpus_available':self.meta['available'],
                'compatibility':'Valid format is not verified driver support. Apply checks the address Windows actually reports.',
                'scope':'Checked against this computer’s adapters only; other devices on the LAN were not checked.',
                'privacy':'A MAC change does not alter DHCP fingerprints, hostnames, discovery services, public IP addresses, or signed-in accounts.'}
