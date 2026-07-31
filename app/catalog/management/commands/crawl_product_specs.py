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

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import (
    ComparisonTemplate,
    Product,
    ProductSpec,
    SourceDocument,
    SpecDefinition,
    SpecEvidence,
    TemplateField,
)
from catalog.product_types import product_type_code
from catalog.services import select_comparison_template

OFFICIAL_DOMAINS = {
    "TP-Link": ("tp-link.com", "omadanetworks.com"),
    "Ubiquiti": ("ui.com", "ubnt.com"),
    "Ruijie": ("ruijienetworks.com", "ruijie.com"),
    "Reyee": ("reyee.ruijie.com", "ruijienetworks.com", "ruijie.com"),
    "Aruba": ("arubanetworks.com", "hpe.com"),
    "RUCKUS": ("ruckusnetworks.com",),
    "Grandstream": ("grandstream.com",),
    "Cisco": ("cisco.com",),
    "Meraki": ("meraki.cisco.com", "documentation.meraki.com"),
    "D-Link": ("dlink.com",),
    "NETGEAR": ("netgear.com",),
    "Zyxel": ("zyxel.com",),
    "Huawei": ("huawei.com",),
    "Hikvision": ("hikvision.com",),
    "EnGenius": ("engeniustech.com",),
    "Fortinet": ("fortinet.com",),
    "MikroTik": ("mikrotik.com",),
    "DrayTek": ("draytek.com",),
    "Dahua": ("dahuasecurity.com",),
    "TRENDnet": ("trendnet.com",),
    "H3C": ("h3c.com",),
    "HPE": ("hpe.com",),
    "Tenda": ("tenda.com.cn", "tendacn.com"),
    "Linksys": ("linksys.com",),
    "Buffalo": ("buffalotech.com", "buffaloamericas.com"),
}

USER_AGENT = "Mozilla/5.0"

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
    "rate_2g_mbps": ("2.4 GHz Max Rate", "Performance", "integer", "Mbps", "higher", "p0"),
    "rate_5g_mbps": ("5 GHz Max Rate", "Performance", "integer", "Mbps", "higher", "p0"),
    "rate_6g_mbps": ("6 GHz Max Rate", "Performance", "integer", "Mbps", "higher", "p0"),
    "max_channel_width_mhz": ("Max Channel Width", "Wireless", "integer", "MHz", "higher", "p0"),
    "ethernet_interfaces": ("Ethernet Interfaces", "Interfaces", "text", "", "none", "p0"),
    "poe_input": ("PoE Input", "Power", "text", "", "equal", "p0"),
    "max_clients": ("Max Clients", "Capacity", "integer", "", "higher", "p0"),
    "ip_rating": ("IP Rating", "Physical", "text", "", "equal", "p0"),
    "switching_capacity_gbps": ("Switching Capacity", "Performance", "decimal", "Gbps", "higher", "p0"),
    "packet_forwarding_rate_mpps": ("Packet Forwarding Rate", "Performance", "decimal", "Mpps", "higher", "p0"),
    "mac_address_table": ("MAC Address Table", "Capacity", "text", "", "higher", "p1"),
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


def fetch_url(url, timeout=20, max_bytes=3_000_000, attempts=3):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.5",
            "Accept-Language": "en-US,en;q=0.8",
        },
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                data = response.read(max_bytes)
                return response.geturl(), content_type, data
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


def model_token_present(model, value):
    parts = re.findall(r"[a-z0-9]+", model.casefold())
    if not parts:
        return False
    pattern = r"(?<![a-z0-9])" + r"[^a-z0-9]*".join(re.escape(part) for part in parts) + r"(?![a-z0-9])"
    return re.search(pattern, value.casefold()) is not None


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
    return int(round(number * 1000)) if unit.casefold().startswith("g") else int(round(number))


def clean_labeled_value(value, limit=350):
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


