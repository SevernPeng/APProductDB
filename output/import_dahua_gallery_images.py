from django.core.files.base import ContentFile
from catalog.management.commands.crawl_product_specs import fetch_url, verified_image_suffix
from catalog.models import Product

images = {
    'PFS4207-4GT-DP': 'https://material.dahuasecurity.com/uploads/image/20210518/10-1.png',
    'PFT1500': 'https://material.dahuasecurity.com/uploads/image/20211112/1_0_01_20_10754_2006672588.png',
}
for model, url in images.items():
    product = Product.objects.get(brand__name='Dahua', model=model)
    final_url, _, data = fetch_url(url, timeout=30, max_bytes=12_000_000)
    if not final_url.startswith('https://material.dahuasecurity.com/'):
        raise ValueError(final_url)
    suffix = verified_image_suffix(data)
    product.image.save(f'{model.lower()}{suffix}', ContentFile(data), save=True)
    print(model, len(data), product.image.name)
