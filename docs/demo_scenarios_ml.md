# SAM Demo - ML Development Walkthrough Scenarios

Notebook-based demo scenarios for the Data Scientist persona. Each section walks through a complete Snowflake ML lifecycle demonstrated interactively in a Jupyter notebook.

> **Note**: ML Development scenarios are notebook-based (not agent-based). Skills and code execution are used by the agent layer that consumes ML outputs (see investment_strategy, portfolio_modelling_copilot, private_credit scenarios).

---

## Market Regime Detection - ML Development Walkthrough

### Business Context Setup

**Persona**: Dr. Priya Sharma, Lead Data Scientist at Simulated Asset Management
**Business Challenge**: The CIO has asked Dr. Sharma to replace the rule-based market regime classification (VIX threshold approach in `V_MACRO_REGIME`) with a proper ML-based model. The current approach uses hardcoded VIX bands (< 15, 15-20, 20-30, > 30) which fails to capture cross-asset dynamics and produces noisy regime transitions. She needs to demonstrate to the quant team how to build, register, and deploy the model using Snowflake's ML stack — all without moving data out of Snowflake.

**Notebook**: `notebooks/market_regime_detection.ipynb`
**Snowflake ML Features Showcased**: Feature Store, Experiment Tracking, Model Registry, Model Monitor, ML Pipeline (DAG API), Batch Inference

### Demo Flow

#### Step 1: Feature Engineering with Feature Store

**Presenter Transition**:
> "Let me start by showing how we create managed features in Snowflake. Notice how registering a FeatureView automatically creates a Dynamic Table — no separate DDL needed."

**What Happens**:
- Create Entity `MARKET_DATE` with join key `DATE`
- Build feature SQL joining `FACT_VIX_DAILY`, `FACT_BENCHMARK_RETURNS`, and `FACT_SECTOR_RETURNS`
- Features computed: VIX level/trend, realised volatility (20D/60D), momentum (20D/60D), sector dispersion, vol risk premium
- Register FeatureView `REGIME_FEATURES` with `refresh_freq='1 day'`

**Talking Points**:
- Feature Store provides point-in-time correctness — no data leakage
- FeatureView registration auto-creates a Dynamic Table that refreshes daily
- Features are reusable across models (credit risk and factor workflows will reference regime state)

**Key Features**: Feature Store, Dynamic Tables (auto-created via FeatureView)

#### Step 2: Training the Regime Model

**Presenter Transition**:
> "Now we have our features materialised. Let me show you how we train the model without leaving Snowflake..."

**What Happens**:
- Retrieve training data via `fs.generate_training_set()`
- Fit Gaussian Mixture Model (3 components) from scikit-learn
- Label clusters by mean VIX: lowest → RISK_ON, middle → TRANSITIONAL, highest → RISK_OFF
- Visualise clusters via PCA projection and regime timeline
- Compute transition probability matrix
- Log all params and metrics via `ExperimentTracking`

**Talking Points**:
- GMM captures the probabilistic nature of regimes (soft cluster assignments)
- 3 regimes align with investment intuition: risk-on, transitional, risk-off
- Transition matrix shows regime persistence and switching probabilities

**Key Features**: Experiment Tracking (params, metrics), Notebooks on Container Runtime (visualisation)

#### Step 3: Logging to Model Registry

**Presenter Transition**:
> "The model looks good. Now let me register it so the whole team can use it and we can track versions..."

**What Happens**:
- Wrap scaler + GMM in sklearn Pipeline
- `registry.log_model()` with `target_platforms=['WAREHOUSE']` (enables SQL inference)
- Log metrics: silhouette score, BIC, AIC, cluster sizes
- Demonstrate versioning

**Talking Points**:
- `target_platforms=['WAREHOUSE']` means we can call this model from SQL: `MODEL()!predict()`
- Metrics are tracked alongside the model version for comparison
- The registry provides full lineage: who trained it, when, with what data

**Key Features**: Model Registry (versioning, metrics, lineage)

