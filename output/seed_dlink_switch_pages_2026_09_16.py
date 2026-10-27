from catalog.models import Product

pages = {
    'DES-105': 'https://www.dlink.com/sg/en/products/des-105-5-port-fast-ethernet-switch',
    'DGS-1210-10P': 'https://www.dlink.com/us/en/products/dgs-1210-10p-10-port-gigabit-smart-managed-poe-switch',
    'DGS-1510-28X': 'https://www.dlink.com/en/products/dgs-1510-28x-28-port-stackable-gigabit-switch-including-4-10gbe-sfp-ports',
}
for model, url in pages.items():
    product = Product.objects.get(brand__name='D-Link', model=model)
    product.official_url = url
    product.save(update_fields=['official_url'])
