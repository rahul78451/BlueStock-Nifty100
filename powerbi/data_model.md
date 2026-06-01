# BlueStock Nifty 100 — Power BI Data Model

## Database Connection

```
Server:   localhost:5432
Database: bluestock_dw
Username: bluestock
Password: bluestock_2024
```

## Tables to Import

### Dimension Tables
| Table Name | Primary Key | Row Count | Description |
|---|---|---|---|
| `dim_sector` | `sector_id` | 21 | Industry sector classification |
| `dim_company` | `symbol` | 109 | Master company data |
| `dim_year` | `year_id` | 44 | Time periods (Mar 2011 – TTM) |
| `dim_health_label` | `label_id` | 5 | ML score ranges (EXCELLENT→POOR) |

### Fact Tables
| Table Name | Primary Key | Row Count | Description |
|---|---|---|---|
| `fact_profit_loss` | `id` | 1,465 | Annual P&L per company per year |
| `fact_balance_sheet` | `id` | 1,535 | Annual balance sheet per company per year |
| `fact_cash_flow` | `id` | 1,450 | Annual cash flow per company per year |
| `fact_analysis` | `id` | 396 | Growth metrics (10Y/5Y/3Y/TTM) |
| `fact_ml_scores` | `id` | 109 | ML health scores per company |
| `fact_pros_cons` | `id` | 557 | Strengths and concerns per company |
| `documents` | `id` | 1,181 | BSE annual report links |

## Relationship Diagram

```
┌──────────────┐
│  dim_sector   │
│──────────────│
│ sector_id PK │◄─────────────────────────────────────┐
│ sector_name  │                                       │
│ sector_code  │                                       │
│ color_hex    │                                       │
└──────────────┘                                       │
                                                       │
┌──────────────────┐                                   │
│   dim_company     │                                   │
│──────────────────│                                   │
│ symbol PK        │◄──┬──┬──┬──┬──┬──┐               │
│ company_name     │   │  │  │  │  │  │  sector_id FK ─┘
│ sector_id FK ────┘   │  │  │  │  │  │
│ roe_pct, roce_pct│   │  │  │  │  │  │
│ market_cap_cr    │   │  │  │  │  │  │
└──────────────────┘   │  │  │  │  │  │
                       │  │  │  │  │  │
  ┌────────────────────┘  │  │  │  │  │
  │  ┌────────────────────┘  │  │  │  │
  │  │  ┌────────────────────┘  │  │  │
  │  │  │  ┌────────────────────┘  │  │
  │  │  │  │  ┌────────────────────┘  │
  │  │  │  │  │  ┌────────────────────┘
  │  │  │  │  │  │
  ▼  ▼  ▼  ▼  ▼  ▼
┌────────────────┐ ┌─────────────────┐ ┌──────────────┐
│fact_profit_loss│ │fact_balance_sheet│ │ fact_cash_flow│
│  company_id FK │ │  company_id FK  │ │ company_id FK│
│  year_id FK    │ │  year_id FK     │ │ year_id FK   │
└───────┬────────┘ └────────┬────────┘ └──────┬───────┘
        │                   │                  │
        ▼                   ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ fact_analysis│  │fact_ml_scores│  │fact_pros_cons│
│ company_id FK│  │ company_id FK│  │ company_id FK│
│ period_label │  │ health_label │  │ is_pro       │
└──────────────┘  └──────┬───────┘  └──────────────┘
                         │
                         ▼
                  ┌───────────────┐
                  │dim_health_label│
                  │ label_id PK   │
                  │ label_name    │
                  │ min/max_score │
                  └───────────────┘
```

## Relationships to Set Up in Power BI Model View

