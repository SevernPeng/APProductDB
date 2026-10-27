import concurrent.futures
import functools
import gzip
import html
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from catalog.models import (
    Product,
    ProductSpec,
    SourceDocument,
    SpecDefinition,
    SpecEvidence,
)
from catalog.product_types import product_type_code

OFFICIAL_DOMAINS = {
    "TP-Link": ("tp-link.com", "omadanetworks.com"),
    "Ubiquiti": ("ui.com", "ubnt.com"),
    "Ruijie": ("ruijienetworks.com", "ruijie.com"),
    "Reyee": ("reyee.ruijie.com", "ruijienetworks.com", "ruijie.com"),
    "Aruba": ("arubanetworks.com", "hpe.com"),
    "RUCKUS": ("ruckusnetworks.com", "vistancenetworks.com"),
    "Grandstream": ("grandstream.com",),
    "Cisco": ("cisco.com",),
    "Meraki": ("meraki.cisco.com", "documentation.meraki.com"),
    "D-Link": ("dlink.com",),
    "NETGEAR": ("netgear.com",),
    "Zyxel": ("zyxel.com",),
    "Huawei": ("huawei.com",),
    "eKit": ("huawei.com",),
    "Hikvision": ("hikvision.com",),
    "EnGenius": ("engeniustech.com", "engeniuscdn.com"),
    "Fortinet": ("fortinet.com",),
    "MikroTik": ("mikrotik.com",),
    "DrayTek": ("draytek.com",),
    "Dahua": ("dahuasecurity.com",),
    "TRENDnet": ("trendnet.com",),
    "H3C": ("h3c.com",),
    "HPE": ("hpe.com",),
    "Instant On": ("hpe.com", "arubanetworks.com"),
    "Tenda": ("tenda.com.cn", "tendacn.com"),
    "Linksys": ("linksys.com",),
    "Buffalo": ("buffalotech.com", "buffaloamericas.com", "buffalo.jp"),
}

USER_AGENT = "Mozilla/5.0"

REYEE_CATALOG_URLS = (
    "https://reyee.ruijie.com/en-global/products/reyee-wireless/",
    "https://reyee.ruijie.com/en-global/products/reyee-switch/",
    "https://reyee.ruijie.com/en-global/products/reyee-wireless-bridge/",
    "https://reyee.ruijie.com/en-global/products/reyee-router/",
    "https://reyee.ruijie.com/en-global/productsCategories/",
)

_REYEE_COOKIES = {}

SITEMAP_HINTS = {
    "TP-Link": tuple(
        f"https://www.{domain}/{locale}/sitemap.xml"
        for domain in ("tp-link.com", "omadanetworks.com")
        for locale in ("en", "us", "uk", "in", "jp")
    ),
}

SPEC_METADATA = {
    "supported_bands": ("Supported Wireless Bands", "Wireless", "text", "", "none", "p0"),
    "total_spatial_streams": ("Total Spatial Streams", "Wireless", "integer", "", "higher", "p0"),
    "rate_2g_mbps": ("2.4 GHz Max Rate", "Performance", "decimal", "Mbps", "higher", "p0"),
    "rate_5g_mbps": ("5 GHz Max Rate", "Performance", "decimal", "Mbps", "higher", "p0"),
    "rate_6g_mbps": ("6 GHz Max Rate", "Performance", "decimal", "Mbps", "higher", "p0"),
    "max_channel_width_mhz": ("Band Width", "Wireless", "integer", "MHz", "higher", "p0"),
    "ethernet_interfaces": ("Ethernet Interfaces", "Interfaces", "text", "", "none", "p0"),
    "poe_input": ("PoE Input", "Power", "text", "", "equal", "p0"),
    "power_method": ("Power Method", "Power", "text", "", "equal", "p0"),
    "max_clients": ("Max Clients", "Capacity", "integer", "", "higher", "p0"),
    "ip_rating": ("IP Rating", "Physical", "text", "", "equal", "p0"),
    "switching_capacity_gbps": ("Switching Capacity", "Performance", "decimal", "Gbps", "higher", "p0"),
    "packet_forwarding_rate_mpps": ("Packet Forwarding Rate", "Performance", "decimal", "Mpps", "higher", "p0"),
    "mac_address_table": ("MAC Address Table", "Capacity", "text", "", "higher", "p1"),
    "packet_buffer_mb": ("Packet Buffer", "Capacity", "decimal", "MB", "higher", "p1"),
    "jumbo_frame_bytes": ("Jumbo Frame", "Capacity", "integer", "bytes", "higher", "p1"),
    "management_type": ("Management Type", "Management", "text", "", "equal", "p1"),
    "flow_control": ("Flow Control", "Software Features", "text", "", "equal", "p1"),
    "qos_support": ("QoS", "Software Features", "text", "", "equal", "p1"),
    "igmp_snooping": ("IGMP Snooping", "Software Features", "text", "", "equal", "p1"),
    "transmission_method": ("Transmission Method", "Software Features", "text", "", "equal", "p1"),
    "poe_budget_w": ("Total PoE Budget", "Power", "decimal", "W", "higher", "p0"),
    "max_power_consumption_w": ("Max Power Consumption", "Power", "decimal", "W", "lower", "p1"),
    "fanless": ("Fanless Design", "Physical", "boolean", "", "equal", "p1"),
    "dimensions_mm": ("Dimensions", "Physical", "text", "mm", "none", "p1"),
    "operating_temperature_c": ("Operating Temperature", "Environment", "text", "°C", "none", "p1"),
    "vpn_throughput_mbps": ("VPN Throughput", "Performance", "decimal", "Mbps", "higher", "p0"),
    "concurrent_sessions": ("Concurrent Sessions", "Capacity", "integer", "", "higher", "p0"),
    "antenna_gain_dbi": ("Antenna Gain", "Wireless", "text", "dBi", "higher", "p1"),
    "wireless_range": ("Wireless Range", "Coverage", "text", "", "higher", "p0"),
    "lightning_protection_kv": ("Lightning Protection", "Environment", "text", "kV", "higher", "p1"),
}


def parse_reyee_challenge_cookie(data):
    """Return the cookies generated by Reyee's small JavaScript bot challenge."""
    page = data.decode("utf-8", errors="ignore")
    if "EO_Bot_Ssid=" not in page or "__tst_status" not in page:
        return ""
    values_match = re.search(
        r"var\s+e\s*=\s*\{(.*?)\}\s*,\s*t\s*=\s*0",
        page,
        re.DOTALL,
    )
    ssid_match = re.search(r"\bt\s*,\s*(\d{6,})\s*\)", page)
    if not values_match or not ssid_match:
        return ""
    status_values = [int(value) for value in re.findall(r":\s*(\d{6,})", values_match.group(1))]
    if len(status_values) != 3:
        return ""
    return f"__tst_status={sum(status_values)}#; EO_Bot_Ssid={ssid_match.group(1)}"


