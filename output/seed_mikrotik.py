from catalog.models import Product

urls = {
    'ATL 5G R16': 'atl_5g_r16',
    'hAP ax S': 'hap_ax_s',
    'hEX': 'RB750Gr3',
    'hEX RB750Gr3': 'RB750Gr3',
    'hEX S': 'hex_s',
    'hEX S RB760iGS': 'hex_s',
    'hEX lite': 'RB750r2',
    'wAP ax LTE7 kit': 'wap_ax_lte7',
    'Chateau LTE7 ax': 'chateau_lte7_ax',
    'Chateau LTE6 ax': 'chateau_lte6_ax',
    'RB260GSP': 'RB260GSP',
    'CCR1009-7G-1C-1S+': 'CCR1009-7G-1C-1Splus',
}
for model, slug in urls.items():
    product = Product.objects.get(brand__name='MikroTik', model=model)
    product.official_url = f'https://mikrotik.com/product/{slug}'
    product.save(update_fields=['official_url'])
