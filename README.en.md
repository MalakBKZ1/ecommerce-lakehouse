# E-commerce Lakehouse: Shopping Behavior Analytics (REES46, October 2019)

[Version française](README.md)

An end-to-end Big Data project: a **Bronze / Silver / Gold** pipeline built with PySpark on 42 million events from an online store, followed by a **modular web application** of dashboards (Flask, seaborn, matplotlib).

## Business problem

A multi-category online store gets plenty of visits, but very few end in a purchase. The store manager knows the shop sells, but not where customers drop off or what to fix first. The project answers five questions:

1. Where do we lose customers? (conversion funnel)
2. When do they buy? (days and hours)
3. What makes money? (categories and brands)
4. How many carts are abandoned? (sessions)
5. Who are the best customers? (RFM segmentation)

## Key figures (October 2019)

| Metric | Value |
|---|---|
| Events processed | 42,448,764 raw rows, 42,418,542 after cleaning |
| Purchases | 742,773 |
| Revenue (catalog prices) | 229.9 million |
| Buying customers | 347,118 (about 1 in 10 distinct customers) |
| Sessions | 9,244,421 |

## Architecture

```
Kaggle CSV -> Bronze (raw + SHA-256 manifest + Parquet) -> Silver (cleaned, deduplicated)
           -> Gold (Kimball constellation, 8 tables) -> Web application
                                                     -> Db2 Lite (daily aggregate)
```

| Layer | Role |
|---|---|
| Bronze | Original CSV never modified, integrity manifest, Parquet staging partitioned by day |
| Silver | Typing, counted rejections, exact duplicates removed, invalid prices set to NULL |
| Gold | 5 dimensions and 3 fact tables (activity by hour, brand by day, sessions by day), RFM customers |
| Web application | One module per topic, reads only the Gold CSV exports |

The Gold layer is a **galaxy schema** (three fact tables with conformed dimensions). Measures are additive; ratios are computed as sum / sum.

## Web application: modules

| Module | Content |
|---|---|
| Funnel | views, carts, purchases; conversion by category |
| Purchase rhythm | revenue per day, weekday x hour heatmap (UTC), time-of-day split |
| Categories and brands | top 10 brands, revenue and average price per category |
| Sessions and abandonment | abandonment rate, session conversion |
| Customers (RFM) | segments, revenue per segment, recency / spend scatter |
| Totals check | compares displayed totals with the Gold layer |

To add a module, create a file in `webapp/modules/` that defines `META` and `construire()`. The sidebar updates automatically.

## Repository structure

```
scripts/      Spark pipeline (session, manifest, staging, silver, gold, Db2 load)
sql/          Db2 table creation
docs/         Bronze manifest, quality and control reports
notebooks/    advanced analysis
webapp/       web app (app.py, data.py, theme.py, registry.py, modules/, templates/, static/)
data/         local data (not versioned)
```

## Requirements

- Python 3.10 or later
- Java 17 or later and PySpark (only to reproduce the pipeline)
- The data: download `2019-Oct.csv` from Kaggle ("eCommerce behavior data from multi category store", REES46) into `data/bronze/ecommerce/`. **The data is not included in this repository.** Check the license on the Kaggle page.

## Run the web application

Prerequisite: the Gold exports must exist in `data/gold/export/` (produced by `scripts/04_gold.py`).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-webapp.txt
python -m flask --app webapp.app run --debug
```

Open http://127.0.0.1:5000. Run the app from the project root.

## Reproduce the pipeline

```powershell
python scripts/01_bronze_manifest.py
python scripts/02_staging_parquet.py
python scripts/03_silver.py
python scripts/04_gold.py
python scripts/05_load_db2.py   # optional: needs config.env (not versioned)
```

## Project rules

1. The Bronze file is never modified.
2. Every rejected, removed or corrected row is counted.
3. Totals are reconciled at every step: CSV, staging, Silver, Gold, Db2, web app.

## Limitations

- Revenue is the sum of catalog prices (no quantity, discount or order ID).
- Cart abandonment is an upper bound: a customer may buy later in another session.
- Only one month of data: no yearly seasonality.
- Times are in UTC: the store's country is not specified.

## Tech stack

PySpark, Parquet, pandas, Flask, seaborn, matplotlib, IBM Db2 (Lite), Git.

## Author

Malak, Master's student in Data Science.

## Data source

Kaggle, "eCommerce behavior data from multi category store" (Michael Kechinov, collected by REES46 / Open CDP).