#### Step 4: Setting Up ML Observability

**Presenter Transition**:
> "We need to know when the model starts degrading. Let me set up monitoring..."

**What Happens**:
- Create baseline table from training predictions
- `CREATE MODEL MONITOR` with:
  - Source: `FACT_REGIME_PREDICTIONS`
  - Refresh interval: 1 day
  - Baseline: training data for drift comparison
- Show drift query: `MODEL_MONITOR_DRIFT_METRIC()` for PSI/KL divergence
- Show stat query: `MODEL_MONITOR_STAT_METRIC()` for feature distributions

**Talking Points**:
- Model Monitor is fully managed — no external tools needed
- PSI and KL divergence detect when input distributions shift
- Automated refresh means monitoring happens without manual intervention

**Key Features**: Model Monitor (native drift detection, automated refresh, PSI/KL metrics)

#### Step 5: Deploying the ML Pipeline

**Presenter Transition**:
> "The model works interactively. Now let me operationalise it so it scores automatically every day..."

**What Happens**:
- Define DAG with `DAGTask` for daily scoring
- Scoring uses `MODEL()!predict()` SQL syntax against the FeatureView
- Deploy pipeline via `DAGOperation.deploy()`

**Talking Points**:
- DAG API replaces raw `CREATE TASK` SQL with a Python-native interface
- The pipeline runs on a schedule (weekdays 07:00 ET) using existing warehouse
- This is how you go from notebook prototype to production in Snowflake

**Key Features**: ML Pipeline Orchestration (DAG API, DAGTask, DAGOperation)

#### Step 6: Validation and Integration

**Presenter Transition**:
> "Let me score the full history and compare against the old rule-based approach..."

**What Happens**:
- Score all historical data and populate `FACT_REGIME_PREDICTIONS`
- Compare ML regimes against `V_MACRO_REGIME` rule-based classifications
- Show regime distribution and directional agreement metrics

**Talking Points**:
- ML model captures regime transitions that VIX thresholds miss
- Probabilistic output (cluster probabilities) gives confidence levels
- The prediction table is now available for downstream use: credit risk, factor models, agent queries

**Key Features**: End-to-end pipeline validation, agent integration readiness

---

## Predictive Credit Risk - ML Development Walkthrough

### Business Context Setup

**Persona**: Dr. Priya Sharma, Lead Data Scientist at Simulated Asset Management
**Business Challenge**: The credit committee has asked Dr. Sharma to build a predictive default model that goes beyond covenant-based monitoring. Current process relies on manual review of financial ratios and covenant headroom — a lagging indicator. She needs a forward-looking probability of default that incorporates financial health, market conditions, and cross-asset signals.

**Notebook**: `notebooks/credit_risk_model.ipynb`
**Snowflake ML Features Showcased**: Feature Store, Experiment Tracking (XGBoost autologging), Model Registry, SHAP Explainability, Model Monitor, ML Pipeline (DAG API)

### Demo Flow

#### Step 1: Feature Engineering with Feature Store

**Presenter Transition**:
> "We start by building borrower-level features. Notice how we combine financial ratios, covenant health, and the market regime output from our earlier model — all managed by the Feature Store."

**What Happens**:
- Create Entity `BORROWER_QUARTER` with composite join keys `[BORROWERID, QUARTER_DATE]`
- Build features from `FACT_CREDIT_BORROWER_FINANCIALS` (leverage, coverage, margins), `FACT_CREDIT_COVENANT_TRACKING` (headroom, breach counts), and `FACT_REGIME_PREDICTIONS` (market regime state)
- Register FeatureView `CREDIT_RISK_FEATURES` with `refresh_freq='1 day'`

**Key Features**: Feature Store, cross-scenario dependency (regime feeds credit risk)

#### Step 2: Training Data Construction

**What Happens**:
- Retrieve training data via `fs.generate_training_set()`
- Construct binary default target: covenant breach OR min headroom < 5%
- Show class distribution (default rate)

