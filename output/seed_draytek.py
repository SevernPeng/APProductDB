from catalog.models import Product

for model, slug in {'Vigor 2136': 'vigor2136', 'Vigor 3912': 'vigor3912', 'Vigor2962': 'vigor2962'}.items():
    product = Product.objects.get(brand__name='DrayTek', model=model)
    product.official_url = f'https://draytek.com/products/{slug}/'
    product.save(update_fields=['official_url'])
