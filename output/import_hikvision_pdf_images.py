import json
from pathlib import Path

from django.core.files.base import ContentFile
from catalog.models import Product

rows = json.loads(Path('../output/hikvision-pdf-image-probe-2026-09-16.json').read_text(encoding='utf-8'))
count = 0
urls_updated = 0
for row in rows:
    if row['status'] not in {'candidate', 'no_candidate'}:
        continue
    product = Product.objects.get(brand__name='Hikvision', model=row['model'])
    # This database row points at the /M variant data sheet, not the base model.
    if product.model == 'DS-3E0510P-E':
        continue
    if product.official_url != row['url']:
        product.official_url = row['url']
        product.save(update_fields=['official_url'])
        urls_updated += 1
    if row['status'] == 'candidate' and not product.image:
        data = Path(row['path']).read_bytes()
        product.image.save(f'{product.model.lower().replace("/", "-")}.png', ContentFile(data), save=True)
        count += 1
print('images_imported', count, 'urls_updated', urls_updated)