**Talking Points**:
- Feature Store guarantees point-in-time correctness — training uses only data available at each quarter
- Binary target approximates default from observable covenant deterioration

#### Step 3: Model Training — XGBoost with Autologging

**Presenter Transition**:
> "Now I train an XGBoost classifier. Watch how the SnowflakeXgboostCallback automatically logs metrics at every boosting round..."

**What Happens**:
- Walk-forward TimeSeriesSplit (3 folds) with XGBoost
- `SnowflakeXgboostCallback` autologs training/validation metrics
- Report AUC and F1 per fold and mean

**Key Features**: Experiment Tracking, `SnowflakeXgboostCallback` autologging

#### Step 4: SHAP Explainability

**Presenter Transition**:
> "The model performs well, but the credit committee needs to understand WHY a borrower is flagged high-risk. Let me show SHAP explanations..."

**What Happens**:
- SHAP beeswarm: portfolio-level feature importance
- SHAP waterfall: individual borrower drill-down
- Top features ranked by mean absolute SHAP value

**Key Features**: SHAP TreeExplainer (individual + portfolio-level)

#### Step 5: Model Registry

**What Happens**:
- `registry.log_model()` with `target_platforms=['WAREHOUSE']`, AUC/F1 metrics
- Model versioned and ready for SQL inference

#### Step 6: ML Pipeline Deployment

**What Happens**:
- DAG API with monthly scoring schedule (1st of month)
- Scoring uses `MODEL()!predict()` against latest FeatureView data

#### Step 7: ML Observability

**What Happens**:
- Create baseline from training predictions
- `CREATE MODEL MONITOR` with drift detection on financial ratio distributions
- Enables automated alerts when input distributions shift (e.g., rising leverage across portfolio)

---

## End-to-End Quant Factor Workflow - ML Development Walkthrough

### Business Context Setup

**Persona**: Dr. James Chen, Quantitative Analyst at Simulated Asset Management
**Business Challenge**: The CTO wants to evaluate whether the team can consolidate their 4 existing vendor tools (factor library, regression engine, ML platform, portfolio optimiser) into Snowflake. Dr. Chen will build the complete workflow from raw data to deployed pipeline in a single Snowflake notebook.

**Notebook**: `notebooks/factor_discovery.ipynb`
**Snowflake ML Features Showcased**: Feature Store, UDF, UDTF, Cortex AI Functions (`ai_sentiment`), Experiment Tracking (XGBoost autologging), Model Registry, SHAP, Model Monitor, ML Pipeline (DAG API), Portfolio Optimisation

### Demo Flow

#### Step 1: Factor Construction with Feature Store (Phase 1)

**Presenter Transition**:
> "One line of code creates a managed, auto-refreshing feature pipeline."

**What Happens**:
- Create `ZSCORE_NORMALIZE` UDF for cross-sectional normalisation
- Build 12 factors: 5 from `FACT_FACTOR_EXPOSURES` (value, size, quality, growth, momentum), momentum (1M/3M/12M) + volume + market cap from `FACT_STOCK_PRICES`, and 6 fundamentals: volatility (stddev of returns), beta (vs SPX), leverage (D/E), profitability (ROE), earnings revision (QoQ EPS), dividend yield (trailing 12M) from `V_SECURITY_RETURNS`, `FACT_SEC_FINANCIALS`, `FACT_BENCHMARK_RETURNS`, `FACT_DIVIDENDS`
- Entity `SECURITY` (with desc) with join key `SECURITYID`
- 3 domain-specific FeatureViews: `SECURITY_MARKET_FACTORS` (daily, 4 features), `SECURITY_FUNDAMENTAL_FACTORS` (60 days, 8 features), `SECURITY_SENTIMENT_FACTORS` (weekly, 5 NLP features) — each with timestamped versioning + detailed feature-level documentation

**Key Features**: Feature Store (Entity desc, FeatureView versioning), UDF, Dynamic Tables (auto-created)

#### Step 1.5: NLP Sentiment from Earnings Transcripts

