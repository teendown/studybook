"""Recrop all 365 social studies questions with expanded left and safe margins."""
from pathlib import Path
import json
from PIL import Image

SRC_ROOT = Path(r'D:\문제지다운로드\개년완성통합사회2')
DIST = Path(r'd:\문제지다운로드\개념완성통합과학2\science-ipad\dist\social')
cache = json.loads((SRC_ROOT / 'ocr_cache.json').read_text('utf-8'))

questions = []
for page_str, marks in cache.items():
    page = int(page_str)
    if not marks:
        continue
    path = SRC_ROOT / f'통사2_{page}.png'
    with Image.open(path) as img:
        w, h = img.size
    
    is_even = (page % 2 == 0)
    for column in (0, 1):
        cmarks = sorted((m for m in marks if m['column'] == column), key=lambda m: m['y'])
        for i, mark in enumerate(cmarks):
            num = mark['number']
            if is_even:
                l = 0.095 if column == 0 else 0.518
                r = 0.520 if column == 0 else 0.945
            else:
                l = 0.055 if column == 0 else 0.478
                r = 0.480 if column == 0 else 0.905
            
            top = max(int(h * 0.105), int(mark['y'] - h * 0.012))
            bottom = int(cmarks[i + 1]['y'] - h * 0.012) if i + 1 < len(cmarks) else int(h * 0.885)
            
            box = [int(w * l), top, int(w * r), bottom]
            questions.append({
                'id': f'25593-{num:04d}',
                'number': num,
                'page': page,
                'book_page': page,
                'image': path.name,
                'box': box
            })

questions.sort(key=lambda q: q['number'])
(SRC_ROOT / 'questions.json').write_text(json.dumps(questions, ensure_ascii=False, indent=2), 'utf-8')
print(f'Updated questions.json with {len(questions)} items.')

# Recrop WebP images
result = []
(DIST / 'questions').mkdir(parents=True, exist_ok=True)
for q in questions:
    num = q['number']
    page = q['page']
    with Image.open(SRC_ROOT / q['image']) as img:
        crop = img.crop(q['box']).convert('RGB')
        q_path = DIST / 'questions' / f'{num:03d}.webp'
        crop.save(q_path, quality=92)
        
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
print(f'Successfully re-cropped {len(result)} WebP images for social studies!')
