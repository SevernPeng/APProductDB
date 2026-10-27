from pathlib import Path

from pypdf import PdfReader


TERMS = (
    "jumbo",
    "packet buffer",
    "igmp",
    "cable test",
    "aggregation",
    "loop prevention",
    "loop detection",
    "mirroring",
    "qos",
    "vlan",
    "extend mode",
    "poe watchdog",
    "auto recovery",
)


for path in sorted(Path("app").glob("tmp_reyee_es*.pdf")):
    text = "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)
    print(f"\n### {path.name} {len(text)}")
    lines = text.splitlines()
    matched = False
    for index, line in enumerate(lines):
        if any(term in line.lower() for term in TERMS):
            matched = True
            print(" | ".join(lines[max(0, index - 1) : min(len(lines), index + 5)]))
    if not matched:
        print(text)
