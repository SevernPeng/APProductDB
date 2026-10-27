from pathlib import Path

from pypdf import PdfReader


TERMS = (
    "jumbo",
    "vlan",
    "packet buffer",
    "port isolation",
    "storm",
    "dhcp snooping",
    "cpu protection",
    "mac address",
    "system performance capacity",
    "packet forwarding",
    "switching capacity",
    "antenna",
    "gain",
    "coverage",
    "range",
)


TARGET_FRAGMENTS = ("RAP62-OD",)


for path in sorted(Path(".").glob(".tmp_RG-*.pdf")):
    if not any(fragment in path.name for fragment in TARGET_FRAGMENTS):
        continue
    text = "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)
    print(f"\n### {path.name} {len(text)}")
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if any(term in line.lower() for term in TERMS):
            print(" | ".join(lines[max(0, index - 1) : min(len(lines), index + 7)]))
