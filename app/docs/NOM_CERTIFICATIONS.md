# NOM certification badges

Product cards and detail pages show `NOM` when imported tracker evidence has
`READY = YES` and at least one numbered NOM certificate that has not expired
(inclusive end date), or whose end is `Definitiva`. Blank, `N/A`, and `-`
certificate cells do not count. IFT-only and NOM-024 labeling entries do not count.
This reports the supplied tracker evidence, not an independent certification audit.

Import the supplied tracker after applying migrations:

```powershell
.\.venv\Scripts\python.exe manage.py import_nom_certifications "C:\path\tracker.xls" --dry-run
.\.venv\Scripts\python.exe manage.py import_nom_certifications "C:\path\tracker.xls"
```

The importer validates the `NOM_2026` sheet and its certificate headers. It matches
TP-Link products by normalized exact model and listed region; known hardware
versions must also match (`V1` and `V1.0` are equivalent). Products with no hardware
version aggregate the listed versions for that model and region. A tracker row
without region/version restrictions matches any corresponding region/version.
Model suffixes and `TL-` prefixes are not discarded, and `UN` is not a region wildcard.

Each import replaces NOM evidence for existing TP-Link products, including clearing
old evidence when no row matches. Other brands and other product fields are untouched.
No products are created. Import again after adding products or receiving a new tracker.
The stored `nom_records` retain source filename, sheet, row, model label, region,
versions, readiness, certificate numbers and expiry dates. The page evaluates expiry
at request time without additional database queries.
