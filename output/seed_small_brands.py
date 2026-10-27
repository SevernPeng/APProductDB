from catalog.models import Product

pages = {
    ('Buffalo', 'LSW6-GT-5ESL'): 'https://www.buffalo.jp/product/detail/lsw6-gt-5esl_nbk.html',
    ('Buffalo', 'LSW6-GT-8ESL'): 'https://www.buffalo.jp/product/detail/lsw6-gt-8esl_nbk.html',
    ('Linksys', 'SE3005'): 'https://support.linksys.com/kb/article/5926/',
}
for (brand, model), url in pages.items():
    product = Product.objects.get(brand__name=brand, model=model)
    product.official_url = url
    product.save(update_fields=['official_url'])
