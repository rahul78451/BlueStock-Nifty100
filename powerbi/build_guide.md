# BlueStock Power BI — Dashboard Build Guide

## Prerequisites
1. Power BI Desktop installed
2. Docker running: `docker compose up db` (starts PostgreSQL on localhost:5432)
3. Data loaded: `python etl/03_load_to_warehouse.py`
4. Install **Radar Chart** custom visual from AppSource (for radar charts)

## Connection Setup (All Dashboards)
1. Open Power BI Desktop → **Get Data** → **PostgreSQL Database**
2. Server: `localhost:5432` | Database: `bluestock_dw`
3. User: `bluestock` | Password: `bluestock_2024`
4. Select all `dim_*` and `fact_*` tables → **Load**
5. Go to **Model View** → set up relationships per `data_model.md`
6. Copy DAX measures from `dax_measures.dax` via **Modeling → New Measure**

---

## Dashboard 1 — Executive Market Overview
**File:** `01_executive_overview.pbix` | **Pages:** 3

### Page 1.1 — Market Snapshot
| Visual | Type | Fields |
|---|---|---|
| Total Companies | Card | `[Total Companies]` measure |
| Average ROE | Card | `[Avg ROE%]` measure |
| Excellent Health Count | Card | `[Companies Excellent Health]` measure |
| Weak/Poor Health Count | Card | `[Companies Weak or Poor Health]` measure |
| Sector Distribution | Donut Chart | Legend: `dim_sector[sector_name]`, Values: `[Sector Company Count]` |
| Health Label Distribution | Bar Chart | Axis: `dim_health_label[label_name]`, Values: Count of `fact_ml_scores[id]` |
| Top 10 by ROE | Horizontal Bar | Axis: `dim_company[company_name]`, Values: `[ROE Last Year]`. Top N filter = 10 |
| Bottom 10 by Growth | Horizontal Bar | Axis: `dim_company[company_name]`, Values: `[3Y Sales CAGR]`. Bottom N = 10 |
| Sector Avg OPM% | Matrix | Rows: `dim_sector[sector_name]`, Columns: `dim_year[year_label]`, Values: `[Avg OPM%]`. Conditional formatting: red→green |

### Page 1.2 — Sector Performance
| Visual | Type | Fields |
|---|---|---|
| Sector Revenue Trend | Clustered Bar | Axis: `dim_year[year_label]`, Legend: `dim_sector[sector_name]`, Values: `[Total Sales]`. Filter last 5 years. Add Company slicer. |
| Sector Profitability Scatter | Scatter | X: `[3Y Sales CAGR]`, Y: `[ROE 3Y]`, Size: `[Total Revenue Latest Year]`, Legend: `dim_sector[sector_name]` |
| Sector Comparison Table | Matrix | Rows: `dim_sector[sector_name]`. Values: `[Avg OPM%]`, `[Avg D/E]`, `[Avg ROE%]`, `[Avg Health Score]`, `[Sector Company Count]` |
| Sector Treemap | Treemap | Group: `dim_sector[sector_name]`, Values: `[Total Revenue Latest Year]`. Color saturation: `[Avg Health Score]` |
| Top Company per Sector | Table | `dim_sector[sector_name]`, `[Best Company In Sector]` |

### Page 1.3 — YoY Growth Tracker
| Visual | Type | Fields |
|---|---|---|
| Total Revenue | Line Chart | Axis: `dim_year[year_label]`, Values: `[Total Nifty100 Revenue]` |
| Total Net Profit | Area Chart | Axis: `dim_year[year_label]`, Values: `[Total Nifty100 Net Profit]` |
| Growth Distribution | Histogram | Use `[3Y Sales CAGR]` with binning. Or Clustered Bar with ScoreBins table. |
| Year Slicer | Slicer | `dim_year[year_label]`, style: Between |
| Company Slicer | Slicer | `dim_company[company_name]`, style: Dropdown, multi-select |

---

## Dashboard 2 — Company Deep Dive
**File:** `02_company_deep_dive.pbix` | **Pages:** 4
> ⚠️ Add a **Company Selector slicer** (`dim_company[company_name]`, single-select dropdown) at the top of EVERY page. Sync across all pages.

