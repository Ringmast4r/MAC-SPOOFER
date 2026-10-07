"""Read-only packaged app verification and a local-only screenshot."""
import hashlib
import json
import re
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
url='http://127.0.0.1:8802/'
html=urllib.request.urlopen(url).read().decode()
token=re.search(r'name="mac-session" content="([^\"]+)',html)[1]
headers={'X-MAC-Token':token}
state=json.load(urllib.request.urlopen(urllib.request.Request(url+'api/state',headers=headers)))
assert not state['error'],state['error']
assert state['settings']['theme'] in ('light','dark')
assert state['catalog']['records']=='58972'
assert any(a['physical'] for a in state['adapters'])
assert state['intelligence']['signatures']==388354
for name in ['css/style.css','js/app.js','css/intelligence.css','js/intelligence.js','img/nw-globe.png']:
    live=urllib.request.urlopen(url+name).read()
    assert hashlib.sha256(live).digest()==hashlib.sha256((root/'public'/name).read_bytes()).digest(),name
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1240,'height':850})
    errors=[]
    page.on('pageerror',lambda exc:errors.append(str(exc)))
    page.goto(url)
    page.locator('.adapter').first.wait_for()
    from playwright.sync_api import expect
    expect(page.locator('html')).to_have_attribute('data-theme',state['settings']['theme'])
    # Owner may elevate the live app while verification is in progress.
    # Reading the page must never click Apply or Restore.
    assert page.locator('#apply').is_visible()
    assert page.locator('#restore').is_visible()
    page.click('[data-view="fingerprints"]')
    expect(page.locator('#intel-counts')).to_contain_text('388,354')
    expect(page.locator('#profile-results')).to_contain_text('Windows')
    page.fill('#fingerprint-options','1,3,6,15,31,33,43,44,46,47,121,249,252')
    page.click('#fingerprint-check')
    expect(page.locator('#fingerprint-result')).to_contain_text('matching rules')
    expect(page.locator('#fingerprint-result')).to_contain_text('not probabilities')
    page.screenshot(path=str(root/'build/installed-dark-local-only.png'))
    assert not errors,errors
    browser.close()
print('Installed app: saved theme, real read-only enumeration, OUI and Huginn-Muninn corpora, fingerprint lookup and packaged asset hashes passed; zero JS errors. Local screenshot kept under build/.')
