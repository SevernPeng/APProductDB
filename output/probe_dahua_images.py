import re
from catalog.management.commands.crawl_product_specs import fetch_url
from catalog.models import Product

for model in ('PFS4207-4GT-DP', 'PFT1500'):
    product = Product.objects.get(brand__name='Dahua', model=model)
    _, _, data = fetch_url(product.official_url, timeout=20, max_bytes=2_000_000, attempts=1)
    page = data.decode('utf-8', errors='ignore')
    print('\n', model, len(page))
    for url in dict.fromkeys(re.findall(r'(?:src|data-src|href)=["\']([^"\']+)["\']', page, re.I)):
        if any(part in url.casefold() for part in ('pft1500', 'pfs4207', 'productimage', 'thumb', 'material.dahuasecurity')):
            print(url[:300])
    target = '10-1_thumb.png' if model.startswith('PFS') else '1_0_01_20_10754_2006672588_thumb.png'
    pos = page.find(target)
    print('context', page[max(0, pos-250):pos+200].replace('\n', ' ')[:450])
