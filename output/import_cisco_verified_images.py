from django.core.files.base import ContentFile
from catalog.management.commands.crawl_product_specs import fetch_url
from catalog.models import Product

images = {
    'C9115AXI': 'https://www.cisco.com/c/dam/en/us/products/collateral/wireless/catalyst-9100ax-access-points/datasheet-c78-741988.docx/_jcr_content/renditions/datasheet-c78-741988_0.png',
    'C9120AXI': 'https://www.cisco.com/c/dam/en/us/products/collateral/wireless/catalyst-9120ax-series-access-points/datasheet-c78-742115.docx/_jcr_content/renditions/datasheet-c78-742115_0.jpg',
    'CW9172I': 'https://www.cisco.com/content/dam/cisco-cdc/site/images/heroes/products/networking/wireless/access-points/meraki/cw9172i-800x600.jpg',
}

for model, url in images.items():
    product = Product.objects.get(brand__name='Cisco', model=model, is_published=True)
    if product.image:
        print(model, 'already has image')
        continue
    final_url, content_type, data = fetch_url(url, max_bytes=12 * 1024 * 1024)
    if not final_url.startswith('https://www.cisco.com/') or not content_type.startswith('image/'):
        raise ValueError(f'Unexpected image response: {final_url}, {content_type}')
    suffix = '.' + content_type.split('/', 1)[1].split(';', 1)[0]
    product.image.save(f'{model.lower()}{suffix}', ContentFile(data), save=False)
    product.save(update_fields=('image', 'updated_at'))
    print(model, final_url, content_type, len(data))
