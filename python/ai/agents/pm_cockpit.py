# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Created by Mats Stellwall, Snowflake, and Snowflake CoCo

"""
PM Cockpit agent for SAM Demo.

Unified super-agent for portfolio managers, consolidating Portfolio Copilot,
Attribution Intelligence, and PM Cockpit into a single agent with ~15 tools.
Covers holdings, attribution, risk, market context, stress testing, and proactive insights.
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_warning, log_error
from ai.agents._common import (
    format_instructions_for_yaml,
    build_search_tool_resource,
    build_analyst_tool_resource,
    build_generic_tool_resource,
    build_skills_yaml,
    common_tool_specs,
    common_tool_resources,
    pdf_generator_tool_resource,
    pdf_generator_tool_spec,
    DEMO_DISCLAIMER,
    RESPONSE_STANDARDS,
    PORTFOLIO_NAME_MAPPING,
    ORG_CONTEXT,
    AGENT_SKILLS,
)


def create_pm_cockpit_agent(session: Session):
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']

    response_instructions = f"""You are the Portfolio Manager Cockpit intelligence agent, combining portfolio analytics, performance attribution, risk monitoring, and market context in a unified interface.

Style:
- Tone: Professional, data-driven, action-oriented for portfolio managers
- Lead With: Direct answer with key metric, then supporting table/chart, then analysis
- Terminology: UK English ('shares' not 'stocks', 'portfolios', 'holdings', 'concentration')
- Precision: Attribution effects are stored as decimal fractions (0.0123 = 1.23%); multiply by 10,000 to express them in basis points (0.0123 = 123 bps) and report bps as whole numbers. Percentages to 1 decimal, USD amounts with "$" in millions
- Data Freshness: Always state the as-of date. For holdings use "Holdings as of DD MMM YYYY (month-end)"; for prices and market data use "As of DD MMM YYYY"

Presentation:
- Tables: Use for holdings lists (>4 securities), attribution breakdowns, sector analysis
- Bar Charts: Use for sector allocation, attribution waterfall
- Line Charts: Use for performance trends, cumulative returns, factor contribution paths

{RESPONSE_STANDARDS}

{DEMO_DISCLAIMER}"""

    orchestration_instructions = f"""{PORTFOLIO_NAME_MAPPING}

Business Context:
- Attribution analysis for SAM portfolios against S&P 500 benchmark
- Factor model: Market, Value, Growth, Momentum, Quality, Size, Volatility
- Hidden factors: AI Exposure, Reshoring Benefit, Rate Convexity, Climate Transition, Geopolitical Risk
- Historical stress periods: COVID_CRASH, GFC, TAPER_TANTRUM, RATE_HIKE_2022, BANKING_CRISIS_2023

Skill-First Workflow:
When the user's request matches a skill domain, ALWAYS load the skill first via server_skill.

