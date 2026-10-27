import concurrent.futures
import html
import json
import re

from catalog.management.commands.crawl_product_specs import extract_product_image_url, fetch_url
from catalog.models import Product

products = list(Product.objects.filter(brand__name='Instant On', is_published=True).select_related('category'))

def probe(product):
    model = product.model
    if product.category.slug == 'access-point':
        urls = [f'https://www.hpe.com/us/en/instant-on/access-points/access-point-{model[2:].lower()}.html']
    else:
        urls = [f'https://buy.hpe.com/{region}/p/{model.lower()}' for region in ('sg/en', 'it/it', 'fr/fr', 'de/de', 'au/en', 'us/en')]
    for url in urls:
        try:
            final_url, content_type, data = fetch_url(url, timeout=15, max_bytes=800_000, attempts=1)
            if 'html' not in content_type.lower():
                continue
            match = re.search(rb'<title[^>]*>(.*?)</title>', data, re.I | re.S)
            title = html.unescape(re.sub(r'<[^>]+>', ' ', match.group(1).decode('utf-8', 'ignore'))) if match else ''
            if 'Search | HPE Store' in title or '404' in title:
                continue
            if product.category.slug != 'access-point' and ('switch' not in title.lower() or 'instant on' not in title.lower() or f'/p/{model.lower()}' not in final_url.lower()):
                continue
            image_url = extract_product_image_url(final_url, data, ('hpe.com', 'arubanetworks.com'), model)
            return {'model': model, 'url': final_url, 'title': title.strip(), 'image_url': image_url}
        except Exception:
            continue
    return {'model': model, 'url': '', 'image_url': ''}

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    results = list(pool.map(probe, products))
with open('../output/instant-on-page-probe-2026-09-16.json', 'w', encoding='utf-8') as out:
    json.dump(results, out, ensure_ascii=False, indent=2)
for row in results:
    print(row['model'], bool(row['url']), bool(row['image_url']), row['url'])
