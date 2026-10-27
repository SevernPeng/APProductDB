import json
from pathlib import Path
from django.core.management import call_command
from catalog.models import Product

rows = json.loads(Path('../output/dlink-exact-path-probe-2026-09-16.json').read_text(encoding='utf-8'))
verified = [row for row in rows if row['url'] and row['image_url'] and row['model'] not in {'DEM-S2801SR', 'DIS-210G-06P'}]
for row in verified:
    product = Product.objects.get(brand__name='D-Link', model=row['model'])
    product.official_url = row['url']
    product.save(update_fields=['official_url'])

dry_run = False
call_command(
    'crawl_product_specs',
    brands=['D-Link'],
    models=[row['model'] for row in verified],
    dry_run=dry_run,
    report=Path('../output/dlink-exact-pages-dry-run-2026-09-16.json' if dry_run else '../output/dlink-exact-pages-import-2026-09-16.json'),
)
