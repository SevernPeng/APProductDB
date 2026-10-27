from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import TestCase

from catalog.management.commands.sync_syscom_prices import (
    model_key,
    parse_search_hits,
    record_price,
    search_product,
    search_queries,
    select_hit,
)
from catalog.models import (
    Brand,
    Category,
    PriceSource,
    Product,
    ProductPriceListing,
    ProductPriceSnapshot,
)


class SyscomPriceTests(TestCase):
    def setUp(self):
        brand = Brand.objects.create(name="TP-Link", slug="tp-link", is_own_brand=True)
        category = Category.objects.create(name="Wireless Bridge", slug="wireless-bridge")
        self.product = Product.objects.create(brand=brand, category=category, model="EAP215-Bridge KIT")
        self.source = PriceSource.objects.create(code="syscom", name="SYSCOM México", base_url="https://www.syscom.mx")

    def test_model_key_handles_tp_link_prefix_and_separators(self):
        self.assertEqual(model_key("TL-SG3428XMP"), model_key("SG3428XMP"))
        self.assertEqual(model_key("EAP215-BRIDGE-KIT"), model_key("EAP215-Bridge KIT"))
        self.assertNotEqual(model_key("TLX100"), model_key("X100"))

    def test_all_current_names_include_legacy_tl_prefix_fallback(self):
        self.assertEqual(
            search_queries(self.product),
            ["EAP215-Bridge KIT", "TL-EAP215-Bridge KIT"],
        )
        self.product.model = "TL-SG108"
        self.assertEqual(search_queries(self.product), ["TL-SG108"])

    def test_parses_and_selects_exact_embedded_search_hit(self):
        page = r'''\"marca\":\"TP-LINK\",\"objectID\":\"235958\",\"modelo_alias\":\"EAP215-BRIDGE-KIT\",\"precios\":{\"precio_lista_usd\":291.47,\"precio_especial_usd\":262.32,\"precio_unitario_usd\":161.16,\"asteriscos_mxn\":{}}'''
        hits = parse_search_hits(page)
        hit = select_hit(self.product, hits)
        self.assertEqual(hit["external_id"], "235958")
        self.assertEqual(hit["unit_price"], Decimal("161.16"))

    def test_parser_keeps_prices_with_their_object_when_fields_are_reordered(self):
        page = r'''\"marca\":\"TP-LINK\",\"objectID\":\"111\",\"precio_unitario_usd\":99.31,\"padding\":\"x\",\"modelo_alias\":\"TL-SG2210P\"},{\"marca\":\"TP-LINK\",\"objectID\":\"222\",\"modelo_alias\":\"KIT-CERT-OMADA\",\"precio_unitario_usd\":160.51'''

        hits = parse_search_hits(page)

        self.assertEqual(
            [(hit["external_id"], hit["model"], hit["unit_price"]) for hit in hits],
            [
                ("111", "TL-SG2210P", Decimal("99.31")),
                ("222", "KIT-CERT-OMADA", Decimal("160.51")),
            ],
        )

    @patch("catalog.management.commands.sync_syscom_prices.time.sleep")
    def test_search_retries_fluctuating_results(self, sleep):
        client = Mock()
        client.search.side_effect = [[], [], [], [{
            "external_id": "191393",
            "model": "TL-SG2210P",
            "brand": "TP-LINK",
            "currency": "USD",
            "unit_price": Decimal("99.31"),
            "list_price": None,
            "special_price": None,
        }]]
        self.product.model = "SG2210P"

        hit = search_product(client, self.product, attempts=3, retry_delay=0.5)

        self.assertEqual(hit["external_id"], "191393")
        self.assertEqual(client.search.call_count, 4)
        sleep.assert_called_once_with(0.5)

    def test_records_only_when_account_price_changes(self):
        hit = {"external_id": "235958", "model": "EAP215-BRIDGE-KIT", "currency": "USD", "unit_price": Decimal("161.16"), "list_price": Decimal("291.47"), "special_price": Decimal("262.32")}
        self.assertTrue(record_price(self.source, self.product, hit))
        self.assertFalse(record_price(self.source, self.product, hit))
        hit["unit_price"] = Decimal("159.00")
        self.assertTrue(record_price(self.source, self.product, hit))
        self.assertEqual(ProductPriceSnapshot.objects.count(), 2)
        listing = ProductPriceListing.objects.get(source=self.source, product=self.product)
        self.assertEqual(listing.external_id, "235958")
        self.assertEqual(listing.external_model, "EAP215-BRIDGE-KIT")

    def test_saved_listing_code_disambiguates_search_results(self):
        listing = ProductPriceListing.objects.create(
            source=self.source,
            product=self.product,
            external_id="correct",
            external_model="EAP215-BRIDGE-KIT",
            product_url="https://www.syscom.mx/products/correct",
        )
        hits = [
            {"external_id": "other", "model": "EAP215-BRIDGE-KIT", "brand": "TP-LINK"},
            {"external_id": "correct", "model": "KIT-WITH-EAP215", "brand": "TP-LINK"},
        ]

        self.assertEqual(select_hit(self.product, hits, listing)["external_id"], "correct")
        self.assertEqual(search_queries(self.product, listing)[0], "EAP215-BRIDGE-KIT")
