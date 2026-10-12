"""Run Chromium + WebKit tablet checks against a local preview server."""
from pathlib import Path
import json
import threading
from http.server import ThreadingHTTPServer
from serve import Handler
from playwright.sync_api import sync_playwright, expect

BASE = Path(__file__).resolve().parent
OUT = BASE / 'test-output'
OUT.mkdir(exist_ok=True)
URL = 'http://127.0.0.1:8765'

def draw(page, pointer_type='pen', offset=0):
    page.locator('#ink').evaluate('''(canvas, input) => {
      const rect = canvas.getBoundingClientRect();
      for (const [type,x,y,p] of [['pointerdown',.2,.2,.2],['pointermove',.3,.21,.8],['pointerup',.4,.22,.6]]) {
        canvas.dispatchEvent(new PointerEvent(type,{bubbles:true,pointerId:17,
          pointerType:input.type,clientX:rect.left+rect.width*x,
          clientY:rect.top+rect.height*y+input.offset,pressure:p}));
      }
    }''', {'type':pointer_type, 'offset':offset})

def records(page):
    return page.evaluate('''async () => {
      const db = await new Promise((resolve,reject) => { const r=indexedDB.open('science-pencil-v1');r.onsuccess=()=>resolve(r.result);r.onerror=reject; });
      return await new Promise(resolve => {const tx=db.transaction('records');const r=tx.objectStore('records').getAll();r.onsuccess=()=>resolve(r.result);});
    }''')

def check(engine, browser_type):
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}'
    browser = browser_type.launch(headless=True)
    context = browser.new_context(viewport={'width':820,'height':1180}, device_scale_factor=2, has_touch=True, accept_downloads=True)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(url)
    expect(page.locator('#save-status')).to_have_text('이 기기에 저장됨')
    page.wait_for_function("document.getElementById('question-image').complete && document.getElementById('question-image').naturalWidth > 0")
    overflow = page.evaluate('''() => ({width:innerWidth, scrollWidth:document.documentElement.scrollWidth,
      items:[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth).map(e=>[e.tagName,e.id,e.className,e.getBoundingClientRect().width,e.getBoundingClientRect().right]).slice(0,20)})''')
    assert overflow['scrollWidth'] <= overflow['width'] + 1, overflow
    first = page.locator('#question-title').inner_text()
    draw(page, 'touch')
    expect(page.locator('#undo')).to_be_disabled()
    draw(page)
    expect(page.locator('#undo')).to_be_enabled()
    expect(page.locator('#save-status')).to_have_text('이 기기에 저장됨')
    note = next(r for r in records(page) if 'strokes' in r)
    assert len(note['strokes']) == 1
    assert note['strokes'][0]['points'][0]['p'] < note['strokes'][0]['points'][1]['p']
    page.locator('#next').click()
    expect(page.locator('#question-title')).not_to_have_text(first)
    expect(page.locator('#undo')).to_be_disabled()
    page.locator('#previous').click()
    expect(page.locator('#question-title')).to_have_text(first)
    expect(page.locator('#undo')).to_be_enabled()
    page.reload()
    expect(page.locator('#question-title')).to_have_text(first)
    expect(page.locator('#undo')).to_be_enabled()
    page.locator('#undo').click()
    expect(page.locator('#undo')).to_be_disabled()
    page.locator('#redo').click()
    expect(page.locator('#undo')).to_be_enabled()
    page.set_viewport_size({'width':1180,'height':820})
    page.set_viewport_size({'width':820,'height':1180})
    expect(page.locator('#save-status')).to_have_text('이 기기에 저장됨')
    assert next(r for r in records(page) if 'strokes' in r)['strokes'] == note['strokes']
    page.locator('[data-tool=eraser]').click()
    draw(page)
    expect(page.locator('#save-status')).to_have_text('이 기기에 저장됨')
    assert next(r for r in records(page) if 'strokes' in r)['strokes'][-1]['tool'] == 'eraser'
    page.locator('#undo').click()
    page.locator('[data-tool=marker]').click()
    draw(page, offset=60)
    page.locator('#bookmark').click()
    expect(page.locator('#bookmark')).to_have_attribute('aria-pressed','true')
    page.locator('#review-only').check()
    page.locator('#filters button').click()
    expect(page.locator('#position')).to_have_text('1 / 1')
    expect(page.locator('#question-title')).to_have_text(first)
    page.locator('#source').click()
    expect(page.locator('#source-dialog')).to_be_visible()
    page.locator('[data-close=source-dialog]').click()
    page.locator('.storage summary').click()
    with page.expect_download() as info:
        page.locator('#export').click()
    backup = OUT / f'{engine}-backup.json'
    info.value.save_as(backup)
    data = json.loads(backup.read_text('utf-8'))
    assert data['format'] == 'science-pencil'
    with page.expect_download() as info:
        page.locator('#download').click()
    info.value.save_as(OUT / f'{engine}-solution.png')
    page.once('dialog', lambda d: d.accept())
    page.locator('#clear').click()
    expect(page.locator('#undo')).to_be_disabled()
    page.once('dialog', lambda d: d.accept())
    page.locator('#backup-file').set_input_files(backup)
    expect(page.locator('#undo')).to_be_enabled()
    expect(page.locator('#toast')).to_contain_text('불러왔습니다')
    page.locator('[data-tool=move]').click()
    assert page.locator('#ink').evaluate("e=>getComputedStyle(e).touchAction") == 'auto'
    page.locator('[data-tool=pen]').click()
    page.screenshot(path=str(OUT / f'{engine}-ipad.png'), full_page=True)
    # Verify the complete question inventory remains available offline.
    page.wait_for_function('navigator.serviceWorker.controller !== null')
    page.locator('#offline').click()
    expect(page.locator('#offline-status')).to_contain_text('355문제와 원본', timeout=120000)
    # Stop the origin, rather than use WebKit's unsupported offline emulation.
    server.shutdown()
    server.server_close()
    page.reload()
    expect(page.locator('#question-title')).to_have_text(first)
    page.wait_for_function("document.getElementById('question-image').complete && document.getElementById('question-image').naturalWidth > 0")
    page.locator('#review-only').uncheck()
    page.locator('#filters button').click()
    expect(page.locator('#position')).to_have_text('1 / 355')
    page.locator('#next').click()
    expect(page.locator('#position')).to_have_text('2 / 355')
    page.wait_for_function("document.getElementById('question-image').complete && document.getElementById('question-image').naturalWidth > 0")
    page.set_viewport_size({'width':390,'height':844})
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
    assert not errors, errors
    context.close(); browser.close()
    print(f'{engine}: tablet layout, pen pressure, touch rejection, undo/redo, eraser, persistence, navigation, rotation, review, export/import, offline PASS', flush=True)

if __name__ == '__main__':
    import sys
    with sync_playwright() as p:
        for engine in sys.argv[1:] or ['chromium','webkit']:
            check(engine, getattr(p, engine))
