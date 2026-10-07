"""Offline prefix matching. Local administration is not proof of randomization."""
import re
import secrets
import sqlite3
import json
from . import BUNDLE

def normalize(value):
    value = str(value).strip()
    if not (re.fullmatch(r'[0-9a-fA-F]{12}', value) or
            re.fullmatch(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', value) or
            re.fullmatch(r'(?:[0-9a-fA-F]{2}-){5}[0-9a-fA-F]{2}', value) or
            re.fullmatch(r'(?:[0-9a-fA-F]{4}\.){2}[0-9a-fA-F]{4}', value)):
        raise ValueError('Enter a 12-digit MAC address, with optional colons, dashes or dotted groups.')
    raw = re.sub(r'[:.\-]', '', value).upper()
    return ':'.join(raw[i:i+2] for i in range(0, 12, 2))

def valid_target(value):
    mac = normalize(value)
    if mac == '00:00:00:00:00:00' or int(mac[:2], 16) & 1:
        raise ValueError('Use a nonzero unicast address. Multicast and broadcast addresses cannot identify an adapter.')
    return mac

class Catalog:
    def __init__(self, path=None):
        self.path = path or BUNDLE / 'data' / 'oui.sqlite3'
        with self.connect() as db:
            self.meta = dict(db.execute('SELECT key,value FROM metadata'))

    def connect(self):
        db = sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True)
        db.row_factory = sqlite3.Row
        return db

    def inspect(self, value):
        mac = normalize(value)
        raw = mac.replace(':', '')
        first = int(raw[:2], 16)
        local, multicast = bool(first & 2), bool(first & 1)
        with self.connect() as db:
            row = db.execute('SELECT * FROM prefixes WHERE prefix IN (?,?,?) ORDER BY length(prefix) DESC LIMIT 1',
                             (raw[:9], raw[:7], raw[:6])).fetchone()
        match = dict(row) if row and not local and not multicast else None
        convention = next((name for prefix, name in [('0242', 'Docker'), ('025056', 'VMware NSX'), ('525400', 'QEMU / KVM')]
                           if raw.startswith(prefix)), None)
        kind = 'Multicast / group' if multicast else 'Locally administered' if local else 'Globally administered'
        if raw == '000000000000': kind = 'Unspecified / all zero'
        if raw == 'FFFFFFFFFFFF': kind = 'Broadcast'
        if match:
            match['sources'] = json.loads(match['sources'])
        return {'mac': mac, 'local': local, 'multicast': multicast, 'kind': kind, 'match': match,
                'convention': convention, 'usable': not multicast and raw != '000000000000',
                'note': ('Local administration does not establish a manufacturer or prove randomization.' if local else
                         'An OUI identifies a registered address block, not a device model or verified hardware identity.')}

    def search(self, query='', limit=60):
        query = str(query).strip()[:120]
        escaped = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        raw = re.sub(r'[:.\-]', '', query).upper()
        with self.connect() as db:
            rows = db.execute("SELECT * FROM prefixes WHERE vendor LIKE ? ESCAPE '\\' OR prefix LIKE ? ESCAPE '\\' ORDER BY vendor,prefix LIMIT ?",
                              ('%' + escaped + '%', raw + '%' if re.fullmatch('[0-9A-F]+', raw) else '!', limit)).fetchall()
        return [dict(row) for row in rows]

    def generate(self, prefix=None, mode='compatible'):
        if mode not in ('compatible', 'exact'):
            raise ValueError('Choose compatible local or exact registered prefix mode.')
        if not prefix:
            octets = bytearray(secrets.token_bytes(6))
            octets[0] = (octets[0] & 0xFC) | 2
            return self.inspect(octets.hex())
        prefix = str(prefix).upper()
        with self.connect() as db:
            row = db.execute('SELECT * FROM prefixes WHERE prefix=?', (prefix,)).fetchone()
        if not row or row['status'] != 'current' or int(prefix[:2], 16) & 3:
            raise ValueError('Select a current globally administered unicast prefix from the catalog.')
        # Nibble precision is essential for MA-M (/28) and MA-S (/36).
        suffix = secrets.token_hex(6).upper()[:12-len(prefix)]
        raw = prefix + suffix
        if mode == 'compatible':
            # Preserve the old GUI's local-bit conversion without claiming a vendor identity.
            raw = f'{int(raw[:2], 16) | 2:02X}' + raw[2:]
        result = self.inspect(raw)
        result['generation'] = {'mode':mode, 'source_prefix':prefix, 'source_vendor':row['vendor']}
        return result