def linked_official_documents(base_url, data, domains, model, limit=3):
    decoded = data.decode("utf-8", errors="ignore")
    normalized_model = re.sub(r"[^a-z0-9]", "", model.casefold())
    candidates = []
    for href, anchor in re.findall(
        r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        decoded,
        re.IGNORECASE | re.DOTALL,
    ):
        url = urllib.parse.urljoin(base_url, html.unescape(href))
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
        if detected_bands:
            results["supported_bands"] = ("text", " / ".join(detected_bands), " / ".join(detected_bands))
        widths = [int(value) for value in re.findall(r"\b(160|240|320)\s*MHz\b", compact, re.IGNORECASE)]
        if widths:
            results["max_channel_width_mhz"] = ("number", max(widths), f"{max(widths)} MHz")
        poe_standards = sorted(set(re.findall(r"802\.3(?:af|at|bt)", compact, re.IGNORECASE)))
        if poe_standards:
            value = " / ".join(item.lower().replace("802.3", "802.3") for item in poe_standards)
            results["poe_input"] = ("text", value, value)
        clients_match = first_match([
            r"(\d{2,5})\+?\s+(?:Concurrent Clients|Connected Devices|Connected Clients)",
            r"Concurrent Clients\s*[:|]?\s*(\d{2,5})\+?",
        ], compact)
        if clients_match:
            results["max_clients"] = ("number", int(clients_match.group(1)), clients_match.group(0))
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
            ("Ethernet Ports", "Ethernet Interface", "Network Interface", "Interfaces", "Ports"),
        )
        if re.search(r"RJ-?45|Ethernet|GbE|Gigabit|Mbps|Gbps|\b\d+(?:\.\d+)?G\b", interface_value, re.IGNORECASE):
            add_text_result(results, "ethernet_interfaces", interface_value)
        add_text_result(results, "antenna_type", labeled_value(text, ("Antenna Type", "Antenna")))
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
                add_text_result(results, code, mimo_match.group(1), mimo_match.group(0))
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
        if roaming:
            add_text_result(results, "fast_roaming", " / ".join(roaming))
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
            r"(?:Total )?PoE Budget\s*[:|]?\s*(?:up to\s*)?(\d+(?:\.\d+)?)\s*W",
            r"Up to\s*(\d+(?:\.\d+)?)\s*W\s*(?:total )?PoE budget",
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
            add_text_result(results, code, labeled_value(text, labels))
        if category_slug == "unmanaged-easy-smart-switches":
            management_match = first_match(
                (r"\bEasy Smart\b", r"\bWeb Smart\b", r"\bUnmanaged\b", r"\bSmart Managed\b"),
                compact,
                flags=re.IGNORECASE,
            )
            if management_match:
                add_text_result(results, "management_type", management_match.group(0))
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
            "wan_interfaces": ("WAN Ports", "WAN Interfaces"),
            "lan_interfaces": ("LAN Ports", "LAN Interfaces"),
            "uplink_interfaces": ("SFP Ports", "SFP Interfaces", "Uplink Interfaces"),
            "usb_interfaces": ("USB Ports", "USB Interfaces"),
            "sd_wan": ("SD-WAN", "SD WAN"),
            "firewall_features": ("Firewall", "Firewall Features", "Security Features"),
            "vpn_protocols": ("VPN Protocols", "VPN Features", "VPN"),
            "controller_management": ("Cloud Management", "Controller Management", "Management Platform"),
        }.items():
            add_text_result(results, code, labeled_value(text, labels))
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

    return results


