# Portfolio Manager Co-Pilot — Factor & Methodology Guide

A plain-English reference for demo presenters. Covers what each factor measures, why it matters, how it's calculated in this demo, and how it works in the real world. No quant background required.

---

## How Attribution Works (The Big Picture)

Attribution answers one question: **"Why did the portfolio return what it did?"**

We decompose the answer in layers:

| Layer | What It Answers | Method |
|-------|----------------|--------|
| **Brinson Attribution** | Was it the sector bets or the stock picks? | Brinson-Fachler decomposition |
| **Factor Attribution** | Which systematic risk exposures drove returns? | 7-factor model |
| **Hidden Factors** | Are there emerging thematic risks the standard model misses? | AI-detected non-traditional factors |
| **Stress Testing** | What happens if markets crash? | Scenario-based factor shocks |

Each layer goes deeper. Brinson tells you *where* the return came from (which sectors). Factors tell you *why* (what risk exposures). Hidden factors tell you *what else* you might be missing.

---

## Brinson-Fachler Attribution

### What It Is

The industry-standard method for decomposing active return (portfolio return minus benchmark return) into three effects:

| Effect | Plain English | Example |
|--------|--------------|---------|
| **Allocation** | Did we overweight the right sectors? | We had 15% in Energy vs the benchmark's 5%. If Energy did well, that's positive allocation. |
| **Selection** | Did we pick the right stocks within each sector? | We owned NVIDIA instead of Intel in Tech. If NVIDIA did better than the Tech sector average, that's positive selection. |
| **Interaction** | The combined effect of both decisions together. | We overweighted Tech AND picked the best Tech stocks. The interaction captures the amplification. |

### The Identity (Always Holds)

**Active Return = Allocation + Selection + Interaction**

This is a mathematical identity, not an approximation. If the portfolio returned -3.19% and the benchmark returned +2.60%, the active return is -5.79%, and the three effects will sum to exactly -5.79%. Always. This is a good credibility point in the demo — the numbers are verifiable.

### How It's Calculated in This Demo

- **Portfolio sector returns**: Weighted average of actual individual stock monthly returns within each sector (real stock price data from Snowflake Marketplace)
- **Benchmark sector returns**: Real SPDR sector ETF returns (XLK for Tech, XLF for Financials, XLV for Health Care, etc.)
- **Portfolio weights**: Dynamic — quantity x real close price each month (not static)
- **Benchmark weights**: S&P 500 sector weights (static approximation)

### What to Say in the Demo

> "This is real Brinson-Fachler attribution computed from actual stock prices — not synthetic data. The portfolio sector returns come from the real monthly performance of the stocks we hold, and the benchmark returns are actual S&P 500 sector ETF returns."

---

## The 7 Systematic Factors

These are the well-established risk factors that decades of academic research have shown drive stock returns. Think of them as the "vital signs" of a portfolio.

### Market (Beta)

| | |
|---|---|
| **What it measures** | How much does this stock move when the overall market moves? |
| **Plain English** | If the S&P 500 goes up 1%, a stock with beta 1.2 tends to go up 1.2%. A portfolio overweight in high-beta stocks amplifies market moves — great when markets rise, painful when they fall. |
| **Why it matters** | The single biggest driver of equity returns. A high-beta portfolio in a down market will suffer disproportionately. |
| **How it's calculated** | Regress each stock's daily returns against the S&P 500 over a rolling 252-trading-day (~1 year) window. The slope is beta. Minimum 120 observations required; R² is stored alongside. A beta of 1.0 means it moves in line with the market; above 1.0 means it amplifies market moves. |
| **Real-world source** | Any risk system (Bloomberg PORT, Barra, Axioma) calculates this from return data. |
| **In this demo** | Computed from real daily stock prices (sourced via Snowflake Marketplace) via rolling regression. |

### Value