def fetch_url(url, timeout=20, max_bytes=3_000_000, attempts=3):
    host = (urllib.parse.urlparse(url).hostname or "").casefold()

    def request_for(cookie=""):
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,image/avif,image/webp,*/*;q=0.5",
            "Accept-Language": "en-US,en;q=0.8",
        }
        if cookie:
            headers["Cookie"] = cookie
        return urllib.request.Request(url, headers=headers)

    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(
                request_for(_REYEE_COOKIES.get(host, "")), timeout=timeout
            ) as response:
                content_type = response.headers.get("Content-Type", "")
                data = response.read(max_bytes)
                final_url = response.geturl()
            challenge_cookie = parse_reyee_challenge_cookie(data)
            if challenge_cookie:
                _REYEE_COOKIES[host] = challenge_cookie
                with urllib.request.urlopen(
                    request_for(challenge_cookie), timeout=timeout
                ) as response:
                    content_type = response.headers.get("Content-Type", "")
                    data = response.read(max_bytes)
                    final_url = response.geturl()
            return final_url, content_type, data
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt + 1 >= attempts:
                raise
            retry_after = exc.headers.get("Retry-After", "")
            delay = float(retry_after) if retry_after.isdigit() else 1.5 * (2**attempt)
            time.sleep(min(delay, 8))
        except (urllib.error.URLError, TimeoutError):
            if attempt + 1 >= attempts:
                raise
            time.sleep(1.5 * (2**attempt))


def host_is_allowed(url, domains):
    host = (urllib.parse.urlparse(url).hostname or "").casefold()
    return any(host == domain or host.endswith(f".{domain}") for domain in domains)


def encode_http_url(url):
    """Percent-encode Unicode and spaces without double-encoding existing URLs."""
    parsed = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(
        urllib.parse.unquote(parsed.path), safe="/:@-._~!$&'()*+,;="
    )
    query = urllib.parse.quote(
        urllib.parse.unquote(parsed.query), safe="=&?/:;+,%@-._~!$'()*"
    )
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, path, query, parsed.fragment)
    )


def model_token_present(model, value):
    parts = re.findall(r"[a-z0-9]+", model.casefold())
    if not parts:
        return False
    pattern = r"(?<![a-z0-9])" + r"[^a-z0-9]*".join(re.escape(part) for part in parts) + r"(?![a-z0-9])"
    return re.search(pattern, value.casefold()) is not None


def aruba_switch_sku_matches(model, url, title):
    """Accept a verified HPE switch SKU when its title abbreviates our model name."""
    sku = re.search(r"\b([A-Z]{1,3}\d{3,4}[A-Z])\)?$", model, re.I)
    family = re.search(r"\b(?:CX\s*)?(\d{4}[A-Z]?)\b", model, re.I)
    if not sku or not family:
        return False
    path = urllib.parse.urlparse(url).path.casefold()
    return (
        path.endswith("/p/" + sku.group(1).casefold())
        and re.search(r"\b" + re.escape(family.group(1)) + r"\b", title, re.I) is not None
        and "switch" in title.casefold()
    )


@functools.lru_cache(maxsize=1)
def reyee_catalog_product_urls():
    urls = []
    for catalog_url in REYEE_CATALOG_URLS:
        try:
            final_url, content_type, data = fetch_url(
                catalog_url, timeout=30, max_bytes=3_000_000
            )
        except Exception:
            continue
        if "html" not in content_type.casefold():
            continue
        page = data.decode("utf-8", errors="ignore")
        for href in re.findall(r"href=[\"']([^\"']+)[\"']", page, re.IGNORECASE):
            product_url = urllib.parse.urljoin(final_url, html.unescape(href))
            path = urllib.parse.urlparse(product_url).path.casefold()
            if (
                host_is_allowed(product_url, OFFICIAL_DOMAINS["Reyee"])
                and "/products/" in path
                and "/resources/" not in path
            ):
                urls.append(product_url)
    return tuple(dict.fromkeys(urls))


def reyee_catalog_product_url(model):
    normalized_model = re.sub(r"[^a-z0-9]", "", model.casefold())
    model_keys = {normalized_model}
    if normalized_model.startswith("rg"):
        model_keys.add(normalized_model[2:])
    candidates = []
    for url in reyee_catalog_product_urls():
        normalized_url = re.sub(
            r"[^a-z0-9]", "", urllib.parse.unquote(urllib.parse.urlparse(url).path).casefold()
        )
        matching_keys = [key for key in model_keys if key and key in normalized_url]
        if not matching_keys:
            continue
        slug = urllib.parse.urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
        normalized_slug = re.sub(r"[^a-z0-9]", "", slug.casefold())
        exact = normalized_slug in model_keys
        longest_match = max(len(key) for key in matching_keys)
        candidates.append((not exact, -longest_match, len(normalized_slug), len(url), url))
    return min(candidates)[-1] if candidates else None


def lookup_model_name(model):
    return re.sub(r"\s+(?:V(?:ER(?:SION)?)?\s*)?\d+(?:\.\d+)+$", "", model, flags=re.I).strip()


@functools.lru_cache(maxsize=32)
def official_sitemap_urls(brand, domains):
    seeds = list(SITEMAP_HINTS.get(brand, ()))
    if not seeds:
        return ()
    product_urls = []
    visited = set()
    queue = list(dict.fromkeys(seeds))
    while queue and len(visited) < 20:
        sitemap_url = queue.pop(0)
        if sitemap_url in visited:
            continue
        visited.add(sitemap_url)
        try:
            _, _, data = fetch_url(sitemap_url, timeout=25, max_bytes=5_000_000)
            if data.startswith(b"\x1f\x8b"):
                data = gzip.decompress(data)
            root = ET.fromstring(data)
        except (urllib.error.URLError, TimeoutError, ET.ParseError, OSError, ValueError):
            continue
        locations = [(node.text or "").strip() for node in root.findall(".//{*}loc")]
        if root.tag.casefold().endswith("sitemapindex"):
            queue.extend(url for url in locations if url and len(queue) < 40)
        else:
            product_urls.extend(url for url in locations if url and host_is_allowed(url, domains))
    return tuple(dict.fromkeys(product_urls))


def search_yahoo_official(brand, model, domains):
    query = f'site:{domains[0]} "{model}" {brand}'
    search_url = "https://search.yahoo.com/search?p=" + urllib.parse.quote_plus(query)
    _, _, data = fetch_url(search_url, timeout=20, max_bytes=600_000, attempts=1)
    page = data.decode("utf-8", errors="ignore")
    normalized_model = re.sub(r"[^a-z0-9]", "", model.casefold())
    candidates = []
    for encoded_href in re.findall(r'href=["\']([^"\']+)', page, re.IGNORECASE):
        href = html.unescape(encoded_href)
        redirect_match = re.search(r"/RU=(.*?)/RK=", href)
        if redirect_match:
            href = urllib.parse.unquote(redirect_match.group(1))
        if not href.startswith(("http://", "https://")) or not host_is_allowed(href, domains):
            continue
        lowered = href.casefold()
        score = 0
        if normalized_model in re.sub(r"[^a-z0-9]", "", urllib.parse.unquote(lowered)):
            score += 6
        if any(token in lowered for token in ("/product", "/products", "/business-networking", "/datasheet", "/resource")):
            score += 3
        if lowered.endswith(".pdf"):
            score += 1
        if any(token in lowered for token in ("/press", "/news", "/blog", "/community", "/forum", "end-of-sale", "end_of_sale", "announcement")):
            score -= 5
        candidates.append((score, href))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    return candidates[0][1]


def search_brave_official(brand, model, domains):
    query = f'site:{domains[0]} "{model}" {brand}'
    search_url = "https://search.brave.com/search?q=" + urllib.parse.quote_plus(query)
    _, _, data = fetch_url(search_url, timeout=20, max_bytes=700_000, attempts=1)
    page = data.decode("utf-8", errors="ignore")
    normalized_model = re.sub(r"[^a-z0-9]", "", model.casefold())
    candidates = []
    for encoded_href in re.findall(r'href=["\']([^"\']+)', page, re.IGNORECASE):
        href = html.unescape(encoded_href)
        if not href.startswith(("http://", "https://")) or not host_is_allowed(href, domains):
            continue
        lowered = href.casefold()
        score = 0
        if normalized_model in re.sub(r"[^a-z0-9]", "", urllib.parse.unquote(lowered)):
            score += 6
        if any(token in lowered for token in ("/product", "/products", "/business-networking", "/datasheet", "/resource")):
            score += 3
        if "datasheet" in lowered or lowered.endswith(".pdf"):
            score += 2
        if any(token in lowered for token in ("manual", "release_note", "release-note", "/press", "/news", "/blog", "/forum", "end-of-sale", "end_of_sale", "announcement")):
            score -= 5
        candidates.append((score, href))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    return candidates[0][1]


def search_duckduckgo_official(brand, model, domains):
    query = f'site:{domains[0]} "{model}" {brand} specifications datasheet'
    search_url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(query)
    request = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read(800_000)
    page = data.decode("utf-8", errors="ignore")
    normalized_model = re.sub(r"[^a-z0-9]", "", model.casefold())
    candidates = []
    for encoded_href in re.findall(r'href=["\']([^"\']+)', page, re.IGNORECASE):
        href = html.unescape(encoded_href)
        parsed = urllib.parse.urlparse(urllib.parse.urljoin("https://duckduckgo.com", href))
        if parsed.hostname and parsed.hostname.endswith("duckduckgo.com"):
            href = urllib.parse.parse_qs(parsed.query).get("uddg", [""])[0]
        if not href.startswith(("http://", "https://")) or not host_is_allowed(href, domains):
            continue
        lowered = urllib.parse.unquote(href).casefold()
        score = 0
        if normalized_model in re.sub(r"[^a-z0-9]", "", lowered):
            score += 8
        if any(token in lowered for token in ("/product", "/products", "datasheet", "data-sheet", "specification")):
            score += 4
        if lowered.split("?", 1)[0].endswith(".pdf"):
            score += 2
        if any(token in lowered for token in ("manual", "release-note", "firmware", "end-of-sale", "announcement")):
            score -= 8
        candidates.append((score, href))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    return candidates[0][1]


def search_official_page(brand, model, domains):
    if brand == "Reyee":
        catalog_match = reyee_catalog_product_url(model)
        if catalog_match:
            return catalog_match
    normalized_model = re.sub(r"[^a-z0-9]", "", model.casefold())
    sitemap_matches = [
        url for url in official_sitemap_urls(brand, tuple(domains))
        if normalized_model in re.sub(r"[^a-z0-9]", "", urllib.parse.unquote(url).casefold())
    ]
    if sitemap_matches:
        locale_rank = {"en": 0, "us": 1, "uk": 2, "in": 3, "au": 4, "jp": 9}
        def page_rank(url):
            path_parts = urllib.parse.urlparse(url).path.casefold().split("/")
            locale = next((part for part in path_parts if part in locale_rank), "")
            return (locale_rank.get(locale, 5), "/support/" in url.casefold(), len(url), url)
        sitemap_matches.sort(key=page_rank)
        return sitemap_matches[0]

    try:
        duckduckgo_match = search_duckduckgo_official(brand, model, domains)
    except (urllib.error.URLError, TimeoutError, ValueError):
        duckduckgo_match = None
    if duckduckgo_match:
        return duckduckgo_match

    try:
        yahoo_match = search_yahoo_official(brand, model, domains)
    except (urllib.error.URLError, TimeoutError, ValueError):
        yahoo_match = None
    if yahoo_match:
        return yahoo_match

    try:
        brave_match = search_brave_official(brand, model, domains)
    except (urllib.error.URLError, TimeoutError, ValueError):
        brave_match = None
    if brave_match:
        return brave_match

    query = f'site:{domains[0]} "{model}" specifications datasheet'
    search_url = "https://www.bing.com/search?format=rss&q=" + urllib.parse.quote_plus(query)
    _, _, data = fetch_url(search_url, timeout=20, max_bytes=500_000, attempts=2)
    root = ET.fromstring(data)
    candidates = []
    for item in root.findall(".//item"):
        link = (item.findtext("link") or "").strip()
        title = (item.findtext("title") or "").strip()
        description = (item.findtext("description") or "").strip()
        if not link or not host_is_allowed(link, domains):
            continue
        haystack = re.sub(r"[^a-z0-9]", "", f"{link} {title} {description}".casefold())
        if normalized_model not in haystack:
            continue
        score = 0
        lowered_link = link.casefold()
        if normalized_model in re.sub(r"[^a-z0-9]", "", lowered_link):
            score += 5
        if "spec" in lowered_link or "product" in lowered_link:
            score += 3
        if lowered_link.endswith(".pdf"):
            score += 1
        if any(token in lowered_link for token in ("press", "news", "forum", "community", "end-of-sale", "end_of_sale", "announcement")):
            score -= 5
        candidates.append((score, link, title))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def probe_tp_link_accessory_page(model):
    slug = re.sub(r"[^a-z0-9]+", "-", model.casefold()).strip("-")
    slugs = [slug]
    if not slug.startswith("tl-"):
        slugs.insert(0, f"tl-{slug}")
    paths = (
        "business-networking/accessory/{slug}/",
        "business-networking/omada-accessory/{slug}/",
        "business-networking/omada-accessory-poe-adapter/{slug}/",
        "business-networking/omada-accessory-module-cable/{slug}/",
        "business-networking/omada-accessory-power-poe/{slug}/",
        "service-provider/switch-accessory/{slug}/",
    )
    for locale in ("en", "us", "uk", "de", "es", "jp", "br"):
        for path in paths:
            for candidate_slug in slugs:
                candidate = f"https://www.tp-link.com/{locale}/{path.format(slug=candidate_slug)}"
                try:
                    final_url, content_type, data = fetch_url(
                        candidate,
                        timeout=8,
                        max_bytes=500_000,
                        attempts=1,
                    )
                except Exception:
                    continue
                if "html" not in content_type.casefold():
                    continue
                title_match = re.search(
                    rb"<title[^>]*>(.*?)</title>", data, re.I | re.S
                )
                evidence = final_url
                if title_match:
                    evidence += " " + title_match.group(1).decode(
                        "utf-8", errors="ignore"
                    )
                if model_token_present(model, evidence):
                    return final_url
    return None


def html_to_text(data):
    decoded = data.decode("utf-8", errors="ignore")
    decoded = re.sub(r"<script\b[^>]*>.*?</script>", " ", decoded, flags=re.IGNORECASE | re.DOTALL)
    decoded = re.sub(r"<style\b[^>]*>.*?</style>", " ", decoded, flags=re.IGNORECASE | re.DOTALL)
    decoded = re.sub(r"</(?:p|div|li|tr|td|th|h[1-6]|section)>", "\n", decoded, flags=re.IGNORECASE)
    decoded = re.sub(r"<[^>]+>", " ", decoded)
    decoded = html.unescape(decoded)
    return re.sub(r"[ \t]+", " ", re.sub(r"\r", "", decoded))


def pdf_to_text(data):
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages[:80])


def first_match(patterns, text, flags=re.IGNORECASE | re.DOTALL):
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match
    return None


def speed_to_mbps(value, unit):
    cleaned = re.sub(r"[^0-9.]", "", str(value).replace(",", ""))
    if not cleaned or cleaned == ".":
        return None
    number = float(cleaned)
    converted = number * 1000 if unit.casefold().startswith("g") else number
    return int(converted) if converted.is_integer() else round(converted, 3)


def clean_labeled_value(value, limit=350):
    if "\ufffd" in value:
        return ""
    value = (
        value.replace("¡Á", "×").replace("℅", "×").replace("脳", "×")
        .replace("��", "•")
    )
    value = re.sub(r"\s+", " ", html.unescape(value)).strip(" \t:|;-")
    if not value or len(value) > limit or not re.search(r"[A-Za-z0-9]", value):
        return ""
    return value


def labeled_value(text, labels, limit=350):
    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(
        rf"(?:^|\n)\s*(?:{label_pattern})\s*(?:[:|]\s*|\n\s*)([^\n]{{1,{limit}}})",
        text,
        re.IGNORECASE,
    )
    return clean_labeled_value(match.group(1), limit) if match else ""


def labeled_number(text, labels, units="", integer=False):
    label_pattern = "|".join(re.escape(label) for label in labels)
    unit_pattern = rf"\s*(?:{units})?" if units else ""
    match = re.search(
        rf"(?:{label_pattern})[^\d]{{0,40}}([0-9]+(?:[,.][0-9]+)*){unit_pattern}",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    value = float(match.group(1).replace(",", ""))
    return int(round(value)) if integer else value


def add_text_result(results, code, value, raw_value=None):
    value = clean_labeled_value(value)
    if value:
        results.setdefault(code, ("text", value, (raw_value or value)[:1000]))


def add_number_result(results, code, value, raw_value=None):
    if value is not None:
        results.setdefault(code, ("number", value, str(raw_value or value)[:1000]))


def add_boolean_result(results, code, text, patterns):
    match = first_match(patterns, text, flags=re.IGNORECASE)
    if match:
        results.setdefault(code, ("boolean", True, match.group(0)[:1000]))


def infer_wifi_standard(text):
    compact = re.sub(r"\s+", " ", text)
    for pattern, value in (
        (r"\b(?:Wi-?Fi\s*7|802\.11be)\b", "Wi-Fi 7"),
        (r"\b(?:Wi-?Fi\s*6E)\b", "Wi-Fi 6E"),
        (r"\b(?:Wi-?Fi\s*6|802\.11ax)\b", "Wi-Fi 6"),
        (r"\b(?:Wi-?Fi\s*5|802\.11ac)\b", "Wi-Fi 5"),
        (r"\b802\.11n\b", "Wi-Fi 4"),
    ):
        if re.search(pattern, compact, re.I):
            return value
    return ""


def linked_official_documents(base_url, data, domains, model, limit=3):
    decoded = data.decode("utf-8", errors="ignore")
    normalized_model = re.sub(r"[^a-z0-9]", "", model.casefold())
    candidates = []
    links = list(re.findall(
        r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        decoded,
        re.IGNORECASE | re.DOTALL,
    ))
    links.extend(
        (href, "")
        for href in re.findall(
            r"(?:href|src|data-url|data-src)=[\"']([^\"']+)[\"']",
            decoded,
            re.IGNORECASE,
        )
    )
    decoded_urls = html.unescape(decoded).replace(r"\/", "/")
    links.extend(
        (href.rstrip("\\\"'<>),;"), "")
        for href in re.findall(r"https?://[^\s\"'<>]+", decoded_urls, re.IGNORECASE)
    )
    for href, anchor in links:
        url = urllib.parse.urljoin(base_url, html.unescape(href))
        parsed = urllib.parse.urlparse(url)
        viewer_file = urllib.parse.parse_qs(parsed.query).get("file", [])
        if viewer_file and viewer_file[0].startswith(("http://", "https://")):
            url = viewer_file[0]
        if not url.startswith(("http://", "https://")) or not host_is_allowed(url, domains):
            continue
        label = re.sub(r"<[^>]+>", " ", html.unescape(anchor))
        haystack = f"{url} {label}".casefold()
        model_present = normalized_model in re.sub(r"[^a-z0-9]", "", haystack)
        is_pdf = url.casefold().split("?", 1)[0].endswith(".pdf")
        explicit_sheet = any(token in haystack for token in ("datasheet", "data-sheet", "spec sheet"))
        if urllib.parse.urldefrag(url)[0] == urllib.parse.urldefrag(base_url)[0]:
            continue
        if not model_present and not (is_pdf and explicit_sheet):
            continue
        score = 0
        if any(token in haystack for token in ("datasheet", "data-sheet", "specification", "spec sheet")):
            score += 8
        if is_pdf:
            score += 5
        if normalized_model in re.sub(r"[^a-z0-9]", "", haystack):
            score += 4
        if any(token in haystack for token in ("manual", "firmware", "release note", "warranty")):
            score -= 8
        if score > 5:
            candidates.append((score, url))
    candidates.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    return list(dict.fromkeys(url for _, url in candidates))[:limit]


def extract_product_image_url(base_url, data, domains, model):
    """Pick the primary official product image and reject decorative page assets."""
    page = data.decode("utf-8", errors="ignore")
    if (urllib.parse.urlparse(base_url).hostname or "").casefold() == "ekit.huawei.com":
        payload_match = re.search(
            r'<script[^>]*id=["\']__NUXT_DATA__["\'][^>]*>(.*?)</script>',
            page,
            re.IGNORECASE | re.DOTALL,
        )
        if payload_match:
            try:
                payload = json.loads(payload_match.group(1))
                lookup = re.sub(r"^ekit\s+", "", model, flags=re.I)
                for entry in payload:
                    if not isinstance(entry, dict):
                        continue
                    name_ref = entry.get("name")
                    image_ref = entry.get("pictureUrl")
                    if not all(isinstance(ref, int) and 0 <= ref < len(payload) for ref in (name_ref, image_ref)):
                        continue
                    name = payload[name_ref]
                    image_value = payload[image_ref]
                    if not isinstance(name, str) or not isinstance(image_value, str):
                        continue
                    image_url = encode_http_url(urllib.parse.urljoin(base_url, image_value))
                    if (
                        model_token_present(lookup, name)
                        and host_is_allowed(image_url, domains)
                        and re.search(r"\.(?:png|jpe?g|webp|avif)$", urllib.parse.urlparse(image_url).path, re.I)
                    ):
                        return image_url
            except (ValueError, TypeError, KeyError):
                pass
    candidates = []
    tags = re.findall(r"<(?:meta|img)\b[^>]*>", page, re.IGNORECASE)
    for position, tag in enumerate(tags):
        attributes = {
            key.casefold(): html.unescape(value)
            for key, _, value in re.findall(
                r"([:\w-]+)\s*=\s*([\"'])(.*?)\2", tag, re.DOTALL
            )
        }
        property_name = (attributes.get("property") or attributes.get("name") or "").casefold()
        is_social_image = property_name in {"og:image", "og:image:url", "twitter:image"}
        image_value = (
            attributes.get("content") if is_social_image else
            attributes.get("src") or attributes.get("data-src") or attributes.get("data-original")
        )
        if not image_value:
            continue
        image_url = encode_http_url(
            urllib.parse.urljoin(base_url, image_value.strip())
        )
        parsed = urllib.parse.urlparse(image_url)
        if parsed.scheme not in {"http", "https"} or not host_is_allowed(image_url, domains):
            continue
        path = parsed.path.casefold()
        if any(token in path for token in ("logo", "icon", "banner", "close", "arrow", "phone", "bg_", "opacity", "placeholder", "blank", "package-content", "packge-content", "documentation-menu")):
            continue
        is_netgear_transform = (
            (parsed.hostname or "").casefold() == "assets.netgear.com"
            and path.startswith("/transform/")
        )
        is_ruckus_image_server = (
            (parsed.hostname or "").casefold() == "productresources.vistancenetworks.com"
            and path.endswith("/imageserver.php")
            and "downloadname=" in parsed.query.casefold()
        )
        is_hpe_product_image = (
            (parsed.hostname or "").casefold() == "assets.ext.hpe.com"
            and path.startswith("/is/image/hpedam/")
            and ("$product$" in parsed.query.casefold() or "$zoom$" in parsed.query.casefold())
        )
        if not (is_netgear_transform or is_ruckus_image_server or is_hpe_product_image) and not re.search(r"\.(?:png|jpe?g|webp|avif)(?:$|\?)", path):
            continue
        label = " ".join((attributes.get("alt", ""), attributes.get("title", "")))
        haystack = f"{image_url} {label}"
        model_match = model_token_present(model, haystack)
        is_dlink_image = (parsed.hostname or "").casefold().endswith("dlink.com")
        if is_dlink_image and not model_match:
            normalized_model = re.sub(r"[^a-z0-9]", "", model.casefold())
            model_match = re.search(
                rf"{re.escape(normalized_model)}(?:[abc]\d)?(?:image|[-_.]|$)", path
            ) is not None
        if is_dlink_image and not model_match:
            continue
        if (parsed.hostname or "").casefold() == "documentation.grandstream.com" and not model_match:
            continue
        is_ruijie_primary_upload = "/fu/upload/product/" in path
        if not model_match and not is_social_image and not is_ruijie_primary_upload and not is_hpe_product_image:
            continue
        score = 40 if model_match else 25 if is_ruijie_primary_upload or is_hpe_product_image else 10
        if attributes.get("data-index") == "0" or re.search(r"(?:^|\D)1(?:\D|$)", label):
            score += 12
        if is_social_image:
            score += 8
        if is_dlink_image and model_match:
            if "/product-images/" in path or re.search(r"(?:front|side)(?:\.|-|_)", path):
                score += 20
            if "/assets/" in path and not re.search(r"(?:front|side)(?:\.|-|_)", path):
                score -= 15
        if (parsed.hostname or "").casefold().endswith("grandstream.com"):
            if "zoom-img" in attributes.get("class", "") and model_match:
                score += 10
            if model_match and re.search(r"_1\.(?:png|jpe?g|webp|avif)$", path):
                score += 20
            if "social-image" in path:
                score -= 10
        candidates.append((score, -position, image_url))
    if not candidates:
        return ""
    candidates.sort(reverse=True)
    return candidates[0][2]


def trendnet_support_image_url(model):
    """Find a model photo without replacing its datasheet as the spec source."""
    base_model = re.sub(r"\s*\([^)]*\)$", "", model).strip()
    url = "https://www.trendnet.com/support/versions.asp?pID=" + urllib.parse.quote(base_model)
    try:
        final_url, content_type, data = fetch_url(url, timeout=15, max_bytes=500_000, attempts=1)
    except Exception:
        return ""
    if "html" not in content_type.casefold() or not host_is_allowed(final_url, OFFICIAL_DOMAINS["TRENDnet"]):
        return ""
    if not model_token_present(base_model, html_to_text(data)):
        return ""
    return extract_product_image_url(final_url, data, OFFICIAL_DOMAINS["TRENDnet"], base_model)


def verified_image_suffix(data):
    """Validate raster bytes; some official CDNs label PNGs as text/plain."""
    from PIL import Image

    try:
        with Image.open(io.BytesIO(data)) as picture:
            image_format = picture.format
            picture.verify()
    except OSError as exc:
        raise ValueError("invalid image data") from exc
    suffix = {
        "PNG": ".png",
        "JPEG": ".jpg",
        "WEBP": ".webp",
        "AVIF": ".avif",
    }.get(image_format)
    if not suffix:
        raise ValueError(f"unsupported image format: {image_format}")
    return suffix


def official_image_redirect_allowed(brand, original_url, final_url):
    if host_is_allowed(final_url, OFFICIAL_DOMAINS[brand]):
        return True
    original = urllib.parse.urlparse(original_url)
    final = urllib.parse.urlparse(final_url)
    return (
        brand == "Meraki"
        and (original.hostname or "").casefold() == "documentation.meraki.com"
        and original.path.startswith("/@api/deki/files/")
        and final.scheme == "https"
        and (final.hostname or "").casefold() == "files.mtstatic.com"
        and final.path.startswith("/site_13505/")
    )


def extract_specs(text, category_slug):
    compact = re.sub(r"\s+", " ", text)
    results = {}

    ip_match = re.search(r"\bIP(?:55|65|66|67|68)\b", compact, re.IGNORECASE)
    if ip_match:
        results["ip_rating"] = ("text", ip_match.group(0).upper(), ip_match.group(0))

    dimension_match = first_match([
        r"Dimensions?\s*(?:\([^)]*\))?\s*[:|]?\s*([^\n]{0,100}?\d+(?:\.\d+)?\s*[×x*]\s*\d+(?:\.\d+)?(?:\s*[×x*]\s*\d+(?:\.\d+)?)?\s*mm)",
        r"(\d+(?:\.\d+)?\s*[×x*]\s*\d+(?:\.\d+)?\s*[×x*]\s*\d+(?:\.\d+)?\s*mm)",
    ], text)
    if dimension_match:
        raw = dimension_match.group(1).strip()
        metric = re.findall(
            r"\d+(?:\.\d+)?\s*[×xX*]\s*\d+(?:\.\d+)?(?:\s*[×xX*]\s*\d+(?:\.\d+)?)?\s*mm",
            raw,
            re.IGNORECASE,
        )
        if metric:
            raw = metric[-1]
        results["dimensions_mm"] = ("text", raw, raw)

    temperature_match = first_match([
        r"Operating Temperature\s*[:|]?\s*(.*?)(?=\s*[•;]|\s+Storage|\n|$)",
        r"Operating temperature[^-\d]{0,20}(-?\d+(?:\.\d+)?)\s*(?:°\s*)?C\s*(?:to|–|—|~)\s*(-?\d+(?:\.\d+)?)\s*(?:°\s*)?C",
    ], text)
    if temperature_match:
        raw = " ".join(group for group in temperature_match.groups() if group).strip()
        if raw.casefold().startswith(("supports working", "working in temperatures")):
            range_match = re.search(
                r"[−–-]?\d+(?:\.\d+)?\s*°\s*C\s*(?:to|~|–|—)\s*[+−–-]?\d+(?:\.\d+)?\s*°\s*C",
                raw,
                re.I,
            )
            raw = range_match.group(0) if range_match else ""
        if re.search(r"-?\d+(?:\.\d+)?", raw) and "\ufffd" not in raw:
            results["operating_temperature_c"] = ("text", raw, temperature_match.group(0)[:200])

    power_match = first_match([
        r"Max(?:imum)?\.? Power Consumption\s*[:|]?\s*(\d+(?:\.\d+)?)\s*W",
        r"Power Consumption[^\d]{0,30}(\d+(?:\.\d+)?)\s*W",
    ], compact)
    if power_match:
        results["max_power_consumption_w"] = ("number", float(power_match.group(1)), power_match.group(0))

    if re.search(r"\bFanless\b", compact, re.IGNORECASE):
        results["fanless"] = ("boolean", True, "Fanless")

    lightning_match = re.search(r"([±+\-]?\d+(?:\.\d+)?)\s*kV\s+(?:Lightning|Surge) Protection", compact, re.IGNORECASE)
    if lightning_match:
        results["lightning_protection_kv"] = ("text", f"{lightning_match.group(1)} kV", lightning_match.group(0))

    if category_slug in {"access-point", "wireless-bridge"}:
        stream_match = re.search(r"\b(\d{1,2})[-\s]?Stream\b", compact, re.IGNORECASE)
        if stream_match:
            results["total_spatial_streams"] = ("number", int(stream_match.group(1)), stream_match.group(0))
        for band, code in (("2.4", "rate_2g_mbps"), ("5", "rate_5g_mbps"), ("6", "rate_6g_mbps")):
            matches = []
            band_pattern = re.escape(band)
            patterns = [
                rf"(\d+(?:\.\d+)?)\s*(Mbps|Gbps)\s*\({band_pattern}\s*GHz\)",
                rf"{band_pattern}\s*GHz\s*(?:[:：\-–]\s*)?(?:Up to\s*)?(\d+(?:\.\d+)?)\s*(Mbps|Gbps)",
                rf"{band_pattern}\s*GHz\s+wireless data rate\s*(?:[:|]\s*)?(\d+(?:\.\d+)?)\s*(Mbps|Gbps)",
            ]
            for pattern in patterns:
                for match in re.finditer(pattern, compact, re.IGNORECASE):
                    matches.append((speed_to_mbps(match.group(1), match.group(2)), match.group(0)))
            if matches:
                value, raw = max(matches, key=lambda item: item[0])
                results[code] = ("number", value, raw)
        detected_bands = [
            band
            for band, code in (
                ("2.4 GHz", "rate_2g_mbps"),
                ("5 GHz", "rate_5g_mbps"),
                ("6 GHz", "rate_6g_mbps"),
            )
            if code in results
        ]
        if not detected_bands:
            frequency_value = labeled_value(text, ("Frequency", "Frequency Band", "Radio"))
            detected_bands = [
                band
                for band in ("2.4 GHz", "5 GHz", "6 GHz")
                if re.search(re.escape(band), frequency_value, re.IGNORECASE)
            ]
        if not detected_bands:
            radio_design = first_match(
                (r"Radio design\s*(.*?)(?=Maximum wireless data rate|Antenna|Dimensions)",),
                text,
            )
            radio_text = radio_design.group(1) if radio_design else ""
            detected_bands = [
                band for band in ("2.4 GHz", "5 GHz", "6 GHz")
                if re.search(re.escape(band), radio_text, re.IGNORECASE)
            ]
        if detected_bands:
            results["supported_bands"] = ("text", " / ".join(detected_bands), " / ".join(detected_bands))
        widths = [int(value) for value in re.findall(r"\b(160|240|320)\s*MHz\b", compact, re.IGNORECASE)]
        if widths:
            results["max_channel_width_mhz"] = ("number", max(widths), f"{max(widths)} MHz")
        poe_standards = sorted(set(re.findall(r"802\.3(?:af|at|bt)", compact, re.IGNORECASE)))
        if poe_standards:
            value = " / ".join(item.lower().replace("802.3", "802.3") for item in poe_standards)
            power_code = "power_method" if category_slug == "access-point" else "poe_input"
            results[power_code] = ("text", f"PoE ({value})", value)
        clients_match = first_match([
            r"(\d{2,5})\+?\s+(?:Concurrent Clients|Concurrent Connections|Connected Devices|Connected Clients)",
            r"(?:Concurrent Clients|Concurrent Connections|Wireless Client Capacity)\s*[:|]?\s*(\d{2,5})\+?",
        ], compact)
        if clients_match:
            results["max_clients"] = ("number", int(clients_match.group(1)), clients_match.group(0))
        elif associated_clients := re.search(
            r"Maximum number of associated wireless clients\s*(.*?)(?=Maximum number of devices|IP Service|Resources|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        ):
            client_values = [int(value) for value in re.findall(r"\b(\d{2,5})\b", associated_clients.group(1))]
            if client_values:
                results["max_clients"] = (
                    "number", max(client_values), associated_clients.group(0)[:1000]
                )
        antenna_match = re.search(r"(?:Antenna(?: Gain)?|Gain)\s*[:|]?\s*([^\n]{0,100}?\d+(?:\.\d+)?\s*dBi)", text, re.IGNORECASE)
        if antenna_match:
            results["antenna_gain_dbi"] = ("text", antenna_match.group(1).strip(), antenna_match.group(0)[:200])
        range_match = first_match([
            r"(?:Coverage|Range|Transmission Distance)\s*[:|]?\s*([^\n]{0,100}?\d+(?:\.\d+)?\s*(?:km|m|ft))",
        ], text)
        if range_match:
            results["wireless_range"] = ("text", range_match.group(1).strip(), range_match.group(0)[:200])
        interface_value = labeled_value(
            text,
            ("Ethernet Ports", "Ethernet Port", "Ethernet Interface", "LAN Interfaces", "LAN Interface", "LAN Port", "Network Interface", "Interfaces", "Interface", "Ports"),
        )
        if not interface_value:
            interface_match = first_match(
                (
                    r"(\d+\s*[x×]\s*(?:10G|5G|2\.5G|Gigabit|GbE|10/100/1000(?:\s*Mbps)?)\s+(?:PoE\+?\s+)?(?:Ethernet\s+)?Ports?)",
                    r"(\d+\s*[x×]\s*(?:RJ-?45|Ethernet|LAN)\s+Ports?)",
                ),
                compact,
                flags=re.I,
            )
            interface_value = interface_match.group(1) if interface_match else ""
        if re.search(r"RJ-?45|Ethernet|GbE|Gigabit|Mbps|Gbps|\b\d+(?:\.\d+)?G\b", interface_value, re.IGNORECASE):
            add_text_result(results, "ethernet_interfaces", interface_value)
        uplink_value = labeled_value(text, ("Uplink Interface", "Uplink Port", "Uplink"))
        if uplink_value:
            existing_interface = results.get("ethernet_interfaces", (None, "", ""))[1]
            combined_interface = (
                f"{existing_interface}; Uplink: {uplink_value}"
                if existing_interface and uplink_value.casefold() not in str(existing_interface).casefold()
                else existing_interface or f"Uplink: {uplink_value}"
            )
            results["ethernet_interfaces"] = ("text", combined_interface, combined_interface)
        explicit_power = labeled_value(
            text, ("Power Method", "Power Supply Method", "Power Mode", "Power Supply")
        )
        methods = []
        existing_power = results.get("power_method")
        if existing_power:
            methods.append(str(existing_power[1]))
        if explicit_power and re.search(r"PoE|DC|AC|adapter", explicit_power, re.I):
            methods.append(explicit_power)
        dc_match = re.search(r"\b(?:12|24|48|53\.5)\s*V\s*DC\b|\bDC\s+Power\b", compact, re.I)
        if dc_match and not any("dc" in method.casefold() for method in methods):
            methods.append(dc_match.group(0))
        if methods and category_slug == "access-point":
            combined = " / ".join(dict.fromkeys(methods))
            results["power_method"] = ("text", combined, combined)
        antenna_value = labeled_value(text, ("Antenna Type", "Antennas", "Antenna"))
        antenna_block = re.search(
            r"(?:^|\n)\s*Antenna\s*\n\s*Antenna\s*\n(.*?)(?=\n\s*(?:Dimensions and Weight|Port Specifications|Power Supply and Consumption)\b)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if antenna_block:
            antenna_lines = [
                clean_labeled_value(line)
                for line in antenna_block.group(1).splitlines()
                if re.search(r"(?:2\.4|5|6)\s*GHz", line, re.IGNORECASE)
            ]
            antenna_lines = [line for line in antenna_lines if line]
            if antenna_lines:
                antenna_value = "\n".join(dict.fromkeys(antenna_lines))
        add_text_result(results, "antenna_type", antenna_value)
        add_text_result(results, "beamwidth", labeled_value(text, ("Antenna Beamwidth", "Beamwidth")))
        add_text_result(results, "bridge_modes", labeled_value(text, ("Operating Modes", "Operation Mode", "Wireless Modes", "Bridge Modes")))
        add_text_result(results, "poe_output", labeled_value(text, ("PoE Output", "PoE Passthrough", "PoE Out")))
        add_number_result(results, "max_ssids", labeled_number(text, ("Maximum SSIDs", "Max. SSIDs", "Multiple SSIDs", "SSID"), integer=True))
        add_number_result(results, "max_bridge_pairs", labeled_number(text, ("Maximum Bridge Links", "Maximum Bridge Pairs", "Max. PtMP Clients"), integer=True))
        for band, code in (("2.4", "mimo_2g"), ("5", "mimo_5g"), ("6", "mimo_6g")):
            mimo_match = re.search(
                rf"{re.escape(band)}\s*GHz[^\n]{{0,120}}?\b(\d+\s*[x×]\s*\d+(?:\s*(?:MU-)?MIMO)?)",
                text,
                re.IGNORECASE,
            )
            if mimo_match:
                line_start = text.rfind("\n", 0, mimo_match.start()) + 1
                line_end = text.find("\n", mimo_match.end())
                line = text[line_start:line_end if line_end >= 0 else len(text)]
                # A combined-band operating mode does not establish the MIMO
                # configuration of each band independently.
                if len(re.findall(r"(?:2\.4|5|6)\s*GHz", line, re.I)) == 1:
                    add_text_result(results, code, mimo_match.group(1), mimo_match.group(0))
        if "total_spatial_streams" not in results:
            stream_total = 0
            for code in ("mimo_2g", "mimo_5g", "mimo_6g"):
                value = results.get(code, (None, "", ""))[1]
                match = re.search(r"(\d+)\s*[x×]", str(value), re.I)
                if match:
                    stream_total += int(match.group(1))
            if stream_total:
                add_number_result(results, "total_spatial_streams", stream_total, "Sum of per-radio MIMO streams")
        management_match = first_match(
            (r"\bOmada(?: SDN)?\b", r"\bUniFi Network\b", r"\bNuclias(?: Cloud)?\b", r"\bAruba Central\b", r"\bCloud-managed\b"),
            compact,
            flags=re.IGNORECASE,
        )
        management = (
            management_match.group(0)
            if management_match
            else labeled_value(text, ("Centralized Management", "Management Platform", "Network Management"))
        )
        add_text_result(results, "centralized_management", management)
        add_boolean_result(results, "mesh_support", compact, (r"\b(?:wireless |wi-?fi )?mesh\b",))
        roaming = sorted(set(re.findall(r"802\.11[krv]", compact, re.IGNORECASE)))
        if re.search(r"\b(?:Smart\s+)?K\s*/\s*V\s+Roaming\b", compact, re.IGNORECASE):
            roaming.extend(("802.11k", "802.11v"))
        if roaming:
            add_text_result(results, "fast_roaming", " / ".join(dict.fromkeys(roaming)))
        security_match = first_match(
            (r"\bWPA3(?:-[A-Z0-9]+)?\b", r"\bWPA2(?:-[A-Z0-9]+)?\b", r"\b802\.1X\b"),
            compact,
            flags=re.IGNORECASE,
        )
        add_text_result(
            results,
            "wireless_security",
            labeled_value(text, ("Wireless Security", "Security")) or (security_match.group(0) if security_match else ""),
        )

    if category_slug in {"managed-switches", "unmanaged-easy-smart-switches"}:
        interface_match = first_match([
            r"(?:^|\n)\s*(?:Interface|Ports?)\s*[:|]?\s*([^\n]{5,300})",
            r"((?:\d+\s*[×x]\s*)?\d+(?:\.\d+)?\s*(?:Gbps|Gigabit|G)[^\n]{0,180}(?:RJ45|SFP\+?|ports?))",
        ], text)
        if interface_match:
            raw = re.sub(r"\s+", " ", interface_match.group(1)).strip()[:300]
            if re.search(r"RJ-?45|SFP|GbE|Gigabit|Mbps|Gbps|\b\d+(?:\.\d+)?G\b|\bWAN\b|\bLAN\b", raw, re.IGNORECASE):
                results["ethernet_interfaces"] = ("text", raw, raw)
        capacity_match = re.search(r"Switching Capacity\s*[:|]?\s*(\d+(?:\.\d+)?)\s*Gbps", compact, re.IGNORECASE)
        if capacity_match:
            results["switching_capacity_gbps"] = ("number", float(capacity_match.group(1)), capacity_match.group(0))
        forwarding_match = re.search(r"Packet Forwarding Rate\s*[:|]?\s*(\d+(?:\.\d+)?)\s*Mpps", compact, re.IGNORECASE)
        if forwarding_match:
            results["packet_forwarding_rate_mpps"] = ("number", float(forwarding_match.group(1)), forwarding_match.group(0))
        mac_match = re.search(r"MAC Address Table\s*[:|]?\s*([\d.]+\s*[KM]?)", compact, re.IGNORECASE)
        if mac_match:
            results["mac_address_table"] = ("text", mac_match.group(1).strip(), mac_match.group(0))
        budget_match = first_match([
            r"(?:Total )?PoE(?: Power)? Budget\s*[:|]?\s*(?:up to\s*)?(\d+(?:\.\d+)?)\s*W",
            r"(?:Total )?PoE(?: Power)? Budget\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*W",
            r"Up to\s*(\d+(?:\.\d+)?)\s*W\s*(?:total )?PoE budget",
            r"Power Budget\s*[:|]?\s*(\d+(?:\.\d+)?)\s*W",
        ], compact)
        if budget_match:
            results["poe_budget_w"] = ("number", float(budget_match.group(1)), budget_match.group(0))
        add_text_result(results, "uplink_interfaces", labeled_value(text, ("Uplink Ports", "Uplink Interfaces", "SFP Ports", "SFP Interfaces")))
        poe_standards = set(item.lower() for item in re.findall(r"802\.3(?:af|at|bt)", compact, re.IGNORECASE))
        for first, second in re.findall(r"802\.3(af|at|bt)\s*/\s*(af|at|bt)", compact, re.IGNORECASE):
            poe_standards.update((f"802.3{first.lower()}", f"802.3{second.lower()}"))
        poe_standards = sorted(poe_standards)
        if poe_standards:
            add_text_result(results, "poe_standard", " / ".join(poe_standards))
        poe_ports_match = first_match(
            (
                r"(\d{1,3})\s*(?:×|x)?\s*(?:PoE\+\+|PoE\+|PoE)[-\s]?(?:capable\s+)?ports?",
                r"(\d{1,3})[-\s]+Ports?\s+(?:Gigabit\s+)?(?:PoE\+\+|PoE\+|PoE)\b",
                r"(?:PoE Ports?|PoE\+ Ports?)\s*(?:[:|]\s*|\n\s*)(\d+)",
            ),
            compact,
        )
        if poe_ports_match and int(poe_ports_match.group(1)) <= 128:
            add_number_result(results, "poe_ports", int(poe_ports_match.group(1)), poe_ports_match.group(0))
        per_port = labeled_number(text, ("Maximum PoE per Port", "Max. PoE Power per Port", "PoE Power per Port"), r"W")
        if per_port is None:
            per_port_match = re.search(r"(?:up to\s*)?(\d+(?:\.\d+)?)\s*W\s+(?:PoE )?(?:output )?per port", compact, re.I)
            per_port = float(per_port_match.group(1)) if per_port_match else None
        add_number_result(results, "max_poe_per_port_w", per_port)
        buffer_match = re.search(r"Packet Buffer(?: Memory)?\s*[:|]?\s*([\d.]+)\s*(KB|Kb|MB|Mb)", compact)
        if buffer_match:
            buffer_mb = float(buffer_match.group(1))
            if buffer_match.group(2) == "KB":
                buffer_mb /= 1024
            elif buffer_match.group(2) == "Kb":
                buffer_mb /= 8192
            elif buffer_match.group(2) == "Mb":
                buffer_mb /= 8
            add_number_result(results, "packet_buffer_mb", round(buffer_mb, 3), buffer_match.group(0))
        jumbo_match = re.search(r"Jumbo Frames?\s*[:|]?\s*([\d,.]+)\s*(bytes?|KB)", compact, re.IGNORECASE)
        if jumbo_match:
            jumbo = float(jumbo_match.group(1).replace(",", ""))
            if jumbo_match.group(2).casefold() == "kb":
                jumbo *= 1024
            add_number_result(results, "jumbo_frame_bytes", int(round(jumbo)), jumbo_match.group(0))
        add_number_result(results, "vlan_count", labeled_number(text, ("Maximum VLANs", "Max. VLANs", "VLAN IDs", "Active VLANs"), integer=True))
        for code, labels in {
            "l2_features": ("Layer 2 Features", "L2 Features", "Layer 2 Switching"),
            "l3_features": ("Layer 3 Features", "L3 Features", "Layer 3 Routing"),
            "stacking": ("Stacking", "Stacking Capability"),
            "acl_security": ("ACL", "Access Control List", "Port Security"),
            "management_methods": ("Management", "Management Methods", "Management Interface"),
            "vlan_support": ("VLAN", "VLAN Features"),
            "qos_support": ("QoS", "Quality of Service"),
            "link_aggregation": ("Link Aggregation", "LAG"),
            "igmp_snooping": ("IGMP Snooping",),
            "port_mirroring": ("Port Mirroring",),
            "cable_test": ("Cable Diagnostics", "Cable Test"),
            "installation": ("Installation", "Mounting"),
        }.items():
            value = labeled_value(text, labels)
            if code == "installation" and not re.search(r"\b(?:wall|pole|ceiling|rack|desktop|desk|din.rail|mount)\b", value, re.I):
                value = ""
            if code == "management_methods" and not re.search(r"\b(?:web|snmp|cloud|cli|ssh|telnet|console|app|controller)\b", value, re.I):
                value = ""
            add_text_result(results, code, value)
        if category_slug == "unmanaged-easy-smart-switches":
            management_match = first_match(
                (r"\bEasy Smart\b", r"\bWeb Smart\b", r"\bUnmanaged\b", r"\bSmart Managed\b"),
                compact,
                flags=re.IGNORECASE,
            )
            if management_match:
                add_text_result(results, "management_type", management_match.group(0))
            if re.search(r"\b802\.3X\s+Flow Control\b", compact, re.I):
                add_text_result(results, "flow_control", "802.3X Flow Control")
            qos_match = re.search(r"\b802\.1p(?:/DSCP)?\s+QoS\b", compact, re.I)
            if qos_match:
                add_text_result(results, "qos_support", qos_match.group(0))
            igmp_match = re.search(r"\bIGMP Snooping(?:\s+V?\d+(?:/V?\d+)*)?", compact, re.I)
            if igmp_match:
                add_text_result(results, "igmp_snooping", igmp_match.group(0))
            transmission_match = re.search(r"\bStore[- ]and[- ]Forward\b", compact, re.I)
            if transmission_match:
                add_text_result(results, "transmission_method", "Store and Forward", transmission_match.group(0))
            for code, patterns in {
                "extend_mode": (r"\b(?:PoE )?Extend Mode\b",),
                "poe_auto_recovery": (r"\bPoE Auto Recovery\b", r"\bPoE Auto-Recovery\b"),
                "port_isolation": (r"\bPort Isolation\b",),
                "loop_prevention": (r"\bLoop Prevention\b", r"\bLoop Detection\b"),
            }.items():
                add_boolean_result(results, code, compact, patterns)
        add_boolean_result(results, "redundant_power", compact, (r"\bRedundant Power Supply\b", r"\bDual hot-swappable power supplies\b"))

    if category_slug == "gateway":
        interface_match = first_match([r"(?:^|\n)\s*(?:Interface|Ports?)\s*[:|]?\s*([^\n]{5,300})"], text)
        if interface_match:
            raw = re.sub(r"\s+", " ", interface_match.group(1)).strip()[:300]
            if re.search(r"RJ-?45|SFP|GbE|Gigabit|Mbps|Gbps|\b\d+(?:\.\d+)?G\b|\bWAN\b|\bLAN\b", raw, re.IGNORECASE):
                results["ethernet_interfaces"] = ("text", raw, raw)
        vpn_match = first_match([
            r"(?:IPsec )?VPN Throughput\s*[:|]?\s*(\d+(?:\.\d+)?)\s*(Mbps|Gbps)",
            r"SD-WAN[^\n]{0,80}Throughput\s*[:|]?\s*(\d+(?:\.\d+)?)\s*(Mbps|Gbps)",
        ], compact)
        if vpn_match:
            results["vpn_throughput_mbps"] = ("number", speed_to_mbps(vpn_match.group(1), vpn_match.group(2)), vpn_match.group(0))
        sessions_match = re.search(r"Concurrent Sessions\s*[:|]?\s*([\d,]+)", compact, re.IGNORECASE)
        if sessions_match:
            results["concurrent_sessions"] = ("number", int(sessions_match.group(1).replace(",", "")), sessions_match.group(0))
        for code, labels in {
            "wan_interfaces": ("WAN Ports", "WAN Interfaces", "WAN/LAN Ports", "WAN/LAN Interfaces"),
            "lan_interfaces": ("LAN Ports", "LAN Interfaces"),
            "uplink_interfaces": ("SFP Ports", "SFP Interfaces", "Uplink Interfaces"),
            "usb_interfaces": ("USB Ports", "USB Interfaces"),
            "sd_wan": ("SD-WAN", "SD WAN"),
            "firewall_features": ("Firewall", "Firewall Features", "Security Features"),
            "vpn_protocols": ("VPN Protocols", "VPN Features", "VPN"),
            "controller_management": ("Cloud Management", "Controller Management", "Management Platform"),
        }.items():
            add_text_result(results, code, labeled_value(text, labels))
        if "wan_interfaces" not in results:
            wan_match = re.search(
                r"((?:\d+\s*[x×]\s*)?(?:10G|5G|2\.5G|Gigabit|GbE)?\s*(?:RJ-?45\s+)?WAN(?:/LAN)?\s+Ports?)",
                compact,
                re.I,
            )
            if wan_match:
                add_text_result(results, "wan_interfaces", wan_match.group(1))
        if "ethernet_interfaces" not in results:
            port_match = re.search(
                r"((?:\d+\s*[x×]\s*)+(?:10G|5G|2\.5G|Gigabit|GbE)[^.;]{0,120}(?:RJ-?45|WAN|LAN|Ports?))",
                compact,
                re.I,
            )
            if port_match:
                add_text_result(results, "ethernet_interfaces", port_match.group(1))
        for code, labels in {
            "routing_throughput_mbps": ("Routing Throughput", "Firewall Throughput"),
            "nat_throughput_mbps": ("NAT Throughput",),
        }.items():
            match = re.search(
                rf"(?:{'|'.join(re.escape(label) for label in labels)})\s*[:|]?\s*([0-9]+(?:[,.][0-9]+)*)\s*(Mbps|Gbps)",
                compact,
                re.IGNORECASE,
            )
            if match:
                add_number_result(results, code, speed_to_mbps(match.group(1).replace(",", ""), match.group(2)), match.group(0))
        add_number_result(results, "vpn_tunnels", labeled_number(text, ("VPN Tunnels", "IPsec VPN Tunnels", "Concurrent VPN Tunnels"), integer=True))
        add_boolean_result(results, "wan_load_balancing", compact, (r"\b(?:Multi-?WAN )?Load Balanc(?:e|ing)\b",))
        if "vpn_protocols" not in results:
            protocols = [
                name
                for name, pattern in (
                    ("IPsec", r"\bIPsec\b"),
                    ("SSL", r"\bSSL\s+VPN\b"),
                    ("OpenVPN", r"\bOpenVPN\b"),
                    ("WireGuard", r"\bWireGuard\b"),
                    ("L2TP", r"\bL2TP\b"),
                    ("PPTP", r"\bPPTP\b"),
                    ("GRE", r"\bGRE\b"),
                )
                if re.search(pattern, compact, re.I)
            ]
            if protocols:
                add_text_result(results, "vpn_protocols", " / ".join(protocols))
        if re.search(r"\bOmada(?: SDN)?\b", compact, re.I):
            add_text_result(results, "controller_management", "Omada SDN")
        cellular_match = re.search(r"\b(5G|4G\+?|LTE(?:-A)?)\b", compact, re.I)
        if cellular_match:
            add_text_result(results, "cellular_standard", cellular_match.group(1).upper())
        sim_value = labeled_value(text, ("SIM Interfaces", "SIM Slots", "SIM Slot", "Nano SIM Slot"))
        add_text_result(results, "sim_interfaces", sim_value)
        cellular_rate = first_match(
            (
                r"(?:Cellular|5G|4G|LTE)[^\n]{0,80}(?:Downlink|Download)[^\d]{0,20}(\d+(?:\.\d+)?)\s*(Mbps|Gbps)",
                r"(?:Downlink|Download)\s+(?:Speed|Rate)?[^\d]{0,20}(\d+(?:\.\d+)?)\s*(Mbps|Gbps)",
            ),
            compact,
            flags=re.I,
        )
        if cellular_rate:
            add_number_result(
                results,
                "cellular_downlink_mbps",
                speed_to_mbps(cellular_rate.group(1), cellular_rate.group(2)),
                cellular_rate.group(0),
            )
        if poe_standards := sorted(set(re.findall(r"802\.3(?:af|at|bt)", compact, re.I))):
            router_poe_ports = labeled_number(text, ("PoE Ports", "PoE+ Ports"), integer=True)
            if router_poe_ports is None:
                router_poe_match = re.search(r"(\d+)\s*[x×-]?\s*PoE\+?\s+Ports?", compact, re.I)
                router_poe_ports = int(router_poe_match.group(1)) if router_poe_match else None
            add_number_result(results, "router_poe_ports", router_poe_ports)
            router_budget = labeled_number(text, ("PoE Power Budget", "Total PoE Budget", "PoE Budget"), r"W")
            add_number_result(results, "router_poe_budget_w", router_budget)
        router_standard = infer_wifi_standard(compact)
        if router_standard:
            add_text_result(results, "router_wifi_standard", router_standard)
            router_bands = "2.4 GHz / 5 GHz / 6 GHz" if router_standard in {"Wi-Fi 7", "Wi-Fi 6E"} else "2.4 GHz / 5 GHz"
            add_text_result(results, "router_supported_bands", router_bands)
            router_rates = []
            for band in ("2.4", "5", "6"):
                match = re.search(rf"(\d+(?:\.\d+)?)\s*(Mbps|Gbps)\s+(?:on|at)\s+{re.escape(band)}\s*GHz", compact, re.I)
                if match:
                    router_rates.append(speed_to_mbps(match.group(1), match.group(2)))
            if router_rates:
                add_number_result(results, "router_wireless_rate_mbps", sum(router_rates), "Sum of published per-band rates")

    if category_slug == "accessories":
        interface = labeled_value(
            text,
            ("Transceiver Form Factor", "Form Factor", "Interface Type", "Interface"),
        )
        if not interface:
            interface_match = re.search(
                r"\b(QSFP28|QSFP\+|SFP28|SFP\+|SFP|RJ-?45|USB-C|LC duplex|MPO|MTP)\b",
                compact,
                re.I,
            )
            interface = interface_match.group(1) if interface_match else ""
        add_text_result(results, "accessory_interface_type", interface)

        connector = labeled_value(text, ("Connector Type", "Connector"))
        if not connector:
            connector_match = re.search(r"\b(LC(?: duplex)?|MPO-?12|MPO|MTP|RJ-?45|SC/APC|SC/UPC)\b", compact, re.I)
            connector = connector_match.group(1) if connector_match else ""
        add_text_result(results, "accessory_connector_type", connector)

        rate_match = first_match(
            (
                r"(?:Maximum |Max\.? )?(?:Data|Transmission|Line) Rate\s*[:|]?\s*(\d+(?:\.\d+)?)\s*(Gbps|Mbps)",
                r"\b(1|2\.5|5|10|25|40|50|100|200|400)\s*(G(?:bps)?)\b[^\n]{0,60}(?:SFP|QSFP|Ethernet|transceiver)",
            ),
            compact,
            flags=re.I,
        )
        if rate_match:
            unit = rate_match.group(2)
            rate_gbps = float(rate_match.group(1)) / 1000 if unit.casefold().startswith("m") else float(rate_match.group(1))
            add_number_result(results, "accessory_data_rate_gbps", rate_gbps, rate_match.group(0))

        wavelength = first_match(
            (r"(?:Wavelength|Tx/Rx Wavelength)\s*[:|]?\s*(\d{3,4})\s*nm", r"\b(850|1310|1490|1550)\s*nm\b"),
            compact,
            flags=re.I,
        )
        if wavelength:
            add_number_result(results, "accessory_wavelength_nm", int(wavelength.group(1)), wavelength.group(0))

        fiber_match = re.search(r"\b(Single[- ]?mode|Multi[- ]?mode|SMF|MMF)\b", compact, re.I)
        if fiber_match:
            fiber_value = "Single-mode" if fiber_match.group(1).casefold() in {"single-mode", "single mode", "smf"} else "Multi-mode"
            add_text_result(results, "accessory_fiber_mode", fiber_value, fiber_match.group(0))

        distance = first_match(
            (
                r"(?:Maximum |Max\.? )?(?:Transmission |Cable )?(?:Distance|Length)\s*[:|]?\s*(\d+(?:\.\d+)?)\s*(km|m)\b",
                r"(?:Reach|Range)\s*[:|]?\s*(?:up to\s*)?(\d+(?:\.\d+)?)\s*(km|m)\b",
            ),
            compact,
            flags=re.I,
        )
        if distance:
            distance_km = float(distance.group(1)) / 1000 if distance.group(2).casefold() == "m" else float(distance.group(1))
            add_number_result(results, "accessory_max_distance_km", distance_km, distance.group(0))

        cable_length = first_match(
            (r"Cable Length\s*[:|]?\s*(\d+(?:\.\d+)?)\s*(m|cm|ft)\b",),
            compact,
            flags=re.I,
        )
        if cable_length:
            length = float(cable_length.group(1))
            unit = cable_length.group(2).casefold()
            if unit == "cm":
                length /= 100
            elif unit == "ft":
                length *= 0.3048
            add_number_result(results, "accessory_cable_length_m", round(length, 3), cable_length.group(0))

        poe_standards = sorted(set(item.casefold() for item in re.findall(r"802\.3(?:af|at|bt)", compact, re.I)))
        if poe_standards:
            add_text_result(results, "accessory_poe_standard", " / ".join(poe_standards))
        input_power = labeled_value(text, ("Input Power", "Power Input", "Input Voltage", "AC Input", "Power Supply"))
        output_power = labeled_value(text, ("Output Power", "Power Output", "Output Voltage", "DC Output"))
        add_text_result(results, "accessory_input_power", input_power)
        add_text_result(results, "accessory_output_power", output_power)
        output_w = labeled_number(text, ("Maximum Output Power", "Max. Output Power", "Output Power", "Power Supply"), r"W")
        add_number_result(results, "accessory_power_w", output_w)
        add_text_result(results, "accessory_compatibility", labeled_value(text, ("Compatible Products", "Compatibility", "Compatible With")))
        mounting = labeled_value(text, ("Mounting Type", "Mounting", "Installation"))
        if not mounting:
            mounting_match = re.search(r"\b(?:rack|wall|pole|desktop)[- /](?:mount|mounting|desktop|wall)[A-Za-z /-]*", compact, re.I)
            mounting = mounting_match.group(0) if mounting_match else ""
        add_text_result(results, "accessory_mounting_type", mounting)
        rack_units = labeled_number(text, ("Rack Units", "Rack Height", "Rack Space"), r"U", integer=False)
        add_number_result(results, "accessory_rack_units", rack_units)
        antenna_gain = labeled_number(text, ("Antenna Gain", "Peak Gain", "Gain"), r"dBi", integer=False)
        add_number_result(results, "accessory_antenna_gain_dbi", antenna_gain)
        add_text_result(results, "accessory_frequency_range", labeled_value(text, ("Frequency Range", "Operating Frequency", "Frequency")))

    return results


