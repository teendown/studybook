"""Embed every social asset into one transferable HTML file."""
from pathlib import Path
import base64
import json
import re

BASE = Path(__file__).resolve().parent
DIST = BASE / 'dist' / 'social'
OUTPUT1 = Path(r'D:\문제지다운로드\개년완성통합사회2\통합사회2_아이패드_필기.html')
OUTPUT2 = BASE.parent / '통합사회2_아이패드_필기.html'

def data_url(path):
    mime = 'image/webp' if path.suffix == '.webp' else 'image/png'
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode('ascii')

def replace_once(source, before, after):
    assert source.count(before) == 1, f'Expected one replacement: {before[:80]}'
    return source.replace(before, after, 1)

def main():
    html = (DIST / 'index.html').read_text('utf-8')
    css = (DIST / 'style.css').read_text('utf-8')
    app = (DIST / 'app.js').read_text('utf-8')
    questions = json.loads((DIST / 'questions.json').read_text('utf-8'))
    paths = sorted({q[key] for q in questions for key in ('image','source')})
    assets = {name: data_url(DIST / name) for name in paths}
    bundle = json.dumps({'questions':questions, 'assets':assets}, ensure_ascii=False, separators=(',',':'))
    
    html = replace_once(html, '<link rel="manifest" href="manifest.webmanifest">', '')
    for size in (180,192):
        html = html.replace(f'href="icon-{size}.png"', f'href="{data_url(DIST / f"icon-{size}.png")}"')

    banner_css = """
.single-file-note {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 20px;
  background: #eaf0f6;
  border-bottom: 1px solid #ccd9e5;
  color: #1a2e40;
  font-size: 13px;
  line-height: 1.5;
}
.single-file-note .banner-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.single-file-note .badge {
  background: #1a2e40;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 9px;
  border-radius: 12px;
  letter-spacing: -0.2px;
}
.single-file-note .banner-close {
  background: transparent;
  border: 0;
  color: #1a2e40;
  font-size: 15px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  min-height: unset;
  line-height: 1;
}
"""
    html = replace_once(html, '<link rel="stylesheet" href="style.css">', f'<style>{css}\n{banner_css}</style>')
    html = replace_once(html, '<script src="app.js" defer></script>', '')
    html = replace_once(html, 'class="brand" href="./"', 'class="brand" href="#"')
    
    banner_html = '''<body>
<div class="single-file-note" id="offline-banner">
  <div class="banner-content">
    <span class="badge">완전 오프라인 단일 파일</span>
    <span><strong>비밀번호·로그인 없음</strong> · 365개 전 문제와 원본 그림이 내장되어 있어 다른 기기에서도 파일 하나로 바로 열립니다.</span>
  </div>
  <button type="button" class="banner-close" onclick="document.getElementById('offline-banner').style.display='none'" aria-label="안내 닫기">✕</button>
</div>
'''
    html = replace_once(html, '<body>', banner_html)
    html = html.replace('<button id="offline">오프라인용 문제 저장</button>', '<button id="offline" hidden>모든 문제 포함됨</button>')
    html = html.replace('<span id="offline-status" role="status"></span>', '<span id="offline-status" role="status">이 파일에 365개 전 문제와 이미지가 내장되어 있어 비밀번호나 인터넷 없이 언제든 열 수 있습니다.</span>')

    app = replace_once(app,
        "const response = await fetch('questions.json'); if (!response.ok) throw new Error('문제 목록을 불러올 수 없습니다.');\n    questions = await response.json();",
        "questions = window.SOCIETY_BUNDLE.questions.map(q => ({...q, image:window.SOCIETY_BUNDLE.assets[q.image], source:window.SOCIETY_BUNDLE.assets[q.source]}));")
    app = replace_once(app,
        "if ('serviceWorker' in navigator && window.isSecureContext) navigator.serviceWorker.register('sw.js').then(reg => { reg.update(); }).catch(() => { $('offline-status').textContent = '오프라인 기능을 준비하지 못했습니다. 온라인 학습은 가능합니다.'; });",
        '// Standalone file: every asset is embedded; no service worker or server is needed.')
    
    app = re.sub(r"\$\('offline'\)\.onclick = async \(\) => \{.*?\n\};", "$('offline').onclick = () => toast('모든 문제와 이미지가 이미 이 파일에 들어 있습니다.');", app, flags=re.S)
    
    script = ('window.SOCIETY_BUNDLE=' + bundle + ';\n' + app).replace('</script', '<\\/script')
    html = replace_once(html, '</body></html>', f'<script>{script}</script>\n</body></html>')
    
    OUTPUT1.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT1.write_text(html, 'utf-8')
    OUTPUT2.write_text(html, 'utf-8')
    print(f'Social single file generated: {OUTPUT1.stat().st_size / 1024 / 1024:.1f} MiB; {len(questions)} questions')

if __name__ == '__main__':
    main()