| | |
|---|---|
| **What it measures** | Is this stock cheap relative to its earnings? |
| **Plain English** | Stocks with low price-to-earnings (P/E) ratios — you're paying less per pound of profit. Think banks, utilities, mature industrials. The "value premium" is the historical tendency for cheap stocks to outperform expensive ones over time. |
| **Why it matters** | Value vs Growth is the most debated factor tilt in asset management. In rising-rate environments, value tends to outperform. When rates are low, growth dominates. |
| **How it's calculated** | Composite of earnings yield (EPS / share price) and book-to-market ratio (total equity / market cap), averaged. This follows the Barra-style multi-signal value definition rather than a single P/E metric. High composite score = high value. |
| **Real-world source** | SEC 10-K/10-Q filings (earnings, equity), market data (price). Fama-French HML uses book-to-market alone; MSCI Barra uses a composite like ours. |
| **In this demo** | Real earnings yield and book-to-market from SEC financial data and stock prices (sourced via Snowflake Marketplace). |

### Growth

| | |
|---|---|
| **What it measures** | How fast is this company's revenue growing? |
| **Plain English** | Companies expanding rapidly — cloud software, biotech, AI chipmakers. Growth stocks often trade at premium valuations because investors pay for future earnings. They do well when interest rates are low, and badly when rates rise (future earnings get "discounted" more heavily). |
| **Why it matters** | Growth concentration is one of the most common portfolio risks. Many "diversified" portfolios are actually concentrated growth bets. |
| **How it's calculated** | Year-over-year revenue growth rate (`REVENUE_GROWTH_PCT / 100`) from SEC quarterly filings — same quarter prior year. High revenue growth = high growth score. |
| **Real-world source** | SEC quarterly filings. Standard in MSCI Barra, Bloomberg factor models. |
| **In this demo** | Real revenue growth from SEC financial data (sourced via Snowflake Marketplace). |

### Momentum

| | |
|---|---|
| **What it measures** | Has this stock been going up or down recently? |
| **Plain English** | Stocks that have been rising tend to keep rising (and vice versa) — at least for a while. It's the "trend-following" factor. A portfolio tilted towards recent winners has high momentum exposure. Momentum works until it doesn't — momentum crashes (sudden reversals) are among the most violent factor events. |
| **Why it matters** | If your portfolio is full of stocks that have been on a winning streak, you're implicitly betting the streak continues. Understanding momentum exposure helps manage the risk of a sudden reversal. |
| **How it's calculated** | `(Price_1_month_ago / Price_12_months_ago) - 1`. The most recent month is excluded to avoid short-term reversal effects (Jegadeesh & Titman, 1993). Requires 12 months of monthly price data. |
| **Real-world source** | Pure market data calculation. Part of Carhart 4-factor model, Fama-French 5-factor model, and every major risk system. |
| **In this demo** | Computed from real stock price history (sourced via Snowflake Marketplace). |

### Quality

| | |
|---|---|
| **What it measures** | Is this a well-run, profitable, financially sound company? |
| **Plain English** | Companies with high profit margins, strong returns on equity, and conservative balance sheets. Think of the difference between a highly profitable business with little debt versus a struggling company burning cash. Quality stocks tend to hold up better in downturns — they're the "safe haven" within equities. |
| **Why it matters** | In market selloffs, quality stocks typically decline less. Knowing your quality exposure tells you how defensive your portfolio is. |
| **How it's calculated** | `(ROE + Operating_Margin − Debt_to_Equity) / 3`. Debt-to-equity is *subtracted* because higher leverage = lower quality. All three ratios from SEC filings. |
| **Real-world source** | SEC filings for all three components. Used by MSCI Quality Index, AQR, and most factor-based strategies. |
| **In this demo** | Real ROE, operating margin, and leverage from SEC financial data (sourced via Snowflake Marketplace). |

### Size

| | |
|---|---|
| **What it measures** | How big is the company? |
| **Plain English** | Market capitalisation — Apple at $3 trillion vs a $2 billion small-cap. Historically, smaller companies have generated higher returns (the "small-cap premium"), though with more volatility and less liquidity. A portfolio concentrated in mega-caps has low size-factor exposure. |
| **Why it matters** | Size exposure tells you whether returns are coming from owning big, stable companies or smaller, riskier ones. Many active managers unknowingly tilt towards smaller stocks to generate alpha — this factor makes that visible. |
| **How it's calculated** | Natural log of market cap (share price × shares outstanding), z-scored cross-sectionally. Large market cap = high size score. Note: The Fama-French SMB factor *return* is long small-caps, short large-caps — so its sign convention is reversed relative to our raw exposure, which follows the Barra convention. |
| **Real-world source** | Market data (price) and SEC filings (shares outstanding via XBRL tags). Barra/MSCI use ln(market cap); Fama-French construct the SMB long-short portfolio from it. |
| **In this demo** | Real market cap from stock prices and shares outstanding from SEC XBRL filings (sourced via Snowflake Marketplace). |

