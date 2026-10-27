import concurrent.futures
import html
import json
import re

from catalog.management.commands.crawl_product_specs import extract_product_image_url, fetch_url, model_token_present
from catalog.models import Product

products = list(Product.objects.filter(brand__name='D-Link', is_published=True, image='').select_related('category'))

def probe(product):
    slug = re.sub(r'[^a-z0-9]+', '-', product.model.casefold()).strip('-')
    for locale in ('en', 'uk/en'):
        url = f'https://www.dlink.com/{locale}/products/{slug}'
        try:
            final_url, content_type, data = fetch_url(url, timeout=10, max_bytes=1_000_000, attempts=1)
            if 'html' not in content_type.casefold():
                continue
            title_match = re.search(rb'<title[^>]*>(.*?)</title>', data, re.I | re.S)
            title = html.unescape(re.sub(r'<[^>]+>', ' ', title_match.group(1).decode('utf-8', 'ignore'))).strip() if title_match else ''
            if not model_token_present(product.model, title):
                continue
            image_url = extract_product_image_url(final_url, data, ('dlink.com',), product.model)
            return {'model': product.model, 'category': product.category.slug, 'url': final_url, 'title': title, 'image_url': image_url}
        except Exception:
            continue
    return {'model': product.model, 'category': product.category.slug, 'url': '', 'image_url': ''}

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    rows = list(pool.map(probe, products))
with open('../output/dlink-exact-path-probe-2026-09-16.json', 'w', encoding='utf-8') as output:
    json.dump(rows, output, indent=2, ensure_ascii=False)
for row in rows:
    if row['url']:
        print(row['model'], bool(row['image_url']), row['url'])
print('found', sum(bool(row['url']) for row in rows), 'of', len(rows))
