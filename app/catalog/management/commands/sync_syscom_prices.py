import html
import http.cookiejar
import json
import os
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import (
    PriceSource,
    Product,
    ProductPriceListing,
    ProductPriceSnapshot,
)


BASE_URL = "https://www.syscom.mx"
USER_AGENT = "APProductDB/1.0 (SYSCOM weekly price synchronization)"


def model_key(value):
    value = re.sub(r"^TL[-_\s]+", "", (value or "").upper())
    return re.sub(r"[^A-Z0-9]", "", value)


def decimal_value(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def parse_search_hits(page_html):
    text = html.unescape(page_html)
    hits = []
    model_markers = list(re.finditer(r'\\"modelo_alias\\":\\"([^\\"]+)\\"', text))
    for index, model_match in enumerate(model_markers):
        start = model_markers[index - 1].end() if index else 0
        end = model_markers[index + 1].start() if index + 1 < len(model_markers) else len(text)
        before = text[start:model_match.start()]
        after = text[model_match.end():end]
        external_ids = re.findall(r'\\"objectID\\":\\"(\d+)\\"', before)
        brands = re.findall(r'\\"marca\\":\\"([^\\"]+)\\"', before)
        unit_matches_before = re.findall(r'\\"precio_unitario_usd\\":([0-9.]+)', before)
        unit = re.search(r'\\"precio_unitario_usd\\":([0-9.]+)', after)
        unit_value = unit.group(1) if unit else (unit_matches_before[-1] if unit_matches_before else None)
        if not (external_ids and brands and unit_value):
            continue
        price_block = after if unit else before
        list_price = re.search(r'\\"precio_lista_usd\\":([0-9.]+)', price_block)
        special_price = re.search(r'\\"precio_especial_usd\\":([0-9.]+)', price_block)
        hits.append(
            {
                "external_id": external_ids[-1],
                "model": model_match.group(1),
                "brand": brands[-1],
                "currency": "USD",
                "unit_price": decimal_value(unit_value),
                "list_price": decimal_value(list_price.group(1)) if list_price else None,
                "special_price": decimal_value(special_price.group(1)) if special_price else None,
            }
        )
    unique = {}
    for hit in hits:
        unique[(hit["external_id"], hit["model"])] = hit
    return list(unique.values())


class SyscomClient:
    def __init__(self, username, password, timeout=30):
        self.username = username
        self.password = password
        self.timeout = timeout
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def request(self, path, *, data=None, content_type=None):
        url = urllib.parse.urljoin(BASE_URL, path)
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json, text/html;q=0.9"}
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(url, data=data, headers=headers)
        with self.opener.open(request, timeout=self.timeout) as response:
            return response.read().decode("utf-8", errors="replace")

    def login(self):
        credentials = {"no_de_cliente": self.username, "password": self.password}
        prelogin = json.loads(
            self.request(
                "/api/auth/pre-login",
                data=json.dumps(credentials).encode("utf-8"),
                content_type="application/json",
            )
        )
        if not prelogin.get("success"):
            raise CommandError("SYSCOM rejected the configured credentials.")
        if prelogin.get("requires_mfa"):
            raise CommandError("SYSCOM requires MFA; unattended synchronization cannot continue.")
        csrf = json.loads(self.request("/api/auth/csrf")).get("csrfToken")
        if not csrf:
            raise CommandError("SYSCOM did not return a CSRF token.")
        form = urllib.parse.urlencode(
            {
                **credentials,
                "csrfToken": csrf,
                "callbackUrl": f"{BASE_URL}/",
                "json": "true",
            }
        ).encode("utf-8")
        self.request(
            "/api/auth/callback/credentials",
            data=form,
            content_type="application/x-www-form-urlencoded",
        )
        session = json.loads(self.request("/api/auth/session"))
        if not session.get("user"):
            raise CommandError("SYSCOM session was not established.")

    def search(self, query):
        encoded = urllib.parse.urlencode({"query": query})
        return parse_search_hits(self.request(f"/products?{encoded}"))


def select_hit(product, hits, listing=None):
    tp_link_hits = [
        hit
        for hit in hits
        if hit["brand"].upper().replace(" ", "") in {"TP-LINK", "TPLINK"}
    ]
    if listing:
        external_matches = [
            hit for hit in tp_link_hits if hit["external_id"] == listing.external_id
        ]
        if len(external_matches) == 1:
            return external_matches[0]
    expected = model_key(product.model)
    matches = [
        hit for hit in tp_link_hits if model_key(hit["model"]) == expected
    ]
    unique_matches = {
        (hit["external_id"], model_key(hit["model"])): hit for hit in matches
    }
    return next(iter(unique_matches.values())) if len(unique_matches) == 1 else None


def search_queries(product, listing=None):
    queries = [listing.external_model] if listing else []
    queries.append(product.model)
    if not re.match(r"^TL[-_\s]+", product.model, flags=re.IGNORECASE):
        queries.append(f"TL-{product.model}")
    return list(dict.fromkeys(query for query in queries if query))


def search_product(client, product, listing=None, attempts=3, retry_delay=0.75):
    """Search every model spelling per pass because SYSCOM results can fluctuate."""
    queries = search_queries(product, listing)
    for attempt in range(attempts):
        for query in queries:
            hit = select_hit(product, client.search(query), listing)
            if hit:
                return hit
        if attempt + 1 < attempts and retry_delay > 0:
            time.sleep(retry_delay * (attempt + 1))
    return None


def record_price(source, product, hit):
    now = timezone.now()
    ProductPriceListing.objects.update_or_create(
        source=source,
        product=product,
        defaults={
            "external_id": hit["external_id"],
            "external_model": hit["model"],
            "product_url": f"{BASE_URL}/products/{hit['external_id']}",
            "active": True,
            "last_checked_at": now,
            "last_seen_at": now,
        },
    )
    latest = product.price_snapshots.filter(source=source).order_by("-created_at", "-pk").first()
    if latest and latest.currency == hit["currency"] and latest.unit_price == hit["unit_price"]:
        return False
    ProductPriceSnapshot.objects.create(
        source=source,
        product=product,
        external_id=hit["external_id"],
        external_model=hit["model"],
        product_url=f"{BASE_URL}/products/{hit['external_id']}",
        currency=hit["currency"],
        unit_price=hit["unit_price"],
        list_price=hit["list_price"],
        special_price=hit["special_price"],
        tax_included=False,
    )
    return True


class Command(BaseCommand):
    help = "Synchronize account prices for published TP-Link products from SYSCOM."

    def add_arguments(self, parser):
        parser.add_argument("--product-id", type=int)
        parser.add_argument("--limit", type=int)
        parser.add_argument("--delay", type=float, default=0.2)
        parser.add_argument("--passes", type=int, default=3)
        parser.add_argument("--search-attempts", type=int, default=1)
        parser.add_argument("--retry-delay", type=float, default=0.75)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        username = os.getenv("SYSCOM_USERNAME", "").strip()
        password = os.getenv("SYSCOM_PASSWORD", "")
        if not username or not password:
            raise CommandError("SYSCOM_USERNAME and SYSCOM_PASSWORD must be configured.")

        source, _ = PriceSource.objects.get_or_create(
            code="syscom",
            defaults={"name": "SYSCOM México", "base_url": BASE_URL},
        )
        products = Product.objects.filter(brand__slug="tp-link", is_published=True).order_by("model", "pk")
        if options["product_id"]:
            products = products.filter(pk=options["product_id"])
        if options["limit"]:
            products = products[: options["limit"]]
        products = list(products)
        if options["passes"] < 1:
            raise CommandError("--passes must be at least 1.")
        if options["search_attempts"] < 1:
            raise CommandError("--search-attempts must be at least 1.")
        counts = Counter({"products": len(products)})
        errors = []
        unresolved = {product.pk: product for product in products}
        listings = {
            listing.product_id: listing
            for listing in ProductPriceListing.objects.filter(
                source=source, product_id__in=unresolved
            )
        }
        try:
            for pass_number in range(1, options["passes"] + 1):
                if not unresolved:
                    break
                client = SyscomClient(username, password)
                client.login()
                matched_this_pass = 0
                self.stdout.write(
                    f"PASS {pass_number}/{options['passes']} searching {len(unresolved)} unresolved products"
                )
                for product in list(unresolved.values()):
                    try:
                        hit = search_product(
                            client,
                            product,
                            listings.get(product.pk),
                            attempts=options["search_attempts"],
                            retry_delay=options["retry_delay"],
                        )
                        counts["checks"] += 1
                        if not hit:
                            continue
                        unresolved.pop(product.pk, None)
                        counts["matched"] += 1
                        matched_this_pass += 1
                        if options["dry_run"]:
                            counts["would_record"] += 1
                        else:
                            with transaction.atomic():
                                changed = record_price(source, product, hit)
                            counts["recorded" if changed else "unchanged"] += 1
                        self.stdout.write(
                            f"{product.model}: {hit['currency']} {hit['unit_price']} "
                            f"({'new' if options['dry_run'] else 'checked'})"
                        )
                    except Exception as exc:
                        counts["errors"] += 1
                        errors.append(f"pass {pass_number} {product.model}: {exc}")
                    if options["delay"] > 0:
                        time.sleep(options["delay"])
                self.stdout.write(
                    f"PASS {pass_number} matched {matched_this_pass}; {len(unresolved)} unresolved"
                )
            counts["not_matched"] = len(unresolved)
            if unresolved and not options["dry_run"]:
                ProductPriceListing.objects.filter(
                    source=source, product_id__in=unresolved
                ).update(last_checked_at=timezone.now())
            status = "success" if not errors else "partial"
            message = f"{dict(counts)}"
        except Exception as exc:
            status = "error"
            message = str(exc)
            raise
        finally:
            if not options["dry_run"]:
                source.last_synced_at = timezone.now()
                source.last_sync_status = status
                source.last_sync_message = message[:4000]
                source.save(update_fields=("last_synced_at", "last_sync_status", "last_sync_message", "updated_at"))
        self.stdout.write(f"SUMMARY {dict(counts)}")
        if errors:
            self.stdout.write("ERRORS\n" + "\n".join(errors))
