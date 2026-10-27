import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from html import unescape
from pathlib import Path
from urllib.parse import urljoin

from django.core.management.base import BaseCommand, CommandError

from catalog.management.commands.sync_official_accessory_images import fetch


BASE = "https://www.omadanetworks.com/en/business-networking/"
PAGES = {
    "wireless": "all-omada-wifi/",
    "switching": "all-omada-switch/",
    "gateways": "all-omada-router/",
    "accessories": "all-omada-accessory/",
    "wireless/wifi-7": "all-omada-wifi/?filterby=6271",
    "wireless/ceiling-mount": "omada-wifi-ceiling-mount/",
    "wireless/wall-plate": "omada-wifi-wall-plate/",
    "wireless/outdoor": "omada-wifi-outdoor/",
    "wireless/wireless-bridge": "omada-wifi-wireless-bridge/",
    "wireless/gpon": "omada-wifi-gpon/",
    "wireless/desktop": "omada-wifi-desktop/",
    **{f"switching/{key}": f"omada-switch-{key}/" for key in (
        "campus", "aggregation", "access-max", "access-pro", "access-plus", "access",
        "agile", "industrial",
    )},
    "switching/unmanaged": "https://www.tp-link.com/en/business-networking/soho-switch-unmanaged/",
    "switching/easy-smart": "https://www.tp-link.com/en/business-networking/soho-switch-easy-smart/",
    "switching/legacy-all": "https://www.tp-link.com/en/business-networking/all-soho-switch/",
    "gateways/fusion": "all-omada-fusion-gateway/",
    "gateways/wired": "omada-router-wired-router/",
    "gateways/wifi": "omada-router-wifi-router/",
    "gateways/cellular": "omada-router-5g-4g-wifi-router/",
    "gateways/integrated": "omada-router-integrated-router/",
    "accessories/poe-injectors": "omada-accessory-power-poe/",
    "accessories/power-supplies": "omada-accessory-power-poe/",
    "accessories/media-converters": "omada-accessory-media-converter/",
    "accessories/optical-modules": "omada-accessory-module-cable/",
    "accessories/dac-cables": "omada-accessory-module-cable/",
    "accessories/mounting": "omada-accessory-mounting-bracket/",
}
DEFAULT_PATH = Path(__file__).resolve().parents[2] / "official_product_order.json"


def parse_order(page):
    models = []
    for block in re.split(r'<li\s+class="tp-product-item"', page, flags=re.I)[1:]:
        label = re.search(r'aria-label="([^"]+)"', block, flags=re.I)
        if label:
            model = unescape(label.group(1)).strip()
            if model and model not in models:
                models.append(model)
    return models


class Command(BaseCommand):
    help = "Save the Global Omada catalog's display order without changing product data."

    def add_arguments(self, parser):
        parser.add_argument("--output", type=Path, default=DEFAULT_PATH)

    def handle(self, *args, **options):
        def read_page(path):
            url = urljoin(BASE, path)
            data, content_type = fetch(url)
            if "html" not in content_type:
                raise CommandError(f"Unexpected content type: {url}")
            models = parse_order(data.decode("utf-8"))
            if not models:
                raise CommandError(f"No product cards found: {url}")
            return path, models

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = dict(pool.map(read_page, dict.fromkeys(PAGES.values())))
        snapshot = {
            "retrieved_on": date.today().isoformat(),
            "pages": {key: {"url": urljoin(BASE, path), "models": results[path]} for key, path in PAGES.items()},
        }
        path = options["output"]
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
        for key, page in snapshot["pages"].items():
            self.stdout.write(f"{key}: {len(page['models'])}")
        self.stdout.write(self.style.SUCCESS(f"Saved {path}"))
