from datetime import date

from catalog.models import Product, ProductSpec

product = Product.objects.get(brand__name='Cisco', model='CW9172I', is_published=True)
source = 'https://www.cisco.com/c/en/us/td/docs/wireless/access_point/technical-reference/cw9172-dg.html'
values = {
    'mimo_2g': ('2x2', '2.4 GHz (Slot 0), 2x2:2 spatial streams'),
    'mimo_5g': ('2x2 (tri-radio) / 4x4 (dual-radio)', '5 GHz (Slot 1), 2x2:2 in tri-radio mode or 4x4:4 in dual-radio mode'),
    'mimo_6g': ('2x2 (tri-radio)', '6 GHz (Slot 2), 2x2:2 spatial streams in tri-radio mode'),
}
for code, (value, raw) in values.items():
    spec = ProductSpec.objects.get(product=product, definition__code=code)
    spec.value_text = value
    spec.value_number = None
    spec.normalized_value = value
    spec.raw_value = raw
    spec.source_url = source
    spec.source_note = 'Verified from the official Cisco CW9172 deployment guide.'
    spec.verified_date = date.today()
    spec.save(update_fields=('value_text', 'value_number', 'normalized_value', 'raw_value', 'source_url', 'source_note', 'verified_date', 'updated_at'))

streams = ProductSpec.objects.get(product=product, definition__code='total_spatial_streams')
streams.value_number = 6
streams.normalized_value = '6'
streams.raw_value = 'Three 2x2:2 radios, or one 2x2:2 and one 4x4:4 radio; both modes total 6 spatial streams.'
streams.source_url = source
streams.source_note = 'Verified from the official Cisco CW9172 deployment guide.'
streams.verified_date = date.today()
streams.save(update_fields=('value_number', 'normalized_value', 'raw_value', 'source_url', 'source_note', 'verified_date', 'updated_at'))
print('Corrected CW9172I MIMO and total spatial streams from', source)
