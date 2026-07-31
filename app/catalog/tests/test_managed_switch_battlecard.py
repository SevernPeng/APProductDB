from django.test import SimpleTestCase

from catalog.management.commands.import_managed_switch_battlecard import (
    latest_version_value,
    model_key,
    model_version,
)


class ManagedSwitchBattlecardParsingTests(SimpleTestCase):
    def test_latest_version_value_keeps_only_highest_version_section(self):
        value = (
            "V1.2: 8× 2.5G PoE++ Ports; total budget 500W\n"
            "V2: 24× 2.5G PoE++ Ports; total budget 770W"
        )

        self.assertEqual(
            latest_version_value(value),
            "V2: 24× 2.5G PoE++ Ports; total budget 770W",
        )
        self.assertEqual(
            latest_version_value("V1: 2GB; V1.2: 1GB"),
            "V1.2: 1GB",
        )

    def test_model_key_preserves_sku_slash_as_one_model(self):
        self.assertEqual(
            model_key("DGS-1210-28/ME"),
            model_key("DGS-1210-28ME"),
        )

    def test_revision_detection_excludes_huawei_v2_sku_suffix(self):
        self.assertEqual(model_version("GS716Tv3"), "V3")
        self.assertEqual(model_version("SG3428X v1.20"), "V1.20")
        self.assertEqual(model_version("S6730-H48X6C-V2"), "")
