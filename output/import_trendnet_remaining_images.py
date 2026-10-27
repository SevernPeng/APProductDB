from django.core.files.base import ContentFile

from catalog.management.commands.crawl_product_specs import (
    fetch_url,
    host_is_allowed,
    trendnet_support_image_url,
    verified_image_suffix,
)
from catalog.models import Product

models = ('TEG-10GBRJ100', 'TI-G62', 'TI-G642i', 'TI-G80', 'TI-PG50', 'TWG-431BR')
for model in models:
    product = Product.objects.get(brand__name='TRENDnet', model=model, is_published=True)
    if product.image:
        print(model, 'already has image')
        continue
    image_url = trendnet_support_image_url(model)
    if not image_url:
        print(model, 'no official image')
        continue
    final_url, _, data = fetch_url(image_url, timeout=30, max_bytes=12 * 1024 * 1024)
    if not host_is_allowed(final_url, ('trendnet.com',)):
        raise ValueError(f'Unexpected image redirect for {model}: {final_url}')
    suffix = verified_image_suffix(data)
    product.image.save(f'{model.lower()}{suffix}', ContentFile(data), save=False)
    product.save(update_fields=('image', 'updated_at'))
    print(model, final_url, len(data))
