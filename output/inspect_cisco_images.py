import html
import io
import json
import re
from pathlib import Path
from urllib.parse import urljoin

from PIL import Image, ImageDraw

from catalog.management.commands.crawl_product_specs import fetch_url

report = json.loads(Path('../output/cisco-crawl-dry-run-2026-09-16.json').read_text(encoding='utf-8'))
models = {'C9115AXI', 'C9120AXI', 'C9124AXE', 'C1300-24FP-4X', 'C9200L-24P-4X', 'CBS250-16P-2G'}
cards = []
for result in report['results']:
    if result['model'] not in models:
        continue
    url = result['url'].split('?', 1)[0].replace('.pdf', '.html')
    try:
        final_url, _, data = fetch_url(url)
        page = data.decode('utf-8', 'ignore')
        images = re.findall(r'<img\b[^>]*>', page, re.I)
        image_tag = next((tag for tag in images if '_0.png' in tag), '')
        match = re.search(r'src=["\']([^"\']+)', image_tag, re.I)
        if not match:
            print(result['model'], 'no primary image')
            continue
        image_url = urljoin(final_url, html.unescape(match.group(1)))
        _, content_type, image_data = fetch_url(image_url)
        picture = Image.open(io.BytesIO(image_data)).convert('RGB')
        picture.thumbnail((300, 220))
        cards.append((result['model'], picture, image_url))
        print(result['model'], content_type, picture.size, image_url)
    except Exception as exc:
        print(result['model'], type(exc).__name__, str(exc)[:100])

sheet = Image.new('RGB', (600, ((len(cards) + 1) // 2) * 260), 'white')
draw = ImageDraw.Draw(sheet)
for index, (model, picture, _) in enumerate(cards):
    x = (index % 2) * 300
    y = (index // 2) * 260
    sheet.paste(picture, (x, y + 25))
    draw.text((x + 6, y + 5), model, fill='black')
sheet.save('../output/cisco-image-contact-sheet.png')