def crawl_product(payload):
    product_id, brand, model, category_slug, official_url = payload
    domains = OFFICIAL_DOMAINS.get(brand)
    if not domains:
        return {"product_id": product_id, "status": "unsupported_brand", "brand": brand, "model": model}
    try:
        page_url = official_url if official_url and host_is_allowed(official_url, domains) else search_official_page(brand, model, domains)
        if not page_url:
            return {"product_id": product_id, "status": "not_found", "brand": brand, "model": model}
        final_url, content_type, data = fetch_url(page_url)
        if not host_is_allowed(final_url, domains):
            return {"product_id": product_id, "status": "off_domain_redirect", "brand": brand, "model": model, "url": final_url}
        is_pdf = "pdf" in content_type.casefold() or final_url.casefold().endswith(".pdf")
        if "html" not in content_type.casefold() and not is_pdf:
            return {"product_id": product_id, "status": "unsupported_content", "brand": brand, "model": model, "url": final_url}
        if is_pdf and not data.lstrip().startswith(b"%PDF"):
            is_pdf = False
        text_parts = [pdf_to_text(data) if is_pdf else html_to_text(data)]
        source_urls = [final_url]
        if not is_pdf:
            for document_url in linked_official_documents(final_url, data, domains, model):
                try:
                    document_final_url, document_type, document_data = fetch_url(
                        document_url,
                        timeout=25,
                        max_bytes=8_000_000,
                    )
                    document_is_pdf = "pdf" in document_type.casefold() or document_final_url.casefold().split("?", 1)[0].endswith(".pdf")
                    if document_is_pdf and not document_data.lstrip().startswith(b"%PDF"):
                        document_is_pdf = False
                    if not host_is_allowed(document_final_url, domains):
                        continue
                    text_parts.append(pdf_to_text(document_data) if document_is_pdf else html_to_text(document_data))
                    source_urls.append(document_final_url)
                except Exception:
                    continue
        text = "\n".join(text_parts)
        title_match = None if is_pdf else re.search(r"<title[^>]*>(.*?)</title>", data.decode("utf-8", errors="ignore"), re.IGNORECASE | re.DOTALL)
        title = html.unescape(re.sub(r"<[^>]+>", " ", title_match.group(1))).strip() if title_match else f"{brand} {model} official datasheet"
        model_evidence = text if is_pdf else f"{final_url}\n{title}"
        if not model_token_present(model, model_evidence):
            return {"product_id": product_id, "status": "model_not_on_page", "brand": brand, "model": model, "url": final_url}
        specs = extract_specs(text, category_slug)
        return {
            "product_id": product_id,
            "status": "ok" if specs else "page_found_no_specs",
            "brand": brand,
            "model": model,
            "url": final_url,
            "source_urls": source_urls,
            "evidence_url": source_urls[-1],
            "title": title[:250],
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
        parser.add_argument("--limit", type=int)
        parser.add_argument("--workers", type=int, default=6)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--report", type=Path)
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
        if options["models"]:
            queryset = queryset.filter(model__in=options["models"])
        if options["missing_only"]:
            queryset = queryset.filter(specs__isnull=True)
        queryset = queryset.order_by("brand__name", "model", "hardware_version")
        if options["limit"]:
            queryset = queryset[: options["limit"]]
        products = list(queryset)
        if not products:
            raise CommandError("No products matched the crawl selection.")

        payloads = [(p.pk, p.brand.name, p.model, p.category.slug, p.official_url) for p in products]
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
        verified_date = date.today()
        for result in results:
            if result["status"] not in {"ok", "page_found_no_specs"}:
                continue
            product = Product.objects.select_related("brand", "category").get(pk=result["product_id"])
            evidence_url = result.get("evidence_url") or result["url"]
            is_datasheet = evidence_url.casefold().split("?", 1)[0].endswith(".pdf") or "datasheet" in evidence_url.casefold()
            source, _ = SourceDocument.objects.update_or_create(
                url=evidence_url,
                document_version="",
                defaults={
                    "brand": product.brand,
                    "document_type": SourceDocument.DocumentType.DATASHEET if is_datasheet else SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": result["title"] or f"{product.brand.name} {product.model}",
                    "region": product.region,
                    "accessed_date": verified_date,
                    "active": True,
                },
            )
            if not product.official_url and len(result["url"]) <= 200:
                product.official_url = result["url"]
                product.save(update_fields=("official_url", "updated_at"))
            template = select_comparison_template(
                product.category,
                product_type_code(product),
            )
            if not template:
                template, _ = ComparisonTemplate.objects.get_or_create(
                    category=product.category,
                    form_factor="",
                    name=f"{product.category.name} General",
                    version=1,
                    defaults={"active": True},
                )

            for code, (value_kind, value, raw_value) in result["specs"].items():
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
                TemplateField.objects.get_or_create(
                    template=template,
                    spec_definition=definition,
                    defaults={
                        "priority": priority,
                        "required": priority == "p0",
                        "display_group": group,
                        "display_order": definition.display_order,
                    },
                )
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                if existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and existing.display_value != "Unknown":
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
                        "source_note": "Automated extraction from official product page.",
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
        self.stdout.write(self.style.SUCCESS(f"{mode}: products={len(products)}, statuses={stats}, specs_imported={imported_specs}, specs_retained={retained_specs}, elapsed={elapsed}s"))
