import mimetypes
import re
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from catalog.models import Product


INDEX_URL = "https://www.omadanetworks.com/en/business-networking/all-omada-accessory/"
ALLOWED_IMAGE_HOST = "static.tp-link.com"
USER_AGENT = "APProductDB/1.0 (+official TP-Link product image synchronization)"


def fetch(url, *, timeout=30):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get_content_type()


def parse_product_cards(html):
    cards = {}
    for block in re.split(r'<li\s+class="tp-product-item"', html, flags=re.IGNORECASE)[1:]:
        model_match = re.search(r'aria-label="([^"]+)"', block, flags=re.IGNORECASE)
        href_match = re.search(r'<a[^>]+class="[^"]*tp-product-link[^"]*"[^>]+href="([^"]+)"', block, flags=re.IGNORECASE)
        image_match = re.search(
            r'<img[^>]+class="[^"]*tp-product-default[^"]*"[^>]+data-src="([^"]+)"',
            block,
            flags=re.IGNORECASE,
        )
        if not (model_match and href_match and image_match):
            continue
        model = model_match.group(1).strip()
        cards[model.casefold()] = {
            "model": model,
            "page_url": urllib.parse.urljoin(INDEX_URL, href_match.group(1)),
            "image_url": urllib.parse.urljoin(INDEX_URL, image_match.group(1)),
        }
    return cards


class Command(BaseCommand):
    help = "Fill missing TP-Link accessory images from the official global Omada catalog."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        html_bytes, content_type = fetch(INDEX_URL)
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise CommandError(f"Unexpected catalog content type: {content_type}")
        cards = parse_product_cards(html_bytes.decode("utf-8", errors="replace"))
        if not cards:
            raise CommandError("No product cards found on the official accessories page.")

        products = Product.objects.filter(
            category__slug="accessories",
            brand__slug="tp-link",
            is_published=True,
            image="",
        ).order_by("model")
        counts = Counter()
        missing = []
        for product in products:
            card = cards.get(product.model.casefold())
            if not card:
                missing.append(product.model)
                counts["not_listed"] += 1
                continue

            parsed_image = urllib.parse.urlparse(card["image_url"])
            parsed_page = urllib.parse.urlparse(card["page_url"])
            if parsed_image.scheme != "https" or parsed_image.hostname != ALLOWED_IMAGE_HOST:
                raise CommandError(f"Rejected non-official image URL for {product.model}: {card['image_url']}")
            if parsed_page.scheme != "https" or parsed_page.hostname != "www.omadanetworks.com":
                raise CommandError(f"Rejected non-global product URL for {product.model}: {card['page_url']}")

            if options["dry_run"]:
                self.stdout.write(f"MATCH {product.model}: {card['image_url']}")
                counts["matched"] += 1
                continue

            image_bytes, image_type = fetch(card["image_url"])
            if not image_type.startswith("image/"):
                raise CommandError(f"Unexpected image content type for {product.model}: {image_type}")
            if not image_bytes or len(image_bytes) > 12 * 1024 * 1024:
                raise CommandError(f"Invalid image size for {product.model}: {len(image_bytes)} bytes")
            suffix = Path(parsed_image.path).suffix.lower()
            if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
                suffix = mimetypes.guess_extension(image_type) or ".jpg"
            product.official_url = card["page_url"]
            product.image.save(
                f"{slugify(product.model) or 'accessory'}{suffix}",
                ContentFile(image_bytes),
                save=False,
            )
            product.save(update_fields=("image", "official_url", "updated_at"))
            counts["saved"] += 1
            self.stdout.write(f"SAVED {product.model}")

        self.stdout.write(f"SUMMARY {dict(counts)}")
        if missing:
            self.stdout.write("NOT LISTED: " + ", ".join(missing))
