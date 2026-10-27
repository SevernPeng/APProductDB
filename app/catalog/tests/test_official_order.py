from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from catalog.management.commands.sync_official_product_order import parse_order
from catalog.models import Brand, Category, Product
from catalog.official_order import model_aliases, order_products


class OfficialOrderParsingTests(SimpleTestCase):
    def test_preserves_first_occurrence_and_decodes_labels(self):
        page = '<a aria-label="Navigation">x</a>' + ''.join(
            f'<li class="tp-product-item"><a aria-label="{m}">x</a></li>'
            for m in ['Z100', 'A200', 'Z100', 'A&amp;B']
        )
        self.assertEqual(parse_order(page), ['Z100', 'A200', 'A&B'])

    def test_aliases_do_not_strip_meaningful_suffixes(self):
        self.assertEqual(model_aliases('SG3210(TL-SG3210)'), ['SG3210', 'TLSG3210'])
        self.assertEqual(model_aliases('MC211CS-20'), ['MC211CS20'])
        self.assertEqual(model_aliases('Antenna(2-pack)'), ['ANTENNA(2PACK)'])


class OfficialOrderTests(TestCase):
    @patch('catalog.official_order.load_order')
    def test_category_order_fallback_and_brand_isolation(self, load):
        load.return_value = {
            'accessories': {'models': ['MC420L', 'MC220L', 'MC100CM']},
            'accessories/media-converters': {'models': ['MC220L', 'MC420L', 'MC100CM']},
        }
        brand = Brand.objects.create(name='TP-Link', slug='tp-link')
        competitor = Brand.objects.create(name='Other', slug='other')
        category = Category.objects.create(name='Accessories', slug='accessories')
        for model in ['MC100CM', 'MC420L', 'MC220L', 'AAA-legacy']:
            Product.objects.create(brand=brand, category=category, model=model)
        other = Product.objects.create(brand=competitor, category=category, model='MC220L')
        qs = Product.objects.all()
        self.assertEqual(list(order_products(qs, 'accessories').values_list('model', flat=True))[:3],
                         ['MC420L', 'MC220L', 'MC100CM'])
        ordered = order_products(qs, 'accessories', 'media-converters')
        self.assertEqual(list(ordered.values_list('model', flat=True))[:3],
                         ['MC220L', 'MC420L', 'MC100CM'])
        self.assertIn(other, list(ordered)[3:])
        # Filtering preserves source order, rather than re-sorting alphabetically.
        self.assertEqual(list(order_products(qs.filter(brand=brand, model__in=['MC100CM', 'MC420L']),
                                            'accessories').values_list('model', flat=True)),
                         ['MC420L', 'MC100CM'])
        # Pagination slices retain the same order without dropping records.
        from django.core.paginator import Paginator
        paginator = Paginator(ordered, 2)
        paged_ids = [p.pk for number in paginator.page_range for p in paginator.page(number)]
        self.assertEqual(len(paged_ids), 5)
        self.assertEqual(len(set(paged_ids)), 5)
        self.assertEqual(paged_ids, list(ordered.values_list('pk', flat=True)))