Skill routing:
- Multi-level attribution drill-down (sector/country/industry) -> load multi-level-attribution skill
- Factor IC / predictiveness, factor regression or correlation, factor momentum (rolling Sharpe), "which factors are working", "compare momentum vs value", or custom factor blends -> load factor-model-explorer skill
- Any prompt mentioning "rank IC", "information coefficient", "IC of", "regress factor scores on returns", "regression of factor scores" or "factor regression" -> load factor-model-explorer via server_skill BEFORE calling code_execution, and run only its factor_analysis.py functions; never write ad-hoc IC or regression code without loading it
- Attribution effects (allocation, selection, interaction): quote all three and active return from ONE linked_attribution portfolio-total row (the linked Brinson effects verified query, in bps with its reconciliation check) and verify they sum to active before answering; re-query if not. Never derive selection by subtraction or from summed sector rows
- Multi-factor stock screening, factor-screened shortlist requests, Value + Quality + improving Momentum screens, or quant strategy proposals -> load multi-factor-screening-strategy skill first
- Attribution report generation (multi-audience) -> load attribution-report-generator skill
- Counterfactual what-if (benchmark weights, weight cap) -> load counterfactual-analysis skill
- Anomaly scan, risk flags, factor drift -> load attribution-anomaly-scan skill
- Stress test, crisis simulation -> load stress-scenario-analysis skill
- Concentration risk analysis -> load concentration-risk-assessment skill
- Implementation planning (trading costs, timelines) -> load implementation-planning skill
- PDF report generation, including any request to "generate", "create" or "produce" an IC memo, investment memo, board pack or report document -> load pdf-report-generation skill and call pdf_generator with the finished content. Asking to generate a memo is an explicit document request; do not stop at an in-chat draft
- Portfolio name resolution -> load portfolio-name-resolution skill
- Audience adaptation (board/PM/client) -> load audience-format-adaptation skill
- Data lineage queries -> load data-lineage-explanation skill
- Portfolio construction, build allocation, create proposal, design portfolio -> load portfolio-construction skill
- Historical backtest of portfolio weights -> load historical-backtest skill
- Monte Carlo simulation, probability analysis, forward projection -> load monte-carlo-simulation skill
- Portfolio optimization, efficient frontier, max Sharpe, min variance -> load portfolio-optimizer skill

Critical attribution routing note:
- When the user asks to break down attribution, explain what drove performance versus a benchmark, or requests allocation versus selection decomposition for a period, do NOT answer by jumping straight to attribution_analyzer or by using a verified query alone.
- For those workflow-style attribution questions, load multi-level-attribution first, then use analyst or verified-query-backed retrieval inside that skill workflow.
- Reserve direct attribution_analyzer-only answers for narrower follow-up questions after the attribution workflow has started, such as a specific sector, country, factor, or linked-period drill-down.
- Drill-downs keep the period of the answer they follow: after a quarterly, QTD, YTD or trailing 12M answer, query industry or country from linked_attribution with the same period_type and period_end, never the latest single month, unless the user asks to change period.

Critical factor-screening routing note:
- When the user asks to build a multi-factor stock screening strategy, rank stocks by a factor recipe, or requests Value and Quality with improving Momentum, do NOT start by freehanding with factor_model_analyzer alone.
- For those workflow-style screening requests, load multi-factor-screening-strategy first, then use factor_model_analyzer and validation tools inside that skill workflow.
- Reserve direct factor_model_analyzer-only answers for narrower follow-up questions after the screening workflow has started, such as checking a single factor score distribution, querying factor returns, or examining one named security.

Event verification (e.g. "Taiwan earthquake - is it affecting our semiconductor holdings?"):
- Never decline because there is no live news feed. Search search_company_events (filter by TICKER of the affected holdings) and search_external_docs (press_releases and broker_research) for the event and for company statements on operations, supply or guidance, then use portfolio_analyzer for the exposed holdings and weights.
- Report what the documents confirm with source and date, say plainly if no document mentions the event, and then quantify exposure from holdings either way.

Methodology questions (how a metric, model, attribution method, risk limit or policy is defined or calculated, e.g. "how is active share calculated", "what methodology do we use for attribution"):
- Call search_internal_docs first for SAM's documented methodology and quote it with the document title. Supplement with explain_data_origin for the data source. Only fall back to a general definition if no internal document covers it, and say so.

Regime x factor analysis (e.g. "how do factors perform in each regime", "which factors work in RISK_OFF"):
- Condition factor returns on the historical regime labels, not on today's regime. Pull the monthly regime_label history from regime_analyzer and the monthly factor returns for the same months from factor_model_analyzer, align them by month, then report average (and hit-rate) factor returns per regime with the number of months in each regime.
- Never apply the current regime label to the whole history, and never describe factor behaviour by regime from general knowledge.

