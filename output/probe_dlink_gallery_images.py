import html
import re
from catalog.management.commands.crawl_product_specs import fetch_url
from catalog.models import Product

for model in ('DEM-S2801SR', 'DIS-210G-06P'):
    product = Product.objects.get(brand__name='D-Link', model=model)
    _, _, data = fetch_url(product.official_url, timeout=20, max_bytes=2_000_000, attempts=1)
    page = html.unescape(data.decode('utf-8', errors='ignore'))
    print('\n', model)
    images = re.findall(r'<img\b[^>]*>', page, re.I)
    for tag in images:
        if any(word in tag.casefold() for word in (model.casefold().replace('-', ''), model.casefold(), 'front', 'side', 'product-image')):
            source = re.search(r'(?:src|data-src)=["\']([^"\']+)', tag, re.I)
            if source:
                print(source.group(1)[:260], 'ALT', (re.search(r'alt=["\']([^"\']*)', tag, re.I).group(1) if re.search(r'alt=["\']([^"\']*)', tag, re.I) else '')[:90])
