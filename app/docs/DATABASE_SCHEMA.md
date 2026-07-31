# Product and Competitive Benchmark Database

## Design goals

The database separates reusable product identity, market-specific variants,
typed specifications, evidence, comparison templates, and curated competitor
relationships. A specification value is stored once and reused by every
comparison view.

## Catalog hierarchy

- Wireless
  - Access Point
- Switching
  - Managed
  - Unmanaged / Easy Smart

`Category` remains a general tree so future product families can be introduced
without adding category-specific columns to `Product`.

## Core catalog entities

- `ProductModel`: canonical brand/model identity, for example TP-Link EAP773.
- `Product`: deployable market variant identified by region, hardware version,
  and optional SKU. Existing application code continues to use this model while
  the migration to canonical model identity is completed.
- `SpecDefinition`: reusable field definition with data type, canonical unit,
  collection rule, comparison direction, and category scope.
- `ProductSpec`: one typed value for a product variant and definition. Missing
  states are explicit: Published, Not Published, Not Applicable, and Unknown.
- `SourceDocument` and `SpecEvidence`: source-level provenance for each fact.
- `ProductHighlight`: vendor marketing claims stored separately from factual
  specifications.

New and existing `Product` rows are linked to `ProductModel`. The legacy brand,
category, model, and model-key columns remain temporarily to preserve the
current import, change-review, and product-query workflows. Model validation
prevents these fields from disagreeing with the canonical record.

## Comparison entities

- `ComparisonTemplate`: versioned parameter template for a category and optional
  form factor.
- `TemplateField`: ordered P0/P1/P2 field selection, requirement flag, and
  optional weight.
- `BenchmarkCase`: directional benchmark anchored on an own-brand product
  variant, region, scenario, and template.
- `ProductMatch`: competitor candidate inside a benchmark case, including match
  type, level, rank, confidence, validity dates, rationale, and review metadata.

The application chooses a form-factor template where possible and falls back to
the category-level template. Existing product matches are migrated into approved
benchmark cases grouped by own product and region.

## Data integrity rules

- Canonical product models are unique by brand and normalized model key.
- Product variants remain unique by brand, normalized model key, region, and
  hardware version during the compatibility phase.
- A product and specification definition have one current value.
- Typed values cannot populate more than one of text, number, or boolean.
- Non-published states cannot contain typed values.
- A benchmark anchor must belong to an own brand.
- A candidate cannot match a product to itself.
- Candidate region and anchor must match their benchmark case.
- A competitor appears at most once in a benchmark case.

## Initialization

Run `python manage.py initialize_catalog` after migrations. The command is
idempotent and creates the category hierarchy, the current AP specification
definitions, and the AP General, Outdoor AP, and Wall Plate AP templates.