### Page 2.1 — Financial Summary
| Visual | Type | Fields |
|---|---|---|
| Company Name | Card | `[Selected Company Name]` |
| Health Score | Gauge | Value: `[Company Health Score]`. Min=0, Max=100. Color: 0-35 red, 35-50 orange, 50-70 yellow, 70-85 light green, 85-100 green |
| Health Label | Card | `[Company Health Label]` |
| Revenue vs Profit | Combo Chart | Shared axis: `dim_year[year_label]`. Column: `[Total Sales]`. Line: `[Total Net Profit]`. Filter last 12 years. |
| OPM% Trend | Line Chart | Axis: `dim_year[year_label]`, Values: `[OPM Pct]`. Add constant line: `[Sector Avg OPM%]` |
| EPS Trend | Bar Chart | Axis: `dim_year[year_label]`, Values: `[EPS]` |
| Key Metrics Table | Table | `dim_year[year_label]`, `[Total Sales]`, `[Total Net Profit]`, `[OPM Pct]`, `[EPS]`, `[Dividend Payout Pct]` |
| CAGR 10Y | Card | `[CAGR 10Y Sales]` |
| CAGR 5Y | Card | `[CAGR 5Y Sales]` |
| CAGR 3Y | Card | `[CAGR 3Y Sales]` |
| CAGR TTM | Card | `[CAGR TTM Sales]` |

### Page 2.2 — Balance Sheet Health
| Visual | Type | Fields |
|---|---|---|
| D/E Trend | Line Chart | Axis: `dim_year[year_label]`, Values: `[Debt to Equity]`. Constant line at 1.0 |
| Asset Composition | 100% Stacked Bar | Axis: `dim_year[year_label]`, Values: `[Fixed Assets Pct]`, `[Investments Pct]`, `[Other Assets Pct]` |
| Borrowings vs Reserves | Area Chart | Axis: `dim_year[year_label]`, Values: `[Borrowings]` (red), `[Reserves]` (green) |
| Total Asset Growth | Bar Chart | Axis: `dim_year[year_label]`, Values: `[Total Assets]` |
| Balance Sheet Summary | Matrix | Rows: `dim_year[year_label]` (filter last 8 years). Values: `[Equity Capital]`, `[Reserves]`, `[Borrowings]`, `[Total Assets]` |
| Equity Ratio | Line Chart | Axis: `dim_year[year_label]`, Values: `[Equity Ratio Computed]` |

### Page 2.3 — Cash Flow Analysis
| Visual | Type | Fields |
|---|---|---|
| Cash Flow Waterfall | Clustered Bar | Axis: `dim_year[year_label]`, Values: `[Operating Cash Flow]` (green), `[Investing Cash Flow]` (blue), `[Financing Cash Flow]` (orange) |
| Free Cash Flow Trend | Line Chart | Axis: `dim_year[year_label]`, Values: `[Free Cash Flow]`. Conditional color: green if >0, red if <0 |
| Cash Conversion Ratio | Line Chart | Axis: `dim_year[year_label]`, Values: `[Cash Conversion Ratio]`. Constant line at 1.0 |
| Operating CF vs Net Profit | Dual-line | Axis: `dim_year[year_label]`, Values: `[Operating Cash Flow]`, `[Total Net Profit]` |
| Cash Flow Table | Table | `dim_year[year_label]`, `[Operating Cash Flow]`, `[Investing Cash Flow]`, `[Financing Cash Flow]`, `[Net Cash Flow]` |

### Page 2.4 — Growth & Returns Analysis
| Visual | Type | Fields |
|---|---|---|
| Sales Growth YoY | Bar Chart | Axis: `dim_year[year_label]`, Values: `[Sales Growth YoY%]`. Conditional: green >0, red <0 |
| Profit Growth YoY | Bar Chart | Axis: `dim_year[year_label]`, Values: `[Profit Growth YoY%]`. Same coloring. |
| ROE vs Industry | Combo Chart | Line: `dim_company[roe_pct]`. Shaded area: `[Sector Avg ROE]` |
| Dividend History | Combo Chart | Bar: `[Dividend Payout Pct]`. Line: `[EPS]`. Axis: `dim_year[year_label]` |
| CAGR Radar | Radar Chart (custom visual) | Categories: PeriodLabels. Values: Sales Growth, Profit Growth, Stock CAGR, ROE |
| Return Metrics | Table | `dim_year[year_label]`, `[ROE Last Year Measure]`, `[ROCE]`, `[ROA]`. Filter last 5 years. |

