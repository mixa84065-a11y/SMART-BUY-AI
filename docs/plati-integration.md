# Plati.Market integration

The backend uses the official public Plati.Market MCP catalogue, not the seller-scoped Digiseller XML search.

## Endpoints
- `GET /v1/integrations/plati/status`
- `GET /v1/integrations/plati/search?q=steam&page=1&page_size=10`

## Upstream
- MCP endpoint: `https://mcp.plati.market/mcp`
- Tool `get_products_from_plati_market` searches the public catalogue without a token.
- Tool `get_product_from_plati_market` retrieves a product card and seller metadata.
- Returned price fields include RUB, USD, EUR and UAH; SMART BUY AI displays RUB.
- Product pages are restricted to HTTPS `plati.market` links. Image requests use the Digiseller image host.

Official docs: https://my.digiseller.com/inside/api_mcp.asp

## Configuration
Public catalogue search requires no API key or partner ID. Set Render environment variable `PLATI_PARTNER_ID` only if the project has an approved affiliate identifier. The adapter then appends the official `ai` partner parameter to safe Plati product links. Never put this identifier or any secret in the APK.

## Scope and limitations
- The source contains digital goods listed on Plati.Market; it does not cover general clothing, home goods, physical electronics or all SMART BUY AI categories.
- The adapter is read-only. It does not purchase, pay, edit seller data or bypass CAPTCHA/access controls.
- Product descriptions, seller identity and sales counts are shown only when returned by Plati.Market. Ratings are not invented.
- Prices and availability can change; users must verify the offer on the seller's page before purchase.
