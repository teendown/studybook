import threading
from http.server import ThreadingHTTPServer
from serve import Handler
from playwright.sync_api import sync_playwright
from pathlib import Path

ARTIFACT_DIR = Path(r'C:\Users\PC\.gemini\antigravity-ide\brain\26f9fb11-0771-4ee1-a413-f451b950f040')

server = ThreadingHTTPServer(('127.0.0.1', 8999), Handler)
t = threading.Thread(target=server.serve_forever, daemon=True)
t.start()

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(viewport={'width': 1024, 'height': 1200}, device_scale_factor=2)
    page = context.new_page()
    
    # 1. Dashboard
    page.goto('http://127.0.0.1:8999/')
    page.wait_for_timeout(1000)
    dash_path = ARTIFACT_DIR / 'dashboard_preview.png'
    page.screenshot(path=str(dash_path))
    print('Dashboard screenshot saved to', dash_path)
    
    # 2. Social Studies
    page.goto('http://127.0.0.1:8999/social/')
    page.wait_for_function("document.getElementById('question-image').complete && document.getElementById('question-image').naturalWidth > 0")
    page.wait_for_timeout(1000)
    soc_path = ARTIFACT_DIR / 'social_preview.png'
    page.screenshot(path=str(soc_path))
    print('Social studies screenshot saved to', soc_path)

    # 3. Science
    page.goto('http://127.0.0.1:8999/science/')
    page.wait_for_function("document.getElementById('question-image').complete && document.getElementById('question-image').naturalWidth > 0")
    page.wait_for_timeout(1000)
    sci_path = ARTIFACT_DIR / 'science_preview.png'
    page.screenshot(path=str(sci_path))
    print('Science screenshot saved to', sci_path)
    
    browser.close()

server.shutdown()
print('All previews captured successfully!')
