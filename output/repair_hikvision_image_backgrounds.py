import json
from pathlib import Path
from catalog.models import Product

rows = json.loads(Path('../output/hikvision-pdf-image-probe-2026-09-16.json').read_text(encoding='utf-8'))
count = 0
for row in rows:
    if row['status'] != 'candidate' or row['model'] == 'DS-3E0510P-E':
        continue
    product = Product.objects.get(brand__name='Hikvision', model=row['model'])
    if not product.image:
        continue
    path = Path(row['path'])
    data = path.read_bytes()
    with product.image.storage.open(product.image.name, 'wb') as image_file:
        image_file.write(data)
    count += 1
print('repaired', count)