def crawl_product(payload):
    product_id, brand, model, category_slug, official_url = payload
    domains = OFFICIAL_DOMAINS.get(brand)
    if not domains:
        return {"product_id": product_id, "status": "unsupported_brand", "brand": brand, "model": model}
    try:
        lookup_model = lookup_model_name(model)
        catalog_url = reyee_catalog_product_url(lookup_model) if brand == "Reyee" else None
        if catalog_url:
            page_url = catalog_url
        elif official_url and host_is_allowed(official_url, domains):
            page_url = official_url
        elif brand == "TP-Link" and category_slug == "accessories":
            page_url = probe_tp_link_accessory_page(lookup_model)
        else:
            page_url = search_official_page(brand, lookup_model, domains)
        if not page_url:
            return {"product_id": product_id, "status": "not_found", "brand": brand, "model": model}
        if brand == "Aruba" and any(
            token in page_url.casefold()
            for token in ("/services-support/", "airheads.hpe.com/", "eos_notice", "partsurfer.hpe.com/")
        ):
            return {"product_id": product_id, "status": "not_product_page", "brand": brand, "model": model, "url": page_url}
        final_url, content_type, data = fetch_url(page_url)
        if not host_is_allowed(final_url, domains):
            return {"product_id": product_id, "status": "off_domain_redirect", "brand": brand, "model": model, "url": final_url}
        is_pdf = "pdf" in content_type.casefold() or final_url.casefold().split("?", 1)[0].endswith(".pdf")
        if "html" not in content_type.casefold() and not is_pdf:
            return {"product_id": product_id, "status": "unsupported_content", "brand": brand, "model": model, "url": final_url}
        if is_pdf and not data.lstrip().startswith(b"%PDF"):
            return {"product_id": product_id, "status": "unsupported_content", "brand": brand, "model": model, "url": final_url}
        page_text = pdf_to_text(data) if is_pdf else html_to_text(data)
        documents = [(final_url, is_pdf, page_text)]
        source_urls = [final_url]
        is_zyxel_download_listing = (
            brand == "Zyxel" and "/support/download" in urllib.parse.urlparse(final_url).path.casefold()
        )
        if not is_pdf and not is_zyxel_download_listing:
            for document_url in linked_official_documents(final_url, data, domains, lookup_model):
                try:
                    document_final_url, document_type, document_data = fetch_url(
                        document_url,
                        timeout=25,
                        max_bytes=8_000_000,
                    )
                    document_is_pdf = "pdf" in document_type.casefold() or document_final_url.casefold().split("?", 1)[0].endswith(".pdf")
                    if document_is_pdf and not document_data.lstrip().startswith(b"%PDF"):
                        continue
                    if not host_is_allowed(document_final_url, domains):
                        continue
                    document_text = pdf_to_text(document_data) if document_is_pdf else html_to_text(document_data)
                    documents.append((document_final_url, document_is_pdf, document_text))
                    source_urls.append(document_final_url)
                except Exception:
                    continue
        title_match = None if is_pdf else re.search(r"<title[^>]*>(.*?)</title>", data.decode("utf-8", errors="ignore"), re.IGNORECASE | re.DOTALL)
        title = html.unescape(re.sub(r"<[^>]+>", " ", title_match.group(1))).strip() if title_match else f"{brand} {model} official datasheet"
        if brand in {"Aruba", "Instant On"} and title.casefold().startswith("search | hpe store"):
            return {"product_id": product_id, "status": "not_product_page", "brand": brand, "model": model, "url": final_url}
        model_evidence = page_text if is_pdf else f"{final_url}\n{title}"
        sku_verified = (
            brand == "Aruba"
            and category_slug == "managed-switches"
            and aruba_switch_sku_matches(model, final_url, title)
        )
        mikrotik_alias_verified = (
            brand == "MikroTik"
            and model in {"hEX RB750Gr3", "hEX S RB760iGS"}
            and model.casefold().split()[-1] in page_text.casefold()
            and "hex" in title.casefold()
        )
        if not sku_verified and not mikrotik_alias_verified and not model_token_present(model, model_evidence) and not model_token_present(lookup_model, model_evidence):
            return {"product_id": product_id, "status": "model_not_on_page", "brand": brand, "model": model, "url": final_url}
        specs = {}
        spec_sources = {}
        # Product-page values are the fallback. Official linked PDFs are processed
        # afterwards and take precedence field by field.
        document_order = (
            (lambda item: not item[1]) if brand == "Reyee"
            else (lambda item: item[1])
        )
        for document_url, document_is_pdf, document_text in sorted(documents, key=document_order):
            document_specs = extract_specs(document_text, category_slug)
            for code, value in document_specs.items():
                specs[code] = value
                spec_sources[code] = document_url
        if is_zyxel_download_listing:
            specs = {}
            spec_sources = {}
        if brand == "Instant On" and "/instant-on/access-points/" in urllib.parse.urlparse(final_url).path.casefold():
            # HPE's marketing-page navigation includes site-wide Security,
            # Management and Mesh text that does not describe this AP model.
            specs = {code: value for code, value in specs.items() if spec_sources.get(code) != final_url}
            spec_sources = {code: url for code, url in spec_sources.items() if code in specs}
        image_url = "" if is_pdf else extract_product_image_url(final_url, data, domains, lookup_model)
        if brand == "TRENDnet" and not image_url:
            image_url = trendnet_support_image_url(lookup_model)
        return {
            "product_id": product_id,
            "status": "ok" if specs else "page_found_no_specs",
            "brand": brand,
            "model": model,
            "url": final_url,
            "source_urls": source_urls,
            "evidence_url": source_urls[-1],
            "spec_sources": spec_sources,
            "title": title[:250],
            "image_url": image_url,
            "wifi_standard": infer_wifi_standard("\n".join(item[2] for item in documents))
            if category_slug == "access-point"
            else "",
            "specs": specs,
        }
    except Exception as exc:
        return {"product_id": product_id, "status": "error", "brand": brand, "model": model, "error": str(exc)[:300]}