| # | From Table | From Column | To Table | To Column | Cardinality | Cross-Filter |
|---|---|---|---|---|---|---|
| 1 | `fact_profit_loss` | `company_id` | `dim_company` | `symbol` | Many-to-One | Single |
| 2 | `fact_profit_loss` | `year_id` | `dim_year` | `year_id` | Many-to-One | Single |
| 3 | `fact_balance_sheet` | `company_id` | `dim_company` | `symbol` | Many-to-One | Single |
| 4 | `fact_balance_sheet` | `year_id` | `dim_year` | `year_id` | Many-to-One | Single |
| 5 | `fact_cash_flow` | `company_id` | `dim_company` | `symbol` | Many-to-One | Single |
| 6 | `fact_cash_flow` | `year_id` | `dim_year` | `year_id` | Many-to-One | Single |
| 7 | `fact_analysis` | `company_id` | `dim_company` | `symbol` | Many-to-One | Single |
| 8 | `fact_ml_scores` | `company_id` | `dim_company` | `symbol` | Many-to-One | Single |
| 9 | `fact_ml_scores` | `health_label_id` | `dim_health_label` | `label_id` | Many-to-One | Single |
| 10 | `fact_pros_cons` | `company_id` | `dim_company` | `symbol` | Many-to-One | Single |
| 11 | `dim_company` | `sector_id` | `dim_sector` | `sector_id` | Many-to-One | Single |
| 12 | `documents` | `company_id` | `dim_company` | `symbol` | Many-to-One | Single |
| 13 | `documents` | `year_id` | `dim_year` | `year_id` | Many-to-One | Single |

### Steps to Create Relationships
1. Open Power BI Desktop → **Model View** (left sidebar icon)
2. Drag `fact_profit_loss[company_id]` onto `dim_company[symbol]`
3. In the dialog, confirm **Many-to-One**, **Single** cross-filter direction
4. Repeat for all relationships listed above
5. Verify all lines show the correct `*` (many) and `1` (one) markers

## Column Reference per Table

### dim_sector
| Column | Type | Description |
|---|---|---|
| `sector_id` | INT (PK) | Auto-incrementing ID |
| `sector_name` | TEXT | Full sector name (e.g. "Banking", "IT") |
| `sector_code` | TEXT | Short code |
| `description` | TEXT | Sector description |
| `color_hex` | TEXT | Hex color for charts |

### dim_company
| Column | Type | Description |
|---|---|---|
| `symbol` | TEXT (PK) | NSE ticker symbol (e.g. "RELIANCE") |
| `company_name` | TEXT | Full company name |
| `sector_id` | INT (FK) | Links to dim_sector |
| `sub_sector` | TEXT | Sub-sector classification |
| `face_value` | DECIMAL | Face value per share |
| `book_value` | DECIMAL | Book value per share |
| `roce_pct` | DECIMAL | Return on Capital Employed % |
| `roe_pct` | DECIMAL | Return on Equity % |
| `market_cap_cr` | DECIMAL | Market capitalization (₹ Cr) |
| `about_company` | TEXT | Company description |

### dim_year
| Column | Type | Description |
|---|---|---|
| `year_id` | INT (PK) | Auto-incrementing ID |
| `year_label` | TEXT | Period label (e.g. "Mar 2024", "TTM") |
| `fiscal_year` | INT | Fiscal year (e.g. 2024) |
| `is_ttm` | BOOLEAN | True for trailing twelve months |
| `sort_order` | INT | Chronological sort key |

### dim_health_label
| Column | Type | Description |
|---|---|---|
| `label_id` | INT (PK) | Auto-incrementing ID |
| `label_name` | TEXT | EXCELLENT / GOOD / AVERAGE / WEAK / POOR |
| `min_score` | DECIMAL | Lower bound of score range |
| `max_score` | DECIMAL | Upper bound of score range |
| `color_hex` | TEXT | Color for label |

