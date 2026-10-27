import json
from catalog.models import Product

rows = json.load(open('../output/huawei-ekit-import-2026-09-16.json', encoding='utf-8'))['results']
n = 0
for row in rows:
    product = Product.objects.filter(brand__name='eKit', model=row['model'].removeprefix('eKit ')).first()
    if product:
        product.official_url = row['url']
        product.save(update_fields=['official_url'])
        n += 1
for model, url in {
    'AP265E': 'https://ekit.huawei.com/ekit/front/ssr/en/product/1480064306648244992',
    'AP271E': 'https://ekit.huawei.com/ekit/front/ssr/en/product/1626930002148196722',
}.items():
    product = Product.objects.get(brand__name='eKit', model=model)
    product.official_url = url
    product.save(update_fields=['official_url'])
    n += 1
print('seeded', n)