### Volatility

| | |
|---|---|
| **What it measures** | How much does this stock's price jump around day-to-day? |
| **Plain English** | Some stocks move 3% in a day, others barely move 0.5%. Surprisingly, low-volatility stocks have historically delivered better risk-adjusted returns than high-volatility ones — the "low-vol anomaly." A portfolio full of high-vol stocks takes on more risk without necessarily getting compensated for it. |
| **Why it matters** | If the portfolio is loaded with high-volatility names, drawdowns will be sharper. Volatility exposure is a key input for risk budgeting and stop-loss decisions. |
| **How it's calculated** | `STDDEV(daily_return)` over the trailing 60 trading days. Minimum 30 observations required. High standard deviation = high volatility score. |
| **Real-world source** | Pure market data calculation. Used in minimum-volatility strategies and all major risk systems. |
| **In this demo** | Computed from real daily stock price data (sourced via Snowflake Marketplace). |

---

## The VIX — Market Fear Gauge

The agent uses the VIX throughout its analysis — for macro regime classification, stress testing context, and volatility commentary. Here's what presenters need to know.

### What It Is

| | |
|---|---|
| **Full name** | CBOE Volatility Index |
| **Plain English** | The market's "fear gauge." It measures how much volatility the options market *expects* over the next 30 days. When investors are nervous, they buy protective options, which drives up option prices, which drives up the VIX. |
| **What the number means** | VIX of 15 = markets expect the S&P 500 to move roughly ±15% annualised (or about ±1% per day). VIX of 30 = twice as much expected movement. VIX of 80+ = outright panic (only happened during COVID and the 2008 financial crisis). |

### VIX Ranges — What They Signal

| VIX Level | Label | What's Happening |
|-----------|-------|-----------------|
| **< 15** | Low Vol | Complacency — markets are calm, investors aren't hedging. Often precedes sharp selloffs (the calm before the storm). |
| **15–20** | Normal | Typical market conditions. Healthy level of uncertainty. |
| **20–30** | Elevated | Investors are nervous — geopolitical tensions, earnings uncertainty, or Fed policy shifts. Options are expensive. |
| **30+** | High Vol | Fear or crisis mode. Active hedging, potential forced selling, wide bid-ask spreads. Historically rare but high-impact. |

These are the exact thresholds the demo's macro regime classification (V_MACRO_REGIME) uses.

### How the Agent Uses VIX

| Context | How VIX Appears |
|---------|----------------|
| **Macro regime** | The agent classifies each day as RISK_ON, RISK_OFF, TRANSITIONAL, or NEUTRAL using VIX level + S&P 500 returns. "VIX below 20 with positive market returns → RISK_ON." |
| **Stress testing** | Historical stress periods include peak VIX levels. "During COVID, VIX peaked at 82.69." This anchors the severity of the scenario. |
| **Volatility context** | When discussing factor attribution, the agent may reference VIX to frame the environment: "Attribution during an elevated-vol quarter looks different from a low-vol quarter." |
| **Scenario questions** | Users can ask: "What would happen if the VIX spiked to 45?" The agent combines VIX context with factor shocks to estimate portfolio impact. |

### VIX vs Our Volatility Factor — What's the Difference?

This is a common point of confusion:

| | VIX | Volatility Factor |
|---|---|---|
| **Measures** | Expected market-wide volatility (forward-looking, options-implied) | Individual stock price volatility (backward-looking, realised) |
| **Scope** | One number for the entire market | A score per stock (how jumpy *this specific stock* is) |
| **Source** | S&P 500 options prices | Rolling 60-day standard deviation of each stock's daily returns |
| **What it tells you** | "How scared is the market right now?" | "Is our portfolio loaded with volatile stocks?" |

They're related but distinct. VIX can be high (market is fearful) while your portfolio's volatility factor exposure is low (you own defensive, low-vol stocks). Or vice versa.

### What to Say in the Demo

