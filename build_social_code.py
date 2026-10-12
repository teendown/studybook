"""Generate web app code for social studies."""
from pathlib import Path

DIST = Path(r'd:\문제지다운로드\개념완성통합과학2\science-ipad\dist')
SCI = DIST / 'science'
SOC = DIST / 'social'

# 1. index.html
sci_html = (SCI / 'index.html').read_text('utf-8')
soc_html = sci_html.replace('통합과학 2', '통합사회 2')
soc_html = soc_html.replace('통합과학 2의 355문제를', '통합사회 2의 365문제를')
soc_html = soc_html.replace('value="22"', 'value="12"')
soc_html = soc_html.replace('min="1" max="176"', 'min="1" max="169"')
soc_html = soc_html.replace('value="176"', 'value="169"')
soc_html = soc_html.replace('0 / 355', '0 / 365')
soc_html = soc_html.replace('max="355"', 'max="365"')
soc_html = soc_html.replace('355문제', '365문제')
soc_html = soc_html.replace('#133d38', '#1a2b3c')
(SOC / 'index.html').write_text(soc_html, 'utf-8')

# 2. app.js
sci_app = (SCI / 'app.js').read_text('utf-8')
soc_app = sci_app.replace('science-pencil-v1', 'society-pencil-v1')
soc_app = soc_app.replace('science-pencil:', 'society-pencil:')
soc_app = soc_app.replace('science-pencil-session', 'society-pencil-session')
soc_app = soc_app.replace("'22'", "'12'")
soc_app = soc_app.replace("'176'", "'169'")
soc_app = soc_app.replace('355문제', '365문제')
(SOC / 'app.js').write_text(soc_app, 'utf-8')

# 3. style.css (with sophisticated navy/slate palette for social studies)
sci_css = (SCI / 'style.css').read_text('utf-8')
soc_css = sci_css.replace('--green:#133d38', '--green:#1a2e40')
soc_css = soc_css.replace('--ink:#203b36', '--ink:#1f2933')
soc_css = soc_css.replace('#133d38', '#1a2e40')
soc_css = soc_css.replace('#21594f', '#2a445d')
soc_css = soc_css.replace('#eef6f2', '#eaf0f6')
soc_css = soc_css.replace('#e8eee6', '#e5ecf2')
soc_css = soc_css.replace('#cce3d8', '#ccd9e5')
soc_css = soc_css.replace('#789087', '#5f7387')
(SOC / 'style.css').write_text(soc_css, 'utf-8')

# 4. manifest.webmanifest
soc_manifest = '''{
  "name": "통합사회 2 · 펜슬 문제집",
  "short_name": "사회 문제집",
  "start_url": "./",
  "display": "standalone",
  "background_color": "#f3f5f8",
  "theme_color": "#1a2e40",
  "icons": [
    {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}
  ]
}'''
(SOC / 'manifest.webmanifest').write_text(soc_manifest, 'utf-8')

# 5. sw.js
sci_sw = (SCI / 'sw.js').read_text('utf-8')
soc_sw = sci_sw.replace('science-pencil', 'society-pencil')
(SOC / 'sw.js').write_text(soc_sw, 'utf-8')

print('Social studies app files created successfully!')