### fact_profit_loss
| Column | Type | Description |
|---|---|---|
| `id` | INT (PK) | Row ID |
| `company_id` | TEXT (FK) | → dim_company.symbol |
| `year_id` | INT (FK) | → dim_year.year_id |
| `sales` | DECIMAL | Revenue (₹ Cr) |
| `expenses` | DECIMAL | Total expenses |
| `operating_profit` | DECIMAL | EBIT |
| `opm_pct` | DECIMAL | Operating profit margin % |
| `other_income` | DECIMAL | Non-operating income |
| `interest` | DECIMAL | Interest expense |
| `depreciation` | DECIMAL | Depreciation & amortization |
| `profit_before_tax` | DECIMAL | PBT |
| `tax_pct` | DECIMAL | Effective tax rate % |
| `net_profit` | DECIMAL | PAT (₹ Cr) |
| `eps` | DECIMAL | Earnings per share |
| `dividend_payout_pct` | DECIMAL | Dividend payout ratio % |
| `net_profit_margin_pct` | DECIMAL | Net margin % |
| `expense_ratio_pct` | DECIMAL | Expense/Sales ratio % |
| `interest_coverage` | DECIMAL | Operating profit / Interest |

### fact_balance_sheet
| Column | Type | Description |
|---|---|---|
| `id` | INT (PK) | Row ID |
| `company_id` | TEXT (FK) | → dim_company.symbol |
| `year_id` | INT (FK) | → dim_year.year_id |
| `equity_capital` | DECIMAL | Paid-up equity capital |
| `reserves` | DECIMAL | Reserves & surplus |
| `borrowings` | DECIMAL | Total borrowings |
| `other_liabilities` | DECIMAL | Other liabilities |
| `total_liabilities` | DECIMAL | Total liabilities |
| `fixed_assets` | DECIMAL | Net fixed assets |
| `cwip` | DECIMAL | Capital work in progress |
| `investments` | DECIMAL | Total investments |
| `other_assets` | DECIMAL | Other assets |
| `total_assets` | DECIMAL | Total assets |
| `debt_to_equity` | DECIMAL | D/E ratio |
| `equity_ratio` | DECIMAL | Equity / Total assets |

### fact_cash_flow
| Column | Type | Description |
|---|---|---|
| `id` | INT (PK) | Row ID |
| `company_id` | TEXT (FK) | → dim_company.symbol |
| `year_id` | INT (FK) | → dim_year.year_id |
| `operating_activity` | DECIMAL | Cash from operations |
| `investing_activity` | DECIMAL | Cash from investing |
| `financing_activity` | DECIMAL | Cash from financing |
| `net_cash_flow` | DECIMAL | Net cash change |
| `free_cash_flow` | DECIMAL | FCF = Operating + Investing |

### fact_analysis
| Column | Type | Description |
|---|---|---|
| `id` | INT (PK) | Row ID |
| `company_id` | TEXT (FK) | → dim_company.symbol |
| `period_label` | TEXT | 10Y, 5Y, 3Y, TTM |
| `compounded_sales_growth_pct` | DECIMAL | Sales CAGR % |
| `compounded_profit_growth_pct` | DECIMAL | Profit CAGR % |
| `stock_price_cagr_pct` | DECIMAL | Stock price CAGR % |
| `roe_pct` | DECIMAL | Return on Equity % for period |

### fact_ml_scores
| Column | Type | Description |
|---|---|---|
| `id` | INT (PK) | Row ID |
| `company_id` | TEXT (FK) | → dim_company.symbol |
| `computed_at` | DATETIME | When score was computed |
| `overall_score` | DECIMAL | Composite health score (0-100) |
| `profitability_score` | DECIMAL | Profitability sub-score |
| `growth_score` | DECIMAL | Growth sub-score |
| `leverage_score` | DECIMAL | Leverage sub-score |
| `cashflow_score` | DECIMAL | Cash flow sub-score |
| `dividend_score` | DECIMAL | Dividend sub-score |
| `trend_score` | DECIMAL | Trend sub-score |
| `health_label_id` | INT (FK) | → dim_health_label.label_id |

### fact_pros_cons
| Column | Type | Description |
|---|---|---|
| `id` | INT (PK) | Row ID |
| `company_id` | TEXT (FK) | → dim_company.symbol |
| `is_pro` | BOOLEAN | True = Strength, False = Concern |
| `category` | TEXT | Category tag |
| `text` | TEXT | Description text |
| `source` | TEXT | MANUAL or ML |
| `confidence` | DECIMAL | ML confidence score |
| `generated_at` | DATETIME | Timestamp |