---

## Dashboard 3 — Sector Comparison Analyzer
**File:** `03_sector_comparison.pbix` | **Pages:** 3

### Page 3.1 — Sector vs Sector
| Visual | Type | Fields |
|---|---|---|
| Sector Selector | Slicer (multi) | `dim_sector[sector_name]` |
| Revenue by Sector | Clustered Bar | Axis: `dim_year[year_label]`, Legend: `dim_sector[sector_name]`, Values: `[Total Sales]` |
| Profitability | Line Chart | Axis: `dim_year[year_label]`, Legend: `dim_sector[sector_name]`, Values: `[Avg OPM%]` |
| Leverage | Line Chart | Axis: `dim_year[year_label]`, Legend: `dim_sector[sector_name]`, Values: `[Avg D/E]` |
| Scorecard Matrix | Matrix | Rows: `dim_sector[sector_name]`. Values: `[Avg Health Score]`, `[Avg ROE%]`, `[Avg OPM%]`, `[3Y Sales CAGR]`, `[Best Company In Sector]`, `[Worst Company In Sector]` |

### Page 3.2 — Companies Within a Sector
| Visual | Type | Fields |
|---|---|---|
| Sector Slicer | Slicer (single) | `dim_sector[sector_name]` |
| Company List | Table | `dim_company[company_name]`, `[Health Score]`, `[Health Label Display]`, `[OPM Pct]`, `[Debt to Equity]`, `[3Y Sales CAGR]` |
| Revenue Ranking | Horizontal Bar | Axis: `dim_company[company_name]`, Values: `[Revenue Latest Year]` |
| Health Score Ranking | Horizontal Bar | Axis: `dim_company[company_name]`, Values: `[Health Score]` |
| OPM% Comparison | Grouped Bar | Axis: `dim_company[company_name]`, Legend: `dim_year[year_label]` (last 3), Values: `[OPM Pct]` |

### Page 3.3 — Sector Trends Over Time
| Visual | Type | Fields |
|---|---|---|
| Year Slicer | Range slicer | `dim_year[fiscal_year]` |
| Revenue Growth | Line Chart | Axis: `dim_year[year_label]`, Legend: `dim_sector[sector_name]`, Values: `[Total Sales]` |
| Profit Margin | Line Chart | Axis: `dim_year[year_label]`, Legend: `dim_sector[sector_name]`, Values: `[Avg OPM%]` |
| Health Shift | Stacked Bar | Axis: `dim_sector[sector_name]`, Legend: `dim_health_label[label_name]`, Values: Count of companies |

---

## Dashboard 4 — Financial Health Scorecard
**File:** `04_health_scorecard.pbix` | **Pages:** 2

### Page 4.1 — Health Score Leaderboard
| Visual | Type | Fields |
|---|---|---|
| Company Slicer | Multi-select | `dim_company[company_name]` |
| Sector Slicer | Dropdown | `dim_sector[sector_name]` |
| Health Label Filter | Slicer (buttons) | `dim_health_label[label_name]` |
| Leaderboard | Table | `[Health Score Rank]`, `dim_company[company_name]`, `dim_sector[sector_name]`, `[Health Score]`, `[Health Label Display]`, `[OPM Pct]`, `[Debt to Equity]`, `[3Y Sales CAGR]`, `[Avg ROE%]` |
| Score Distribution | Clustered Bar | Axis: ScoreBins[Value], Values: `[Companies In Bin]` |
| Score by Sector | Box Plot or Bar | Axis: `dim_sector[sector_name]`, Values: `[Health Score]` |
| Needing Attention | Table | Filter: `dim_health_label[label_name]` IN {WEAK, POOR}. Columns: company, score, `fact_pros_cons[text]` where `is_pro=FALSE` |

