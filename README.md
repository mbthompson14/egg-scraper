# egg-scraper

Scrapes egg product listings from Spain's top supermarkets and compares the
production-system breakdown (caged / barn / free-range / organic) against each
retailer's publicly reported cage-free progress.

Run quarterly to track whether catalog listings reflect stated commitments.

> **Scope note:** this project was built within a ~5-hour time budget, which
> is reflected in the deliberately simple approach. Carrefour and Lidl are not
> included because both require infrastructure beyond plain HTTP requests to scrape
> (Cloudflare protection and client-side rendering respectively).

---

## Retailers

| Retailer  | Method | Notes |
|-----------|--------|-------|
| Mercadona | REST API (`tienda.mercadona.es/api`) | ✓ |
| DIA       | SSR JSON embedded in category page | ✓ |
| Eroski    | GTM ecommerce data in HTML | ✓ |
| Alcampo   | JSON-LD `Product` schema on product pages | ✓ |
| Carrefour | — | ✗ Cloudflare-protected |
| Lidl      | — | ✗ Client-side rendered via internal APIs |

---

## Usage

```bash
pip install requests pandas pyyaml

python analysis/report.py --output analysis/report.md
```

Produces a single markdown table: one row per retailer with the production-system
breakdown from the live catalog alongside self-reported and third-party cage-free figures.
Also writes `analysis/data.csv` with the full scraped product-level data.

A pre-generated snapshot is at [analysis/report.md](analysis/report.md).

A GitHub Action ([`.github/workflows/quarterly_report.yml`](.github/workflows/quarterly_report.yml))
runs this automatically on the first day of each quarter and commits the updated report.

---

## Updating commitment figures

Reported cage-free percentages are hard-coded in `analysis/report.py` under the
`COMMITMENTS` dict. Update these manually when retailers publish new figures.

---

## Data fields

Each `EggProduct` record contains:

| Field | Description |
|-------|-------------|
| `retailer` | Retailer name |
| `sku` | Retailer product ID |
| `name` | Full product name |
| `production_system` | `caged` · `barn` · `free_range` · `organic` |
| `price` | Pack price (€) |
| `price_per_egg` | Derived: `price / quantity` |
| `quantity` | Number of eggs in the pack |
| `source` | How data was obtained (`API` / `SSR` / `HTML`) |
| `url` | Product page URL |
| `scraped_at` | Timestamp |
