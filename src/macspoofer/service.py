import json
import threading
from datetime import datetime
from . import __version__
from .engine import WindowsAdapters, is_admin
from .oui import Catalog, valid_target
from .paths import DATA
from .log import write_log

def timestamp():
    return datetime.now().astimezone().isoformat(timespec='seconds')

def save_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(path)

class Service:
    def __init__(self, engine=None, catalog=None, preview=False):
        self.engine = engine or WindowsAdapters()
        self.catalog = catalog or Catalog()
        self.preview = preview
        self.lock = threading.RLock()
        self.adapters = []
        self.refreshing = False
        self.error = ''
        self.updated = None
        self.busy = False
        self.result = None
        self.events = []
        self.ui = {}
        self.settings = {'theme':'light'}
        try: self.settings.update(json.loads((DATA / 'settings.json').read_text()))
        except (OSError, ValueError): pass
        self.log('Ready. Select an adapter to inspect its address.')
        self.refresh()

    def log(self, message):
        with self.lock:
            self.events.append({'time':timestamp(), 'message':str(message)})
            self.events = self.events[-200:]
        write_log(message)

    def state(self):
        with self.lock:
            return {'version':__version__, 'admin':is_admin() and not self.preview, 'preview':self.preview,
                    'adapters':list(self.adapters),'refreshing':self.refreshing,'error':self.error,'updated':self.updated,
                    'busy':self.busy,'result':self.result,'events':list(self.events),'settings':dict(self.settings),
                    'catalog':self.catalog.meta}

    def refresh(self):
        with self.lock:
            if self.refreshing or self.busy: return {'ok':True}
            self.refreshing = True
        def work():
            try:
                adapters = self.engine.list()
                for item in adapters:
                    item['intel'] = self.catalog.inspect(item['mac']) if item['mac'] else None
                with self.lock:
                    self.adapters, self.updated, self.error = adapters, timestamp(), ''
            except Exception as exc:
                with self.lock: self.error = str(exc)
                self.log('Adapter refresh failed: ' + str(exc))
            finally:
                with self.lock: self.refreshing = False
        threading.Thread(target=work, daemon=True).start()
        return {'ok':True}

    def theme(self, theme):
        if theme not in ('light','dark'): raise ValueError('Unknown theme.')
        with self.lock:
            self.settings['theme'] = theme
            save_json(DATA / 'settings.json', self.settings)
        return {'ok':True}

    def change(self, adapter_id, address, confirmed=False):
        if self.preview: raise PermissionError('Preview mode cannot modify adapters.')
        if not confirmed: raise ValueError('Confirm the selected adapter and connection restart first.')
        if not is_admin(): raise PermissionError('Relaunch as administrator before changing an adapter.')
        address = valid_target(address) if address is not None else None
        with self.lock:
            if self.busy or self.refreshing: raise ValueError('Wait for the current adapter operation to finish.')
            self.busy, self.result = True, None
        def journal(record):
            record['time'] = timestamp()
            with (DATA / 'changes.jsonl').open('a', encoding='utf-8') as f:
                f.write(json.dumps(record)+'\n')
                f.flush()
                import os
                os.fsync(f.fileno())
        def work():
            try:
                result = self.engine.change(adapter_id, address, journal, self.log)
            except Exception as exc:
                result = {'status':'failed','message':str(exc)}
            with self.lock:
                self.result = {**result, 'time':timestamp()}
                self.busy = False
            self.log(result['message'])
            self.refresh()
        threading.Thread(target=work, daemon=True).start()
        return {'ok':True}
