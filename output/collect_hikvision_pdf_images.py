import concurrent.futures
import io
import json
import re
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

from catalog.management.commands.crawl_product_specs import fetch_url
from catalog.models import Product

OUT = Path('../output/hikvision_pdf_images')
OUT.mkdir(exist_ok=True)
products = list(Product.objects.filter(brand__name='Hikvision', is_published=True).exclude(official_url='').order_by('model'))

def candidates(url):
    if 'assets.hikvision.com/' in url:
        yield url
        return
    match = re.search(r'(M\d+)/Data_Sheet/([^/?]+\.pdf)', url, re.I)
    if match:
        for channel in ('public', 'normal'):
            yield f'https://assets.hikvision.com/prd/{channel}/all/doc/{match.group(1).lower()}/{match.group(2)}'
    yield url

def inspect(product):
    if not product.official_url.lower().split('?', 1)[0].endswith('.pdf'):
        return {'model': product.model, 'status': 'not_pdf'}
    for url in candidates(product.official_url):
        try:
            final_url, _, data = fetch_url(url, timeout=20, max_bytes=10_000_000, attempts=1)
            if not data.startswith(b'%PDF'):
                continue
            doc = fitz.open(stream=data, filetype='pdf')
            page = doc[0]
            options = []
            for entry in page.get_images(full=True):
                xref = entry[0]
                smask = entry[1]
                info = doc.extract_image(xref)
                for rect in page.get_image_rects(xref):
                    if rect.y0 > page.rect.height * .56 or rect.width < 50 or rect.height < 25:
                        continue
                    if rect.width > page.rect.width * .8 and rect.height < page.rect.height * .25:
                        continue
                    if rect.width > page.rect.width * .8 and rect.height > page.rect.height * .8:
                        continue
                    if info['width'] < 150 or info['height'] < 100:
                        continue
                    options.append((rect.width * rect.height, xref, smask, rect, info))
            if not options:
                return {'model': product.model, 'status': 'no_candidate', 'url': final_url}
            options.sort(reverse=True, key=lambda item: item[0])
            _, xref, smask, rect, info = options[0]
            # Render the exact image rectangle from the PDF page. PDF soft masks
            # can have different pixel dimensions from the source image.
            pixmap = page.get_pixmap(matrix=fitz.Matrix(5, 5), clip=rect, alpha=False)
            image = Image.open(io.BytesIO(pixmap.tobytes('png')))
            image.load()
            filename = re.sub(r'[^A-Za-z0-9._-]+', '_', product.model) + '.png'
            path = OUT / filename
            rgba = image.convert('RGBA')
            white = Image.new('RGBA', image.size, (255, 255, 255, 255))
            white.alpha_composite(rgba)
            white.convert('RGB').save(path)
            return {
                'model': product.model, 'status': 'candidate', 'url': final_url,
                'path': str(path), 'width': image.width, 'height': image.height,
                'rect': [round(rect.x0), round(rect.y0), round(rect.width), round(rect.height)],
            }
        except Exception as exc:
            last_error = str(exc)[:120]
    return {'model': product.model, 'status': 'failed', 'error': locals().get('last_error', '')}

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    rows = list(pool.map(inspect, products))
Path('../output/hikvision-pdf-image-probe-2026-09-16.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
print('statuses', {s: sum(r['status'] == s for r in rows) for s in sorted({r['status'] for r in rows})})
for row in rows:
    print(row['model'], row['status'], row.get('width', ''), row.get('height', ''), row.get('url', '')[:100])

candidates_found = [row for row in rows if row['status'] == 'candidate']
thumb_w, thumb_h = 260, 180
cols = 5
rows_count = (len(candidates_found) + cols - 1) // cols
sheet = Image.new('RGB', (cols * thumb_w, rows_count * (thumb_h + 30)), 'white')
draw = ImageDraw.Draw(sheet)
for i, row in enumerate(candidates_found):
    image = Image.open(row['path']).convert('RGB')
    image.thumbnail((thumb_w - 15, thumb_h - 10))
    x = (i % cols) * thumb_w + (thumb_w - image.width) // 2
    y = (i // cols) * (thumb_h + 30) + (thumb_h - image.height) // 2
    sheet.paste(image, (x, y))
    draw.text(((i % cols) * thumb_w + 5, (i // cols) * (thumb_h + 30) + thumb_h), row['model'], fill='black')
sheet.save(OUT / 'contact-sheet.png')