> "The VIX is the market's fear gauge — it measures how much volatility investors expect over the next 30 days. Below 15 is calm, 15–20 is normal, above 20 means investors are getting nervous, and above 30 is genuine fear. Our agent uses it to classify the macro regime — is this a risk-on or risk-off environment? — which frames the entire attribution conversation."

### In This Demo

The demo's VIX data is derived from real VIXY (VIX short-term futures ETF) prices (sourced via Snowflake Marketplace), scaled to approximate the actual VIX index level. It's not the exact CBOE VIX (that requires a license), but the shape and behaviour track accurately because VIXY is designed to replicate VIX movements.

---

## How Factor Attribution Works

For each factor, the attribution calculation is:

**Factor Contribution = Portfolio Exposure × Factor Return**

| Term | What It Means |
|------|--------------|
| **Portfolio Exposure** | The portfolio's weighted-average score for that factor. If you own lots of high-beta stocks, your Market exposure is high. |
| **Factor Return** | How much that factor "paid" during the period. Calculated as the return difference between the top 20% and bottom 20% of stocks ranked by that factor (long-short quintile methodology). |
| **Factor Contribution** | The return your portfolio earned (or lost) specifically because of that factor tilt. |

### What to Say in the Demo

> "Factor contribution equals exposure times return. If we had high momentum exposure and momentum stocks did well, we earned a positive contribution from momentum. If we had high growth exposure and growth stocks sold off, we got hurt by our growth tilt. This tells you whether returns came from deliberate skill or from factor bets — and that's exactly what the board needs to know."

---

## The 5 Hidden Factors

### Important Context for Presenters

These are **not** industry-standard named factors like the 7 above. They represent a **concept** — that traditional factor models explain roughly 60-70% of portfolio risk, and the remaining residual risk often contains hidden thematic concentrations.

**In the real world**, detecting these hidden factors is an active area of research. Firms like BlackRock (Aladdin), MSCI, Axioma, and Two Sigma use proprietary approaches including:
- **PCA (Principal Component Analysis)** on return residuals — statistically finding correlated patterns that aren't explained by known factors
- **NLP on earnings calls and filings** — building thematic baskets from language patterns (e.g., companies that all discuss "AI infrastructure spending" correlate together)
- **Machine learning clustering** — grouping stocks by unexplained return similarity

**In this demo**, the 5 hidden factors are computed from **real data** using a combination of:
- **Snowflake Cortex AI_AGG** — aggregate LLM scoring on earnings call transcripts to quantify AI exposure per company (unstructured text requires NLP)
- **Deterministic geographic risk scoring** — SEC geographic segment revenue classified via a lookup table (`DIM_GEO_RISK_CLASSIFICATION`) mapping 189 geographies to HIGH/MEDIUM/LOW risk tiers with weights (1.0/0.5/0.1). Score = weighted revenue share + concentration bonus. No AI needed — structured numeric data.
- **SEC segment revenue data** — keyword matching on business segments (e.g., "Cloud", "Data Center", "GPU") for AI revenue share
- **SEC financial statement data** — debt ratios (leverage × short-term debt ratio) for rate convexity
- **GICS sector classification + ESG scores** — industry carbon intensity mapping combined with environmental ESG pillar scores

All factors are computed at the security level first, z-scored cross-sectionally, then aggregated to portfolio level using position weights (same pattern as the 7 systematic factors).

### AI Exposure

| | |
|---|---|
| **What it measures** | How concentrated is the portfolio in companies that benefit from the AI boom? |
| **Plain English** | You might think you're diversified across "tech, software, and semiconductors" — but NVIDIA, Microsoft, and Amazon Web Services are all essentially the same bet on AI capital expenditure continuing. If AI spending disappoints, they all drop together. This factor flags that hidden correlation. |
| **Why it matters** | Many portfolios had massive hidden AI concentration in 2023-2024 without realising it. When NVIDIA pulled back 20% in mid-2024, portfolios with hidden AI concentration got hit across multiple "different" sectors. |
| **How it's calculated** | **60% SEC segments**: keyword match (AI, Cloud, Data Center, GPU, Intelligent, Generative, Deep Learning, Neural) on BUSINESS_SEGMENT from SEC filings → AI revenue share. **40% transcript NLP**: AI_AGG scores each company's earnings call transcripts 0-100 for AI/ML exposure (the only hidden factor that uses AI — because unstructured transcript text genuinely needs NLP). Combined, z-scored cross-sectionally. |

