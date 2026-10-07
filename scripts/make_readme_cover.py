"""Render a CSS perspective cover from the verified synthetic-data UI screenshot."""
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
shot=base64.b64encode((root/'docs/assets/desktop-dark.png').read_bytes()).decode()
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1500,'height':990},device_scale_factor=1)
    page.set_content('''<!doctype html><html><style>
    *{box-sizing:border-box}body{margin:0;background:#07120e;color:#fff;font-family:Arial,sans-serif;overflow:hidden}
    .grid{position:absolute;inset:0;background:radial-gradient(ellipse at 65% 30%,#1f855f88,transparent 60%),linear-gradient(120deg,#07120e,#111);}
    .title{position:relative;margin:44px 70px;font-size:14px;letter-spacing:4px;color:#75dbb0}
    h1{position:relative;margin:0 70px;font-size:55px;letter-spacing:-2px}h1 span{color:#7abda2}
    .stage{position:relative;perspective:1800px;margin:50px auto;width:1130px}
    img{width:1130px;display:block;border:1px solid #718379;border-radius:6px;transform:rotateY(-12deg) rotateX(7deg) rotateZ(-2deg);box-shadow:22px 30px 0 #0b241b,35px 48px 0 #173c2c,0 45px 85px #000a}
    .note{position:absolute;bottom:24px;left:70px;font:11px monospace;color:#9bb7aa;letter-spacing:2px}
    </style><div class="grid"></div><div class="title">NET WORKS LAB LLC / WINDOWS DESKTOP</div><h1>MAC <span>//</span> SPOOFER</h1><div class="stage"><img src="data:image/png;base64,'''+shot+'''"></div><div class="note">SIN CITY / 58,972 OFFLINE OUI BLOCKS / SYNTHETIC ADAPTER DEMONSTRATION</div></html>''')
    page.screenshot(path=str(root/'docs/assets/desktop-perspective.png'))
    browser.close()
