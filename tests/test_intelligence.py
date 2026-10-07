import json
import sqlite3
import pytest
from macspoofer.intelligence import Intelligence, option55
from macspoofer.oui import Catalog

@pytest.fixture
def index(tmp_path):
    path=tmp_path/'intel.db'
    with sqlite3.connect(path) as db:
        db.executescript('''
        CREATE TABLE metadata(key TEXT,value TEXT);
        CREATE TABLE signatures(value TEXT PRIMARY KEY,updated_at TEXT);
        CREATE TABLE labels(prefix TEXT,vendor TEXT);
        CREATE TABLE profiles(id INTEGER PRIMARY KEY,name TEXT,vendor TEXT,device_type TEXT,os_name TEXT,updated_at TEXT,source TEXT);
        CREATE TABLE rules(id INTEGER PRIMARY KEY,profile_id INTEGER,signature TEXT,packet_type TEXT,weight TEXT,conditions TEXT,source TEXT);
        ''')
        db.execute('INSERT INTO metadata VALUES (?,?)',('source',json.dumps('Synthetic corpus')))
        db.executemany('INSERT INTO signatures VALUES (?,?)',[('1,3,6','2026-01-01'),('2,4,6','2026-01-01')])
        db.executemany('INSERT INTO labels VALUES (?,?)',[('000393','Apple'),('020393','Not valid as local attribution')])
        db.execute('INSERT INTO profiles VALUES (1,?,?,?,?,?,?)',('Test Device','Test Vendor','Computer','Test OS','2020-01-01','Satori'))
        db.execute('INSERT INTO rules VALUES (1,1,?,?,?,?,?)',('1,3,6','Discover','5',json.dumps({'dhcpvendorcode':'TEST'}),'Satori exact Option 55 rule'))
    return Intelligence(path)

def test_normalize_keeps_parameter_order():
    assert option55(' 01, 003,6 ')=='1,3,6'
    assert option55('6,3,1')!='1,3,6'

@pytest.mark.parametrize('value',['','1,,3','1;3;6','256,1','-1,3','1,2.0',','.join(['1']*256)])
def test_malformed_sequence_rejected(value):
    with pytest.raises(ValueError): option55(value)

def test_known_without_mapping_is_not_device_identification(index):
    result=index.dhcp('2,4,6')
    assert result['known_signature'] and result['matches']==[] and result['total_rules']==0
    assert not index.dhcp('6,4,2')['known_signature']

def test_rule_keeps_unchecked_conditions_and_weight(index):
    result=index.dhcp(' 1,3,6 ')
    match=result['matches'][0]
    assert match['packet_type']=='Discover' and match['conditions']=={'dhcpvendorcode':'TEST'}
    assert match['weight']=='5' and 'confidence' not in match
    assert 'not checked' in result['scope']

def test_local_and_multicast_have_no_vendor_corroboration(index):
    assert index.labels('00:03:93:12:34:56')==['Apple']
    assert index.labels('02:03:93:12:34:56')==[]
    assert index.labels('01:03:93:12:34:56')==[]

def test_search_and_reference_validation(index):
    rows=index.profiles('Test')
    assert len(rows)==1 and rows[0]['rules']==1
    assert index.profiles("%' OR 1=1 --")==[]
    assert index.profile(1)['rules'][0]['signature']=='1,3,6'
    with pytest.raises(ValueError): index.profile('not-an-id')
    with pytest.raises(ValueError): index.profile(999)

def test_adviser_checks_host_collisions_and_hardware_address(index):
    info=Catalog().inspect('02:03:93:12:34:56')
    adapter={'id':'one','name':'Ethernet','physical':True,'permanent':'00:03:93:12:34:56'}
    other={'id':'two','name':'Wi-Fi','mac':info['mac']}
    advice=index.advice(info,adapter,[other])
    assert advice['tone']=='warning' and 'Wi-Fi' in advice['issues'][0]
    assert advice['corpus_labels']==[]
    hardware=index.advice(Catalog().inspect(adapter['permanent']),adapter,[])
    assert hardware['tone']=='warning' and 'hardware address' in hardware['title']

def test_missing_index_does_not_break_basic_advice(tmp_path):
    index=Intelligence(tmp_path/'missing.sqlite3')
    assert not index.meta['available']
    assert index.advice(Catalog().inspect('02:03:93:12:34:56'))['tone']=='good'
    with pytest.raises(ValueError,match='unavailable'): index.dhcp('1,3,6')

def test_bundled_corpus_is_real_and_reports_filtered_coverage():
    index=Intelligence()
    assert index.meta['signatures']==388354 and index.meta['invalid_signatures']==121474
    assert index.meta['rules']==1374 and index.meta['labels']==40289
    assert index.profiles('Windows 10')
    assert index.dhcp('1,3,6,15,31,33,43,44,46,47,121,249,252')['total_rules']>0
