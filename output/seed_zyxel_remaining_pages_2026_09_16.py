from catalog.models import Product

pages = {
    'NWA110AX': 'https://www.zyxel.com/uk/en-gb/products/wireless/ax1800-4-stream-wifi-6-dual-radio-nebulaflex-access-point-nwa110ax',
    'WAX650S': 'https://store.zyxel.com/wax650s-us0101f.html',
    'WBE665S': 'https://www.zyxel.com/global/en/products/wireless/be22000-12-stream-wifi-7-triple-radio-nebulaflex-pro-ruggedized-access-point-wbe665s',
    'RGS200-12P': 'https://www.zyxel.com/em/en-em/products/switch/12-port-gbe-managed-poe-switch-rgs200-12p',
}
for model, url in pages.items():
    product = Product.objects.get(brand__name='Zyxel', model=model)
    product.official_url = url
    product.save(update_fields=['official_url'])
