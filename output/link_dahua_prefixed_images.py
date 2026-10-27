from catalog.models import Product

for alias, base in [('DH-PFM886-15', 'PFM886-15'), ('DH-PFWB5-90ac', 'PFWB5-90ac')]:
    source = Product.objects.get(brand__name='Dahua', model=base)
    target = Product.objects.get(brand__name='Dahua', model=alias)
    target.image = source.image
    target.save(update_fields=['image'])
    print(alias, target.image.name)