class Command(BaseCommand):
    help = "Locate official product pages, extract comparable specifications, and store evidence."

    def add_arguments(self, parser):
        parser.add_argument("--brand", action="append", dest="brands")
        parser.add_argument("--model", action="append", dest="models")
        parser.add_argument("--region", action="append", dest="regions")
        parser.add_argument("--category", action="append", dest="categories")
        parser.add_argument("--limit", type=int)
        parser.add_argument("--workers", type=int, default=6)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--report", type=Path)
        parser.add_argument(
            "--missing-images-only",
            action="store_true",
            help="Only crawl products that do not have a saved product image.",
        )
        parser.add_argument(
            "--missing-only",
            action="store_true",
            help="Only crawl products that have no specification rows.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        queryset = Product.objects.filter(is_published=True).select_related("brand", "category")
        if options["regions"]:
            queryset = queryset.filter(region__in=options["regions"])
        if options["brands"]:
            queryset = queryset.filter(brand__name__in=options["brands"])
        if options["categories"]:
            queryset = queryset.filter(category__slug__in=options["categories"])
        if options["models"]:
            queryset = queryset.filter(model__in=options["models"])
        if options["missing_only"]:
            queryset = queryset.filter(specs__isnull=True)
        if options["missing_images_only"]:
            queryset = queryset.filter(image="")
        queryset = queryset.order_by("brand__name", "model", "hardware_version")
        if options["limit"]:
            queryset = queryset[: options["limit"]]
        products = list(queryset)
        if not products:
            raise CommandError("No products matched the crawl selection.")

        payloads = [
            (p.pk, p.brand.name, p.model, p.category.slug, p.official_url)
            for p in products
        ]
        for brand in sorted({payload[1] for payload in payloads}):
            domains = OFFICIAL_DOMAINS.get(brand)
            if domains:
                official_sitemap_urls(brand, tuple(domains))
        results = []
        started = time.monotonic()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(options["workers"], 10))) as executor:
            futures = [executor.submit(crawl_product, payload) for payload in payloads]
            for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                results.append(future.result())
                if index % 25 == 0 or index == len(futures):
                    self.stdout.write(f"Crawled {index}/{len(futures)} products")

        stats = {status: sum(1 for item in results if item["status"] == status) for status in sorted({item["status"] for item in results})}
        imported_specs = 0
        retained_specs = 0
        imported_images = 0
        image_errors = 0
        verified_date = date.today()
        for result in results:
            if result["status"] not in {"ok", "page_found_no_specs"}:
                continue
            product = Product.objects.select_related("brand", "category").get(pk=result["product_id"])
            product_update_fields = []
            should_refresh_reyee_url = (
                product.brand.name == "Reyee"
                and "/products/" in urllib.parse.urlparse(result["url"]).path.casefold()
                and product.official_url != result["url"]
            )
            if (not product.official_url or should_refresh_reyee_url) and len(result["url"]) <= 200:
                product.official_url = result["url"]
                product_update_fields.append("official_url")
            if result.get("wifi_standard") and not product.wifi_standard:
                product.wifi_standard = result["wifi_standard"]
                product_update_fields.append("wifi_standard")
            if product_update_fields:
                product.save(update_fields=(*product_update_fields, "updated_at"))
            image_url = result.get("image_url", "")
            if image_url and not product.image and not options["dry_run"]:
                try:
                    image_final_url, image_type, image_data = fetch_url(
                        image_url, timeout=30, max_bytes=12 * 1024 * 1024
                    )
                    if not official_image_redirect_allowed(product.brand.name, image_url, image_final_url):
                        raise ValueError("image redirected outside the official domains")
                    if not image_data or len(image_data) >= 12 * 1024 * 1024:
                        raise ValueError(f"invalid image size: {len(image_data)}")
                    suffix = verified_image_suffix(image_data)
                    product.image.save(
                        f"{slugify(product.model) or 'product'}{suffix}",
                        ContentFile(image_data),
                        save=False,
                    )
                    product.save(update_fields=("image", "updated_at"))
                    imported_images += 1
                except Exception as exc:
                    image_errors += 1
                    self.stderr.write(f"IMAGE ERROR {product.model}: {exc}")
            for code, (value_kind, value, raw_value) in result["specs"].items():
                if code == "management_type":
                    switch_type = product_type_code(product)
                    if switch_type == "unmanaged":
                        value_kind, value, raw_value = (
                            "text",
                            "Unmanaged",
                            "Official product taxonomy: unmanaged switch",
                        )
                    elif switch_type == "easy_smart":
                        value_kind, value, raw_value = (
                            "text",
                            "Easy Smart",
                            "Official product taxonomy: Easy Smart switch",
                        )
                evidence_url = result.get("spec_sources", {}).get(code) or result.get("evidence_url") or result["url"]
                is_datasheet = evidence_url.casefold().split("?", 1)[0].endswith(".pdf") or "datasheet" in evidence_url.casefold()
                source, _ = SourceDocument.objects.update_or_create(
                    url=evidence_url,
                    document_version="",
                    defaults={
                        "brand": product.brand,
                        "product": product,
                        "document_type": SourceDocument.DocumentType.DATASHEET if is_datasheet else SourceDocument.DocumentType.PRODUCT_PAGE,
                        "title": result["title"] or f"{product.brand.name} {product.model}",
                        "region": product.region,
                        "accessed_date": verified_date,
                        "active": True,
                    },
                )
                definition = SpecDefinition.objects.filter(code=code).first()
                if definition:
                    display_name = definition.display_name
                    group = definition.group
                    data_type = definition.data_type
                    unit = definition.unit
                    priority = "p1"
                else:
                    metadata = SPEC_METADATA.get(code)
                    if not metadata:
                        continue
                    display_name, group, data_type, unit, direction, priority = metadata
                    definition = SpecDefinition.objects.create(
                        code=code,
                        display_name=display_name,
                        group=group,
                        data_type=data_type,
                        unit=unit,
                        is_filterable=priority == "p0",
                        is_core=True,
                        comparison_direction=direction,
                        collection_rule="Automatically extracted from an official product page; verify page conditions.",
                        active=True,
                    )
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                replaceable_source = bool(
                    existing
                    and (existing.source_note or "").startswith(
                        ("Deterministically derived:", "Automated extraction")
                    )
                )
                reyee_product_page_override = bool(
                    existing
                    and product.brand.name == "Reyee"
                    and code in {
                        "supported_bands", "total_spatial_streams",
                        "rate_2g_mbps", "rate_5g_mbps", "rate_6g_mbps",
                        "antenna_type", "max_clients", "ethernet_interfaces",
                        "power_method", "mesh_support", "fast_roaming",
                    }
                    and not is_datasheet
                    and "/products/" in urllib.parse.urlparse(evidence_url).path.casefold()
                )
                if (
                    existing
                    and existing.value_status == ProductSpec.ValueStatus.PUBLISHED
                    and existing.display_value != "Unknown"
                    and not replaceable_source
                    and not reyee_product_page_override
                ):
                    retained_specs += 1
                    spec = existing
                else:
                    defaults = {
                        "value_status": ProductSpec.ValueStatus.PUBLISHED,
                        "value_text": "",
                        "value_number": None,
                        "value_boolean": None,
                        "normalized_value": str(value),
                        "unit": unit,
                        "raw_value": str(raw_value)[:1000],
                        "source_url": evidence_url if len(evidence_url) <= 200 else "",
                        "source_note": (
                            "Automated extraction from official manufacturer datasheet PDF."
                            if is_datasheet else
                            "Automated extraction from official product page."
                        ),
                        "verified_date": verified_date,
                    }
                    if value_kind == "text":
                        defaults["value_text"] = str(value)
                    elif value_kind == "number":
                        defaults["value_number"] = Decimal(str(value)).quantize(Decimal("0.001"))
                    else:
                        defaults["value_boolean"] = bool(value)
                    spec, _ = ProductSpec.objects.update_or_create(
                        product=product,
                        definition=definition,
                        defaults=defaults,
                    )
                    imported_specs += 1
                SpecEvidence.objects.get_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"Automated extraction: {code}",
                    defaults={
                        "source_excerpt": str(raw_value)[:1000],
                        "evidence_level": SpecEvidence.EvidenceLevel.A if is_datasheet else SpecEvidence.EvidenceLevel.B,
                    },
                )

        if options["report"]:
            report_path = options["report"].resolve()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps({"stats": stats, "results": sorted(results, key=lambda item: (item["brand"], item["model"]))}, ensure_ascii=False, indent=2), encoding="utf-8")
        if options["dry_run"]:
            transaction.set_rollback(True)
        elapsed = round(time.monotonic() - started, 1)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: products={len(products)}, statuses={stats}, "
            f"specs_imported={imported_specs}, specs_retained={retained_specs}, "
            f"images_imported={imported_images}, image_errors={image_errors}, elapsed={elapsed}s"
        ))
