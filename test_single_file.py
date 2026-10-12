"""Verify the portable deliverable with networking blocked."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from test_browser import draw

FILE = Path(__file__).resolve().parent.parent / '통합과학2_아이패드_필기.html'
with sync_playwright() as p:
    for name in ('chromium','webkit'):
        browser = getattr(p,name).launch()
        context = browser.new_context(viewport={'width':820,'height':1180},has_touch=True)
        requests, errors = [], []
        context.route('http://**/*', lambda route: (requests.append(route.request.url), route.abort()))
        context.route('https://**/*', lambda route: (requests.append(route.request.url), route.abort()))
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(FILE.as_uri())
        expect(page.locator('#question-title')).to_contain_text('문제 ')
        page.wait_for_function("document.getElementById('question-image').naturalWidth > 0")
        assert page.evaluate('window.SCIENCE_BUNDLE.questions.length') == 355
        assert page.locator('#question-image').get_attribute('src').startswith('data:image/webp;base64,')
        first = page.locator('#question-title').inner_text()
        draw(page)
        expect(page.locator('#undo')).to_be_enabled()
        page.locator('#next').click()
        expect(page.locator('#question-title')).not_to_have_text(first)
        page.locator('#previous').click()
        expect(page.locator('#question-title')).to_have_text(first)
        expect(page.locator('#undo')).to_be_enabled()
        page.locator('#source').click()
        expect(page.locator('#source-dialog')).to_be_visible()
        assert page.locator('#source-image').get_attribute('src').startswith('data:image/webp;base64,')
        page.locator('[data-close=source-dialog]').click()
        page.locator('#undo').click()
        expect(page.locator('#undo')).to_be_disabled()
        page.locator('#redo').click()
        expect(page.locator('#undo')).to_be_enabled()
        page.locator('.storage summary').click()
        with page.expect_download() as downloaded:
            page.locator('#export').click()
        assert downloaded.value.suggested_filename.endswith('.json')
        assert not requests, requests
        assert not errors, errors
        print(f'{name}: file:// opened, 355 questions, embedded images, pen, navigation, undo/redo, backup, zero network requests PASS', flush=True)
        context.close(); browser.close()
