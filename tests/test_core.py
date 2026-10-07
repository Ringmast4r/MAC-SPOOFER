import json
import re
import urllib.request
import urllib.error
import pytest
from macspoofer.oui import Catalog, normalize, valid_target
from macspoofer import engine
from macspoofer.engine import WindowsAdapters
from macspoofer.server import start_server

@pytest.mark.parametrize('value',['aa:bb:cc:dd:ee:00','AA-BB-CC-DD-EE-00','aabb.ccdd.ee00','aabbccddee00'])
def test_notation(value): assert normalize(value)=='AA:BB:CC:DD:EE:00'

@pytest.mark.parametrize('value',['00:00:00:00:00:00','ff:ff:ff:ff:ff:ff','01:00:5e:00:00:01','not a mac','00:11-22:33:44:55'])
def test_reject_invalid_target(value):
    with pytest.raises(ValueError): valid_target(value)

def test_generation_bits_and_local_attribution():
    c=Catalog()
    generated=[c.generate() for _ in range(100)]
    assert len({a['mac'] for a in generated})==100
    assert all(a['local'] and a['usable'] and not a['match'] for a in generated)
    intel=c.inspect('52-54-00-12-34-56')
    assert intel['convention']=='QEMU / KVM' and intel['local'] and intel['match'] is None

def test_longest_prefix_and_vendor_bits():
    c=Catalog()
    with c.connect() as db:
        for length in (6,7,9):
            r=db.execute("SELECT prefix FROM prefixes WHERE length(prefix)=? AND status='current' AND substr(prefix,2,1) IN ('0','4','8','C') LIMIT 1",(length,)).fetchone()
            info=c.generate(r['prefix'], mode='exact')
            assert info['mac'].replace(':','').startswith(r['prefix'])
            assert not info['local'] and not info['multicast']
            assert len(info['match']['prefix'])>=length
    assert c.inspect('00:03:93:12:34:56')['match']['vendor']=='Apple'
    assert c.search('Apple')
    assert c.search("%' OR 1=1 --")==[]

def test_vendor_generation_defaults_to_legacy_local_conversion(monkeypatch):
    c=Catalog()
    monkeypatch.setattr('macspoofer.oui.secrets.token_hex', lambda _: 'ABCDEF123456')
    with c.connect() as db:
        for length in (6,7,9):
            row=db.execute("SELECT prefix FROM prefixes WHERE length(prefix)=? AND status='current' AND substr(prefix,2,1) IN ('0','4','8','C') LIMIT 1",(length,)).fetchone()
            exact=c.generate(row['prefix'],mode='exact')
            local=c.generate(row['prefix'])
            assert local['mac'][2:]==exact['mac'][2:]
            assert int(local['mac'][:2],16)==(int(exact['mac'][:2],16)|2)
            assert local['local'] and local['usable'] and local['match'] is None
            assert local['generation']['source_prefix']==row['prefix']
    with pytest.raises(ValueError): c.generate('000393',mode='unknown')

ID='12345678-1234-1234-1234-123456789012'
BEFORE='00:11:22:33:44:55'
AFTER='02:12:34:56:78:90'
class Fake(WindowsAdapters):
    def __init__(self, reject=False, permanent=BEFORE, fail_restart=False):
        self.override=('021122334455',1)
        self.mac=BEFORE
        self.permanent=permanent
        self.reject=reject
        self.restarts=0
        self.writes=[]
        self.fail_restart=fail_restart
    def list(self): return [{'id':ID,'name':"Adapter [1]';x",'mac':self.mac,'permanent':self.permanent,'status':'Up'}]
    def registry_path(self, adapter_id): assert adapter_id==ID; return 'exact-key'
    def read_override(self,path): return self.override
    def write_override(self,path,value): self.writes.append(value);self.override=value
    def restart(self, adapter_id):
        self.restarts+=1
        if self.fail_restart: raise RuntimeError('driver restart failed')
        if not self.reject:self.mac=normalize(self.override[0]) if self.override else self.permanent

def test_apply_verifies_and_journals_before_mutation(monkeypatch):
    monkeypatch.setattr(engine,'is_admin',lambda:True)
    f=Fake();records=[]
    def journal(r):assert not f.writes;records.append(r)
    result=f.change(ID,AFTER,journal,lambda _:None,wait=lambda _:None)
    assert result['status']=='verified' and result['observed']==AFTER
    assert records[0]['previous_override']==('021122334455',1)
    assert f.restarts==2

def test_driver_rejection_restores_exact_previous_override(monkeypatch):
    monkeypatch.setattr(engine,'is_admin',lambda:True)
    f=Fake(reject=True)
    with pytest.raises(RuntimeError,match='did not report'):
        f.change(ID,AFTER,lambda _:None,lambda _:None,wait=lambda _:None)
    assert f.override==('021122334455',1) and f.restarts==3

