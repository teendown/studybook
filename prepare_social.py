from pathlib import Path
import json
from PIL import Image, ImageDraw

SRC_ROOT = Path(r'D:\문제지다운로드\개년완성통합사회2')
DIST = Path(r'd:\문제지다운로드\개념완성통합과학2\science-ipad\dist\social')
(DIST / 'questions').mkdir(parents=True, exist_ok=True)
(DIST / 'pages').mkdir(parents=True, exist_ok=True)

questions = json.loads((SRC_ROOT / 'questions.json').read_text('utf-8'))
result = []
print(f'Starting conversion for {len(questions)} social questions...')
for q in questions:
    num = q['number']
    page = q['page']
    with Image.open(SRC_ROOT / q['image']) as img:
        crop = img.crop(q['box']).convert('RGB')
        q_path = DIST / 'questions' / f'{num:03d}.webp'
        crop.save(q_path, quality=92)
        
        page_path = DIST / 'pages' / f'{page:03d}.webp'
        if not page_path.exists():
            img.convert('RGB').save(page_path, quality=90)
            
        result.append({
            'id': q['id'],
            'number': num,
            'page': q['book_page'],
            'image': f'questions/{num:03d}.webp',
            'source': f'pages/{page:03d}.webp',
            'width': crop.width,
            'height': crop.height
        })

(DIST / 'questions.json').write_text(json.dumps(result, ensure_ascii=False), 'utf-8')
print(f'Saved {len(result)} questions in social/questions.json')

# Generate icons with warm earth/terracotta theme
for size in (180, 192, 512):
    icon = Image.new('RGB', (size, size), '#332318')
    draw = ImageDraw.Draw(icon)
    draw.rounded_rectangle((size*0.2, size*0.16, size*0.8, size*0.84), radius=size*0.06, fill='#fcf6ee')
    for y in (0.35, 0.48, 0.61):
        draw.line((size*0.31, size*y, size*0.65, size*y), fill='#332318', width=max(2, size//30))
    draw.line((size*0.65, size*0.68, size*0.85, size*0.38), fill='#c75b28', width=size//13)
    icon.save(DIST / f'icon-{size}.png')
print('Generated icons for social.')
