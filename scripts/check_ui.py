"""Real browser UI checks using a synthetic adapter; never touches host adapters."""
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch
root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
os.environ['MACSPOOFER_DATA']=str(root/'build'/'ui-test-data')
from macspoofer.service import Service
from macspoofer.server import start_server
from playwright.sync_api import sync_playwright

class Fixture:
    def __init__(self): self.mac='00:03:93:12:34:56';self.override=None;self.calls=[]
    def list(self):
        return [{'id':'12345678-1234-1234-1234-123456789012','name':'Ethernet · Demo',
          'description':'Synthetic adapter for interface verification','mac':self.mac,
          'permanent':'00:03:93:12:34:56','status':'Up','physical':True,'speed':'1 Gbps',
          'index':1,'ipv4':['192.0.2.10'],'override':self.override,'registry_available':True}]
    def change(self, adapter_id,address,journal,log):
        self.calls.append((adapter_id,address))
        self.mac=address or '00:03:93:12:34:56';self.override=address
        log('Synthetic adapter: verification completed.')
        return {'status':'verified','message':'Synthetic adapter reports requested address.'}

fixture=Fixture()
with patch('macspoofer.service.is_admin',return_value=True):
    service=Service(engine=fixture)
    service.theme("light")
    server,url=start_server(service,port=0)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True)
            page=browser.new_page(viewport={'width':1240,'height':850},device_scale_factor=1,bypass_csp=True)
            page.set_default_timeout(12000)
            errors=[]
            page.on('pageerror',lambda exc:errors.append(str(exc)))
            page.goto(url)
            page.wait_for_function('window.appReady && document.querySelectorAll(".adapter").length===1')
            assert page.locator('#current-mac').inner_text()=='00:03:93:12:34:56'
            page.click('#generate')
            page.wait_for_function('document.querySelector("#candidate").value.length===17')
            page.wait_for_function('!document.querySelector("#apply").disabled')
            candidate=page.input_value('#candidate')
            assert int(candidate[:2],16)&3==2
            assert not fixture.calls
            page.click('#apply')
            assert page.locator('#confirm-dialog').is_visible()
            page.click('[data-close="confirm-dialog"]')
            assert not fixture.calls
            # A real browser click reaches the simulated engine only after confirmation.
            page.click('#apply');page.click('#confirm-change')
            page.wait_for_function('document.querySelector("#notice").textContent.startsWith("VERIFIED")')
            assert fixture.calls[-1][1]==candidate
            page.click('#restore');page.click('#confirm-change')
            page.wait_for_function('document.querySelector("#current-mac").textContent==="00:03:93:12:34:56"')
            assert fixture.calls[-1][1] is None
            # Invalid input cannot be applied.
            page.fill('#candidate','FF:FF:FF:FF:FF:FF')
            page.wait_for_function('document.querySelector("#candidate-info").textContent.includes("Not valid")')
            assert page.locator('#apply').is_disabled()
            page.click('#choose-vendor')
            page.fill('#vendor-search','Apple')
            page.wait_for_function('document.querySelector("#vendor-results").textContent.includes("Apple")')
            page.locator('#vendor-results button').first.click()
            page.wait_for_function('document.querySelector("#candidate-info").textContent.includes("Apple")')
            assert int(page.input_value('#candidate')[:2],16)&3==0
            page.click('[data-view="catalog"]')
            page.fill('#lookup-mac','52-54-00-12-34-56');page.click('#inspect')
            page.wait_for_function('document.querySelector("#inspection").textContent.includes("QEMU")')
            assert 'No reliable vendor attribution' in page.locator('#inspection').inner_text()
            page.screenshot(path=str(root/'docs/assets/oui-catalog.png'),full_page=True)
            page.click('[data-view="workspace"]')
            page.click('#generate')
            page.wait_for_function('document.querySelector("#candidate-info").textContent.includes("Private address")')
            page.evaluate('window.scrollTo(0,0)')
            page.screenshot(path=str(root/'docs/assets/desktop-light.png'))
            page.click('#theme')
            page.wait_for_function('document.documentElement.dataset.theme==="dark"')
            page.reload();page.wait_for_function('window.appReady')
            assert page.locator('html').get_attribute('data-theme')=='dark'
            page.screenshot(path=str(root/'docs/assets/desktop-dark.png'))
            for width,height in [(900,660),(1240,850),(1600,1000),(650,850)]:
                page.set_viewport_size({'width':width,'height':height})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,height)
            page.set_viewport_size({'width':900,'height':660})
            page.screenshot(path=str(root/'build/ui-minimum.png'),full_page=True)
            page.click('#settings')
            assert page.locator('#settings-dialog').is_visible()
            page.click('[data-close="settings-dialog"]')
            page.click('[data-view="activity"]')
            with page.expect_download() as download:
                page.click('#export')
            report=json.loads(Path(download.value.path()).read_text())
            assert report['company']=='Net Works Lab LLC' and report['adapters'][0]['name']=='Ethernet · Demo'
            assert not errors,errors
            strict=browser.new_page(viewport={'width':1240,'height':850})
            strict.goto(url)
            strict.locator('.adapter').wait_for()
            strict.click('#generate')
            from playwright.sync_api import expect
            expect(strict.locator('#candidate-info')).to_contain_text('Private address')
            strict.close()
            browser.close()
            print('UI PASS: generation, validation, exact vendor, lookup, confirmed apply/restore with simulated engine, theme persistence, four layouts, dialogs, export; no JS errors.')
    finally:
        server.shutdown();server.server_close()