def test_restart_failure_is_not_success(monkeypatch):
    monkeypatch.setattr(engine,'is_admin',lambda:True)
    f=Fake(fail_restart=True)
    with pytest.raises(RuntimeError,match='Recovery needs attention'):
        f.change(ID,AFTER,lambda _:None,lambda _:None,wait=lambda _:None)
    assert f.override==('021122334455',1)

def test_driver_requiring_reset_before_replacement(monkeypatch):
    monkeypatch.setattr(engine,'is_admin',lambda:True)
    class NeedsReset(Fake):
        clean=False
        def restart(self, adapter_id):
            if self.override is None: self.clean=True
            elif self.override[0]==AFTER.replace(':','') and not self.clean:
                self.restarts+=1
                return  # Driver keeps its old address without a baseline reset.
            super().restart(adapter_id)
    f=NeedsReset()
    result=f.change(ID,AFTER,lambda _:None,lambda _:None,wait=lambda _:None)
    assert result['status']=='verified' and result['observed']==AFTER
    assert f.writes==[None,(AFTER.replace(':',''),1)]

def test_failure_during_baseline_reset_recovers_previous_value(monkeypatch):
    monkeypatch.setattr(engine,'is_admin',lambda:True)
    class ResetFailsOnce(Fake):
        def restart(self, adapter_id):
            if not self.restarts:
                self.restarts+=1
                raise RuntimeError('baseline reset failed')
            super().restart(adapter_id)
    f=ResetFailsOnce()
    with pytest.raises(RuntimeError,match='baseline reset failed'):
        f.change(ID,AFTER,lambda _:None,lambda _:None,wait=lambda _:None)
    assert f.override==('021122334455',1)
    assert f.mac=='02:11:22:33:44:55' and f.restarts==2

def test_transient_enumeration_after_restart_is_retried(monkeypatch):
    monkeypatch.setattr(engine,'is_admin',lambda:True)
    class ReturningDevice(Fake):
        unavailable=2
        def list(self):
            if self.restarts==2 and self.unavailable:
                self.unavailable-=1
                raise RuntimeError('adapter enumeration not ready')
            return super().list()
    f=ReturningDevice()
    result=f.change(ID,AFTER,lambda _:None,lambda _:None,wait=lambda _:None)
    assert result['status']=='verified' and result['observed']==AFTER
    assert f.override==(AFTER.replace(':',''),1) and f.restarts==2

def test_restore_removes_override(monkeypatch):
    monkeypatch.setattr(engine,'is_admin',lambda:True)
    f=Fake()
    assert f.change(ID,None,lambda _:None,lambda _:None)['status']=='verified'
    assert f.override is None

def test_restore_unknown_hardware_is_unverified(monkeypatch):
    monkeypatch.setattr(engine,'is_admin',lambda:True)
    f=Fake(permanent=None)
    assert f.change(ID,None,lambda _:None,lambda _:None)['status']=='unverified'

def test_elevation_required_before_any_mutation(monkeypatch):
    monkeypatch.setattr(engine,'is_admin',lambda:False)
    f=Fake()
    with pytest.raises(PermissionError):f.change(ID,AFTER,lambda _:None,lambda _:None)
    assert not f.writes

def test_http_session_and_preview_guard():
    from macspoofer.service import Service
    svc=Service(engine=Fake(),preview=True)
    server,url=start_server(svc,port=0)
    try:
        html=urllib.request.urlopen(url).read().decode()
        token=re.search(r'name="mac-session" content="([^"]+)',html)[1]
        with pytest.raises(urllib.error.HTTPError) as exc: urllib.request.urlopen(url+'api/state')
        assert exc.value.code==403
        def request(path,body=None,extra=None):
            headers={'X-MAC-Token':token,'Content-Type':'application/json'};headers.update(extra or {})
            return urllib.request.urlopen(urllib.request.Request(url+path,data=json.dumps(body).encode() if body is not None else None,headers=headers))
        assert json.load(request('api/state'))['preview']
        assert json.load(request('api/generate',{'prefix':'000393'}))['local']
        assert not json.load(request('api/generate',{'prefix':'000393','mode':'exact'}))['local']
        assert json.load(request('api/advice?mac=02:03:93:12:34:56'))['corpus_labels']==[]
        assert json.load(request('api/profiles?q=Windows'))
        assert json.load(request('api/fingerprints?options=1,3,6,15,31,33,43,44,46,47,121,249,252'))['total_rules']>0
        with pytest.raises(urllib.error.HTTPError) as exc:request('api/change',{'id':ID,'address':AFTER,'confirmed':True})
        assert exc.value.code==403 and not svc.engine.writes
        with pytest.raises(urllib.error.HTTPError) as exc:request('api/generate',{}, {'Origin':'https://example.com'})
        assert exc.value.code==403
        with pytest.raises(urllib.error.HTTPError) as exc:request('../VERSION')
        assert exc.value.code==404
    finally:server.shutdown();server.server_close()
