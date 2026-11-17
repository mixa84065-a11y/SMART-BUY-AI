# Plati / Digiseller integration

The backend adapter is installed by `patches/apply_v0519.py` and exposes:

- `GET /v1/integrations/plati/status`
- `GET /v1/integrations/plati/search?q=steam&page=1&page_size=10`

The search implementation follows the official Digiseller API:
- Search: `POST https://shop.digiseller.ru/xml/shop_search.asp` with XML body, Russian language and RUB currency.
- Product metadata: `GET https://api.digiseller.com/api/products/{product_id}/data?currency=RUB&lang=ru-RU`.
- Main product image fallback: `https://graph.digiseller.ru/img.ashx?id_d={product_id}&maxlength=400`.
- Product URLs are accepted only from approved Plati hostnames. The partner parameter `ai` is appended only when a valid partner identifier is configured.

## Configuration

The product catalog search does not require a partner identifier. For tracked affiliate links, set Render environment variable `PLATI_PARTNER_ID` to the partner identifier from the Digiseller/Plati affiliate account. Do not put it in the Android APK or public repository.

Register for the affiliate program and obtain the identifier through the official instructions: https://plati.digital/partners/link/

## Scope and data quality

- This source covers digital goods listed on Plati/Digiseller. It is not a general source for clothing, home goods, electronics, or all SMART BUY AI categories.
- Search responses supply product ID, name, price and partner commission. Product details are fetched separately to obtain the product URL and metadata. Missing fields remain null; they are never fabricated.
- The adapter is read-only. It does not perform purchases, payments, seller edits, or checkout.
- The endpoint must be smoke-tested against the live upstream service before being advertised as fully operational. If the upstream API rejects a request or changes its schema, the backend returns an upstream error rather than inventing product data.
- Review current affiliate/API terms before public display. Partner link format is `?ai=XXXXX` (or `&ai=XXXXX` when the URL already has a query string).