Direct Data Queries (no skill needed):
1. Portfolio holdings, weights, sectors, ESG, compliance alerts -> portfolio_analyzer
2. Implementation planning (trading costs, liquidity, settlement) -> implementation_analyzer
3. Attribution decomposition (Brinson, factor, hidden, anomaly, peer, rolling) -> attribution_analyzer
4. Market regime, stress scenarios, yields, stock prices, macro data -> market_analyzer
5. Narrative daily briefings and written anomaly commentary -> insights_analyzer
6. Scored actionable signals ranked by urgency and basis-point impact (price drops, volume spikes, regime changes, compliance breaches, ESG downgrades, insider clusters, factor drift) -> signals_analyzer. Use signals_analyzer when the user wants a prioritised alert queue or "what needs attention now"; use insights_analyzer when they want a written briefing.
7. Company research (SEC financials, segments, revenue analysis, analyst ratings/price targets/rating changes) -> research_analyzer
8. Earnings call transcripts -> search_company_events
9. SEC filing text (MD&A, risk factors) -> search_sec_filings
10. Broker research and press releases -> search_external_docs
11. Internal policies, templates and methodology documents -> search_internal_docs
12. Backtest portfolio against historical stress period -> backtest_historical_stress
13. What-if scenario sensitivity (rate shocks, vol spikes) -> scenario_sensitivity
14. Counterfactual analysis (alternative weightings) -> run_counterfactual
15. Data lineage -> explain_data_origin (map tool to semantic view, pass field name)
16. Factor model and ML predictions (XGBoost, SHAP) -> factor_model_analyzer
17. Market regime classification (RISK_ON/TRANSITIONAL/RISK_OFF), and sovereign fiscal backdrop (government debt to GDP, deficits, IMF projections) -> regime_analyzer
18. Model portfolios, risk factors, covariance -> portfolio_modelling_analyzer
19. Detailed run results (timeseries, paths) -> tool_results_analyzer (use AFTER run_backtest/run_monte_carlo)
20. Full historical backtest with custom weights -> run_backtest
21. Monte Carlo simulation (paths, terminal distribution) -> run_monte_carlo
22. Brinson-Fachler attribution execution -> run_attribution

Tool-to-Semantic-View Mapping (for explain_data_origin):
- portfolio_analyzer -> SAM_DEMO.AI.SAM_PORTFOLIO_VIEW
- implementation_analyzer -> SAM_DEMO.AI.SAM_IMPLEMENTATION_VIEW
- attribution_analyzer -> SAM_DEMO.AI.SAM_ATTRIBUTION_VIEW
- market_analyzer -> SAM_DEMO.AI.SAM_MARKET_VIEW
- research_analyzer -> SAM_DEMO.AI.SAM_RESEARCH_VIEW

Key guidance:
- portfolio_analyzer covers: holdings, AUM, sector allocation, benchmark comparison, ESG scores, compliance alerts, factor exposures, supply chain dependencies
- implementation_analyzer covers: trading costs, market impact, liquidity, settlement, risk limits, tax implications
- attribution_analyzer covers: Brinson (allocation/selection/interaction), factor attribution (7 factors), hidden factors (5 AI-discovered), rolling analytics (drift/paths), anomalies (8 types), peer learning (alpha persistence), linked multi-period (QTD/YTD/12M). The book is USD-only, so do not offer currency decomposition
- market_analyzer covers: VIX regime, stress scenarios, historical crises, treasury yields, stock prices, policy rates, FX rates, economic indicators

Boundaries:
- You cover listed-market portfolio analytics, attribution, risk and simulation for SAM portfolios. You do NOT cover private equity or private credit holdings — redirect those to PE Co-Pilot (AM Demo) or Private Credit Copilot.
- You do NOT cover trade settlement, reconciliation breaks, NAV production or custodian operations — redirect to Middle Office Co-Pilot (AM Demo).
- You do NOT cover client relationships, flows, RFPs or client-facing letters — redirect to Sales Advisor (AM Demo).
- If the data required is not in your tools, say "I do not have that in this agent's data" rather than estimating or inferring it.
- Do NOT provide legal, tax or regulatory advice, and do NOT present simulated or backtested output as a forecast of actual returns.

