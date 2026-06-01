// ============================================================
// BlueStock Nifty 100 — Power Query M Connection Scripts
// ============================================================
// Use these in Power BI Desktop → Transform Data → Advanced Editor
// Connection: PostgreSQL localhost:5432 / bluestock_dw
// ============================================================


// ────────────────────────────────────────────────────────────
// DIMENSION TABLES
// ────────────────────────────────────────────────────────────

// dim_sector
let
    Source = PostgreSQL.Database("localhost:5432", "bluestock_dw"),
    dim_sector = Source{[Schema="public", Item="dim_sector"]}[Data],
    #"Set Types" = Table.TransformColumnTypes(dim_sector, {
        {"sector_id", Int64.Type},
        {"sector_name", type text},
        {"sector_code", type text},
        {"description", type text},
        {"color_hex", type text}
    })
in
    #"Set Types"


// dim_company
let
    Source = PostgreSQL.Database("localhost:5432", "bluestock_dw"),
    dim_company = Source{[Schema="public", Item="dim_company"]}[Data],
    #"Set Types" = Table.TransformColumnTypes(dim_company, {
        {"symbol", type text},
        {"company_name", type text},
        {"sector_id", Int64.Type},
        {"sub_sector", type text},
        {"company_logo", type text},
        {"website", type text},
        {"nse_url", type text},
        {"bse_url", type text},
        {"face_value", type number},
        {"book_value", type number},
        {"roce_pct", type number},
        {"roe_pct", type number},
        {"about_company", type text},
        {"market_cap_cr", type number}
    }),
    #"Remove Nulls" = Table.ReplaceValue(#"Set Types", null, "", Replacer.ReplaceValue, {"sub_sector", "company_logo", "website"})
in
    #"Remove Nulls"


// dim_year
let
    Source = PostgreSQL.Database("localhost:5432", "bluestock_dw"),
    dim_year = Source{[Schema="public", Item="dim_year"]}[Data],
    #"Set Types" = Table.TransformColumnTypes(dim_year, {
        {"year_id", Int64.Type},
        {"year_label", type text},
        {"fiscal_year", Int64.Type},
        {"quarter", type text},
        {"is_ttm", type logical},
        {"is_half_year", type logical},
        {"sort_order", Int64.Type}
    }),
    #"Sorted" = Table.Sort(#"Set Types", {{"sort_order", Order.Ascending}})
in
    #"Sorted"


// dim_health_label
let
    Source = PostgreSQL.Database("localhost:5432", "bluestock_dw"),
    dim_health_label = Source{[Schema="public", Item="dim_health_label"]}[Data],
    #"Set Types" = Table.TransformColumnTypes(dim_health_label, {
        {"label_id", Int64.Type},
        {"label_name", type text},
        {"min_score", type number},
        {"max_score", type number},
        {"color_hex", type text}
    })
in
    #"Set Types"


// ────────────────────────────────────────────────────────────
// FACT TABLES
// ────────────────────────────────────────────────────────────

// fact_profit_loss
let
    Source = PostgreSQL.Database("localhost:5432", "bluestock_dw"),
    fact_profit_loss = Source{[Schema="public", Item="fact_profit_loss"]}[Data],
    #"Set Types" = Table.TransformColumnTypes(fact_profit_loss, {
        {"id", Int64.Type},
        {"company_id", type text},
        {"year_id", Int64.Type},
        {"sales", type number},
        {"expenses", type number},
        {"operating_profit", type number},
        {"opm_pct", type number},
        {"other_income", type number},
        {"interest", type number},
        {"depreciation", type number},
        {"profit_before_tax", type number},
        {"tax_pct", type number},
        {"net_profit", type number},
        {"eps", type number},
        {"dividend_payout_pct", type number},
        {"net_profit_margin_pct", type number},
        {"expense_ratio_pct", type number},
        {"interest_coverage", type number}
    })
in
    #"Set Types"


// fact_balance_sheet
let
    Source = PostgreSQL.Database("localhost:5432", "bluestock_dw"),
    fact_balance_sheet = Source{[Schema="public", Item="fact_balance_sheet"]}[Data],
    #"Set Types" = Table.TransformColumnTypes(fact_balance_sheet, {
        {"id", Int64.Type},
        {"company_id", type text},
        {"year_id", Int64.Type},
        {"equity_capital", type number},
        {"reserves", type number},
        {"borrowings", type number},
        {"other_liabilities", type number},
        {"total_liabilities", type number},
        {"fixed_assets", type number},
        {"cwip", type number},
        {"investments", type number},
        {"other_assets", type number},
        {"total_assets", type number},
        {"debt_to_equity", type number},
        {"equity_ratio", type number}
    })
in
    #"Set Types"


// fact_cash_flow
let
    Source = PostgreSQL.Database("localhost:5432", "bluestock_dw"),
    fact_cash_flow = Source{[Schema="public", Item="fact_cash_flow"]}[Data],
    #"Set Types" = Table.TransformColumnTypes(fact_cash_flow, {
        {"id", Int64.Type},
        {"company_id", type text},
        {"year_id", Int64.Type},
        {"operating_activity", type number},
        {"investing_activity", type number},
        {"financing_activity", type number},
        {"net_cash_flow", type number},
        {"free_cash_flow", type number}
    })
in
    #"Set Types"


// fact_analysis
let
    Source = PostgreSQL.Database("localhost:5432", "bluestock_dw"),
    fact_analysis = Source{[Schema="public", Item="fact_analysis"]}[Data],
    #"Set Types" = Table.TransformColumnTypes(fact_analysis, {
        {"id", Int64.Type},
        {"company_id", type text},
        {"period_label", type text},
        {"compounded_sales_growth_pct", type number},
        {"compounded_profit_growth_pct", type number},
        {"stock_price_cagr_pct", type number},
        {"roe_pct", type number}
    })
in
    #"Set Types"


// fact_ml_scores
let
    Source = PostgreSQL.Database("localhost:5432", "bluestock_dw"),
    fact_ml_scores = Source{[Schema="public", Item="fact_ml_scores"]}[Data],
    #"Set Types" = Table.TransformColumnTypes(fact_ml_scores, {
        {"id", Int64.Type},
        {"company_id", type text},
        {"computed_at", type datetime},
        {"overall_score", type number},
        {"profitability_score", type number},
        {"growth_score", type number},
        {"leverage_score", type number},
        {"cashflow_score", type number},
        {"dividend_score", type number},
        {"trend_score", type number},
        {"health_label_id", Int64.Type}
    })
in
    #"Set Types"


// fact_pros_cons
let
    Source = PostgreSQL.Database("localhost:5432", "bluestock_dw"),
    fact_pros_cons = Source{[Schema="public", Item="fact_pros_cons"]}[Data],
    #"Set Types" = Table.TransformColumnTypes(fact_pros_cons, {
        {"id", Int64.Type},
        {"company_id", type text},
        {"is_pro", type logical},
        {"category", type text},
        {"text", type text},
        {"source", type text},
        {"confidence", type number},
        {"generated_at", type datetime}
    })
in
    #"Set Types"


// documents
let
    Source = PostgreSQL.Database("localhost:5432", "bluestock_dw"),
    documents = Source{[Schema="public", Item="documents"]}[Data],
    #"Set Types" = Table.TransformColumnTypes(documents, {
        {"id", Int64.Type},
        {"company_id", type text},
        {"year_id", Int64.Type},
        {"document_type", type text},
        {"url", type text}
    })
in
    #"Set Types"