### Page 4.2 — Scorecard Breakdown
| Visual | Type | Fields |
|---|---|---|
| Company Selector | Single dropdown | `dim_company[company_name]` |
| Score Radar | Radar Chart | 6 axes: `[Profitability Score]`, `[Growth Score]`, `[Leverage Score]`, `[Cash Flow Score]`, `[Dividend Score]`, `[Trend Score]` |
| Score Trend | Line Chart | Axis: `fact_ml_scores[computed_at]`, Values: `fact_ml_scores[overall_score]` |
| Pros List | Table | Filter: `fact_pros_cons[is_pro]=TRUE`. Columns: `category`, `text` |
| Cons List | Table | Filter: `fact_pros_cons[is_pro]=FALSE`. Columns: `category`, `text` |
| Peer Comparison | Bar Chart | Company + top/bottom 3 peers in sector. Use `[Top 3 Peers]` / `[Bottom 3 Peers]` filters |

---

## Dashboard 5 — Growth & Valuation Analytics
**File:** `05_growth_analytics.pbix` | **Pages:** 3

### Page 5.1 — Revenue & Profit Growth
| Visual | Type | Fields |
|---|---|---|
| Company Slicer | Multi-select | `dim_company[company_name]` |
| Year Slicer | Range | `dim_year[fiscal_year]` |
| YoY Revenue Growth | Waterfall or Bar | Axis: `dim_year[year_label]`, Values: `[Sales Growth YoY%]` |
| Growth Scatter | Scatter | X: `[5Y Sales CAGR]`, Y: `[CAGR 5Y Profit]`, Size: `[Revenue Latest Year]`. Quadrant lines at 10%. |
| Consistent Growers | Table | `dim_company[company_name]`, `[Is Consistent Grower]`. Filter: "✅ Yes" |
| CAGR Comparison | Grouped Bar | Axis: `dim_company[company_name]`, Values: `[10Y Sales CAGR]`, `[5Y Sales CAGR]`, `[3Y Sales CAGR]`, `[TTM Sales Growth]` |

### Page 5.2 — Margin Evolution
| Visual | Type | Fields |
|---|---|---|
| OPM% Heatmap | Matrix | Rows: `dim_company[company_name]`, Columns: `dim_year[year_label]`, Values: `[OPM Pct]`. Conditional: red <10%, yellow 10-20%, green >20% |
| Net Profit Margin | Line Chart | Axis: `dim_year[year_label]`, Legend: `dim_company[company_name]`, Values: `[Net Profit Margin]` |
| Expense Ratio | Area Chart | Axis: `dim_year[year_label]`, Values: `[Expense Ratio]` |
| Margin Leaders | Bar Chart | Axis: `dim_company[company_name]`, Values: `[OPM Improvement 3Y]`. Top N = 10. |
| Interest Coverage | Line Chart | Axis: `dim_year[year_label]`, Values: `[Interest Coverage]`. Constant lines at 2.0 and 3.0. |

### Page 5.3 — EPS & Earnings Quality
| Visual | Type | Fields |
|---|---|---|
| EPS Growth Ranking | Horizontal Bar | Axis: `dim_company[company_name]`, Values: `[EPS 3Y CAGR]` |
| EPS vs Cash Conversion | Scatter | X: `[EPS 3Y CAGR]`, Y: `[Avg Cash Conversion Ratio]` |
| Earnings Consistency | Matrix | Rows: `dim_company[company_name]`, Columns: `dim_year[year_label]`, Values: `[Total Net Profit]`. Conditional: red if <0, green gradient if >0 |

---

## Dashboard 6 — Debt & Leverage Monitor
**File:** `06_debt_leverage.pbix` | **Pages:** 2

