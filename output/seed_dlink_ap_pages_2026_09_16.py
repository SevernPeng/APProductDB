from catalog.models import Product

pages = {
    'DAP-2610': 'https://www.dlink.com/uk/en/products/dap-2610-wireless-ac1300-wave-2-dualband-poe-access-point',
    'DAP-2622': 'https://inweb.dlink.com/uk/en/products/dap-2622-wireless-ac1200-wave-2-in-wall-poe-access-point',
    'DAP-2680': 'https://inweb.dlink.com/uk/en/products/dap-2680-wireless-ac1750-wave-2-dualband-poe-access-point',
    'DAP-E3620': 'https://www2.dlink.com/en/products/dap-e3620-be3600-wi-fi-7-ceiling-mount-access-point',
    'DAP-E3620OU': 'https://www.dlink.com/en/products/dap-e3620ou-be3600-wi-fi-7-outdoor-access-point',
    'DAP-E9560': 'https://www.dlink.com/uk/en/products/dap-e9560-be9500-wifi-7-ceiling-mount-access-point',
    'DAP-X2810': 'https://www.dlink.com/uk/en/products/dap-x2810-ax1800-wifi-6-dualband-poe-access-point',
    'DAP-X2850': 'https://www.dlink.com/uk/en/products/dap-x2850-ax3600-wifi-6-dualband-poe-access-point',
    'DAP-X3060': 'https://www.dlink.com/uk/en/products/dap-x3060-ax3000-wi-fi-6-dual-band-poe-access-point',
    'DAP-X3060OU': 'https://www.dlink.com/es/es/products/dap-x3060ou-ax3000-wi-fi-6-outdoor-poe-access-point',
    'DAP-X3060W': 'https://www2.dlink.com/uk/en/products/dap-x3060w-ax3000-wi-fi-6-wall-plate-access-point',
    'DBA-X1230P': 'https://www.dlink.com/en/products/dba-x1230p-ax1800-wi-fi-6-cloud-managed-access-point',
    'DBA-X2830P': 'https://www.dlink.com/en/products/dba-x2830p-nuclias-wireless-ax3600-cloud-managed-access-point',
}
for model, url in pages.items():
    product = Product.objects.get(brand__name='D-Link', model=model)
    product.official_url = url
    product.save(update_fields=['official_url'])
print('seeded', len(pages))
