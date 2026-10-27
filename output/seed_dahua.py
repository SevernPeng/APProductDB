from catalog.models import Product

paths = {
    'IS4210-8GT-120': '/in/products/Transmission/PoE-Switches/Industrial-PoE-Switch/IS4210-8GT-120',
    'PFM885-I': '/in/products/transmission/wireless-devices/other-wireless-bridge/pfm885-i',
    'PFM886-15': '/uk/products/discontinued-products/transmission/pfm886-15',
    'PFS3009-8ET-65': '/in/products/Transmission/PoE-Switches/Desktop-PoE-Switch/PFS3009-8ET-65',
    'PFS3010-8ET-65': '/uk/products/Transmission/PoE-Switches/Desktop-PoE-Switch/PFS3010-8ET-65',
    'PFS4207-4GT-DP': '/in/products/Transmission/PoE-Switches/Industrial-PoE-Switch/PFS4207-4GT-DP',
    'PFT1500': '/in/products/transmission/accessories/poe-extender/pft1500',
    'PFWB5-90ac': '/in/products/Transmission/Wireless-Devices/V-Radio-Wireless-Bridge/PFWB5-90ac',
    'WBC5-30AC-05P': '/in/products/Transmission/Wireless-Devices/WBC-Series-Wireless-Bridge/WBC5-30AC-05P',
    'WBC5-90AC-01P': '/in/products/Transmission/Wireless-Devices/WBC-Series-Wireless-Bridge/WBC5-90AC-01P',
}
for model, path in paths.items():
    product = Product.objects.get(brand__name='Dahua', model=model)
    product.official_url = 'https://www.dahuasecurity.com' + path
    product.save(update_fields=['official_url'])