### Page 6.1 — Leverage Snapshot
| Visual | Type | Fields |
|---|---|---|
| D/E Heatmap | Matrix | Rows: `dim_company[company_name]`, Columns: `dim_year[year_label]`, Values: `[Debt to Equity]`. Conditional: red >2, yellow 1-2, green <1 |
| Borrowings Trend | Clustered Bar | Axis: `dim_year[year_label]`, Legend: `dim_company[company_name]` (Top 10 by borrowings), Values: `[Borrowings]` |
| D/E Scatter | Scatter | X: `[D/E Latest Year]`, Y: `[Interest Coverage Latest]`. Add quadrant lines. |
| Debt-Free | Table | `dim_company[company_name]`, `[Is Debt Free]`. Filter: "✅ Debt Free" |
| D/E Change YoY | Bar Chart | Axis: `dim_company[company_name]`, Values: `[D/E Change YoY]`. Sort desc. Top N = 10. |
| Interest Coverage Ranking | Horizontal Bar | Axis: `dim_company[company_name]`, Values: `[Interest Coverage Latest]` |

### Page 6.2 — Debt Trajectory
| Visual | Type | Fields |
|---|---|---|
| Company Slicer | Single dropdown | `dim_company[company_name]` |
| Debt Journey | Line Chart | Axis: `dim_year[year_label]`, Values: `[Borrowings]` |
| Reserves vs Borrowings | Dual-line | Axis: `dim_year[year_label]`, Values: `[Reserves]`, `[Borrowings]` |
| Debt Repayment Signal | Bar Chart | Axis: `dim_year[year_label]`, Values: `[Financing Cash Flow]`. Negative = repaying. |
| Sector Avg D/E | Reference line on D/E chart | `[Sector Avg D/E]` |

---

## Dashboard 7 — Dividend & Shareholder Returns
**File:** `07_dividend_returns.pbix` | **Pages:** 2

### Page 7.1 — Dividend Analysis
| Visual | Type | Fields |
|---|---|---|
| Dividend Payout Ranking | Horizontal Bar | Axis: `dim_company[company_name]`, Values: `[Avg Dividend Payout 5Y]`. Top N = 20. |
| Consistent Payers | Table | `dim_company[company_name]`, `[Is Consistent Dividend Payer]`. Filter: "✅ Yes" |
| Payout vs EPS Growth | Scatter | X: `[Dividend Payout Pct]`, Y: `[EPS 3Y CAGR]` |
| Dividend Trend | Line Chart | Axis: `dim_year[year_label]`, Legend: `dim_company[company_name]`, Values: `[Dividend Payout Pct]` |
| Year Slicer | Range | `dim_year[fiscal_year]` |

### Page 7.2 — Shareholder Value
| Visual | Type | Fields |
|---|---|---|
| EPS Compounding | Line Chart | Axis: `dim_year[year_label]`, Legend: `dim_company[company_name]`, Values: `[EPS]` |
| ROE Comparison | Grouped Bar | Axis: `dim_company[company_name]`, Values: `[ROE Last Year Measure]`, `[ROE 3Y Avg]`, `[ROE 10Y Avg]` |
| Stock CAGR Table | Table | `dim_company[company_name]`, `[Stock CAGR 10Y Table]`, `[Stock CAGR 5Y Table]`, `[Stock CAGR 3Y Table]` |
| Value Creation Radar | Radar Chart | 4 axes: `[ROE Last Year Measure]`, `[Dividend Consistency Score]`, `[EPS 3Y CAGR]`, `[Stock CAGR 3Y]` |

---

## Formatting & Design Tips

### Color Palette
| Purpose | Color | Hex |
|---|---|---|
| Primary (positive/good) | Green | `#10B981` |
| Secondary (warning) | Amber | `#F59E0B` |
| Danger (negative/bad) | Red | `#EF4444` |
| Neutral | Slate | `#64748B` |
| Accent | Indigo | `#6366F1` |

### Conditional Formatting Rules
- **Health Score**: 85-100 `#10B981`, 70-84 `#22C55E`, 50-69 `#F59E0B`, 35-49 `#F97316`, 0-34 `#EF4444`
- **D/E Ratio**: <1 `#10B981`, 1-2 `#F59E0B`, >2 `#EF4444`
- **OPM%**: >20% `#10B981`, 10-20% `#F59E0B`, <10% `#EF4444`
- **Interest Coverage**: >3 `#10B981`, 2-3 `#F59E0B`, <2 `#EF4444`

### Slicer Sync Groups
For Dashboard 2, sync the Company slicer across all 4 pages:
1. View → Sync Slicers
2. Select the Company slicer
3. Check ✅ Sync and ✅ Visible for all pages
