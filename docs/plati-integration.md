# Plati / Digiseller integration

The backend read-only search adapter is installed by `patches/apply_v0519.py` and exposes:

- `GET /v1/integrations/plati/status`
- `GET /v1/integrations/plati/search?q=steam&page=1&page_size=20`

It calls the documented Plati affiliate search endpoint with a minimum three-character query, normalizes available title/description/price/image/seller fields, and appends the affiliate parameter `ai` to product URLs. It does not perform purchases, payments, seller edits, or checkout.

## Required configuration

Set Render environment variable `PLATI_PARTNER_ID` to the partner identifier from the Digiseller/Plati affiliate account. Do not put it in the Android APK or public repository. The integration status remains `awaiting_partner_id` until this is configured.

Register for the affiliate program and obtain the identifier through the official partner instructions: https://plati.digital/partners/link/

## Important scope and data quality

- This is a digital-goods catalog source, not a general source for clothing, home goods, electronics, or all SMART BUY AI categories.
- The official API documentation lists search, product descriptions, images, reviews, seller information, prices and discounts. Only fields actually returned by a specific response are displayed.
- Search results must be tested against the live API after the partner ID is configured. If Plati changes the response schema or blocks a request, the backend returns an upstream error instead of inventing product data.
- Before enabling public display, review Plati's current affiliate/API terms and the requirements for showing its catalog and affiliate links.
