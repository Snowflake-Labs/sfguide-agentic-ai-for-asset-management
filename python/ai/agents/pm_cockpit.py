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
- Precision: Attribution effects to 2 decimal places (basis points), percentages to 1 decimal, currency in millions
- Data Freshness: Always include "As of DD MMM YYYY market close"

Presentation:
- Tables: Use for holdings lists (>4 securities), attribution breakdowns, sector analysis
- Bar Charts: Use for sector allocation, attribution waterfall
- Line Charts: Use for performance trends, cumulative returns, factor contribution paths

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
- Attribution report generation (multi-audience) -> load attribution-report-generator skill
- Counterfactual what-if (benchmark weights, weight cap) -> load counterfactual-analysis skill
- Anomaly scan, risk flags, factor drift -> load attribution-anomaly-scan skill
- Stress test, crisis simulation -> load stress-scenario-analysis skill
- Concentration risk analysis -> load concentration-risk-assessment skill
- Implementation planning (trading costs, timelines) -> load implementation-planning skill
- PDF report generation -> load pdf-report-generation skill
- Portfolio name resolution -> load portfolio-name-resolution skill
- Audience adaptation (board/PM/client) -> load audience-adaptive-narrative skill
- Data lineage queries -> load data-lineage-explanation skill
- Portfolio construction, build allocation, create proposal, design portfolio -> load portfolio-construction skill
- Historical backtest of portfolio weights -> load historical-backtest skill
- Monte Carlo simulation, probability analysis, forward projection -> load monte-carlo-simulation skill
- Portfolio optimization, efficient frontier, max Sharpe, min variance -> load portfolio-optimizer skill

Direct Data Queries (no skill needed):
1. Portfolio holdings, weights, sectors, ESG, compliance alerts -> portfolio_analyzer
2. Implementation planning (trading costs, liquidity, settlement) -> implementation_analyzer
3. Attribution decomposition (Brinson, factor, hidden, anomaly, peer, currency, rolling) -> attribution_analyzer
4. Market regime, stress scenarios, yields, stock prices, macro data -> market_analyzer
5. Proactive insights and alerts -> insights_analyzer
6. Company research (SEC financials, segments, revenue analysis) -> research_analyzer
7. Earnings call transcripts -> search_company_events
8. SEC filing text (MD&A, risk factors) -> search_sec_filings
9. Broker research and press releases -> search_external_docs
10. Internal policies and templates -> search_internal_docs
11. Backtest portfolio against historical stress period -> backtest_historical_stress
12. What-if scenario sensitivity (rate shocks, vol spikes) -> scenario_sensitivity
13. Counterfactual analysis (alternative weightings) -> run_counterfactual
14. Data lineage -> explain_data_origin (map tool to semantic view, pass field name)
15. Factor model and ML predictions (XGBoost, SHAP) -> factor_model_analyzer
16. Market regime classification (RISK_ON/TRANSITIONAL/RISK_OFF) -> regime_analyzer
17. Model portfolios, risk factors, covariance -> portfolio_modelling_analyzer
18. Detailed run results (timeseries, paths) -> tool_results_analyzer (use AFTER run_backtest/run_monte_carlo)
19. Full historical backtest with custom weights -> run_backtest
20. Monte Carlo simulation (paths, terminal distribution) -> run_monte_carlo
21. Brinson-Fachler attribution execution -> run_attribution

Tool-to-Semantic-View Mapping (for explain_data_origin):
- portfolio_analyzer -> SAM_DEMO.AI.SAM_PORTFOLIO_VIEW
- implementation_analyzer -> SAM_DEMO.AI.SAM_IMPLEMENTATION_VIEW
- attribution_analyzer -> SAM_DEMO.AI.SAM_ATTRIBUTION_VIEW
- market_analyzer -> SAM_DEMO.AI.SAM_MARKET_VIEW
- research_analyzer -> SAM_DEMO.AI.SAM_RESEARCH_VIEW

Key guidance:
- portfolio_analyzer covers: holdings, AUM, sector allocation, benchmark comparison, ESG scores, compliance alerts, factor exposures, supply chain dependencies
- implementation_analyzer covers: trading costs, market impact, liquidity, settlement, risk limits, tax implications
- attribution_analyzer covers: Brinson (allocation/selection/interaction), factor attribution (7 factors), hidden factors (5 AI-discovered), rolling analytics (drift/paths), anomalies (8 types), peer learning (alpha persistence), currency decomposition, linked multi-period (QTD/YTD)
- market_analyzer covers: VIX regime, stress scenarios, historical crises, treasury yields, stock prices, policy rates, FX rates, economic indicators

