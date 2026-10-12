"""Embed every asset into one transferable HTML file, with no build/runtime dependency."""
from pathlib import Path
import base64
import json
import re

BASE = Path(__file__).resolve().parent
DIST = BASE / 'dist'
OUTPUT = BASE.parent / '통합과학2_아이패드_필기.html'

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
  background: #eef6f2;
  border-bottom: 1px solid #cce3d8;
  color: #133d38;
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
  background: #133d38;
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
  color: #133d38;
  font-size: 15px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  min-height: unset;
  line-height: 1;
}
.single-file-note .banner-close:hover {
  background: #d5ebd0;
}
"""
    html = replace_once(html, '<link rel="stylesheet" href="style.css">', f'<style>{css}\n{banner_css}</style>')
    html = replace_once(html, '<script src="app.js" defer></script>', '')
    html = replace_once(html, 'class="brand" href="./"', 'class="brand" href="#"')
    
    banner_html = '''<body>
<div class="single-file-note" id="offline-banner">
  <div class="banner-content">
    <span class="badge">완전 오프라인 단일 파일</span>
    <span><strong>비밀번호·로그인 없음</strong> · 355개 전 문제와 원본 그림이 내장되어 있어 다른 기기에서도 파일 하나로 바로 열립니다.</span>
  </div>
  <button type="button" class="banner-close" onclick="document.getElementById('offline-banner').style.display='none'" aria-label="안내 닫기">✕</button>
</div>
<noscript>
  <div class="noscript-overlay">
    <div class="noscript-card">
      <div class="noscript-icon">📱</div>
      <h2>아이패드 ‘파일’ 앱 미리보기 상태입니다</h2>
      <p class="noscript-desc">애플 보안 정책상 ‘파일’ 앱의 미리보기에서는 필기 기능(JavaScript)이 잠겨 있습니다.</p>
      <div class="noscript-steps">
        <div class="step-item">
          <span class="step-num">1</span>
          <span>화면 상단(또는 하단)의 <strong>공유 버튼 (⎋ 네모에 화살표)</strong>을 누르세요.</span>
        </div>
        <div class="step-item">
          <span class="step-num">2</span>
          <span>앱 목록에서 <strong>[Safari]</strong> 또는 <strong>[Chrome]</strong>을 선택하세요.</span>
        </div>
        <div class="step-item">
          <span class="step-num">3</span>
          <span><strong>비밀번호나 인터넷 없이</strong> 바로 355문제 풀이와 펜슬 필기가 시작됩니다!</span>
        </div>
      </div>
      <div class="noscript-tip">
        💡 <strong>팁:</strong> 또는 iPad Safari 브라우저에서 이 파일을 직접 열거나, 'Documents' 등 뷰어 앱으로 열어보세요.
      </div>
    </div>
  </div>
  <style>
    .layout, .topbar, .single-file-note { display: none !important; }
    .noscript-overlay { display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 24px; background: #f3f4ef; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    .noscript-card { max-width: 520px; width: 100%; background: #ffffff; border: 1px solid #dce3dc; border-radius: 20px; padding: 36px 30px; box-shadow: 0 10px 40px rgba(19,61,56,0.08); text-align: center; }
    .noscript-icon { font-size: 52px; margin-bottom: 12px; }
    .noscript-card h2 { font-size: 21px; color: #133d38; margin: 0 0 10px; letter-spacing: -0.5px; }
    .noscript-desc { font-size: 14px; color: #62726b; line-height: 1.6; margin: 0 0 22px; }
    .noscript-steps { text-align: left; background: #f6f8f5; border-radius: 14px; padding: 18px 20px; display: flex; flex-direction: column; gap: 14px; margin-bottom: 20px; }
    .step-item { display: flex; align-items: flex-start; gap: 12px; font-size: 14px; color: #203b36; line-height: 1.5; }
    .step-num { flex-shrink: 0; width: 24px; height: 24px; background: #133d38; color: #fff; border-radius: 50%; display: grid; place-items: center; font-size: 12px; font-weight: 700; margin-top: 1px; }
    .noscript-tip { font-size: 12.5px; color: #788a82; line-height: 1.6; text-align: left; border-top: 1px dashed #dce3dc; padding-top: 14px; }
  </style>
</noscript>'''

    html = replace_once(html, '<body>', banner_html)
    html = html.replace('<button id="offline">오프라인용 문제 저장</button>', '<button id="offline" hidden>모든 문제 포함됨</button>')
    html = html.replace('<span id="offline-status" role="status"></span>', '<span id="offline-status" role="status">이 파일에 355개 전 문제와 이미지가 내장되어 있어 비밀번호나 인터넷 없이 언제든 열 수 있습니다.</span>')
    
    # Help dialog replacement
    help_original = '''<dialog id="help-dialog"><div class="dialog-head"><h2>아이패드에서 시작하기</h2><button data-close="help-dialog" aria-label="닫기">✕</button></div><ol><li>Safari에서 이 주소를 열고 로그인하세요.</li><li>공유 메뉴 → <strong>홈 화면에 추가</strong>로 앱처럼 실행할 수 있어요.</li><li><strong>펜</strong>을 선택하고 Apple Pencil로 문제 위에 쓰세요. 필기는 문제별로 자동 저장돼요.</li><li>스크롤·확대는 <strong>이동</strong> 도구에서 손가락으로 하세요. 펜슬 전용을 끄면 손가락으로도 쓸 수 있어요.</li><li><strong>보관함 · 백업</strong>에서 필기를 파일로 보관하세요. 기기·브라우저 간에는 백업 파일로 옮길 수 있어요.</li></ol><p>필기는 이 브라우저에 저장됩니다. 방문 기록·사이트 데이터 삭제 시 사라질 수 있으므로 중요한 필기는 백업하세요. 홈 화면 앱과 Safari의 저장 공간이 다를 수 있어요.</p><p>필압을 제공하는 펜슬에서는 누르는 힘에 따라 펜 굵기가 달라집니다. 펜슬의 이중 탭·스퀴즈 기능은 지원하지 않습니다.</p><p><a href="https://developer.mozilla.org/en-US/docs/Web/API/PointerEvent" target="_blank" rel="noreferrer">입력 기술: 표준 Pointer Events</a></p></dialog>'''
    
    help_replacement = '''<dialog id="help-dialog"><div class="dialog-head"><h2>펜슬 문제집 사용 안내</h2><button data-close="help-dialog" aria-label="닫기">✕</button></div><ol><li><strong>비밀번호·로그인 없음:</strong> 이 HTML 파일 하나에 355개 전 문제와 원본 페이지, 필기 도구가 모두 내장되어 있습니다. 추가 다운로드나 로그인이 필요 없습니다.</li><li><strong>아이패드에서 열기:</strong> '파일' 앱 미리보기 대신 <strong>Safari</strong> 또는 <strong>Chrome</strong> 브라우저로 여세요. (파일 앱 공유 버튼 → Safari 선택)</li><li><strong>홈 화면에 추가:</strong> Safari 공유 메뉴 → <strong>홈 화면에 추가</strong>를 누르면 전체 화면 전용 앱처럼 편리하게 학습할 수 있습니다.</li><li><strong>Apple Pencil 필기:</strong> <strong>펜/형광펜/지우개</strong>를 선택하고 문제 위에 쓰세요. 필압이 반영되며 문제별로 자동 보존됩니다.</li><li><strong>스크롤 및 확대:</strong> <strong>이동</strong> 도구를 선택하면 손가락으로 스크롤과 확대를 할 수 있습니다. (펜슬 전용을 끄면 손가락 필기도 가능)</li><li><strong>보관함 · 백업:</strong> <strong>보관함 · 백업</strong>에서 필기를 JSON 파일로 내보내어 다른 기기로 옮기거나 안전하게 보관할 수 있습니다.</li></ol><p>필기는 현재 브라우저에 안전하게 보존됩니다. 기기를 변경하거나 Safari 캐시를 정리할 때를 대비해 중요한 필기는 정기적으로 백업해 두세요.</p><p>외부 인터넷 서버 연결이 전혀 없는 100% 로컬 독립형 파일입니다.</p></dialog>'''

    html = replace_once(html, help_original, help_replacement)

    app = replace_once(app,
        "const response = await fetch('questions.json'); if (!response.ok) throw new Error('문제 목록을 불러올 수 없습니다.');\n    questions = await response.json();",
        "questions = window.SCIENCE_BUNDLE.questions.map(q => ({...q, image:window.SCIENCE_BUNDLE.assets[q.image], source:window.SCIENCE_BUNDLE.assets[q.source]}));")
    app = replace_once(app,
        "if ('serviceWorker' in navigator && window.isSecureContext) navigator.serviceWorker.register('sw.js').catch(() => { $('offline-status').textContent = '오프라인 기능을 준비하지 못했습니다. 온라인 학습은 가능합니다.'; });",
        '// Standalone file: every asset is embedded; no service worker or server is needed.')
    
    app = re.sub(r"\$\('offline'\)\.onclick = async \(\) => \{.*?\n\};", "$('offline').onclick = () => toast('모든 문제와 이미지가 이미 이 파일에 들어 있습니다.');", app, flags=re.S)
    
    script = ('window.SCIENCE_BUNDLE=' + bundle + ';\n' + app).replace('</script', '<\\/script')
    html = replace_once(html, '</body></html>', f'<script>{script}</script>\n</body></html>')
    
    assert not re.search(r'<(?:script|link)[^>]+(?:src|href)="(?!data:|https:)', html)
    OUTPUT.write_text(html, 'utf-8')
    print(f'{OUTPUT.name}: {OUTPUT.stat().st_size / 1024 / 1024:.1f} MiB; {len(questions)} questions; {len(assets)} embedded images')

if __name__ == '__main__':
    main()
