"""Deskew (auto-rotate tilted scan) and re-crop all social studies pages & questions."""
import cv2
import numpy as np
import json
import time
from pathlib import Path
from PIL import Image

SRC_ROOT = Path(r'D:\문제지다운로드\개년완성통합사회2')
DIST = Path(r'd:\문제지다운로드\개념완성통합과학2\science-ipad\dist\social')
(DIST / 'questions').mkdir(parents=True, exist_ok=True)
(DIST / 'pages').mkdir(parents=True, exist_ok=True)

cache = json.loads((SRC_ROOT / 'ocr_cache.json').read_text('utf-8'))

def detect_skew_projection(gray, search_range=3.0, step=0.05):
    """Detect tilt angle using horizontal projection profile variance on binarized text."""
    h, w = gray.shape
    resized = cv2.resize(gray, (w // 3, h // 3))
    thresh = cv2.adaptiveThreshold(resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 8)
    best_score = -1
    best_angle = 0.0
    angles = np.arange(-search_range, search_range + step, step)
    center = (thresh.shape[1] // 2, thresh.shape[0] // 2)
    for a in angles:
        M = cv2.getRotationMatrix2D(center, a, 1.0)
        rotated = cv2.warpAffine(thresh, M, (thresh.shape[1], thresh.shape[0]), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        proj = np.sum(rotated, axis=1)
        score = np.sum(np.diff(proj) ** 2)
        if score > best_score:
            best_score = score
            best_angle = a
    return round(float(best_angle), 2)

print('Starting deskew analysis and re-cropping for all pages...')
t0 = time.time()

all_questions = []
pages_processed = 0

for page_str, marks in sorted(cache.items(), key=lambda x: int(x[0])):
    page = int(page_str)
    if not marks:
        continue
    
    path = SRC_ROOT / f'통사2_{page}.png'
    if not path.exists():
        continue
    
    # 1. Detect skew angle
    data = np.fromfile(str(path), dtype=np.uint8)
    gray = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
    angle = detect_skew_projection(gray)
    
    # 2. Rotate full page with BICUBIC and white background
    with Image.open(path) as raw_img:
        w, h = raw_img.size
        deskewed_page = raw_img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(255, 255, 255))
        
        # Save deskewed full page webp
        page_webp = DIST / 'pages' / f'{page:03d}.webp'
        deskewed_page.convert('RGB').save(page_webp, quality=90)
        
        # 3. Compute question crop boxes using rotated coordinates
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        is_even = (page % 2 == 0)
        
        for column in (0, 1):
            cmarks = sorted((m for m in marks if m['column'] == column), key=lambda m: m['y'])
            for i, mark in enumerate(cmarks):
                num = mark['number']
                if is_even:
                    l = 0.095 if column == 0 else 0.518
                    r = 0.520 if column == 0 else 0.945
                    cx_val = w * 0.3075 if column == 0 else w * 0.7315
                else:
                    l = 0.055 if column == 0 else 0.478
                    r = 0.480 if column == 0 else 0.905
                    cx_val = w * 0.2675 if column == 0 else w * 0.6915
                
                # Transform mark y by rotation matrix
                pt = np.array([[[cx_val, mark['y']]]], dtype=np.float32)
                rot_y = cv2.transform(pt, M)[0][0][1]
                
                top = max(int(h * 0.105), int(rot_y - h * 0.012))
                if i + 1 < len(cmarks):
                    next_pt = np.array([[[cx_val, cmarks[i+1]['y']]]], dtype=np.float32)
                    next_rot_y = cv2.transform(next_pt, M)[0][0][1]
                    bottom = int(next_rot_y - h * 0.012)
                else:
                    bottom = int(h * 0.885)
                
                box = [int(w * l), top, int(w * r), bottom]
                crop = deskewed_page.crop(box).convert('RGB')
                
                q_webp = DIST / 'questions' / f'{num:03d}.webp'
                crop.save(q_webp, quality=92)
                
                all_questions.append({
                    'id': f'25593-{num:04d}',
                    'number': num,
                    'page': page,
                    'image': f'questions/{num:03d}.webp',
                    'source': f'pages/{page:03d}.webp',
                    'width': crop.width,
                    'height': crop.height,
                    'box': box,
                    'angle': angle
                })
    
    pages_processed += 1
    if pages_processed % 20 == 0:
        print(f'Processed {pages_processed} pages...')

all_questions.sort(key=lambda q: q['number'])

# Save questions.json in dist/social
clean_questions = [
    {
        'id': q['id'],
        'number': q['number'],
        'page': q['page'],
        'image': q['image'],
        'source': q['source'],
        'width': q['width'],
        'height': q['height']
    }
    for q in all_questions
]
(DIST / 'questions.json').write_text(json.dumps(clean_questions, ensure_ascii=False), 'utf-8')
(SRC_ROOT / 'questions.json').write_text(json.dumps(all_questions, ensure_ascii=False, indent=2), 'utf-8')

elapsed = time.time() - t0
print(f'Done! Successfully deskewed and re-cropped all {len(all_questions)} questions across {pages_processed} pages in {elapsed:.1f}s.')