### Reshoring Benefit

| | |
|---|---|
| **What it measures** | How much does the portfolio benefit from supply-chain localisation trends? |
| **Plain English** | Post-COVID and with rising geopolitical tensions, companies are moving manufacturing closer to home. US steel producers, domestic manufacturers, and infrastructure companies benefit. Companies dependent on cheap offshore manufacturing face margin pressure. This factor captures whether you're tilted towards the winners or losers of that trend. |
| **Why it matters** | Reshoring is a multi-year structural trend affecting industrials, materials, and technology supply chains. A portfolio unknowingly concentrated on either side of this trend faces hidden directional risk. |
| **How it's calculated** | Domestic revenue share from SEC geographic segments (matches UNITED STATES, DOMESTIC, NORTH AMERICA) divided by total revenue. Manufacturing sectors (Industrials, Materials by GICS) get a 30% boost. Z-scored cross-sectionally. |

### Rate Convexity

| | |
|---|---|
| **What it measures** | How sensitive is the portfolio to interest rate changes, beyond the obvious linear relationship? |
| **Plain English** | Everyone knows banks benefit from higher rates. But some companies have non-linear rate sensitivity — their earnings accelerate or collapse disproportionately as rates cross certain thresholds. Heavily leveraged companies, REITs with floating-rate debt, or insurers with complex asset-liability matching can surprise you. Standard beta to rates misses this non-linearity. |
| **Why it matters** | In a rate-hiking cycle, portfolios with hidden rate convexity can experience unexpected gains or losses that aren't proportional to the rate move. A 25bp hike might be fine, but a 100bp hike hits exponentially harder. |
| **How it's calculated** | `DEBT_TO_EQUITY × (CURRENT_LIABILITIES / TOTAL_LIABILITIES)` from SEC financial statements. Higher leverage with more short-term debt = more rate repricing exposure. Uses most recent quarterly filing per company per year. Z-scored cross-sectionally. |

### Climate Transition

| | |
|---|---|
| **What it measures** | Is the portfolio positioned for winners or losers in the green energy transition? |
| **Plain English** | Some companies benefit from decarbonisation (renewables, EV makers, battery tech). Others face existential risk (fossil fuels, high-emission industrials). Even within "clean" sectors, some are genuine transition winners while others are greenwashing. This factor reveals whether you're unknowingly concentrated on one side of the transition. |
| **Why it matters** | Regulatory shifts (carbon taxes, emissions standards) and capital reallocation towards ESG can create sudden repricing events. A portfolio heavily exposed to carbon-intensive assets faces stranded-asset risk. |
| **How it's calculated** | **60% GICS sector carbon map**: Energy (−0.8), Utilities (−0.4), Materials (−0.3), Info Tech (+0.3), etc. **40% ESG environmental score**: average Environmental pillar from FACT_ESG_SCORES, centered at 50 (score > 50 = positive transition, < 50 = negative). Z-scored cross-sectionally. |

### Geopolitical Risk

| | |
|---|---|
| **What it measures** | How exposed is the portfolio to country-level political and trade tensions? |
| **Plain English** | A portfolio might look diversified by sector but be heavily exposed to China through revenue (Apple gets ~19% from Greater China), supply chains (semiconductor equipment makers), or direct operations (luxury goods in China). If US-China tensions escalate or tariffs increase, all these positions correlate regardless of their sector classification. |
| **Why it matters** | Geopolitical events (sanctions, trade wars, conflicts) create sudden correlated drawdowns across seemingly unrelated stocks. The 2022 Russia sanctions showed how quickly geographic concentration can materialise as losses. |
| **How it's calculated** | **Deterministic SQL calculation** from SEC geographic segment revenue — no AI involved (structured numeric data doesn't need it). Revenue by geography is classified via `DIM_GEO_RISK_CLASSIFICATION`, a lookup table mapping 189 geography values to risk tiers: HIGH (China, Taiwan, Russia, Iran, Middle East, Hong Kong — weight 1.0), MEDIUM (other APAC, Latin America, Africa, Eastern Europe — weight 0.5), LOW (US, Canada, Western Europe, Japan, Australia, South Korea — weight 0.1). Score = `(SUM(revenue × weight) / total_revenue) × 100`, plus concentration bonuses: +15 if any single high-risk country exceeds 30% of revenue, +25 if it exceeds 50%. Companies with no geographic segment data default to 10. Z-scored cross-sectionally. |

