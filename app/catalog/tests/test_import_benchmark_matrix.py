from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase
from openpyxl import Workbook

from catalog.management.commands.import_benchmark_matrix import SHEET_CONFIG, split_models
from catalog.models import Category, Product
from comparison.models import BenchmarkCase, ProductMatch


class ImportBenchmarkMatrixTests(TestCase):
    def test_split_models_preserves_vendor_suffixes(self):
        self.assertEqual(split_models("—"), [])
        self.assertEqual(split_models("–"), [])
        self.assertEqual(split_models("-"), [])
        self.assertEqual(split_models("DS-3E0105P-E/M(C)"), ["DS-3E0105P-E/M(C)"])
        self.assertEqual(split_models("DGS-1210-28/ME"), ["DGS-1210-28/ME"])
        self.assertEqual(
            split_models("GWN7615/GWN7625"),
            ["GWN7615", "GWN7625"],
        )
        self.assertEqual(
            split_models("RG-RAP62-OD/RG-RAP6262(G)"),
            ["RG-RAP62-OD", "RG-RAP6262(G)"],
        )

    def make_workbook(self, path):
        workbook = Workbook()
        first = True
        for index, sheet_name in enumerate(SHEET_CONFIG, start=1):
            sheet = workbook.active if first else workbook.create_sheet()
            first = False
            sheet.title = sheet_name
            sheet.append(["TP-Link", "Ubiquiti", "Ruijie/Reyee"])
            first_competitor = (
                "SHARED-SWITCH"
                if sheet_name in {"Managed Switch", "Unmanaged_EasySmart Switch"}
                else f"COMP-{index}-A"
            )
            sheet.append([
                "EAP100 (EOL)" if sheet_name == "Access Point" else f"TP-{sheet_name}",
                f"{first_competitor}\nCOMP-{index}-B",
                f"RG-AP{index}/RG-RAP{index}",
            ])
        workbook.save(path)

    def test_import_creates_categories_products_cases_and_matches(self):
        with TemporaryDirectory() as temp_dir:
            workbook_path = Path(temp_dir) / "matrix.xlsx"
            self.make_workbook(workbook_path)
            call_command("import_benchmark_matrix", workbook_path)

        self.assertTrue(Category.objects.filter(name="Managed Switch").exists())
        self.assertTrue(
            Category.objects.filter(name="Unmanaged / Easy Smart Switch").exists()
        )
        self.assertTrue(
            Category.objects.filter(name="Accessories", parent=None).exists()
        )
        self.assertEqual(BenchmarkCase.objects.count(), len(SHEET_CONFIG))
        self.assertEqual(ProductMatch.objects.count(), len(SHEET_CONFIG) * 4)
        access_point = Product.objects.get(model="EAP100")
        self.assertEqual(access_point.lifecycle_status, Product.LifecycleStatus.DISCONTINUED)
        self.assertEqual(access_point.region, "US")
        self.assertFalse(
            Product.objects.filter(category__slug="gateway").exclude(region="UN").exists()
        )
        self.assertFalse(
            Product.objects.filter(
                category__slug__in={
                    "accessories",
                    "managed-switches",
                    "unmanaged-easy-smart-switches",
                }
            )
            .exclude(region="UN")
            .exists()
        )

    def test_dry_run_rolls_back_everything(self):
        with TemporaryDirectory() as temp_dir:
            workbook_path = Path(temp_dir) / "matrix.xlsx"
            self.make_workbook(workbook_path)
            call_command("import_benchmark_matrix", workbook_path, dry_run=True)

        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(ProductMatch.objects.count(), 0)

    def test_prune_stale_removes_only_candidates_absent_from_selected_sheet(self):
        with TemporaryDirectory() as temp_dir:
            workbook_path = Path(temp_dir) / "matrix.xlsx"
            self.make_workbook(workbook_path)
            call_command("import_benchmark_matrix", workbook_path)

            access_case = BenchmarkCase.objects.get(
                anchor_product__model="EAP100",
            )
            stale_product = Product.objects.create(
                brand=access_case.candidates.first().competitor_product.brand,
                category=access_case.anchor_product.category,
                model="STALE-DEMO-MODEL",
                region="US",
                ap_type=Product.APType.CEILING,
                notes="Imported from matrix.xlsx",
            )
            ProductMatch.objects.create(
                our_product=access_case.anchor_product,
                competitor_product=stale_product,
                benchmark_case=access_case,
                match_type=ProductMatch.MatchType.DIRECT,
                status=ProductMatch.Status.CONFIRMED,
                region="US",
                reason="Old demo seed.",
            )
            gateway_match_count = ProductMatch.objects.filter(
                benchmark_case__anchor_product__model="TP-Gateway",
            ).count()

            call_command(
                "import_benchmark_matrix",
                workbook_path,
                sheets=["Access Point"],
                prune_stale=True,
                unpublish_orphans=True,
            )

        self.assertFalse(
            ProductMatch.objects.filter(competitor_product=stale_product).exists()
        )
        stale_product.refresh_from_db()
        self.assertFalse(stale_product.is_published)
        self.assertFalse(stale_product.product_model.active)
        self.assertEqual(
            ProductMatch.objects.filter(benchmark_case=access_case).count(),
            4,
        )
        self.assertEqual(
            ProductMatch.objects.filter(
                benchmark_case__anchor_product__model="TP-Gateway",
            ).count(),
            gateway_match_count,
        )
