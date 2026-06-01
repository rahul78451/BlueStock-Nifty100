# BlueStock Nifty 100 — Power BI Dashboards

## 📋 Overview

This folder contains all assets needed to build the **7 Power BI dashboards** for the BlueStock Financial Intelligence System. Since `.pbix` files are proprietary binary files that can only be created inside Power BI Desktop, this package provides:

| Asset | Purpose |
|---|---|
| `dax_measures.dax` | **All 80+ DAX measures** used across all 7 dashboards |
| `power_query_connections.pq` | **Power Query M code** to connect to PostgreSQL |
| `build_guide.md` | **Step-by-step instructions** to build each dashboard |
| `data_model.md` | **Relationship diagram and table schema** |

## 🗂️ Dashboard Files to Create

| # | File Name | Pages | Audience |
|---|---|---|---|
| 1 | `01_executive_overview.pbix` | 3 | Fund managers, CXOs |
| 2 | `02_company_deep_dive.pbix` | 4 | Individual investors, research analysts |
| 3 | `03_sector_comparison.pbix` | 3 | Sector-level analysts |
| 4 | `04_health_scorecard.pbix` | 2 | Risk analysts, portfolio managers |
| 5 | `05_growth_analytics.pbix` | 3 | Growth investors |
| 6 | `06_debt_leverage.pbix` | 2 | Credit analysts, risk managers |
| 7 | `07_dividend_returns.pbix` | 2 | Income investors, dividend-focused funds |

## 🚀 Quick Start

1. **Start PostgreSQL** — Run `docker compose up db` from the project root
2. **Open Power BI Desktop** → Get Data → PostgreSQL Database
3. **Connect** — Server: `localhost:5432`, Database: `bluestock_dw`, User: `bluestock`, Password: `bluestock_2024`
4. **Import tables** — Select all `dim_*` and `fact_*` tables
5. **Set up relationships** — See `data_model.md`
6. **Import DAX measures** — Copy from `dax_measures.dax`
7. **Build visuals** — Follow `build_guide.md` page by page

## ⚠️ Important Notes

- Power BI cannot connect directly to SQLite. You **must** use the PostgreSQL database via Docker.
- All DAX measures are designed for the exact column names in the PostgreSQL warehouse schema.
- Radar charts require the **Radar Chart** custom visual from AppSource.
- Waterfall charts are available natively in Power BI Desktop.
