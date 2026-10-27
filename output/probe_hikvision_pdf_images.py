from pathlib import Path
import fitz
import re
from catalog.management.commands.crawl_product_specs import fetch_url
from catalog.models import Product

target = Path('../output/hikvision_pdf_samples')
target.mkdir(exist_ok=True)
for model in ('DS-3E0105P-E/M(B)', 'DS-3E0505HP-E', 'DS-3WAP521-SI'):
    product = Product.objects.get(brand__name='Hikvision', model=model)
    match = re.search(r'(M\d+)/Data_Sheet/([^/?]+)', product.official_url, re.I)
    for channel in ('public', 'normal'):
        candidate = f'https://assets.hikvision.com/prd/{channel}/all/doc/{match.group(1).lower()}/{match.group(2)}'
        try:
            final_url, content_type, data = fetch_url(candidate, timeout=30, max_bytes=8_000_000, attempts=1)
            if data.startswith(b'%PDF'):
                break
        except Exception:
            pass
    print('fetch', final_url, content_type, len(data), data[:20])
    doc = fitz.open(stream=data, filetype='pdf')
    print(model, 'pages', len(doc))
    doc[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(target / f'{model.replace("/", "_")}_page.png')
    for index, image in enumerate(doc[0].get_images(full=True)):
        xref = image[0]
        info = doc.extract_image(xref)
        rects = doc[0].get_image_rects(xref)
        print(index, info['width'], info['height'], info['ext'], [(round(r.x0), round(r.y0), round(r.width), round(r.height)) for r in rects])
        if info['width'] >= 100 and info['height'] >= 100:
            path = target / f'{model.replace("/", "_")}_{index}.{info["ext"]}'
            path.write_bytes(info['image'])
