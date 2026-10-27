import io
import json
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from catalog.models import Brand, Category, Product, ProductSpec, SpecDefinition


class SyncCurrentSpecFormatTests(TestCase):
    def test_materialize_preserves_source_and_is_idempotent(self):
        brand = Brand.objects.create(name="TP-Link", slug="tp-link", is_own_brand=True)
        category = Category.objects.create(name="Access Point", slug="access-point")
        product = Product.objects.create(model="EAP787", brand=brand, category=category)
        for code, name, kind, unit in (
            ("supported_bands", "Supported Wireless Bands", "text", ""),
            ("antenna_type", "Antenna Type", "text", ""),
            ("total_spatial_streams", "Total Spatial Streams", "integer", ""),
            ("rate_5g_mbps", "5 GHz Max Rate", "integer", "Mbps"),
            ("mesh_support", "Mesh Support", "boolean", ""),
        ):
            definition = SpecDefinition.objects.create(code=code, display_name=name, data_type=kind, unit=unit)
            ProductSpec.objects.create(product=product, definition=definition, value_status="unknown")
        for i, (label, text) in enumerate((
            ("Frequency", "2.4/5/6 GHz"),
            ("Antenna", "2.4 GHz: 2× 4 dBi\n5 GHz: 4× 5 dBi\n6 GHz: 2× 5 dBi"),
            ("Signal Rate", "5 GHz: 8648 Mbps"),
            ("Wireless Functions", "Mesh\n802.11k/v/r"),
        )):
            definition = SpecDefinition.objects.create(code=f"matrix-test-{i}", display_name=label, data_type="text", is_core=False)
            ProductSpec.objects.create(product=product, definition=definition, value_text=text)
        source = list(product.specs.filter(definition__code__startswith="matrix-").order_by("pk").values())
        call_command("sync_current_spec_format", dry_run=True, stdout=io.StringIO())
        self.assertEqual(product.specs.get(definition__code="rate_5g_mbps").value_status, "unknown")
        call_command("sync_current_spec_format", stdout=io.StringIO())
        self.assertEqual(product.specs.get(definition__code="rate_5g_mbps").value_number, Decimal("8648"))
        self.assertEqual(product.specs.get(definition__code="total_spatial_streams").value_number, Decimal("8"))
        self.assertTrue(product.specs.get(definition__code="mesh_support").value_boolean)
        self.assertEqual(list(product.specs.filter(definition__code__startswith="matrix-").order_by("pk").values()), source)
        output = io.StringIO()
        call_command("sync_current_spec_format", stdout=output)
        self.assertEqual(json.loads(output.getvalue())["changed_specs"], 0)