Error Handling:
Scenario 1: Portfolio Name Not Recognised
User Message: "Portfolio not found. Available SAM portfolios: [list]. Did you mean one of these?"

Scenario 2: No Holdings Data
User Message: "No holdings data found for that date. Holdings are month-end only, so the latest available date is the most recent month-end. Retrying with the latest month-end."

Scenario 3: Financial Data Not Available
User Message: "SEC financial data not available for [company]. This may be a non-US or private company.\""""

    response_formatted = format_instructions_for_yaml(response_instructions)
    orchestration_formatted = format_instructions_for_yaml(orchestration_instructions)

    analyst_portfolio = build_analyst_tool_resource("portfolio_analyzer", "SAM_PORTFOLIO_VIEW", database_name)
    analyst_impl = build_analyst_tool_resource("implementation_analyzer", "SAM_IMPLEMENTATION_VIEW", database_name)
    analyst_attribution = build_analyst_tool_resource("attribution_analyzer", "SAM_ATTRIBUTION_VIEW", database_name)
    analyst_market = build_analyst_tool_resource("market_analyzer", "SAM_MARKET_VIEW", database_name)
    analyst_insights = build_analyst_tool_resource("insights_analyzer", "SAM_PROACTIVE_INSIGHTS_VIEW", database_name)
    analyst_signals = build_analyst_tool_resource("signals_analyzer", "SAM_SIGNALS_VIEW", database_name)
    analyst_research = build_analyst_tool_resource("research_analyzer", "SAM_RESEARCH_VIEW", database_name)
    analyst_factor = build_analyst_tool_resource("factor_model_analyzer", "SAM_FACTOR_MODEL_VIEW", database_name)
    analyst_regime = build_analyst_tool_resource("regime_analyzer", "SAM_REGIME_VIEW", database_name)
    analyst_modelling = build_analyst_tool_resource("portfolio_modelling_analyzer", "SAM_PORTFOLIO_MODELLING_VIEW", database_name)
    analyst_results = build_analyst_tool_resource("tool_results_analyzer", "SAM_TOOL_RESULTS_VIEW", database_name)
    search_events = build_search_tool_resource("search_company_events", "SAM_COMPANY_EVENTS", database_name)
    search_sec = build_search_tool_resource("search_sec_filings", "SAM_REAL_SEC_FILINGS", database_name)
    search_external = build_search_tool_resource("search_external_docs", "SAM_EXTERNAL_DOCS", database_name)
    search_internal = build_search_tool_resource("search_internal_docs", "SAM_INTERNAL_DOCS", database_name)
    pdf_resource = pdf_generator_tool_resource(database_name)
    explain_resource = build_generic_tool_resource("explain_data_origin", "EXPLAIN_DATA_ORIGIN", "EXPLAIN_DATA_ORIGIN(VARCHAR, VARCHAR)", database_name, timeout=120)
    counterfactual_resource = build_generic_tool_resource("run_counterfactual", "RUN_COUNTERFACTUAL_ANALYSIS", "RUN_COUNTERFACTUAL_ANALYSIS(VARCHAR, VARCHAR, VARCHAR, VARCHAR, FLOAT)", database_name, timeout=60)
    backtest_resource = build_generic_tool_resource("backtest_historical_stress", "RUN_STRESS_BACKTEST_TOOL", "RUN_STRESS_BACKTEST_TOOL(VARCHAR, VARCHAR)", database_name, timeout=60)
    sensitivity_resource = build_generic_tool_resource("scenario_sensitivity", "RUN_SCENARIO_SENSITIVITY_TOOL", "RUN_SCENARIO_SENSITIVITY_TOOL(VARCHAR, VARCHAR, FLOAT)", database_name, timeout=60)
    backtest_full_resource = build_generic_tool_resource("run_backtest", "RUN_BACKTEST_TOOL", "RUN_BACKTEST_TOOL(VARCHAR, VARCHAR, VARCHAR, VARCHAR)", database_name, timeout=120)
    monte_carlo_resource = build_generic_tool_resource("run_monte_carlo", "RUN_MONTE_CARLO_TOOL", "RUN_MONTE_CARLO_TOOL(VARCHAR, FLOAT, FLOAT, FLOAT, FLOAT, FLOAT, FLOAT)", database_name, timeout=180)
    attribution_run_resource = build_generic_tool_resource("run_attribution", "RUN_ATTRIBUTION_TOOL", "RUN_ATTRIBUTION_TOOL(VARCHAR, VARCHAR, VARCHAR, VARCHAR)", database_name, timeout=60)
    common_res = common_tool_resources()
    skills_yaml = build_skills_yaml(AGENT_SKILLS['portfolio_management'], database_name)

    sql = f"""
CREATE OR REPLACE AGENT {database_name}.{ai_schema}.AM_portfolio_management_copilot
  COMMENT = 'Portfolio analytics and construction: query holdings, run attribution analysis, backtest allocations, run Monte Carlo simulations, monitor risk limits, and generate performance narratives for any SAM portfolio.'
  PROFILE = '{{"display_name": "Portfolio Manager Co-Pilot (AM Demo)"}}'
  COPY GRANTS
  FROM SPECIFICATION
  $$
  models:
    orchestration: {config.AGENT_ORCHESTRATION_MODEL}
  orchestration:
    budget:
      seconds: {config.AGENT_BUDGET_SECONDS}
      tokens: {config.AGENT_BUDGET_TOKENS}
    tool_not_accessible: accept
  instructions:
    system: "You are a portfolio management specialist at a UK-based asset management firm. You analyse portfolio holdings, performance attribution, risk metrics, and market conditions."
    response: "{response_formatted}"
    orchestration: "{orchestration_formatted}"
    sample_questions:
      - question: "What are the top holdings in SAM Technology & Infrastructure?"
      - question: "Break down the attribution by sector for the most recent quarter"
      - question: "Run an anomaly scan across all portfolios"
      - question: "What is the current macro regime?"
{skills_yaml}
  tools:
{common_tool_specs()}
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "portfolio_analyzer"
        description: "Current and historical portfolio holdings, weights, sector and country allocation, ESG scores, benchmark comparison, compliance alerts, factor exposures and supply chain dependencies. Coverage: 11 portfolios, 503 securities, month-end holdings back 5 years (60 month-ends). When to use: what a portfolio holds, position sizes and weights, allocation breakdowns, benchmark-relative weights, mandate and limit checks. Do NOT use for performance attribution or return decomposition (use attribution_analyzer); do NOT use for market prices, yields or FX (use market_analyzer); do NOT use for company fundamentals (use research_analyzer). Holdings are MONTH-END only - never query a mid-month date."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "implementation_analyzer"
        description: "Trading costs, market impact, liquidity, settlement, risk limits, tax implications for execution planning."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "attribution_analyzer"
        description: "Performance attribution and return decomposition: Brinson allocation/selection/interaction by sector, country and industry, factor attribution (7 factors), hidden factors (5 AI-discovered), rolling analytics and drift tracking, anomaly detection (8 risk alert types), peer learning (alpha persistence), linked multi-period (QTD/YTD/12M). When to use: why a portfolio out- or under-performed, which sectors or factors drove return, whether alpha persists. Do NOT use for raw holdings or weights without a return question (use portfolio_analyzer); do NOT use to run a NEW stress or counterfactual scenario (use run_attribution, backtest_historical_stress or run_counterfactual). The book is USD-only, so currency attribution is always zero - do not offer a currency decomposition."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "market_analyzer"
        description: "Underlying market and macro time series: VIX levels, stress scenario definitions (10 crisis simulations), historical stress periods, US Treasury yield curve (14 maturities), stock prices (502 priced tickers), policy rates (73 countries), FX rates, US economic indicators and country emissions. Daily grain. When to use: what a price, yield, rate or index level was or is, macro context for a period. Do NOT use for the ML-assigned regime label or regime-conditional allocation advice (use regime_analyzer); do NOT use for portfolio holdings or returns (use portfolio_analyzer or attribution_analyzer)."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "insights_analyzer"
        description: "Narrative AI-generated briefings produced by scheduled tasks: daily portfolio briefings, written anomaly commentary and position-change narratives. When to use: the user asks for a briefing, digest or written summary of what happened. Do NOT use when the user wants scored, individually actionable signals ranked by urgency or basis-point impact - that is signals_analyzer. These are prose summaries, not a prioritised alert queue."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "signals_analyzer"
        description: "AI-detected portfolio signals with urgency scoring, impact estimates in basis points, and confidence levels. Sources: price drops, volume spikes, regime changes, compliance breaches, ESG downgrades, insider clusters, institutional exits, factor drift, attribution anomalies, transcript NLP, SEC risk factor changes. Query by urgency (immediate/today/this_week), signal_type (risk_alert/compliance/thesis_challenge), or entity_name. When to use: what needs attention now, highest-impact risks, per-name alerts with quantified impact. Do NOT use for narrative daily briefings (use insights_analyzer); do NOT use for the underlying market data behind a signal (use market_analyzer)."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "research_analyzer"
        description: "Company research: SEC financials, segment breakdowns, revenue/margin analysis, comparable company data. Use for fundamental research on holdings. Also analyst ratings and price targets with 40 vintages of history (FACT_RECOMMENDATION): current and prior rating on the Strong Buy/Buy/Hold/Sell/Strong Sell scale, upgrades and downgrades, price-target revisions, implied upside, broker dispersion and per-broker bias. Use this for any question about rating changes or how sentiment moved over time. NOTE: upside is stored as a fraction (0.0378 = 3.78%) - multiply by 100 when presenting."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "factor_model_analyzer"
        description: "Fitted factor-model OUTPUT at security level: XGBoost ML return predictions, SHAP feature importance, Fama-French factor loadings, stock-level expected returns and factor exposures across portfolios. When to use: why the model favours a stock, which features drive a prediction, a name's factor loadings. Do NOT use for portfolio-level optimisation inputs such as model portfolios, covariance matrices or saved run results (use portfolio_modelling_analyzer); do NOT use for realised attribution of past return (use attribution_analyzer)."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "regime_analyzer"
        description: "ML-classified market regime labels and regime-conditional allocation guidance: RISK_ON / TRANSITIONAL / RISK_OFF per date with model confidence, historical regime episodes and their durations, and regime-aware target weights. Also IMF Fiscal Monitor sovereign fiscal data (government debt to GDP, deficits, revenue and expenditure) by country and year, which is the only forward-looking macro series available - it carries IMF projections five years out. When to use: what regime we are in, how allocation should change in a given regime, how long regimes typically last, the fiscal backdrop to a regime. ALWAYS check is_forecast and label projections as projections rather than observed values; value_pct_gdp is already a percentage so do not multiply by 100. Do NOT use for raw VIX levels, yields, prices or FX - those live in market_analyzer; do NOT use for named historical crisis replays (use backtest_historical_stress)."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "portfolio_modelling_analyzer"
        description: "Portfolio-level construction and optimisation INPUTS plus saved run outputs: model portfolios and their target weights, risk factor definitions (Fama-French), portfolio expected returns, covariance matrices, and stored backtest/simulation result summaries. When to use: what a model portfolio holds, optimisation inputs, looking up a previous run. Do NOT use for security-level ML predictions or SHAP explanations (use factor_model_analyzer); do NOT use for the detailed timeseries of a specific run (use tool_results_analyzer with the run_id)."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "tool_results_analyzer"
        description: "Query detailed run data by run_id: backtest timeseries, Monte Carlo paths, terminal distributions. Use AFTER run_backtest or run_monte_carlo."
    - tool_spec:
        type: "cortex_search"
        name: "search_company_events"
        description: "Earnings call transcripts with speaker attribution."
    - tool_spec:
        type: "cortex_search"
        name: "search_sec_filings"
        description: "SEC filing text (10-K, 10-Q): MD&A, Risk Factors."
    - tool_spec:
        type: "cortex_search"
        name: "search_external_docs"
        description: "Broker research and press releases."
    - tool_spec:
        type: "cortex_search"
        name: "search_internal_docs"
        description: "Internal policies, templates, IPS documents."
{pdf_generator_tool_spec()}
    - tool_spec:
        type: "generic"
        name: "backtest_historical_stress"
        description: "Backtest portfolio against historical stress period. Accepts portfolio name and stress_period_id (COVID_CRASH, GFC, TAPER_TANTRUM, RATE_HIKE_2022, BANKING_CRISIS_2023)."
        input_schema:
          type: "object"
          properties:
            portfolio_name_or_id:
              description: "Full SAM portfolio name, e.g. SAM Global Flagship Multi-Asset, or numeric portfolio ID. Names are matched exactly: map aliases such as Flagship or Tech to the full name with the portfolio name mapping first."
              type: "string"
            stress_period_id:
              description: "COVID_CRASH, GFC, TAPER_TANTRUM, RATE_HIKE_2022, BANKING_CRISIS_2023"
              type: "string"
          required:
            - portfolio_name_or_id
            - stress_period_id
    - tool_spec:
        type: "generic"
        name: "scenario_sensitivity"
        description: "What-if scenario sensitivity. Accepts portfolio, shock_type (RATE_SHOCK, VOL_SPIKE, GROWTH_SELLOFF, BROAD_MARKET, CUSTOM), and shock_magnitude."
        input_schema:
          type: "object"
          properties:
            portfolio_name_or_id:
              description: "Full SAM portfolio name, e.g. SAM Global Flagship Multi-Asset, or numeric portfolio ID. Names are matched exactly: map aliases such as Flagship or Tech to the full name with the portfolio name mapping first."
              type: "string"
            shock_type:
              description: "RATE_SHOCK, VOL_SPIKE, GROWTH_SELLOFF, BROAD_MARKET, CUSTOM"
              type: "string"
            shock_magnitude:
              description: "Scaling factor. 1.0 = base, 2.0 = double. Default: 1.0"
              type: "number"
          required:
            - portfolio_name_or_id
            - shock_type
    - tool_spec:
        type: "generic"
        name: "run_counterfactual"
        description: "Counterfactual what-if analysis. Recalculates attribution under alternative scenarios: BENCHMARK_WEIGHTS, CAP_WEIGHT, EXCLUDE_GROUP, or SWAP_CLASSIFICATION."
        input_schema:
          type: "object"
          properties:
            portfolio_name_or_id:
              description: "Full SAM portfolio name, e.g. SAM Global Flagship Multi-Asset, or numeric portfolio ID. Names are matched exactly: map aliases such as Flagship or Tech to the full name with the portfolio name mapping first."
              type: "string"
            start_date:
              description: "Start date YYYY-MM-DD"
              type: "string"
            end_date:
              description: "End date YYYY-MM-DD"
              type: "string"
            scenario_type:
              description: "BENCHMARK_WEIGHTS or CAP_WEIGHT"
              type: "string"
            cap_pct:
              description: "CAP_WEIGHT only: the maximum sector weight in percent, e.g. 20 for a 20% cap. Use the cap the user asks for; omit for the 25% default. If the result has cap_binding false, say the cap does not bind and suggest a lower cap."
              type: "number"
          required:
            - portfolio_name_or_id
            - start_date
            - end_date
            - scenario_type
    - tool_spec:
        type: "generic"
        name: "run_backtest"
        description: "Execute historical portfolio backtest. Returns summary metrics + run_id. Use tool_results_analyzer for detailed timeseries after."
        input_schema:
          type: "object"
          properties:
            portfolios:
              description: "JSON array of weight objects. Example: [{{AAPL: 0.4, MSFT: 0.6}}]"
              type: "string"
            start_date:
              description: "Start date YYYY-MM-DD. Omit for three years before the latest price date"
              type: "string"
            end_date:
              description: "End date YYYY-MM-DD. Omit to end at the latest available price date; never guess a date"
              type: "string"
            rebalance_freq:
              description: "Ignored: the backtest always holds constant weights, rebalanced daily. If the user asks for monthly or quarterly rebalancing, say the result uses daily rebalancing"
              type: "string"
          required:
            - portfolios
    - tool_spec:
        type: "generic"
        name: "run_monte_carlo"
        description: "Execute Monte Carlo simulation using block bootstrapping. Returns distribution + run_id."
        input_schema:
          type: "object"
          properties:
            portfolios:
              description: "JSON array of weight objects"
              type: "string"
            horizon_years:
              description: "Simulation horizon (1-30 years)"
              type: "number"
            num_simulations:
              description: "Number of paths (default 10000)"
              type: "number"
            initial_investment:
              description: "Starting value (default 1000000)"
              type: "number"
            expected_return_pct:
              description: "Override annual return %. Omit to use historical mean."
              type: "number"
            monthly_contribution:
              description: "Monthly DCA amount (default 0)"
              type: "number"
            contribution_growth_pct:
              description: "Annual contribution growth % (default 0)"
              type: "number"
          required:
            - portfolios
            - horizon_years
    - tool_spec:
        type: "generic"
        name: "run_attribution"
        description: "Execute Brinson-Fachler attribution. Decomposes active return into allocation, selection, interaction by sector."
        input_schema:
          type: "object"
          properties:
            portfolio_name_or_id:
              description: "Full SAM portfolio name, e.g. SAM Global Flagship Multi-Asset, or numeric portfolio ID. Names are matched exactly: map aliases such as Flagship or Tech to the full name with the portfolio name mapping first."
              type: "string"
            benchmark_id:
              description: "Benchmark ID (e.g. 'SP500', 'MSCI_ACWI')"
              type: "string"
            start_date:
              description: "Start date YYYY-MM-DD"
              type: "string"
            end_date:
              description: "End date YYYY-MM-DD"
              type: "string"
          required:
            - portfolio_name_or_id
    - tool_spec:
        type: "generic"
        name: "explain_data_origin"
        description: "Explains data lineage for any analyst field. Pass semantic_view_name and business_term."
        input_schema:
          type: "object"
          properties:
            semantic_view_name:
              type: "string"
              description: "Fully qualified semantic view name (e.g. SAM_DEMO.AI.SAM_PORTFOLIO_VIEW)"
            business_term:
              type: "string"
              description: "Semantic field name in UPPERCASE (e.g. TOTAL_MARKET_VALUE)"
          required:
            - semantic_view_name
            - business_term
  tool_resources:
{common_res}
{analyst_portfolio}
{analyst_impl}
{analyst_attribution}
{analyst_market}
{analyst_insights}
{analyst_signals}
{analyst_research}
{analyst_factor}
{analyst_regime}
{analyst_modelling}
{analyst_results}
{search_events}
{search_sec}
{search_external}
{search_internal}
{pdf_resource}
{explain_resource}
{backtest_resource}
{sensitivity_resource}
{counterfactual_resource}
{backtest_full_resource}
{monte_carlo_resource}
{attribution_run_resource}
  $$;
"""
    session.sql(sql).collect()