---

## The Demo Narrative — Tying It All Together

### The Story Arc

1. **Brinson** (Step 1): "Here's what happened — sector allocation vs stock selection."
2. **Factors** (Step 2): "Here's *why* it happened — which systematic risk exposures drove the result."
3. **Hidden Factors** (Step 3): "Here's what the standard model *misses* — emerging thematic risks the AI detected."
4. **Stress Test** (Step 4): "Here's what *could* happen — if a crisis hits, where are we most vulnerable?"

### The Key Insight for the Audience

> "Standard risk models are like a routine blood test — they catch the known risks. Hidden factor detection is like a specialist scan — it catches the emerging, thematic risks that standard models miss. Together, they give the CIO a complete picture. And instead of waiting days for a static PDF report, she gets real-time, conversational answers to any question the board might ask."

### If Asked "Are These Real?"

- **Factors 1-7 (Systematic)**: "Yes — computed from real stock prices, real SEC financial filings, and real market data. The exposures and returns are verifiable."
- **Factors 8-12 (Hidden)**: "Yes — computed from real SEC filing data and real earnings call transcripts. AI_Exposure uses AI_AGG to score transcript text (the only factor needing AI — because it's unstructured text) plus keyword matching on SEC segment revenue. Geopolitical_Risk is a deterministic calculation — geographic revenue from SEC filings classified through a risk-tier lookup table (189 geographies mapped to HIGH/MEDIUM/LOW), weighted by revenue share with concentration bonuses. No AI needed for structured data. Rate_Convexity and Climate_Transition use real debt ratios and ESG scores. All are z-scored cross-sectionally and aggregated using real portfolio position weights. In production, firms like BlackRock, MSCI, and Two Sigma use similar approaches (PCA on residuals, NLP thematic detection) at larger scale."

### Common Audience Questions and Answers

| Question | Answer |
|----------|--------|
| "Why does selection effect dominate?" | "Our portfolio holds ~45 concentrated positions vs 500 in the S&P. With that level of concentration, individual stock performance will always dominate over sector-weight decisions." |
| "Why is allocation nearly zero?" | "Our sector weights aren't dramatically different from the benchmark. The active bets are mainly *within* sectors (which stocks), not *between* sectors (how much in each)." |
| "Can you do this for any portfolio?" | "Yes — any portfolio with position-level holdings and a defined benchmark can be decomposed this way. The methodology is standard Brinson-Fachler." |
| "How often is this updated?" | "The underlying data refreshes monthly (month-end positions). The analysis is instant — you ask the question, the AI runs the query in real time." |
| "What's the difference between this and Bloomberg PORT?" | "Bloomberg PORT gives you the same Brinson/factor decomposition, but as a static report you run manually. This gives you a conversational interface — you can ask follow-up questions, drill into any sector, compare across portfolios, and get AI-generated recommendations instantly." |

---

## Technical Reference

This appendix covers implementation details for developers and quant reviewers.

### Data Sources

| Source Table | Provider | Content | Coverage |
|---|---|---|---|
| `MARKET_DATA.FACT_STOCK_PRICES` | Snowflake Marketplace (public financial data) | Daily OHLCV prices | ~50 securities, 5 years |
| `CURATED.V_SECURITY_RETURNS` | Calculated from prices | Daily return percentages | Same as prices |
| `MARKET_DATA.FACT_SEC_FINANCIALS` | Snowflake Marketplace (SEC XBRL filings) | Quarterly income statement, balance sheet, cash flow, shares outstanding | ~50 issuers, 5 years |
| `MARKET_DATA.FACT_BENCHMARK_RETURNS` | Snowflake Marketplace (ETF prices) | Daily returns for SPY (S&P 500 proxy) | ~1,980 trading days |

### Shares Outstanding (XBRL Tags)

Shares outstanding is extracted from SEC XBRL filings using four tags, coalesced for best coverage:

