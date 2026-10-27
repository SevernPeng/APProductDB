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

models = list(Product.objects.filter(brand__name='Huawei', is_published=True, category__slug='access-point').values_list('model', flat=True))
models = [model for model in models if model.startswith('AirEngine ')]

def probe(model):
    slug = model.lower().replace(' ', '-')
    for kind in ('indoor-access-points', 'outdoor-access-points'):
        url = f'https://e.huawei.com/en/products/wlan/{kind}/{slug}'
        try:
            final_url, content_type, data = fetch_url(url, timeout=12, max_bytes=1_000_000, attempts=1)
            if 'html' not in content_type.lower():
                continue
            match = re.search(rb'<title[^>]*>(.*?)</title>', data, re.I | re.S)
            title = html.unescape(re.sub(r'<[^>]+>', ' ', match.group(1).decode('utf-8', 'ignore'))) if match else ''
            if not model_token_present(model, title):
                continue
            image_url = extract_product_image_url(final_url, data, ('huawei.com',), model)
            return {'model': model, 'url': final_url, 'title': title.strip(), 'image_url': image_url}
        except Exception:
            continue
    return {'model': model, 'url': '', 'image_url': ''}

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    results = list(pool.map(probe, models))
with open('../output/huawei-page-probe-2026-09-16.json', 'w', encoding='utf-8') as out:
    json.dump(results, out, ensure_ascii=False, indent=2)
for row in results:
    print(row['model'], bool(row['url']), bool(row['image_url']), row['url'])
