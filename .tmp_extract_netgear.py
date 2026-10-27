from pathlib import Path

from pypdf import PdfReader


TERMS = (
    "packet forwarding rate",
    "forwarding rate",
    "mfps",
    "mpps",
    "performance specification",
    "bandwidth",
)


for path in sorted(Path(".").glob(".tmp_NETGEAR_*.pdf")):
    text = "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)
    print(f"\n### {path.name} {len(text)}")
    lines = text.splitlines()
    matched = False
    for index, line in enumerate(lines):
        if any(term in line.lower() for term in TERMS):
            matched = True
            print(" | ".join(lines[max(0, index - 4) : min(len(lines), index + 12)]))
    if not matched:
        print("NO FORWARDING-RATE TERM FOUND")