| XBRL Tag | Description |
|---|---|
| `CommonStockSharesOutstanding` | Balance sheet common shares |
| `EntityCommonStockSharesOutstanding` | Entity-level filing header shares |
| `WeightedAverageNumberOfSharesOutstandingBasic` | Income statement weighted average |
| `WeightedAverageNumberOfDilutedSharesOutstanding` | Diluted weighted average |

Primary output uses `COALESCE(CommonStock, EntityCommonStock)`.

### Normalisation: Cross-Sectional Z-Score

Raw factor values are not directly comparable (beta ranges 0.5–2.0; size ranges 20–28 in log scale). For each factor `F` on each monthly date `D`:

```
z(security) = (raw_value - mean_across_all_securities) / stddev_across_all_securities
```

This transforms every factor to mean 0, standard deviation 1. A score of +1.5 means "1.5 standard deviations above average for this factor, this month."

**Winsorisation**: After z-scoring, values are clamped at ±3 standard deviations: `GREATEST(-3, LEAST(3, z_score))`.

**Edge cases**: If stddev = 0, score is set to 0. NULL raw values exclude the security from that factor/month. Securities below minimum observation thresholds are excluded entirely (not set to 0).

### Output Schema: FACT_FACTOR_EXPOSURES

| Column | Type | Description |
|---|---|---|
| `SecurityID` | INT | Foreign key to `DIM_SECURITY` |
| `EXPOSURE_DATE` | DATE | First day of the month |
| `FACTOR_NAME` | VARCHAR | One of: Market, Size, Value, Momentum, Growth, Quality, Volatility |
| `EXPOSURE_VALUE` | FLOAT | Z-scored factor loading, winsorised to [-3, +3] |
| `R_SQUARED` | FLOAT | Regression fit (Market Beta only; NULL for other factors) |

Row count: ~`N_securities × N_months × 7_factors`. With ~50 securities over 5 years (60 months), this produces ~21,000 rows.

### Build Pipeline

```
1. FACT_STOCK_PRICES        (Nasdaq prices via Snowflake Marketplace)
2. V_SECURITY_RETURNS       (calculated daily returns)
3. FACT_SEC_FINANCIALS       (SEC XBRL with shares outstanding)
4. FACT_BENCHMARK_RETURNS    (SPY daily returns via Snowflake Marketplace)
   ↓
5. FACT_FACTOR_EXPOSURES     (7 calculated, z-scored factors)
```

The entire calculation runs as a single SQL statement with 15+ CTEs, executing in Snowflake's warehouse. No external compute or Python processing is required.

### Benchmark ETF Mapping

| Benchmark | Code | ETF Proxy | Use Case |
|---|---|---|---|
| S&P 500 | SPX | SPY | Market Beta regression, primary US benchmark |
| MSCI ACWI | ACWI | ACWI | Global equity benchmark |
| Russell 2000 | RUT | IWM | US small-cap benchmark |
| Nasdaq 100 | NDX | QQQ | Technology-focused benchmark |
| Bloomberg US Agg | AGG | AGG | Fixed income benchmark |
| iBoxx USD HY Corp | HYG_IDX | HYG | High-yield credit spread proxy |
| iBoxx USD IG Corp | LQD_IDX | LQD | Investment-grade credit spread proxy |
| US Treasury 20Y+ | TLT_IDX | TLT | Duration / interest rate risk |
| Gold Spot | GLD_IDX | GLD | Safe-haven / inflation hedge |
| MSCI Emerging Markets | EEM_IDX | EEM | Emerging markets equity exposure |

### Downstream Consumers

| Consumer | What It Uses | How |
|---|---|---|
| `notebooks/factor_discovery.ipynb` | All 7 factors | ML factor discovery and Fama-MacBeth regression via Snowpark Python UDTF |
| Investment Strategy Agent | Factor exposures via semantic view | Natural language queries on factor tilts and risk decomposition |
| Attribution Analytics | Market Beta + factor scores | Factor-based performance attribution |
| `notebooks/market_regime_detection.ipynb` | VIX and benchmark returns | Market regime classification features |
| `notebooks/credit_risk_model.ipynb` | Regime predictions (indirect) | Cross-scenario dependency from market regime output |