Error Handling:
Scenario 1: Portfolio Name Not Recognised
User Message: "Portfolio not found. Available SAM portfolios: [list]. Did you mean one of these?"

Scenario 2: No Holdings Data
User Message: "No holdings data found for this date. Data refreshes daily at 6 PM ET."

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
    counterfactual_resource = build_generic_tool_resource("run_counterfactual", "RUN_COUNTERFACTUAL_ANALYSIS", "RUN_COUNTERFACTUAL_ANALYSIS(VARCHAR, VARCHAR, VARCHAR, VARCHAR)", database_name, timeout=60)
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
  FROM SPECIFICATION
  $$
  models:
    orchestration: {config.AGENT_ORCHESTRATION_MODEL}
  orchestration:
    budget:
      seconds: {config.AGENT_BUDGET_SECONDS}
      tokens: {config.AGENT_BUDGET_TOKENS}
  instructions:
    system: "You are a portfolio management specialist at a UK-based asset management firm. You analyse portfolio holdings, performance attribution, risk metrics, and market conditions."
    response: "{response_formatted}"
    orchestration: "{orchestration_formatted}"
    sample_questions:
      - question: "What are the top holdings in SAM Technology & Infrastructure?"
        answer: "I will show the largest positions by market value with sector and weight."
      - question: "Break down the attribution by sector for the most recent quarter"
        answer: "I will decompose returns into allocation, selection, and interaction effects by sector."
      - question: "Run an anomaly scan across all portfolios"
        answer: "I will check for factor drift, concentration, and style inconsistency alerts."
      - question: "What is the current macro regime?"
        answer: "I will check VIX levels and classify the current market regime."
{skills_yaml}
  tools:
{common_tool_specs()}
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "portfolio_analyzer"
        description: "Portfolio holdings, weights, sectors, ESG scores, benchmark comparison, compliance alerts, factor exposures, supply chain dependencies. 11 portfolios, 14,000+ securities."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "implementation_analyzer"
        description: "Trading costs, market impact, liquidity, settlement, risk limits, tax implications for execution planning."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "attribution_analyzer"
        description: "Performance attribution: Brinson (allocation/selection/interaction by sector/country/industry), factor attribution (7 factors), hidden factors (5 AI-discovered), rolling analytics (drift tracking), anomaly detection (8 risk alert types), peer learning (alpha persistence), currency decomposition, linked multi-period (QTD/YTD/12M)."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "market_analyzer"
        description: "Market context: VIX regime classification, stress scenarios (10 crisis simulations), historical stress periods, US Treasury yield curve (14 maturities), stock prices (865+ tickers), policy rates (73 countries), FX rates, US economic indicators, country emissions."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "insights_analyzer"
        description: "Proactive AI insights and alerts generated by automated tasks: daily briefings, anomaly alerts, position change insights."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "signals_analyzer"
        description: "AI-detected portfolio signals with urgency scoring, impact estimates in basis points, and confidence levels. Sources: price drops, volume spikes, regime changes, compliance breaches, ESG downgrades, insider clusters, institutional exits, factor drift, attribution anomalies, transcript NLP, SEC risk factor changes. Query by urgency (immediate/today/this_week), signal_type (risk_alert/compliance/thesis_challenge), or entity_name."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "research_analyzer"
        description: "Company research: SEC financials, segment breakdowns, revenue/margin analysis, comparable company data. Use for fundamental research on holdings."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "factor_model_analyzer"
        description: "Factor model data: XGBoost ML predictions, SHAP feature importance, Fama-French factor loadings, stock-level expected returns, and factor exposures across portfolios."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "regime_analyzer"
        description: "Market regime classifications (RISK_ON, TRANSITIONAL, RISK_OFF) with VIX context, historical regime periods, and regime-aware allocation recommendations."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "portfolio_modelling_analyzer"
        description: "Model portfolios, risk factors (Fama-French), expected returns, covariance matrices, and saved backtest/simulation results."
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
              description: "Portfolio name or numeric ID. Partial names work."
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
              description: "Portfolio name or ID."
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
              description: "Portfolio name or numeric ID"
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
              description: "Start date YYYY-MM-DD"
              type: "string"
            end_date:
              description: "End date YYYY-MM-DD"
              type: "string"
            rebalance_freq:
              description: "daily, monthly, quarterly, annually"
              type: "string"
          required:
            - portfolios
            - start_date
            - end_date
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
              description: "Portfolio name or ID"
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