**Presenter Transition**:
> "Traditional factors capture price and fundamental signals. Can unstructured text add marginal alpha?"

**What Happens**:
- Use Snowpark `ai_sentiment()` with quant-relevant categories (guidance, margins, growth, risk) on `COMPANY_EVENT_TRANSCRIPTS_RAW`
- Function returns categorical labels per category — encode to numeric: positive=+1, negative=-1, neutral/mixed=0
- Flatten category array, pivot to 5 columns, aggregate to monthly per-security scores
- Sentiment flows directly into `factor_df` (no intermediate table) — `AI_SENTIMENT` is supported in DT SELECT clauses, so the FeatureView DT will re-score on refresh. 17 base features (12 quant + 5 NLP)
- **Derived Features FeatureView** (`SECURITY_DERIVED_FEATURES`): 4 interaction features (momentum/value ratio, quality×growth, sentiment×momentum, factor dispersion) read from base FV's managed DT
- **Forward Return FeatureView** (`SECURITY_FORWARD_RETURNS`): 21-day forward return as separate target FV (prevents train/serve skew)
- **DT Health Check**: Monitor refresh status and staleness of all FeatureView DTs

**Key Features**: Cortex AI Functions (`ai_sentiment` with categories), Snowpark DataFrame API (flatten, VARIANT access)

#### Step 2: Cross-Sectional Factor Model (Phase 2)

**Presenter Transition**:
> "We have our factor scores. Now let's estimate which factors generate returns using a Fama-MacBeth regression..."

**What Happens**:
- Register `FAMA_MACBETH_REGRESSION` UDTF via `session.udtf.register()` (Python, numpy + pandas)
- Run cross-sectional regressions per month
- Visualise: cumulative factor returns, Sharpe ratios

**Key Features**: UDTF (`session.udtf.register()`), Snowpark DataFrames, `join_table_function()`

#### Step 3: ML Factor Discovery (Phase 3)

**Presenter Transition**:
> "Linear regressions capture the big picture, but markets aren't linear. Let me show you what ML finds..."

**What Happens**:
- Retrieve unified feature matrix from Feature Store (`generate_training_set()` with 3 FeatureViews) — 21 features (12 quant + 5 NLP + 4 derived)
- Walk-forward XGBoost training with `SnowflakeXgboostCallback`
- SHAP beeswarm for non-linear factor importance
- Report Information Coefficient (IC) across folds
- **SHAP before/after comparison**: train second model without sentiment features, compare IC uplift and SHAP rankings — answers whether NLP adds marginal alpha
- **Leakage Validation**: Timestamp-based check ensuring no future data in training set

**Key Features**: Experiment Tracking, SHAP, Feature Store training sets, data leakage prevention

#### Step 4: Model Registration (Phase 3)

**What Happens**:
- `registry.log_model()` with `target_platforms=['WAREHOUSE']`, IC and turnover metrics

#### Step 5: Portfolio Construction (Phase 4)

**Presenter Transition**:
> "Now let's turn these ML insights into an actual portfolio..."

**What Happens**:
- Mean-variance optimisation with ML-predicted returns and factor covariance
- Efficient frontier calculation
- Top holdings and portfolio risk metrics
- Write optimal weights to `FACT_OPTIMAL_PORTFOLIO`

**Key Features**: scipy.optimize, portfolio analytics

#### Step 6: ML Observability

**What Happens**:
- `CREATE MODEL MONITOR` for factor score drift (PSI on distributions)
- IC trend tracking via `MODEL_MONITOR_PERFORMANCE_METRIC()`

#### Step 7: Pipeline Deployment

**Presenter Transition**:
> "Everything works interactively. Now the crucial step — how do we make this run automatically every month?"

**What Happens**:
- DAG API with monthly schedule (1st of month)
- End-to-end pipeline: factor refresh -> model scoring -> portfolio rebalance

**Key Features**: ML Pipeline Orchestration (DAG API)
**This is the climax of the demo — showing Snowflake replaces 4 vendor tools**
