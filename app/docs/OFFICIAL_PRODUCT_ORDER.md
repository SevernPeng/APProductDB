# Global catalog display order

Product lists use the ordered model labels in `catalog/official_product_order.json`.
Each family and subcategory has its own Global source URL and the snapshot date.
TP-Link legacy Unmanaged and Easy Smart pages supplement the Omada catalog.

The selected subcategory's sequence takes precedence over its parent family.
The combined catalog follows the existing Wireless, Switches, Gateways, Accessories
family order; there is no manufacturer page defining a single cross-family order.
Models absent from the source follow listed models, ordered by brand, model, region,
hardware version and ID. Competitor models do not inherit TP-Link's rankings.
Filters are applied before sorting and pagination, and preview products use the same
order. Only aliases explicitly printed on the official cards share a ranking.

Refresh using `python manage.py sync_official_product_order`, then restart the service.
The command requires every configured page to return product cards before replacing
the snapshot, so a failed fetch does not erase the current order. The snapshot is
loaded locally; browsing the catalog never makes an external HTTP request.
