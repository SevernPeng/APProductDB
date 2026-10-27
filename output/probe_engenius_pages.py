import concurrent.futures
import html
import json
import re

from catalog.management.commands.crawl_product_specs import (
    extract_product_image_url,
    fetch_url,
    model_token_present,
)
from catalog.models import Product

models = list(Product.objects.filter(brand__name='EnGenius', is_published=True).values_list('model', flat=True))

def probe(model):
    slug = model.lower()
    for locale in ('in', 'apac', 'eu'):
        for kind in ('indoor-access-points', 'outdoor-access-points'):
            url = f'https://www.engeniustech.com/{locale}/products/wireless/{kind}/{slug}/'
            try:
                final_url, content_type, data = fetch_url(url, timeout=10, max_bytes=900_000, attempts=1)
                if 'html' not in content_type.lower():
                    continue
                match = re.search(rb'<title[^>]*>(.*?)</title>', data, re.I | re.S)
                title = html.unescape(re.sub(r'<[^>]+>', ' ', match.group(1).decode('utf-8', 'ignore'))) if match else ''
                if not model_token_present(model, final_url) or not model_token_present(model, data.decode('utf-8', 'ignore')):
                    continue
                image_url = extract_product_image_url(final_url, data, ('engeniustech.com',), model)
                return {'model': model, 'url': final_url, 'title': title.strip(), 'image_url': image_url}
            except Exception:
                continue
    return {'model': model, 'url': '', 'image_url': ''}

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    results = list(pool.map(probe, models))
with open('../output/engenius-page-probe-2026-09-16.json', 'w', encoding='utf-8') as out:
    json.dump(results, out, ensure_ascii=False, indent=2)
for row in results:
    print(row['model'], bool(row['url']), bool(row['image_url']), row['url'])
