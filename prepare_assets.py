"""Create the iPad app's optimized, self-contained question assets."""
from pathlib import Path
import json
from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
DIST = BASE / 'dist'
(DIST / 'questions').mkdir(exist_ok=True)
(DIST / 'pages').mkdir(exist_ok=True)
questions = json.loads((ROOT / 'questions.json').read_text('utf-8'))
result = []
for q in questions:
    with Image.open(ROOT / q['image']) as image:
        crop = image.crop(q['box']).convert('RGB')
        crop.save(DIST / 'questions' / f"{q['number']:03}.webp", quality=92)
        page_path = DIST / 'pages' / f"{q['page']:03}.webp"
        if not page_path.exists():
            image.convert('RGB').save(page_path, quality=90)
        result.append({'id': q['id'], 'number': q['number'], 'page': q['book_page'],
                       'image': f"questions/{q['number']:03}.webp",
                       'source': f"pages/{q['page']:03}.webp", 'width': crop.width, 'height': crop.height})
(DIST / 'questions.json').write_text(json.dumps(result, ensure_ascii=False), 'utf-8')
for size in (180, 192, 512):
    icon = Image.new('RGB', (size, size), '#133d38')
    draw = ImageDraw.Draw(icon)
    draw.rounded_rectangle((size*.2, size*.16, size*.8, size*.84), radius=size*.06, fill='#fff9ea')
    for y in (.35, .48, .61):
        draw.line((size*.31, size*y, size*.65, size*y), fill='#133d38', width=max(2, size//30))
    draw.line((size*.65, size*.68, size*.85, size*.38), fill='#d8983b', width=size//13)
    icon.save(DIST / f'icon-{size}.png')
print(f'Prepared {len(result)} questions, {len(list((DIST / "pages").glob("*.webp")))} source pages')
