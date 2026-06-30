# SAM Demo - PM Cockpit Scenarios

**Scenario**: `pm_cockpit`
**Agent**: `AM_portfolio_manager_copilot`
**Demo Surfaces**: Snowflake Intelligence, PM Cockpit (SPCS)

Complete demo scenarios for the Portfolio Manager Co-Pilot — covering holdings management, attribution analysis, factor/thematic strategy, portfolio modelling, and stress testing.

---

## Part 1: Portfolio Management

## Portfolio Manager

### Portfolio Copilot - Portfolio Insights & Benchmarking

#### Business Context Setup

**Persona**: Anna, Senior Portfolio Manager at Simulated Asset Management  
**Business Challenge**: Portfolio managers need instant access to portfolio analytics, holdings information, and supporting research to make informed investment decisions. Traditional systems require multiple tools, manual data gathering, and time-consuming analysis that delays critical investment decisions.  
**Value Proposition**: AI-powered portfolio analytics that combines quantitative holdings data with qualitative research insights in seconds, enabling faster decision-making and better risk management.

**Agent**: `pm_cockpit`  
**Data Available**: 10 portfolios, 5,000 securities, 2,800 research documents

#### Demo Flow

**Scene Setting**: Anna is preparing for her weekly portfolio review meeting and needs to quickly assess her Technology & Infrastructure portfolio performance, understand current holdings, and identify any emerging risks that require attention.

##### Step 1: Top Holdings Overview
**User Input**: 
```
What are my top 10 holdings by market value in the SAM Technology & Infrastructure portfolio?
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Query portfolio holdings data from SAM_PORTFOLIO_VIEW

**Expected Response**:
- Table showing: Ticker, Company Name, Weight %, Market Value USD
- Flag any positions >6.5% (concentration warning)
- Total exposure percentage of top 10

**Talking Points**:
- Instant portfolio analytics without SQL or complex queries
- Automatic concentration risk flagging based on business rules
- Real-time data from the data warehouse with no latency

**Key Features Highlighted**: 
- Cortex Analyst semantic understanding of portfolio data
- Business rule integration (6.5% concentration threshold)
- Natural language to SQL conversion

##### Step 2: Latest Research for Top Holdings

**Presenter Transition**:
> "We can see our top holdings clearly, with Apple, Microsoft, and NVIDIA flagged for concentration. But portfolio data alone doesn't tell the full story—what are the analysts actually saying about these large positions? Let me show you how we seamlessly transition from quantitative data to qualitative research..."

*Reasoning: Quantitative holdings data raises questions that qualitative research can answer. This demonstrates the multi-modal capability of combining analytics with document search.*

**User Input**: 
```
Based on those top holdings you just showed me, what is the latest broker research saying about our three largest positions?
```

**Tools Used**:
- `search_external_docs` (Cortex Search) - Search for analyst research on the top 3 companies identified in Step 1

**Expected Response**:
- Bullet list: Company → Recent report titles with dates for the top 3 holdings from Step 1
  - [Top Holding 1]: Recent research reports with ratings and dates
  - [Top Holding 2]: Recent research reports with ratings and dates  
  - [Top Holding 3]: Recent research reports with ratings and dates
- Brief summaries of key investment themes
- Ratings distribution (Buy/Hold/Sell)
- Analysis of how research sentiment aligns with large position sizes

**Talking Points**:
- AI automatically identifies research for the specific holdings shown in Step 1
- Seamless transition from quantitative holdings data to qualitative research insights
- Risk assessment: Large positions supported by positive research sentiment

**Key Features Highlighted**: 
- Contextual follow-up that builds on previous query results
- SecurityID-based linkage between holdings and research
- Automatic citation and source attribution

##### Step 3: Sector Risk Assessment

**Presenter Transition**:
> "The research confirms strong analyst support for our largest holdings. But having multiple large technology positions creates a different kind of risk—sector concentration. Let me show you how we can assess sector-level risk while keeping the context of our individual holdings..."

*Reasoning: Individual position analysis (Step 1) and research sentiment (Step 2) need to be viewed through a sector concentration lens to understand cumulative risk exposure.*

**User Input**: 
```
Looking at those top holdings and their research, what's our sector concentration risk in this portfolio, especially for the companies with the largest positions?
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Analyze sector allocation and concentration risk from SAM_PORTFOLIO_VIEW

**Expected Response**:
- Sector allocation breakdown highlighting the top holdings from Step 1
- Concentration analysis showing sector exposure through large positions
- Comparison to benchmark sector weights
- Risk assessment combining position size and sector concentration
- Specific flagging if top holdings create sector concentration >6.5%

**Talking Points**:
- Integrated risk analysis that combines individual position risk (Step 1) with sector risk
- Research sentiment (Step 2) now viewed through concentration lens
- Comprehensive risk picture that builds on previous analysis

**Key Features Highlighted**: 
- Multi-dimensional risk analysis building on previous queries
- Sector-level concentration assessment linked to specific holdings
- Integrated benchmark comparison with position-level context

##### Step 4: Integrated Risk & Action Plan

**Presenter Transition**:
> "Now we have the complete risk picture—individual positions, research sentiment, and sector concentration. The real value comes from synthesising all of this into actionable recommendations. Let me ask the agent to prioritise which positions need attention and what actions we should consider..."

*Reasoning: Analysis without action is incomplete. This step demonstrates how the AI synthesises multi-step analysis into prioritised, actionable recommendations.*

**User Input**: 
```
Based on our concentration analysis and research findings, which of our largest positions need attention and what actions should we consider?
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Retrieve concentration data
- `search_internal_docs` (Cortex Search) - Get concentration thresholds from firm policies
- `search_external_docs` (Cortex Search) - Reference research sentiment from Step 2

**Expected Response**:
- Integrated risk assessment for the top holdings identified in Steps 1-3
- Combination of concentration risk (Step 3) and research sentiment (Step 2)
- Specific concerns for positions that are both large AND have sector concentration risk
- Prioritized action plan: positions requiring immediate attention vs monitoring
- Recommended actions with specific rationale (reduce for concentration, hold for strong research, etc.)

**Talking Points**:
- Complete investment decision framework combining all previous analysis
- Prioritized action plan based on integrated quantitative and qualitative risk assessment
- Professional portfolio management workflow from analysis to action

**Key Features Highlighted**: 
- Comprehensive decision support building on multi-step analysis
- Integration of position size, sector risk, and research sentiment
- Actionable recommendations with clear prioritization and rationale

##### Step 5: Portfolio Management Decision

**Presenter Transition**:
> "We know what needs attention. But professional portfolio management requires more than just identifying issues—we need specific, executable actions with exact dollar amounts, timelines, and compliance considerations. Let me show you how the agent translates recommendations into a complete implementation plan..."

*Reasoning: Recommendations need to become executable actions. This final step demonstrates end-to-end workflow from analysis to specific implementation with professional-grade detail.*

**User Input**: 
```
Based on our complete analysis, provide me with a specific implementation plan including exact position sizes, timelines, and dollar amounts for the portfolio actions we should take.
```

**Tools Used**:
- `implementation_analyzer` (Cortex Analyst) - Calculate trading costs, market impact, and execution timeline
- `quantitative_analyzer` (Cortex Analyst) - Get current position data and portfolio metrics
- `search_internal_docs` (Cortex Search) - Reference mandate requirements and approval processes

**Expected Response**:
- **Implementation Plan**:
  - Specific position reduction recommendations with target weights
  - Execution approach (TWAP, timeline, market impact considerations)
    | Section | Description |
    |---------|-------------|
    | Execution | Trade approach and timeline |
    | Tax/Liquidity | Tax implications and cash impact |
    | Compliance | Required approvals and mandate checks |
    | Timeline | Day-by-day implementation schedule |
- **Risk Budget Analysis**: Impact on tracking error and mandate utilisation
- **Market Conditions**: Volatility assessment and timing considerations
- **Approval Requirements**: Committee notifications per policy

**Talking Points**:
- **Complete Investment Workflow**: From analysis to specific executable actions
- **Professional Portfolio Management**: Industry-standard implementation planning with exact specifications
- **AI-Powered Decision Support**: Comprehensive analysis translated into precise, actionable investment decisions

**Key Features Highlighted**: 
- **End-to-End Investment Process**: Complete workflow from analysis to implementation
- **Specific Action Planning**: Exact dollar amounts, percentages, and timelines
- **Professional Investment Management**: Industry-standard decision framework with comprehensive risk management

#### Scenario Wrap-up

**Business Impact Summary**:
- **Time Savings**: Reduced portfolio analysis time from hours to minutes
- **Risk Management**: Proactive identification of emerging risks and concentration issues
- **Decision Quality**: Enhanced decision-making through integrated quantitative and qualitative insights
- **Operational Efficiency**: Single interface replacing multiple legacy systems and manual processes

**Technical Differentiators**:
- **Semantic Understanding**: Natural language queries automatically converted to complex SQL
- **Real-time Integration**: Live data warehouse connectivity with no batch processing delays
- **AI-Powered Search**: Intelligent document search with automatic relevance ranking and summarization
- **Multi-modal Analysis**: Seamless combination of structured portfolio data with unstructured research content

---

### Portfolio Copilot - Performance Driver Analysis

#### Business Context Setup

**Persona**: Anna, Senior Portfolio Manager at Simulated Asset Management  
**Business Challenge**: During weekly portfolio reviews, Anna sees holdings and research but cannot immediately answer "why did performance change?" without switching to a separate attribution system. The disconnect between position data and performance attribution slows decision-making.  
**Value Proposition**: Attribution analysis integrated directly into the PM's primary tool, enabling seamless transition from "what do I own?" to "what's driving my performance?" in a single conversation.

**Agent**: `pm_cockpit`  
**Data Available**: Multi-level Brinson attribution (sector, country, industry), anomaly detection with 8 alert types

#### Demo Flow

**Scene Setting**: Anna has just reviewed her top holdings in SAM Technology & Infrastructure. She notices the portfolio is down this month and wants to understand why — without leaving the portfolio copilot.

##### Step 1: Attribution + Anomaly Combined

**Skills Activated**: `multi-level-attribution` + `attribution-anomaly-scan` (composed)
**Workflow**: Sector attribution → anomaly scan → combined presentation → STOPPING POINT
**Demo Value**: One combined question triggers both attribution analysis and risk scanning, giving the PM a complete picture in a single response

**User Input**: 
```
What's driving SAM Technology & Infrastructure this quarter? Flag anything unusual.
```

**Tools Used**:
- `server_skill` — Loads multi-level-attribution and attribution-anomaly-scan skills
- `brinson_analyzer` (Cortex Analyst) - Sector-level attribution
- `anomaly_detector` (Cortex Analyst) - Risk flag scan

**Expected Response**:
- Active return with allocation/selection/interaction breakdown
- Sector-level table showing which sectors helped or hurt
- Any anomaly flags for this portfolio (severity + detail)
- STOPPING POINT: "Technology selection was the main driver. I can drill into which industries within Tech contributed, pivot to country attribution, or show the drift timeline. No HIGH severity anomalies detected."

**Talking Points**:
- One question, two skills composed — the PM gets attribution + risk flags together
- Natural flow: "What do I own?" (previous step) → "Why is it performing, and is anything unusual?" (this step)
- The agent proactively checks for anomalies without being asked separately
- Stopping point offers logical next steps without requiring the PM to know the right question

**Key Features Highlighted**: 
- Skill composition: two skills work together in one response
- Proactive anomaly checking alongside attribution
- Interactive stopping point for PM-driven exploration

##### Step 2: Industry Drill-Down (Stopping Point Continuation)

**Presenter Transition**:
> "The agent combined attribution and anomaly scanning in one response, then offered drill-down options. The PM doesn't need to know 'use brinson_analyzer with grouping_dimension=INDUSTRY' — they just pick from the offered options. Let me drill into Technology industries..."

*Reasoning: This demonstrates how skills remove the cognitive burden from the PM. No need to know tool names or parameters — the skill handles orchestration.*

**User Input**: 
```
Drill into Technology — which industries contributed?
```

**Tools Used**:
- `anomaly_detector` (Cortex Analyst) - Queries SAM_ATTRIBUTION_VIEW for alerts

**Expected Response**:
- Anomaly severity (HIGH/MEDIUM/LOW) for the portfolio
- Specific flags: factor drift, allocation drift, selection reversal, concentration, style inconsistency
- Any HIGH severity items highlighted with recommended actions

**Talking Points**:
- 8 automated anomaly detection rules running continuously
- Factor drift catches when exposure quietly drifts from its trailing average
- Selection reversal flags when a previously positive selection effect flips negative
- In production, these could trigger automated alerts to the PM's inbox

**Key Features Highlighted**: 
- Proactive anomaly detection integrated into the PM workflow
- 8 detection rules covering factor, allocation, selection, concentration, and style dimensions

#### Scenario Wrap-up

**Business Impact Summary**:
- **Workflow Integration**: Attribution answers available in the PM's primary tool
- **Proactive Risk**: Anomaly alerts surface issues before they compound
- **Decision Speed**: "What's driving performance?" answered in seconds

**Technical Differentiators**:
- **Cross-Pollinated Tools**: Same attribution data serves multiple agent personas
- **Anomaly Detection**: 8 automated rules with severity classification
- **Escalation Path**: PM can be directed to Portfolio Manager Co-Pilot for stress testing, counterfactual analysis

---

### Portfolio Copilot - Comprehensive Company Analysis

#### Business Context Setup

**Persona**: Anna, Senior Portfolio Manager at Simulated Asset Management  
**Business Challenge**: Portfolio managers need to rapidly conduct comprehensive company analysis that integrates quantitative financial performance from SEC filings, qualitative management commentary from earnings calls, external analyst perspectives from broker research, corporate developments from press releases, and portfolio positioning context—all while market-moving events demand immediate assessment. Traditional research workflows require hours of manual data gathering across multiple systems, spreadsheet modeling, document review, and synthesis, often missing critical connections between financial performance, strategic narratives, and investment implications.  
**Value Proposition**: AI-powered comprehensive company intelligence that seamlessly integrates authentic SEC financial data, management commentary, analyst research, corporate announcements, and portfolio exposure in a single query—delivering complete, investment-ready analysis within minutes instead of hours, enabling faster response to market events and higher-quality investment decisions.

**Agent**: `pm_cockpit`  
**Data Available**: 28.7M SEC filing records (10+ years), 500 broker research reports, 300 earnings transcripts, 400 press releases, portfolio holdings across 10 strategies

#### Demo Flow

**Scene Setting**: Anna receives an urgent alert that Microsoft has reported earnings that missed analyst expectations. The portfolio management team needs a comprehensive assessment within the hour to determine if current Microsoft positions across portfolios require action. Anna needs to analyze the financial results against SEC data, understand management's explanation, review analyst reactions, check for any related corporate developments, and assess current portfolio exposure—all before the 3 PM investment committee call.

##### Step 1: Comprehensive Multi-Source Analysis
**User Input**: 
```
I'm concerned about Microsoft's recent earnings report. Can you analyze their latest financial performance using SEC filings, compare it to what management said in the earnings call, see what external analysts are saying, and show me our current exposure across all portfolios?
```

**Tools Used**:
- `financial_analyzer` (Cortex Analyst) - Analyze Microsoft financial metrics from SEC filings
- `search_company_events` (Cortex Search) - Retrieve management commentary from earnings call
- `search_external_docs` (Cortex Search) - Find analyst research and reactions
- `search_external_docs` (Cortex Search) - Check for related corporate announcements
- `quantitative_analyzer` (Cortex Analyst) - Calculate portfolio exposure

**Expected Response**:
- **Financial Performance Analysis**:
  - Key metrics from SEC filings compared to consensus estimates
    | Metric Type | Description |
    |-------------|-------------|
    | Revenue/EPS | Reported vs consensus with variance |
    | Margins | Operating margin trends and analysis |
    | Segment | Key segment performance (e.g., cloud revenue) |
    | Balance Sheet | Debt-to-equity and cash position |
  - Key issues and positives identified with investment implications

- **Management Commentary**:
  - Key quotes from earnings call addressing performance drivers
  - Forward guidance and outlook statements
  - Tone assessment (confident/cautious/defensive)

- **Analyst Research Reactions**:
  - Recent broker research with ratings and price target changes
  - Bull/bear case arguments from analysts
  - Consensus rating distribution and shifts
  
- **Recent Corporate Developments**:
  - Recent press releases and strategic announcements
  - Assessment of how developments support or challenge investment thesis

- **Current Portfolio Exposure**:
  - Exposure by portfolio with concentration flagging
  - Total firm exposure and unrealized P&L since event
  - Risk assessment considering existing breaches

- **Integrated Investment Assessment**:
  - Synthesis of financial, management, analyst, and strategic perspectives
  - Prioritised recommendations by portfolio
  - Investment thesis status (maintained/revised/challenged)

**Talking Points**:
- **Comprehensive Intelligence**: Single query orchestrates 4-5 tools spanning SEC filings, earnings transcripts, broker research, press releases, and portfolio holdings
- **Speed to Insight**: Complete investment-ready analysis in under 5 minutes vs 2-3 hours with manual research
- **Multi-Dimensional View**: Integrates quantitative financials, qualitative management perspective, external validation, corporate strategy, and portfolio impact
- **Balanced Assessment**: AI synthesizes bull and bear perspectives from multiple sources into actionable recommendation
- **Context-Aware**: Automatically identifies concentration breach and incorporates into recommendation framework

**Key Features Highlighted**: 
- **Authentic Data Foundation**: 28.7M SEC filing records provide institutional-grade financial analysis with real 10-Q data
- **Document Intelligence**: Cortex Search across earnings transcripts, broker research, press releases with relevance ranking
- **Multi-Source Synthesis**: AI orchestration seamlessly integrates structured financial data with unstructured document insights
- **Portfolio Integration**: Automatic exposure calculation across all portfolios with concentration flagging
- **Analyst Consensus Tracking**: Real-time aggregation of broker research reactions and rating changes
- **Management Tone Analysis**: Qualitative assessment of management confidence and strategic messaging
- **Investment Decision Framework**: Complete analysis from financial metrics through recommendation with specific actions

#### Scenario Wrap-up

**Business Impact Summary**:
- **Analysis Speed**: Comprehensive company assessment reduced from hours to minutes
- **Decision Quality**: Multi-source validation (SEC data + management + analysts + corporate strategy) eliminates single-source bias
- **Market Responsiveness**: Real-time earnings reaction enables same-day investment decisions
- **Risk Management**: Automatic portfolio exposure and concentration checking prevents oversized bets on deteriorating positions

**Technical Differentiators**:
- **Authentic Financial Data**: Real SEC EDGAR filings (28.7M records) provide institutional-grade analysis unavailable from market data vendors
- **Multi-Modal AI**: Seamless orchestration of Cortex Analyst (SEC filings, portfolio data) and Cortex Search (3 document types)
- **Intelligent Synthesis**: Claude 4 planning dynamically sequences tools and synthesizes findings across quantitative and qualitative sources
- **Real-Time Document Intelligence**: Broker research and earnings transcripts indexed within hours of publication for immediate analysis
- **Portfolio-Aware Research**: Automatic integration of company analysis with current holdings and concentration limits
- **Balanced Perspective**: AI synthesizes bull/bear views from multiple analysts into objective, actionable assessment

---

### Portfolio Copilot - Real-Time Event Impact & Second-Order Risk Verification

#### Business Context Setup

**Persona**: Anna, Senior Portfolio Manager at Simulated Asset Management  
**Business Challenge**: Portfolio managers need to rapidly assess portfolio exposure when external events occur, including both direct regional/sector exposure and indirect supply chain dependencies. Traditional risk systems can't model multi-hop supply chain relationships or quantify second-order impacts, leaving managers blind to cascading risks.  
**Value Proposition**: AI-powered event risk verification that combines macro event intelligence, direct portfolio exposure analysis, and sophisticated supply chain dependency mapping to quantify both immediate and indirect portfolio impacts in real-time.

**Agent**: `pm_cockpit`  
**Data Available**: 10 portfolios, supply chain relationships (150+ dependencies), macro events corpus, press releases

#### Demo Flow

**Scene Setting**: Anna receives an external market alert about a recent earthquake in Taiwan affecting semiconductor production. She needs to immediately understand her portfolio's exposure - both direct holdings in affected companies and indirect exposure through supply chain dependencies.

##### Step 1: Event Verification
**User Input**: 
```
I just received an alert about a recent earthquake in Taiwan affecting semiconductor production. Can you verify this event and tell me what sectors are affected?
```

**Tools Used**:
- `search_company_events` (Cortex Search) - Search for Taiwan earthquake event details and sector impacts

**Expected Response**:
- **Event Confirmation**: Details from macro events database
  | Attribute | Description |
  |-----------|-------------|
  | Event Type | Classification (Natural Disaster, etc.) |
  | Region | Geographic location |
  | Severity | Impact level (Critical/High/Medium) |
  | Date | Event date |
- Affected sectors identified:
  * Information Technology (primary impact)
  * Consumer Discretionary (secondary impact via automotive)
- Brief impact description:
  * TSMC facilities affected - wafers in process impacted and scrapped
  * TSMC demonstrated operational resilience and recovered much of lost production
  * Recent quarter revenue came in slightly above guidance midpoint despite disruption

**Talking Points**:
- AI verifies external alerts using structured macro event database
- Extracts precise event characteristics (type, region, severity, sectors)
- Provides authoritative event context for risk assessment
- References real TSMC commentary from recent earnings call

**Key Features Highlighted**: 
- Macro event intelligence repository
- Structured event data with standardized attributes
- Event verification before portfolio impact analysis

##### Step 2: Direct Portfolio Exposure

**Presenter Transition**:
> "The event is confirmed—a 6.4 magnitude earthquake in Taiwan affecting semiconductor production. Now the critical question: how exposed are we? Let me calculate our direct holdings in the affected region..."

*Reasoning: Event verification establishes the risk context; now we need to quantify direct portfolio exposure to determine the urgency and scale of response.*

**User Input**: 
```
What is my direct exposure to Taiwan-based semiconductor companies across all portfolios?
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Query holdings by CountryOfIncorporation='TW' and sector from SAM_PORTFOLIO_VIEW

**Expected Response**:
- Table showing direct Taiwan semiconductor exposure by portfolio:
  * Portfolio Name | Taiwan Semiconductor Exposure (USD) | % of Portfolio | Key Holdings (TSM, etc.)
  * Flag portfolios with >2% exposure to Taiwan semiconductor sector
- Total Taiwan semiconductor exposure across all portfolios
- Specific companies held:
  * Taiwan Semiconductor Manufacturing (TSM) - if held
  * ASE Technology Holding, ChipMOS Technologies, Himax Technologies, etc.
- Regional exposure breakdown: Taiwan % of total portfolio

**Talking Points**:
- Immediate quantification of direct regional exposure
- Portfolio-level impact assessment
- Specific holdings identified for monitoring

**Key Features Highlighted**: 
- Multi-dimensional filtering (country + sector)
- Cross-portfolio exposure aggregation
- Automatic threshold-based flagging

##### Step 3: Second-Order Supply Chain Exposure

**Presenter Transition**:
> "Direct exposure is only part of the picture. Companies like Apple, NVIDIA, and AMD depend heavily on Taiwan semiconductors even though they're US-based. This is where traditional risk systems fail—they can't see through supply chain dependencies. Let me show you our indirect exposure..."

*Reasoning: Direct holdings show first-order risk, but supply chain dependencies create hidden second-order exposure that can be equally material. This demonstrates sophisticated graph-based risk analysis.*

**User Input**: 
```
What is my indirect exposure through supply chain dependencies? Show me which US companies in my portfolio depend on Taiwan semiconductor suppliers.
```

**Tools Used**:
- `supply_chain_analyzer` (Cortex Analyst) - Analyze multi-hop supply chain dependencies from SAM_PORTFOLIO_VIEW
- `quantitative_analyzer` (Cortex Analyst) - Get portfolio weights for US companies with Taiwan dependencies

**Expected Response**:
- Multi-hop supply chain analysis with decay factors:
  * **First-Order Dependencies** (Direct customers of Taiwan semis):
    - NVIDIA: 25% revenue dependency on TSM (High) → Portfolio exposure: [weight]%
    - AMD: 18% revenue dependency on TSM (High) → Portfolio exposure: [weight]%
    - Apple: 30% revenue dependency on TSM (High) → Portfolio exposure: [weight]%
  * **Second-Order Dependencies** (50% decay applied):
    - General Motors: 8% chip dependency on NVIDIA (Medium) → Effective exposure: 4% post-decay
    - Ford: 6% chip dependency on NVIDIA (Medium) → Effective exposure: 3% post-decay
- Summary table:
  * Company | Relationship Type | Dependency % | Post-Decay Exposure | Portfolio Weight | Risk Rating
- Total indirect exposure calculation (weighted by portfolio holdings)
- Flag High dependency relationships (≥20% post-decay)

**Talking Points**:
- **Multi-Hop Analysis**: AI traverses supply chain graph to identify indirect dependencies
- **Decay Factors**: 50% decay per hop reflects diminishing impact through supply chain
- **Criticality Assessment**: Automatic flagging of high-dependency relationships
- **Portfolio Weighting**: Second-order exposure weighted by actual portfolio holdings

**Key Features Highlighted**: 
- Supply chain graph traversal with configurable depth
- Decay factor application for realistic impact modeling
- Upstream (cost) and downstream (revenue) relationship analysis
- Portfolio-weighted exposure calculation

##### Step 4: Corroborating Evidence & Next Steps

**Presenter Transition**:
> "We now know our direct and indirect exposure. But before making decisions, we need to understand how companies are actually responding. Has TSMC recovered? What are their customers saying? Let me search for corroborating evidence from earnings calls and press releases..."

*Reasoning: Quantified exposure needs qualitative context. Company communications provide real evidence of recovery or ongoing issues that should inform investment decisions.*

**User Input**: 
```
Do we have any statements from TSMC or their customers about the Taiwan earthquake impact and supply chain resilience?
```

**Tools Used**:
- `search_company_events` (Cortex Search) - Search for TSMC earnings call commentary on earthquake recovery
- `search_external_docs` (Cortex Search) - Search for NVIDIA, AMD, Apple Taiwan supply chain statements
- `quantitative_analyzer` (Cortex Analyst) - Calculate total exposure (direct + indirect)

**Expected Response**:
- TSMC Recent Earnings Call:
  * Management commentary on earthquake resilience:
    > "Taiwan experienced a significant earthquake, followed by several significant aftershocks. Although a certain number of wafers in process were impacted and had to be scrapped, we worked tirelessly and were able to recover much of the lost production, demonstrating the resilience of our operation in Taiwan."
  * Recent quarter revenue slightly above guidance midpoint despite disruption
- Customer supply chain updates:
  * NVIDIA/AMD - Supply chain update press releases confirming:
    - Continued partnership with TSMC for advanced node production
    - Confidence in TSMC's operational resilience
    - Ongoing geographic diversification planning
- Synthesis and recommendations:
  * **Direct Exposure**: [X]% total exposure to Taiwan IT sector
  * **Indirect Exposure**: [Y]% effective exposure through supply chain (post-decay)
  * **Total Risk**: [X+Y]% combined exposure to Taiwan semiconductor disruption
  * **Risk Assessment**: TSMC demonstrated strong operational resilience - production recovered
  * **Recommended Actions**:
    1. Monitor: Continue tracking TSMC production updates and customer confirmations
    2. Assess: Evaluate long-term supply chain diversification progress at portfolio companies
    3. Document: Note TSMC's demonstrated disaster recovery capabilities for future reference
    4. Review: Consider supply chain resilience as positive factor in semiconductor exposure analysis

**Talking Points**:
- **Real Event Data**: AI finds authentic TSMC earnings call commentary on the Taiwan earthquake
- **Multi-Source Corroboration**: Combines company transcripts with press releases for comprehensive view
- **Demonstrated Resilience**: TSMC's recovery provides confidence in supply chain stability
- **Actionable Intelligence**: Specific recommendations based on real event outcomes

**Key Features Highlighted**: 
- Integration of real earnings call transcripts with generated press releases
- Multi-source intelligence synthesis (portfolio data + supply chain + company events + press releases)
- Evidence-based risk assessment using actual management commentary
- Professional risk management framework informed by real event outcomes

#### Scenario Wrap-up

**Business Impact Summary**:
- **Rapid Event Response**: Assess portfolio impact within minutes vs hours/days with traditional systems
- **Hidden Risk Discovery**: Quantify indirect supply chain exposures that traditional systems miss
- **Comprehensive Risk View**: Combine direct holdings with multi-hop supply chain dependencies
- **Actionable Intelligence**: Specific recommendations with timelines and thresholds

**Technical Differentiators**:
- **Graph Database Analytics**: Multi-hop supply chain traversal with decay factors and criticality scoring
- **Event Intelligence Repository**: Structured macro event database with standardized attributes
- **Real-Time Risk Quantification**: Instant calculation of portfolio-weighted supply chain exposures
- **Multi-Modal Intelligence**: Seamless integration of event data, portfolio holdings, supply chain graphs, and corporate communications

---

### Portfolio Copilot - AI-Assisted Mandate Compliance & Security Replacement

#### Business Context Setup

**Persona**: David Chen, Senior Portfolio Manager at Simulated Asset Management  
**Business Challenge**: Portfolio managers must respond quickly to mandate compliance breaches (e.g., ESG downgrades) by identifying suitable replacement securities that maintain portfolio strategy while meeting compliance requirements. Traditional processes involve manual screening, multiple system lookups, and time-consuming committee documentation.  
**Value Proposition**: AI-powered compliance workflow that automatically identifies pre-screened replacement candidates, analyzes their strategic fit, and generates investment committee documentation—reducing breach response time from days to minutes.

**Agent**: `pm_cockpit`  
**Data Available**: SAM AI & Digital Innovation portfolio, compliance alerts, pre-screened replacements, ESG data, financial filings, broker research

#### Demo Flow

**Scene Setting**: David receives a compliance alert that META has been downgraded to ESG grade CCC due to governance concerns, violating the SAM AI & Digital Innovation fund's minimum BBB ESG requirement. He needs to identify a suitable replacement that maintains the portfolio's AI/digital innovation focus while meeting all mandate requirements, then document his recommendation for the investment committee.

##### Step 1: Verify Compliance Breach
**User Input**: 
```
I've received an alert that META has been downgraded to ESG grade CCC. Can you verify this breach for the SAM AI & Digital Innovation portfolio and show me our current exposure?
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Check META's AI Growth Score and portfolio weight from SAM_PORTFOLIO_VIEW
- `search_internal_docs` (Cortex Search) - Get AI Growth mandate requirements (minimum score 80)

**Expected Response**:
- Confirmation of META's ESG downgrade from BBB to CCC
- Current portfolio exposure to META (weight %, market value)
- Mandate requirement: Minimum ESG grade BBB
- Breach severity: Critical (grade CCC vs required BBB)
- Recommendation: Identify replacement security

**Talking Points**:
- Instant compliance verification using mandate_compliance_analyzer
- Clear identification of mandate breach with specific thresholds
- Portfolio-specific exposure analysis for impact assessment

**Key Features Highlighted**: 
- Cortex Analyst for compliance rule checking
- Real-time ESG data integration
- Portfolio-specific mandate requirements

##### Step 2: Identify Pre-Screened Replacement Candidates

**Presenter Transition**:
> "The breach is confirmed—META's ESG grade CCC violates our BBB minimum. Now we need to act quickly. Rather than manually screening thousands of securities, let me show you how the agent identifies pre-screened replacement candidates that meet both our ESG requirements and AI growth focus..."

*Reasoning: Breach verification requires immediate action. Pre-screened candidates ensure rapid response while maintaining mandate compliance and strategic fit.*

**User Input**: 
```
Based on that breach, what are our pre-screened replacement candidates that meet the mandate requirements and maintain our AI growth focus?
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Query pre-screened replacement securities with AI Growth Score >80 from SAM_PORTFOLIO_VIEW

**Expected Response**:
- Table of pre-screened candidates (NVDA, MSFT, GOOGL):
  - Ticker, Company Name
  - AI Growth Score (0-10 scale)
  - ESG Grade (A/BBB/B)
  - Current portfolio weight
  - Strategic fit rationale
- Ranking by AI Growth Score
- ESG compliance status (all meet BBB+ requirement)

**Talking Points**:
- Pre-screened candidates ensure compliance and strategic fit
- AI Growth Score quantifies alignment with portfolio theme
- Multiple options provide flexibility for committee decision

**Key Features Highlighted**: 
- Mandate-aware candidate identification
- Thematic scoring (AI Growth Score)
- Portfolio positioning context

##### Step 3: Analyze Top Replacement Candidate

**Presenter Transition**:
> "NVIDIA stands out with the highest AI Growth Score and an A ESG grade. But before recommending to the Investment Committee, we need due diligence—financial health, analyst views, and management guidance. Let me show you the comprehensive analysis..."

*Reasoning: Candidate identification is just the first step. Investment committee approval requires thorough multi-source analysis demonstrating fundamental strength.*

**User Input**: 
```
Give me a comprehensive analysis of NVDA as a replacement—include financial health, recent analyst views, and earnings guidance
```

**Tools Used**:
- `financial_analyzer` (Cortex Analyst) - Analyze NVDA financial metrics from SAM_SEC_FILINGS_VIEW
- `search_external_docs` (Cortex Search) - Get analyst research on NVDA
- `search_company_events` (Cortex Search) - Get management AI strategy commentary

**Expected Response**:
- **Financial Health** (from SEC filings):
  - Revenue growth trends, profit margins, cash flow strength
  - Debt-to-equity ratio, balance sheet quality
- **Analyst Views** (from broker research):
  - Recent rating: Buy/Outperform
  - Price targets and investment thesis
  - AI/semiconductor growth outlook
- **Earnings Guidance** (from transcripts):
  - Recent quarter performance
  - Management guidance on AI demand
  - Forward-looking statements

**Talking Points**:
- Multi-source analysis combining structured and unstructured data
- Authentic SEC filing data for fundamental analysis
- Real broker research and earnings commentary for market context

**Key Features Highlighted**: 
- SAM_SEC_FILINGS_VIEW for financial analysis
- Cortex Search across multiple document types
- Integrated quantitative + qualitative insights

##### Step 4: Generate Investment Committee Report

**Presenter Transition**:
> "The analysis confirms NVIDIA as an excellent replacement. Now comes the documentation—Investment Committee approval requires a formal memo with breach details, replacement rationale, and implementation plan. Let me generate the complete report..."

*Reasoning: Professional governance requires formal documentation. This demonstrates end-to-end workflow from alert to audit-ready committee materials.*

**User Input**: 
```
Generate an investment committee memo documenting this compliance breach and recommending NVDA as a replacement
```

**Tools Used**:
- `search_internal_docs` (Cortex Search) - Get Investment Committee Memo template
- `quantitative_analyzer` (Cortex Analyst) - Get breach details and replacement metrics
- `implementation_analyzer` (Cortex Analyst) - Calculate execution costs and timeline

**Expected Response**:
- Confirmation: "I've generated your investment committee memo. Synthesizing from template guidance..."
- Report includes:
  - **Executive Summary**: Clear recommendation to replace META with NVDA
  - **Breach Details**: ESG downgrade specifics and mandate violation
  - **Replacement Analysis**: 
    * NVDA's AI Growth Score (9/10) vs META (8/10)
    * ESG compliance (A grade vs required BBB)
    * Financial strength metrics
    * Analyst support and market positioning
  - **Risk Assessment**: Implementation risks and monitoring requirements
  - **Appendices**: Supporting data tables and research citations
- PDF file path: `@SAM_REPORTS_STAGE/SAM_AI_Digital_Innovation_META_Replacement_YYYYMMDD_HHMMSS.pdf`

**Talking Points**:
- Automated report generation following firm templates
- Comprehensive documentation for audit trail
- Professional PDF output ready for committee review
- Entire workflow completed in minutes vs days

**Key Features Highlighted**: 
- Template-guided report synthesis
- Custom Python stored procedure for PDF generation
- Snowflake stage for secure report storage
- Complete audit trail from alert to documentation

#### Scenario Wrap-up

**Business Impact Summary**:
- **Response Time**: Compliance breach resolution from days to minutes
- **Risk Mitigation**: Immediate identification of compliant alternatives
- **Decision Quality**: Multi-source analysis (financial + research + ESG)
- **Audit Trail**: Automated committee documentation with full lineage

**Technical Differentiators**:
- **Mandate-Aware AI**: Compliance rules integrated into agent planning
- **Multi-View Analytics**: Combines SAM_PORTFOLIO_VIEW, SAM_SEC_FILINGS_VIEW, and Cortex Search
- **Custom Tool Integration**: Python stored procedures for PDF generation
- **Secure Report Storage**: Snowflake stage for governed document management

---

### Portfolio Copilot - Event-Driven Risk Assessment & Response

#### Business Context Setup

**Persona**: Anna, Senior Portfolio Manager at Simulated Asset Management  
**Business Challenge**: Portfolio managers need to rapidly assess portfolio exposure when external events occur, including both direct regional/sector exposure and indirect supply chain dependencies, then validate findings with financial analysis and research, retrieve policy guidance, and document formal recommendations. Traditional risk systems can't model multi-hop supply chain relationships, integrate qualitative research with quantitative risk metrics, or generate audit-ready documentation—leaving managers blind to cascading risks and unable to respond with comprehensive, documented action plans within required timeframes.  
**Value Proposition**: AI-powered comprehensive event risk assessment that seamlessly integrates macro event verification, direct portfolio exposure, supply chain dependency mapping, financial health analysis, management commentary, analyst research, policy compliance, and formal documentation generation—delivering complete, actionable, audit-ready risk assessment within minutes instead of days.

**Agent**: `pm_cockpit`  
**Data Available**: 10 portfolios, supply chain relationships (150+ dependencies), macro events corpus, 28.7M SEC filing records, broker research, earnings transcripts, press releases, policy documents, report templates

#### Demo Flow

**Scene Setting**: Anna receives an external alert about a major earthquake in Taiwan affecting semiconductor production. She needs to immediately understand her portfolio's exposure across multiple dimensions, validate with financial and research data, ensure policy compliance, and prepare formal documentation for the Investment Committee—all within the next hour before an emergency board call.

##### Step 1: Comprehensive Multi-Tool Risk Assessment
**User Input**: 
```
I just heard about a major earthquake in Taiwan affecting semiconductor production. Can you:
1. Verify this event and identify affected sectors
2. Show my direct exposure to Taiwan-based technology holdings across all portfolios
3. Calculate indirect exposure through supply chain dependencies (especially for companies like Apple, NVIDIA)
4. Check if any positions breach our concentration limits
5. Analyze the financial health of my most exposed companies using SEC data
6. Find what management is saying in recent earnings calls about supply chain resilience
7. See what analysts are recommending about semiconductor exposure
8. Review our firm's policy on geographic concentration and event response
9. Generate an Investment Committee memo documenting this risk assessment with specific portfolio actions and timeline
```

**Tools Used**:
- `search_company_events` (Cortex Search) - Verify Taiwan earthquake and identify affected sectors
- `quantitative_analyzer` (Cortex Analyst) - Calculate direct Taiwan technology exposure by portfolio
- `supply_chain_analyzer` (Cortex Analyst) - Map indirect exposures through multi-hop supply chain dependencies
- `search_internal_docs` (Cortex Search) - Retrieve concentration limits and event response procedures
- `financial_analyzer` (Cortex Analyst) - Analyze financial health of exposed companies using SEC filings
- `search_company_events` (Cortex Search) - Find management commentary on supply chain resilience
- `search_external_docs` (Cortex Search) - Get analyst recommendations on semiconductor exposure
- `search_internal_docs` (Cortex Search) - Retrieve Investment Committee memo template
- `generate_investment_committee_pdf` (Python Stored Procedure) - Create formal documentation

**Expected Response**:
- **Event Verification**: Taiwan earthquake confirmed (EventType: Natural Disaster, Severity: Critical, AffectedSectors: Information Technology, Date: [current])
  * TSMC facilities affected (40-50% of global advanced chip capacity)
  * Expected production halt: 2-4 weeks, recovery: 6-8 weeks
  
- **Direct Exposure Analysis**: Taiwan semiconductor holdings by portfolio
  * SAM Technology & Infrastructure: £43.2M (8.6% of portfolio) - 🚨 HIGH EXPOSURE
  * SAM Global Thematic Growth: £28.1M (5.2% of portfolio) - ⚠️ MODERATE EXPOSURE
  * Other portfolios: £12.7M combined (1.1% average) - 🟢 LOW EXPOSURE
  * Total firm exposure: £84.0M (3.4% of total AUM)
  * Key holdings: Taiwan Semiconductor (TSM) £52M, ASE Technology £18M, others £14M
  
- **Indirect Supply Chain Exposure**: Multi-hop dependency analysis with decay factors
  * **First-Order Dependencies**:
    - Apple: 30% revenue dependency on TSM (High) → Portfolio weight: 8.2% (£41.2M)
    - NVIDIA: 25% revenue dependency on TSM (High) → Portfolio weight: 6.8% (£34.1M)
    - AMD: 18% revenue dependency on TSM (Medium) → Portfolio weight: 3.2% (£16.0M)
  * **Second-Order Dependencies** (50% decay):
    - Tesla: 12% chip dependency on NVIDIA → Effective: 6% post-decay (Medium)
    - Ford: 8% chip dependency on AMD → Effective: 4% post-decay (Low)
  * **Total Indirect Exposure**: £91.3M effective exposure (post-decay weighted)
  * **Combined Direct + Indirect**: £175.3M (7.0% of total AUM)
  
- **Concentration Breach Check** (per Concentration Risk Policy §2.1):
  * Apple: 8.2% 🚨 BREACH (exceeds 7.0% limit, £6.0M over threshold)
  * Microsoft: 7.4% 🚨 BREACH (exceeds 7.0% limit, £2.0M over threshold)
  * NVIDIA: 6.8% ⚠️ WARNING (exceeds 6.5% monitoring threshold)
  * **Note**: Taiwan event exacerbates existing concentration issues
  
- **Financial Health Analysis** (SEC Filing Data):
  | Company | Debt/Equity | Operating Margin | Free Cash Flow | Assessment |
  |---------|-------------|------------------|----------------|------------|
  | Apple | 1.4 | 30% | £72B | Strong - can weather disruption |
  | NVIDIA | 0.3 | 54% | £28B | Exceptional - high margin buffer |
  | AMD | 0.8 | 25% | £8B | Solid - adequate resilience |
  | TSM | 0.4 | 45% | £35B | Strong - recovery capacity |
  
- **Management Commentary** (Earnings Transcripts):
  * NVIDIA CEO (recent quarter): "Diversifying fab partnerships, but TSMC remains primary. Have 90-day supply buffer for critical components."
  * Apple CFO (recent quarter): "Supply chain resilience improved post-COVID. Multiple sourcing for most components, working on geographic diversification."
  * AMD CEO (recent quarter): "TSMC accounts for majority of advanced node production. Alternative sourcing limited near-term but exploring Samsung partnership."
  
- **Analyst Recommendations** (Broker Research):
  * Goldman Sachs (recent): "Taiwan supply chain risk warrants 5-10% valuation discount for semiconductor names. Recommend trim on high-beta names."
  * Morgan Stanley (recent): "Event creates near-term headwind but long-term demand intact. Maintain positions in quality names with strong balance sheets."
  * J.P. Morgan (recent): "Geographic concentration remains key risk. Prefer vertically integrated players with diversified manufacturing."
  
- **Policy Guidance** (Concentration Risk Policy §3.4 - Event Response):
  * Geographic event affecting >5% firm AUM triggers mandatory Investment Committee review
  * Positions already in breach (Apple, Microsoft) require immediate remediation plan
  * Supply chain analysis required for indirect exposures >£50M
  * Documentation timeline: IC memo within 24 hours, full remediation plan within 5 business days
  
- **Investment Committee Memo**: Generated PDF at `@SAM_REPORTS_STAGE/IC_MEMO_Taiwan_Earthquake_Risk_Assessment_20250115_143022.pdf`
  * Executive Summary: £175.3M total exposure (7.0% AUM), 2 concentration breaches exacerbated by event
  * Direct Exposure: £84.0M Taiwan semiconductors (detailed portfolio breakdown)
  * Indirect Exposure: £91.3M through supply chain dependencies (multi-hop analysis)
  * Financial Resilience: Exposed companies show strong balance sheets
  * Management Perspective: Supply buffers 60-90 days, diversification underway
  * Analyst Consensus: Near-term headwind, maintain quality positions
  * Recommendations:
    1. **Immediate** (next 2 trading days): Reduce Apple and Microsoft to policy compliance (£8M combined sales)
    2. **Near-term** (within 2 weeks): Monitor TSMC recovery progress, assess NVIDIA/AMD supply impact
    3. **Medium-term** (30-60 days): Review geographic diversification of semiconductor exposure
  * Risk Assessment: **MODERATE** - Strong company fundamentals offset event impact, existing breaches require action
  * Timeline: Remediation within 45 days, quarterly monitoring thereafter

**Talking Points**:
- **Comprehensive Intelligence**: Single query triggers 9-tool orchestration spanning event data, portfolio analytics, supply chain graphs, SEC filings, document search, policy compliance, and report generation
- **Multi-Dimensional Risk View**: Combines direct exposure, indirect supply chain dependencies, concentration breaches, financial health, management perspective, and analyst views
- **Speed & Completeness**: Complete risk assessment with formal documentation in minutes vs days with manual processes
- **Audit-Ready Output**: Professional Investment Committee memo with complete lineage from event to recommendation
- **Actionable Intelligence**: Specific remediation actions with dollar amounts, timelines, and policy citations

**Key Features Highlighted**: 
- **Multi-Tool Orchestration**: Seamless integration of 9 different tools across structured data, unstructured documents, and report generation
- **Graph Analytics**: Supply chain dependency mapping with multi-hop traversal and decay factors
- **Authentic Data Integration**: 28.7M SEC filing records provide institutional-grade financial analysis
- **Policy-Driven Compliance**: Automatic threshold checking and remediation planning per firm policies
- **Document Intelligence**: AI-powered search across earnings transcripts, broker research, and policy documents
- **Professional Documentation**: Python stored procedure generates audit-ready PDF reports with complete analysis
- **Real-Time Event Response**: Macro event database provides structured event data with severity and sector impact
- **End-to-End Workflow**: From external alert to Investment Committee documentation in single comprehensive query

#### Scenario Wrap-up

**Business Impact Summary**:
- **Response Time**: Complete multi-dimensional risk assessment reduced from 2-3 days to under 10 minutes (99% time savings)
- **Risk Coverage**: Comprehensive view spanning direct exposure, supply chain dependencies, financial health, and market sentiment—eliminating blind spots
- **Decision Quality**: Integrated quantitative and qualitative analysis enables confident, well-documented investment decisions
- **Compliance Efficiency**: Automated policy checking and formal documentation ensures audit readiness and regulatory adherence

**Technical Differentiators**:
- **Multi-Modal AI**: Seamless orchestration across Cortex Analyst (4 semantic views), Cortex Search (5 document types), and custom Python procedures
- **Graph Database Analytics**: Multi-hop supply chain traversal with configurable decay factors and criticality scoring unavailable in traditional systems
- **Authentic Data Integration**: Real SEC filing data (28.7M records) combined with real-time document intelligence for institutional-grade analysis
- **Intelligent Orchestration**: Claude 4 planning dynamically sequences 9 tools based on query requirements and intermediate results
- **Professional Reporting**: Custom Python stored procedures generate audit-ready documentation with complete analytical lineage
- **Policy-Aware AI**: Concentration thresholds and response procedures automatically retrieved from policy documents and applied to analysis
- **Event Intelligence Repository**: Structured macro event database with standardized attributes enables rapid event verification and impact assessment

---

> **Note**: Thematic investment strategy scenarios are included in Part 4 below.

---

### Portfolio Copilot - Complete Investment Analysis (Catch-All)

#### Business Context Setup

**Persona**: Anna, Senior Portfolio Manager at Simulated Asset Management  
**Business Challenge**: Portfolio managers sometimes need a complete investment analysis with a single request when preparing for urgent meetings or responding to time-sensitive situations—requiring the AI to autonomously orchestrate all available tools.  
**Value Proposition**: The Portfolio Copilot demonstrates complete autonomous orchestration by selecting and sequencing all tools from a single comprehensive question, delivering a full investment picture without step-by-step guidance.

**Agent**: `pm_cockpit`  
**Data Available**: 10 portfolios, 14,000+ securities, broker research, earnings transcripts, press releases, policy documents

#### Demo Flow

**Scene Setting**: Anna has 10 minutes before an urgent investment committee call and needs a complete analysis of her Technology & Infrastructure portfolio. There's no time for a multi-step conversation.

##### Step 1: Complete Investment Analysis (All Tools)

**User Input**: 
```
Give me a complete investment analysis for SAM Technology & Infrastructure including top holdings with concentration warnings, latest broker research on key positions, management commentary from recent earnings calls, any significant press releases or corporate developments, and relevant policy thresholds I should be aware of for the investment committee.
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Portfolio holdings, concentration analysis, sector allocation
- `search_external_docs` (Cortex Search) - Latest analyst research on major holdings
- `search_company_events` (Cortex Search) - Management commentary and guidance
- `search_external_docs` (Cortex Search) - Recent corporate developments
- `search_internal_docs` (Cortex Search) - Concentration and mandate policy thresholds

**Expected Response**:
- **Holdings Analysis**: Top positions with weights, concentration flags (>6.5% warning)
- **Research Insights**: Key analyst views on major holdings with ratings
- **Management Commentary**: Relevant earnings call highlights and forward guidance
- **Corporate Developments**: Recent announcements affecting portfolio companies
- **Policy Context**: Applicable concentration limits and mandate requirements
- **Integrated Summary**: Synthesized view with actionable recommendations

**Talking Points**:
- **Autonomous Orchestration**: AI independently selects and sequences all five tools
- **Single-Query Capability**: Complete investment picture from one comprehensive question
- **Committee Ready**: Output structured for investment committee discussion

**Key Features Highlighted**: 
- **Multi-Tool AI Orchestration**: Agent autonomously determines tool sequence and synthesis
- **Quantitative + Qualitative Integration**: Holdings data merged with research and commentary
- **Policy-Aware Analysis**: Automatically includes relevant compliance thresholds

#### Scenario Wrap-up

**Business Impact Summary**:
- **Rapid Response**: Complete investment analysis available in under 2 minutes
- **Comprehensive View**: Combines analytics, research, and policy in single output
- **Decision Quality**: Better-informed decisions from integrated multi-source analysis

**Technical Differentiators**:
- **Five-Tool Integration**: Demonstrates full Portfolio Copilot capability in single query
- **Intelligent Synthesis**: AI merges quantitative and qualitative insights coherently
- **Autonomous Operation**: True AI agent capability beyond simple Q&A


---

## Part 2: Attribution & Risk Decomposition

## Attribution Analyst

### Portfolio Manager Co-Pilot - Performance Decomposition Deep Dive

#### Business Context Setup

**Persona**: Victoria Chen, Chief Investment Officer at Simulated Asset Management  
**Business Challenge**: Understanding the true drivers of portfolio performance requires decomposing returns into allocation decisions vs. security selection vs. factor exposures. Traditional attribution reports are static, backward-looking, and require multiple systems. The CIO needs instant answers to board questions about why portfolios outperformed or underperformed benchmarks, what hidden risks exist, and how portfolios would behave under stress scenarios.  
**Value Proposition**: AI-powered attribution intelligence provides instant, multi-dimensional performance decomposition combining Brinson attribution, factor analysis, hidden risk detection, and stress testing in a single conversational interface. Real-time answers enable confident board presentations and rapid investment decision-making.

**Agent**: `AM_portfolio_manager_copilot`  
**Data Available**: 24 months of monthly attribution data across 11 portfolios, 11 GICS sectors, 7 systematic factors, 5 hidden factors, 10 stress scenarios. Brinson and factor attribution are computed from **real market data** (stock prices, sector ETF returns, and SEC financials sourced via Snowflake Marketplace). Portfolio weights are dynamic based on real close prices.

#### Demo Flow

**Scene Setting**: Victoria is preparing for the quarterly board meeting where she needs to explain portfolio performance relative to its benchmark. The board will want a clear decomposition of returns — whether the portfolio outperformed or underperformed — and will ask tough questions about risk exposures and how the portfolio would perform in a crisis.

**Note**: Attribution data reflects real market conditions. The portfolio may outperform or underperform depending on the quarter. **Before presenting**, run the Step 1 question to see the current numbers. Both outcomes make compelling demos:
- **Outperformance quarter**: Highlights what's working — which sector bets and stock picks are generating alpha
- **Underperformance quarter**: Often the *stronger* demo — shows the agent diagnosing problems, identifying the exact source of the drag, and recommending corrective actions. This is when a CIO needs the tool most.

##### Step 1: Brinson Attribution Overview

**Skill Activated**: `multi-level-attribution`
**Workflow**: Sector attribution → STOPPING POINT → [user choice] → drill-down → synthesis
**Demo Value**: One question triggers a structured analytical workflow with interactive checkpoints

**User Input**: 
```
Break down the performance attribution for SAM Global Flagship portfolio versus S&P 500 for the most recent quarter. What drove our performance?
```

**Tools Used**:
- `server_skill` — Loads multi-level-attribution skill
- `brinson_analyzer` (Cortex Analyst) - Retrieves Brinson decomposition into allocation, selection, and interaction effects

**Expected Response**:
- **Attribution Summary**: Portfolio vs benchmark returns with active return breakdown. The agent will automatically frame the narrative around outperformance or underperformance based on the actual data.
- **Sector Breakdown**: Allocation and selection effects by sector (all 11 GICS sectors, including 0-weight benchmark-only sectors like Real Estate and Utilities)
- **Key Insight**: Selection effect typically dominates because the portfolio holds concentrated positions (~45 stocks) vs the broad benchmark (500 stocks). In underperformance quarters, this means specific stock picks are the primary drag; in outperformance quarters, stock picking is the primary driver of alpha.
- **Brinson Identity Check**: Active return = Allocation + Selection + Interaction (holds exactly — mathematically guaranteed)
- **Data Coverage**: 3 monthly data points for a quarter (month-end dates)
- **Actionable Recommendations**: The agent will suggest corrective actions (review underperforming holdings, reassess sector conviction) when underperforming, or reinforcement actions (maintain conviction, monitor risk) when outperforming

**Talking Points**:
- Brinson-Fachler attribution is the industry standard for performance decomposition
- Instant decomposition eliminates days of manual analysis
- Clear separation of "right sectors" (allocation) vs "right stocks" (selection)
- The agent adapts its narrative to the data — it doesn't assume good or bad performance, it diagnoses what actually happened and recommends next steps

**Key Features Highlighted**: 
- Cortex Analyst semantic layer over attribution fact tables
- **Computed from real stock prices (sourced via Snowflake Marketplace)** — portfolio sector returns are weighted averages of actual stock returns, not synthetic data
- Benchmark returns from real SPDR sector ETFs (XLK, XLF, XLV, etc.)
- Industry-standard Brinson-Fachler methodology
- Adaptive narrative: works equally well for outperformance and underperformance quarters

##### Step 1b: Multi-Level Attribution Drill-Down (Stopping Point Continuation)

**Presenter Transition**:
> "Notice the agent paused and offered drill-down options — this is the multi-level-attribution skill's stopping point. The PM can choose to drill into a sector, pivot to country, or see linked periods. This is the key differentiator from traditional attribution tools — it's not just data retrieval, it's a structured analytical workflow with checkpoints. Let me choose country..."

*Reasoning: The skill's stopping point demonstrates interactive workflow orchestration. The agent doesn't just dump data — it presents a summary, then offers contextual next steps.*

**User Input**: 
```
Now show me this by country — which countries drove outperformance last quarter?
```

**Tools Used**:
- `brinson_analyzer` (Cortex Analyst) - Queries FACT_BRINSON_ATTRIBUTION_DETAIL with grouping_dimension = 'COUNTRY'

**Expected Response**:
- Country-level attribution table with allocation and selection effects for each country (26 countries)
- US dominates by weight but may not be the largest contributor
- International holdings (GB, CN, CA) may show outsized effects relative to their small weights
- Active weight column showing over/underweight vs benchmark

**Talking Points**:
- Same Brinson-Fachler methodology applied to any grouping dimension
- The Rainardi insight: "same data, different classification produces different attribution results" — sector vs country decomposition tells different stories
- Country attribution is particularly valuable for global mandates

**Key Features Highlighted**: 
- Multi-level attribution from a single generalised table (FACT_BRINSON_ATTRIBUTION_DETAIL)
- Instant pivot between sector, country, and industry without recalculation
- Industry drill-down via parent_grouping_value hierarchy

**User Input** (follow-up): 
```
Drill down into Information Technology — what industries within tech contributed?
```

**Tools Used**:
- `brinson_analyzer` (Cortex Analyst) - Queries grouping_dimension = 'INDUSTRY' with parent_grouping_value = 'Information Technology'

**Expected Response**:
- Industry-level breakdown within Technology sector
- Semiconductors, Software, IT Services etc. with allocation and selection effects
- Identifies whether tech outperformance is broad-based or concentrated in specific sub-industries

**Talking Points**:
- Hierarchical drill-down from sector to industry — the Rainardi pattern from real AM data warehouses
- This is how portfolio managers actually think: "Tech overweight worked, but was it semis or software?"
- In production, this hierarchy would extend to individual securities

##### Step 2: Factor Attribution Drill-Down

**Presenter Transition** (adapt based on Step 1 results):
> *If underperformance*: "The Brinson analysis identified stock selection as the main drag. But *why* did our stock picks underperform? Were we over-exposed to certain risk factors? Let me pivot to factor-based attribution to find the systematic explanation..."
> *If outperformance*: "We've seen the sector-level attribution. But board members will ask — is this alpha from skill, or are we simply riding factor tailwinds? Let me show how we can instantly decompose the factor exposures..."

*Reasoning: Brinson shows sector effects but doesn't explain systematic risk exposures. Factor attribution provides the "why behind the why" for sophisticated board members.*

**User Input**: 
```
What factor exposures drove our returns? Show me the contribution from all systematic factors.
```

**Tools Used**:
- `factor_analyzer` (Cortex Analyst) - Retrieves factor-based return attribution

**Expected Response**:
- **Factor Contributions**: Return contribution from each systematic factor, computed from **real data**:
  | Factor | How Computed |
  |--------|-------------|
  | Market | Real beta from regression of stock returns vs SPX |
  | Value | Real P/E ratios from SEC financial filings |
  | Growth | Real revenue growth from SEC filings |
  | Momentum | Real 12-month price momentum |
  | Quality | Real ROE + operating margin + leverage from SEC filings |
  | Size | Real market cap (price × shares outstanding) |
  | Volatility | Real 60-day rolling standard deviation of returns |
- **Exposure**: Portfolio-weighted average of security-level factor scores from FACT_FACTOR_EXPOSURES
- **Factor Returns**: Long-short quintile returns (top vs bottom 20% of stocks by factor score)

**Talking Points**:
- Factor attribution computed from **real security-level data** — not synthetic
- Exposures from real regression betas, SEC financials, and market cap data
- Factor returns from actual long-short quintile portfolio performance
- Identifies whether returns came from skill or factor bets — critical for both good and bad quarters

**Key Features Highlighted**: 
- Real factor model built from stock prices and SEC financial data (sourced via Snowflake Marketplace)
- Portfolio-weighted exposure aggregation from 503-security universe
- Quintile-based factor return estimation (industry-standard methodology)

##### Step 3: Hidden Factor Detection

**Presenter Transition** (adapt based on Steps 1-2):
> *If underperformance*: "We've identified selection drag and the factor exposures behind it. But could there be hidden concentrations — AI exposure, geopolitical risk — that our traditional models aren't capturing? This is where AI goes beyond standard attribution..."
> *If outperformance*: "Traditional factors explain about 70% of returns. But what about emerging themes like AI exposure or geopolitical risks that aren't in standard models? Let me check for hidden factors the board should know about..."

*Reasoning: Hidden factors represent uncompensated or emerging risks not captured by traditional factor models. This demonstrates AI sophistication beyond standard attribution.*

**User Input**: 
```
What hidden or alternative factor exposures exist in the portfolio? Are we unknowingly concentrated in AI-related stocks or exposed to geopolitical risks?
```

**Tools Used**:
- `hidden_factors` (Cortex Analyst) - Retrieves AI-detected hidden factor exposures

**Expected Response**:
- **Hidden Factor Exposures**: Portfolio exposure to non-traditional factors
  | Factor | Description |
  |--------|-------------|
  | AI_Exposure | Concentration in AI/ML beneficiary stocks |
  | Reshoring_Benefit | Supply chain relocalisation exposure |
  | Rate_Convexity | Interest rate sensitivity beyond duration |
  | Climate_Transition | Green transition winners/losers exposure |
  | Geopolitical_Risk | Country/region tension sensitivity |
- **Concentration Flags**: High exposure warnings
- **Trend Analysis**: How exposures have changed over time

**Talking Points**:
- Hidden factors are computed from **real SEC filing data and AI analysis of earnings call transcripts** — not simulated
- AI_Exposure combines keyword matching on SEC business segments (Cloud, Data Center, GPU, etc.) with AI_AGG scoring of earnings call text (uses AI because transcript text is unstructured)
- Geopolitical_Risk is a **deterministic SQL calculation** — geographic revenue from SEC segments classified via a risk-tier lookup table (DIM_GEO_RISK_CLASSIFICATION: 189 geographies → HIGH/MEDIUM/LOW), weighted by revenue share with concentration bonuses. No AI needed for structured numeric data.
- Rate_Convexity uses real debt-to-equity and current liability ratios from SEC financials
- Climate_Transition maps GICS sector carbon intensity combined with ESG environmental scores
- All factors are z-scored cross-sectionally and aggregated using real portfolio position weights
- In production, these could also be sourced from specialist providers such as MSCI (Barra thematic factors), Axioma (custom risk models), BlackRock Aladdin (thematic baskets)

**Key Features Highlighted**: 
- AI-powered factor discovery
- Thematic risk detection
- Forward-looking risk identification

##### Step 4: Stress Scenario Analysis

**Presenter Transition**:
> "The board will inevitably ask 'what happens if there's a market crash?' Let me show you how we can instantly stress test the portfolio against historical and hypothetical scenarios..."

*Reasoning: Board members always want to understand downside scenarios. Stress testing demonstrates robust risk management and preparedness.*

**User Input**: 
```
How would our portfolio perform in a 2008-style financial crisis? Also show me the impact of a sudden 200bp rate hike scenario.
```

**Tools Used**:
- `stress_scenarios` (Cortex Analyst) - Retrieves stress scenario definitions and factor shocks

**Expected Response**:
- **Scenario Analysis**: Portfolio impact under each stress scenario
  | Scenario | Description |
  |----------|-------------|
  | Name | Scenario identifier |
  | Factor Shocks | Magnitude of factor movements |
  | Estimated Impact | Portfolio loss/gain estimate |
  | Vulnerable Positions | Most affected holdings |
- **Historical Comparison**: How similar scenarios played out historically
- **Mitigation Options**: Potential hedging or rebalancing actions

**Talking Points**:
- Instant stress testing enables confident board responses
- Both historical and hypothetical scenarios available
- Connects factor exposures to real-world crisis impacts

**Key Features Highlighted**: 
- Pre-built historical and hypothetical stress scenarios
- Factor-based stress transmission
- Actionable risk mitigation suggestions

#### Scenario Wrap-up

**Business Impact Summary**:
- **Board Readiness**: Complete performance narrative prepared in minutes instead of days
- **Risk Transparency**: Hidden exposures and stress vulnerabilities identified proactively
- **Decision Speed**: Real-time attribution enables faster rebalancing decisions
- **Stakeholder Confidence**: Data-driven answers to any attribution question

**Technical Differentiators**:
- **Unified Attribution Platform**: Brinson, factor, hidden factor, and stress analysis in one agent
- **AI-Powered Hidden Factors**: Detection of emerging risks beyond traditional models
- **Real-Time Calculation**: No batch processing delays - instant answers from live data
- **Natural Language Interface**: No SQL or programming required for sophisticated analysis

##### Step 5: Intelligent Driver Discovery (Synthesis)

**Presenter Transition**:
> "We've looked at Brinson, factors, and hidden factors individually. But the real power is when the agent synthesises all three to tell us the *true* story of what drove performance..."

*Reasoning: Demonstrates cross-tool synthesis — the agent combines multiple data sources to deliver a unified narrative that goes beyond what any single analysis provides.*

**User Input**: 
```
Looking at everything together — Brinson, factor exposures, and hidden factors — what are the true drivers of our Flagship portfolio's performance? Is our alpha from real stock-picking skill, or are we riding factor tailwinds?
```

**Tools Used**:
- `brinson_analyzer` + `factor_analyzer` + `hidden_factor_analyzer` (multi-tool synthesis)

**Expected Response**:
- **Unified Narrative**: The agent cross-references Brinson selection effect with factor contributions and hidden factor overlaps
- **True Alpha Assessment**: "Selection effect was +1.2%, but 0.8% is attributable to unintended Momentum exposure in mid-cap tech. Hidden factor analysis shows elevated AI_Exposure (z-score 1.4). Estimated true stock-picking alpha after factor adjustment: ~0.4%."
- **Factor Tailwind/Headwind Decomposition**: Clear separation of systematic vs idiosyncratic returns
- **Actionable Insight**: Whether to maintain current exposures or adjust

**Talking Points**:
- This is the "killer question" that boards actually ask — cross-tool synthesis required
- The agent orchestrates 3 tools and synthesises the results intelligently
- Demonstrates that the platform isn't just retrieval — it's analytical reasoning

---

### Portfolio Manager Co-Pilot - Macro Regime Analysis

#### Business Context Setup

**Persona**: Victoria Chen, Chief Investment Officer at Simulated Asset Management  
**Business Challenge**: Portfolio positioning should adapt to changing market conditions. Understanding the current macro regime helps determine whether growth vs. value tilts are appropriate, and whether risk-on or risk-off positioning is warranted.  
**Value Proposition**: AI-powered regime classification based on market volatility and direction, with historical context and positioning recommendations.

**Agent**: `AM_portfolio_manager_copilot`  
**Data Available**: VIX data, market returns, regime classification history

#### Demo Flow

**Scene Setting**: Victoria is reviewing market conditions to determine if portfolio positioning needs adjustment based on the current macro environment.

##### Step 1: Current Regime Classification

**User Input**: 
```
What is the current macro regime? Are we in a risk-on or risk-off environment?
```

**Tools Used**:
- `macro_regime` (Cortex Analyst) - Query regime classification from VIX and market returns

**Expected Response**:
- Classification of current volatility regime (LOW_VOL, NORMAL, ELEVATED, HIGH_VOL)
- Classification of market direction (RISK_ON, RISK_OFF, TRANSITIONAL, NEUTRAL)
- Historical context for current regime
- How long current regime has persisted
- Typical factor performance in this regime
- Suggested positioning based on regime

**Talking Points**:
- Quantitative regime classification removes subjectivity
- Historical context shows what has worked in similar environments
- Positioning suggestions grounded in data

**Key Features Highlighted**: 
- VIX-based volatility classification
- Market direction analysis
- Historical regime comparison

##### Step 2: Historical Regime Performance

**Presenter Transition**:
> "We're in an elevated volatility environment. Let me check how different factor strategies have performed in similar historical periods..."

*Reasoning: Current regime identification needs historical context to inform positioning decisions.*

**User Input**: 
```
How have value vs growth performed in the current regime historically? When was the last time we were in a high volatility regime?
```

**Tools Used**:
- `macro_regime` (Cortex Analyst) - Query historical regime data and factor performance

**Expected Response**:
- Factor performance by regime (value vs growth in elevated vol)
- Historical high volatility regime dates
- Duration and market events associated with past regimes
- Recovery patterns and timing

**Talking Points**:
- Historical analysis informs current positioning
- Pattern recognition across market cycles
- Risk management through regime awareness

**Key Features Highlighted**: 
- Historical regime database
- Factor performance by regime
- Pattern analysis

##### Step 3: Path-Dependent Regime Attribution

**Presenter Transition**:
> "Now let me show something more sophisticated — how our factor exposures and contributions have evolved *month by month* through regime transitions..."

**User Input**: 
```
Show me the month-by-month factor contribution path for our Flagship portfolio. When did our Growth tilt help vs hurt, and how does that align with regime transitions?
```

**Tools Used**:
- `rolling_analytics_analyzer` (Cortex Analyst) - Retrieves rolling contribution paths with regime overlay

**Expected Response**:
- Monthly contribution timeline per factor with regime labels
- Identification of when tilts were additive vs destructive
- Regime transition points highlighted
- Decision evaluation: "Growth tilt contributed +0.3% in Jan (risk-on), -0.8% in Mar (risk-off transition)"

**Talking Points**:
- Path-dependent analysis shows *when* decisions helped vs hurt — not just endpoints
- Regime overlay explains adverse timing vs bad conviction
- Rolling analytics are a differentiated capability beyond standard attribution

#### Scenario Wrap-up

**Business Impact Summary**:
- **Positioning Confidence**: Data-driven regime analysis for portfolio decisions
- **Risk Awareness**: Understanding of current market environment
- **Historical Context**: Learning from past regime behavior

**Technical Differentiators**:
- **Quantitative Classification**: Objective regime determination
- **Factor Regime Analysis**: How factors behave in different environments
- **Historical Database**: Years of regime data for comparison

---

### Portfolio Manager Co-Pilot - Sector Attribution Deep Dive

#### Business Context Setup

**Persona**: Victoria Chen, Chief Investment Officer at Simulated Asset Management  
**Business Challenge**: Portfolio managers need to understand sector-level performance drivers to determine whether active returns — positive or negative — came from sector allocation decisions or stock selection within sectors.  
**Value Proposition**: AI-powered sector attribution providing detailed breakdown of allocation and selection effects by sector, enabling precise attribution of performance and identification of areas for improvement.

**Agent**: `AM_portfolio_manager_copilot`  
**Data Available**: Sector-level Brinson attribution, sector weights and returns

#### Demo Flow

**Scene Setting**: Victoria needs to explain sector-level performance contributions to the investment committee.

##### Step 1: Sector Contribution Ranking

**User Input**: 
```
Which sectors had the biggest impact on our active return last month? Show me both allocation and selection effects by sector.
```

**Tools Used**:
- `brinson_analyzer` (Cortex Analyst) - Query FACT_BRINSON_BY_SECTOR for detailed sector breakdown

**Expected Response**:
- Portfolio weight vs benchmark weight by sector
- Portfolio return vs benchmark return by sector
- Allocation, selection, and interaction effects by sector
- Sector contribution ranking
- Over/underweight analysis
- Stock selection alpha by sector

**Talking Points**:
- Sector-level granularity for precise attribution
- Clear separation of weight vs stock selection effects
- Ranking identifies biggest contributors

**Key Features Highlighted**: 
- Sector-level Brinson decomposition
- Weight and return comparison
- Contribution ranking

##### Step 2: Position-Level Drill-Down

**Presenter Transition** (adapt to data):
> *If Tech was a detractor*: "Technology had the largest negative selection effect. Let me drill into which specific stocks caused the drag..."
> *If Tech was a contributor*: "Technology had strong selection effect. Let me identify which specific stocks drove that performance..."

*Reasoning: Sector attribution identifies contributors; position-level analysis provides accountability.*

**User Input**: 
```
Which technology stocks drove our selection effect? What was our allocation to healthcare vs. the benchmark?
```

**Tools Used**:
- `brinson_analyzer` (Cortex Analyst) - Query position-level attribution

**Expected Response**:
- Technology holdings with individual contribution
- Top contributors and detractors within sector
- Healthcare weight comparison (portfolio vs benchmark)
- Interaction effect analysis

**Talking Points**:
- Position-level accountability
- Identifies winning and losing stock picks
- Weight analysis for allocation decisions

**Key Features Highlighted**: 
- Position-level attribution
- Sector weight comparison
- Contribution decomposition

#### Scenario Wrap-up

**Business Impact Summary**:
- **Attribution Precision**: Sector and position-level performance understanding
- **Accountability**: Clear identification of allocation vs selection decisions
- **Decision Support**: Data for future sector allocation decisions

**Technical Differentiators**:
- **Multi-Level Attribution**: Portfolio → Sector → Position hierarchy
- **Complete Decomposition**: Allocation, selection, and interaction
- **Real-Time Calculation**: Instant sector-level analysis

---

### Portfolio Manager Co-Pilot - Hidden Factor Alert

#### Business Context Setup

**Persona**: Victoria Chen, Chief Investment Officer at Simulated Asset Management  
**Business Challenge**: Risk managers need to monitor portfolios for emerging concentrations in non-traditional risk factors that aren't captured by standard models.  
**Value Proposition**: AI-powered hidden factor monitoring with automatic alerting when exposures exceed thresholds, enabling proactive risk management.

**Agent**: `AM_portfolio_manager_copilot`  
**Data Available**: Hidden factor exposures across portfolios

#### Demo Flow

**Scene Setting**: Victoria is conducting a risk review to identify any hidden concentrations that require attention.

##### Step 1: Hidden Factor Scan

**User Input**: 
```
Alert me to any hidden factor exposures above 0.5. What thematic risks should I be concerned about?
```

**Tools Used**:
- `hidden_factors` (Cortex Analyst) - Scan FACT_HIDDEN_FACTOR_EXPOSURES for high exposures

**Expected Response**:
- Concentrations exceeding threshold flagged
- Portfolios ranked by hidden factor exposure
- Diversification or hedging suggestions
- Key alerts:
  - AI exposure concentration in tech-heavy portfolios
  - Rate convexity in financial-heavy portfolios
  - Climate transition exposure in energy portfolios

**Talking Points**:
- Proactive identification of emerging risks
- Threshold-based alerting for risk management
- Actionable hedging recommendations

**Key Features Highlighted**: 
- Threshold-based alerting
- Portfolio ranking by exposure
- Hedging suggestions

##### Step 2: Anomaly Cross-Reference

**Presenter Transition**:
> "We've seen the hidden factor exposures. But are any portfolios showing abnormal behaviour — style drift, factor dominance, or unexpected concentration?"

**User Input**: 
```
Run an anomaly scan across all portfolios. Flag any factor drift, style inconsistency, or concentration alerts.
```

**Tools Used**:
- `anomaly_detector` (Cortex Analyst) - Scans V_ATTRIBUTION_ANOMALIES for all flags

**Expected Response**:
- Anomaly summary by portfolio with severity (HIGH/MEDIUM/LOW)
- Specific flags: factor drift alerts, concentration warnings, style inconsistency
- Example: "SAM US Value Equity flagged for STYLE_INCONSISTENCY — Growth exposure exceeds Value exposure"
- Prioritised risk dashboard

**Talking Points**:
- Five distinct anomaly types catch different risk dimensions
- Style inconsistency detects when a portfolio drifts from its stated mandate
- Automated anomaly detection replaces manual risk committee reviews

#### Scenario Wrap-up

**Business Impact Summary**:
- **Proactive Risk Management**: Emerging risks identified before materializing
- **Concentration Awareness**: Hidden exposures surfaced
- **Actionable Intelligence**: Specific recommendations for risk reduction

**Technical Differentiators**:
- **AI-Detected Factors**: Beyond traditional factor models
- **Threshold Alerting**: Automatic flagging of concerning exposures
- **Portfolio Comparison**: Relative exposure across strategies

---

### Portfolio Manager Co-Pilot - Custom Stress Test

#### Business Context Setup

**Persona**: Victoria Chen, Chief Investment Officer at Simulated Asset Management  
**Business Challenge**: CIOs need to test specific market scenarios beyond pre-built stress tests, such as custom combinations of factor shocks or hypothetical events.  
**Value Proposition**: AI-powered custom stress testing that maps user-defined scenarios to factor shocks and calculates portfolio impact.

**Agent**: `AM_portfolio_manager_copilot`  
**Data Available**: Factor exposures, stress scenario framework

#### Demo Flow

**Scene Setting**: Victoria wants to test a specific market scenario that isn't in the pre-built stress library.

##### Step 1: Custom Scenario Definition

**User Input**: 
```
What would happen to our portfolio if the VIX spiked to 45 and growth stocks fell 25%?
```

**Tools Used**:
- `stress_scenarios` (Cortex Analyst) - Map custom scenario to factor shocks and calculate impact

**Expected Response**:
- Mapping of scenario to factor shocks
- Portfolio impact calculation based on exposures
- Most vulnerable positions identified
- Comparison to historical similar events (2020 COVID crash, 2022 growth selloff)
- Estimated portfolio loss
- Position-level impact ranking

**Talking Points**:
- Custom scenario capability beyond pre-built tests
- Factor-based transmission mechanism
- Historical comparison for context

**Key Features Highlighted**: 
- Custom scenario mapping
- Factor-based impact calculation
- Historical event comparison

##### Step 2: Alpha Robustness Assessment

**Presenter Transition**:
> "That custom scenario is useful, but the board will ask: 'How robust is our alpha across *all* scenarios?' Let me run a full sensitivity sweep..."

**User Input**: 
```
How robust is our Flagship portfolio's alpha across all stress scenarios? Run a sensitivity analysis for a rate shock at 1.5x severity.
```

**Tools Used**:
- `scenario_sensitivity` (Stored Procedure) - RUN_SCENARIO_SENSITIVITY_TOOL with RATE_SHOCK, magnitude 1.5

**Expected Response**:
- Factor sensitivity ranking: which factors are most affected
- Estimated total portfolio impact percentage
- Robustness assessment: min/max/median estimated return across all 10 stress scenarios
- Worst-case and best-case scenario identification
- Interpretation text

**Talking Points**:
- Parameterised scenarios — adjust severity with a multiplier
- Multi-scenario sweep provides robustness confidence
- Board can see the full range of outcomes, not just one scenario
- Sensitivity ranking shows which factor bets carry the most risk

#### Scenario Wrap-up

**Business Impact Summary**:
- **Scenario Flexibility**: Test any hypothetical market condition
- **Impact Quantification**: Precise portfolio loss estimation
- **Historical Context**: Comparison to past similar events

**Technical Differentiators**:
- **Custom Scenario Mapping**: Any user-defined conditions
- **Factor Transmission**: Sophisticated impact calculation
- **Position-Level Detail**: Identifies most vulnerable holdings

---

### Portfolio Manager Co-Pilot - Anomaly Dashboard & Risk Scanning

#### Business Context Setup

**Persona**: Victoria Chen, Chief Investment Officer at Simulated Asset Management  
**Business Challenge**: Managing 11 portfolios across different strategies requires systematic monitoring for anomalous behaviour — factor drift, style inconsistency, concentration risk, and attribution spikes. Manual review is time-consuming and error-prone.  
**Value Proposition**: Automated anomaly detection across all portfolios with severity-ranked alerts, enabling the risk team to focus on the highest-priority issues.

**Agent**: `AM_portfolio_manager_copilot`  
**Data Available**: V_ATTRIBUTION_ANOMALIES with 9 anomaly types, severity scoring across all portfolios

#### Demo Flow

**Scene Setting**: Victoria is conducting the weekly risk review. She wants a quick scan of all portfolios for any abnormal behaviour before diving into specifics.

##### Step 1: Portfolio-Wide Anomaly Scan

**Skill Activated**: `attribution-anomaly-scan`
**Workflow**: Scan all portfolios → present by severity → STOPPING POINT → drill into flagged portfolio
**Demo Value**: One question triggers a complete risk scan with automated severity ranking and drill-down offers

**User Input**: 
```
Run a risk scan across all portfolios. Flag anything concerning.
```

**Tools Used**:
- `server_skill` — Loads attribution-anomaly-scan skill
- `anomaly_detector` (Cortex Analyst) - Scans latest month anomaly flags (9 detection rules)

**Expected Response**:
- All portfolios ranked by anomaly severity (HIGH/MEDIUM/LOW)
- HIGH severity portfolios listed with specific flags (factor drift, allocation drift, selection reversal, weight concentration, classification sensitivity, style inconsistency)
- STOPPING POINT: "Found [N] HIGH severity items. I can drill into a specific portfolio's attribution, show the drift timeline, or run a stress test on the flagged portfolio."

##### Step 2: Drill Into Flagged Portfolio (Stopping Point Continuation)

**Presenter Transition**:
> "The skill's stopping point offered three options. This is how the anomaly scan becomes actionable — it doesn't just flag, it offers the logical next analytical step. Let me choose the drift timeline..."

**User Input**: 
```
Show me the drift timeline for the highest severity portfolio.
```

**Tools Used**:
- `rolling_analytics_analyzer` (Cortex Analyst) - Retrieves drift history for flagged portfolio

**Expected Response**:
- Month-by-month exposure drift z-scores for the flagged factor
- Timeline showing when drift started increasing
- Whether drift is accelerating or stabilising

##### Step 3: Forward-Looking Risk Assessment

**User Input**: 
```
Given those anomalies, run a scenario sensitivity to see how vulnerable this portfolio is to a volatility spike.
```

**Tools Used**:
- `scenario_sensitivity` (Stored Procedure) - VOL_SPIKE scenario for flagged portfolio

**Expected Response**:
- Factor sensitivity ranking
- Estimated impact highlighting the drifted factor's contribution
- Robustness assessment across all scenarios

**Talking Points**:
- Three-tool workflow: scan → drill → assess
- Anomaly detection + rolling analytics + scenario sensitivity in one conversation
- Demonstrates the Risk Scanning workflow from agent orchestration

---

### Portfolio Manager Co-Pilot - Cross-Portfolio Peer Learning

#### Business Context Setup

**Persona**: Victoria Chen, Chief Investment Officer at Simulated Asset Management  
**Business Challenge**: With 11 portfolios under management, the CIO needs to identify which strategies consistently generate alpha, which have systematic weaknesses, and what can be learned from top performers to improve underperformers.  
**Value Proposition**: Cross-portfolio analytics enable institutional learning — identifying repeatable alpha sources, decision-making patterns, and factor skill across the platform.

**Agent**: `AM_portfolio_manager_copilot`  
**Data Available**: V_CROSS_PORTFOLIO_ANALYTICS with trailing 12-month attribution statistics per portfolio

#### Demo Flow

**Scene Setting**: Victoria is preparing the annual strategy review. She wants to compare all portfolios to identify best practices and areas for improvement.

##### Step 1: Alpha Persistence Ranking

**User Input**: 
```
Rank all portfolios by alpha persistence over the trailing 12 months. Which strategies most consistently generate positive active returns?
```

**Tools Used**:
- `peer_learning_analyzer` (Cortex Analyst) - Queries V_CROSS_PORTFOLIO_ANALYTICS

**Expected Response**:
- All 11 portfolios ranked by ALPHA_PERSISTENCE (% months with positive active return)
- Allocation and selection consistency scores (lower = more repeatable)
- Best and worst factor source for each portfolio
- Best selection sector for each portfolio

##### Step 2: Repeatable Alpha Sources

**User Input**: 
```
Which portfolios have the most consistent selection effect? What sectors and factors are driving repeatable alpha?
```

**Tools Used**:
- `peer_learning_analyzer` (Cortex Analyst) - Queries selection consistency and factor sources

**Expected Response**:
- Portfolios ranked by SELECTION_CONSISTENCY (lowest stddev = most repeatable)
- Best selection sector for each
- Pattern identification: "Tech & Infrastructure consistently generates selection alpha in Technology"
- Cross-strategy insights on factor skill

**Talking Points**:
- Peer learning is a differentiated capability — most attribution tools analyse one portfolio at a time
- Identifies which decisions are skill vs luck across the platform
- Enables knowledge transfer from top-performing to underperforming strategies
- Trailing 12-month window captures a full market cycle

---

### Portfolio Manager Co-Pilot - Forward-Looking Expected Attribution

#### Business Context Setup

**Persona**: Victoria Chen, Chief Investment Officer at Simulated Asset Management  
**Business Challenge**: Traditional attribution is backward-looking. The board wants to know: "Given our current positioning, what will drive returns *going forward* under different scenarios?"  
**Value Proposition**: Scenario sensitivity analysis combined with current factor exposures provides forward-looking attribution — decomposing expected returns by factor under various market conditions.

**Agent**: `AM_portfolio_manager_copilot`  
**Data Available**: Current factor exposures, stress scenarios, scenario sensitivity tool

#### Demo Flow

**Scene Setting**: Victoria is presenting to the board about portfolio positioning and expected performance under different scenarios.

##### Step 1: Forward-Looking Factor Sensitivity

**User Input**: 
```
If rates rise 100bps, which attribution buckets matter most for our Flagship portfolio? What factors will dominate our returns?
```

**Tools Used**:
- `scenario_sensitivity` (Stored Procedure) - RATE_SHOCK scenario at 1.0x magnitude

**Expected Response**:
- Factor sensitivity ranking for the rate shock
- Most affected factors with exposure × shock breakdown
- Total estimated portfolio impact
- Interpretation: "Under a rate shock, Volatility and Growth are most affected. Your Growth overweight (-0.10 shock × 0.25 exposure) drives most of the estimated -3.2% impact."

##### Step 2: Multi-Scenario Robustness

**User Input**: 
```
Now show me the robustness assessment. How does our alpha hold up across all 10 stress scenarios?
```

**Tools Used**:
- `scenario_sensitivity` (Stored Procedure) - BROAD_MARKET scenario (triggers full sweep)

**Expected Response**:
- Min/max/median estimated return across all 10 scenarios
- Worst and best scenario identification
- Range analysis: "Returns range from -8.2% (Liquidity Crunch) to -1.1% (USD Strengthening). Median: -4.3%."

**Talking Points**:
- Forward-looking attribution answers "what will matter next" — not "what happened last quarter"
- Board members prefer forward-looking risk framing
- Multi-scenario sweep provides confidence bounds, not just point estimates

---

### Portfolio Manager Co-Pilot - Multi-Audience Narrative Demo

#### Business Context Setup

**Persona**: Victoria Chen, Chief Investment Officer at Simulated Asset Management  
**Business Challenge**: The same attribution analysis needs to be communicated differently to the board (themes only), the PM team (full detail), and external clients (plain English). Currently this requires 3 separate reports.  
**Value Proposition**: The agent automatically adapts narrative depth based on audience, generating board-level themes, PM-level decision detail, or client-friendly plain English from the same underlying data.

**Agent**: `AM_portfolio_manager_copilot`  
**Data Available**: Full attribution data set

#### Demo Flow

**Scene Setting**: Victoria needs to explain the same Q4 performance to three different audiences in the next hour.

##### Step 1: Board-Level Summary

**Skill Activated**: `attribution-report-generator` (detects "CIO-level" → executive audience tier)
**Workflow**: Sector attribution → anomaly check → synthesise into executive format
**Demo Value**: One prompt triggers the full 5-step report workflow, automatically formatted for the detected audience

**User Input**: 
```
Generate a quarterly attribution report for SAM Global Flagship — board-level summary for the CIO.
```

**Expected Response**:
- The agent loads the attribution-report-generator skill
- Runs sector attribution + anomaly check automatically (Steps 1-3 of the skill)
- Presents executive-format output:
  - 1-2 sentence headline: outperformed/underperformed
  - 2-3 key drivers as bullet points
  - Any HIGH severity risk flags
  - NO tables, NO individual positions
- Stops with: "Would you like the PM-level detail, a client version, or shall I add currency analysis?"

**Talking Points**:
- One question triggered a complete multi-tool workflow
- The skill automatically detected "board-level" and applied executive formatting
- No manual tool selection needed — the skill orchestrated everything

##### Step 2: PM-Level Detail (Stopping Point Continuation)

**Presenter Transition**:
> "Notice the agent offered to produce different audience versions at the stopping point. This eliminates the need to re-run the analysis — the data is already gathered, we just change the presentation layer. Let me ask for the PM version..."

**User Input**: 
```
Now give me the PM-level version with full attribution tables and factor breakdown.
```

**Expected Response**:
- Full attribution table with allocation, selection, interaction effects by sector
- Factor contribution breakdown with exposures
- Decision accountability: "The Materials overweight was the wrong call — sector underperformed by 8.2%"
- Specific recommendations

##### Step 3: Client-Level Plain English

**User Input**: 
```
Now write this for a client report in plain English. No jargon, no factor names, no basis points.
```

**Expected Response**:
- "Your portfolio gained/lost X% this quarter, ahead of/behind the benchmark by Y%."
- 2-3 plain English explanations
- 1 sentence on positioning and outlook
- NO attribution terminology

**Talking Points**:
- Same data, three narratives — demonstrates adaptive AI communication
- Eliminates the manual work of writing separate board, PM, and client reports
- Audience detection from question context keywords (CIO, board, client, plain English)

---

### Portfolio Manager Co-Pilot - Intelligent Driver Discovery

#### Business Context Setup

**Persona**: Victoria Chen, Chief Investment Officer at Simulated Asset Management  
**Business Challenge**: Standard attribution tools report numbers but don't synthesise. When the board asks "what really drove our performance?", the CIO needs a unified narrative that cross-references sector attribution, factor exposures, and hidden thematic risks.  
**Value Proposition**: The agent's Intelligent Driver Discovery workflow automatically combines three analytical perspectives (Brinson, factor, hidden factor) to determine whether returns came from genuine stock-picking skill, systematic factor exposure, or unintended thematic concentrations.

**Agent**: `AM_portfolio_manager_copilot`  
**Data Available**: Full attribution suite including Brinson, factor, and hidden factor data

#### Demo Flow

**Scene Setting**: Victoria is in a post-mortem meeting after a quarter where the portfolio significantly outperformed. The board is sceptical — was it skill or luck?

##### Step 1: True Driver Analysis

**User Input**: 
```
Our Flagship portfolio outperformed by 200bps last quarter. Was this from genuine stock selection skill, or are we just riding factor tailwinds? Give me the true driver analysis combining all available data.
```

**Tools Used**:
- `brinson_analyzer` + `factor_analyzer` + `hidden_factor_analyzer` (multi-tool synthesis)

**Expected Response**:
- Cross-referenced analysis showing:
  - Brinson selection effect vs factor contribution overlap
  - Hidden factor exposure that might explain "alpha"
  - True residual alpha estimate after accounting for all systematic and thematic factors
- Example: "Of the +200bps active return: +80bps attributable to Momentum factor exposure, +50bps to elevated AI_Exposure concentration in Tech holdings, estimated true stock-picking alpha: +70bps."

##### Step 2: Decision Accountability

**User Input**: 
```
Based on that analysis, which specific decisions generated real alpha vs factor exposure? What should we do differently next quarter?
```

**Expected Response**:
- Decision-level attribution: "The overweight to Semiconductors generated +40bps from selection, but +30bps came from the sector's Growth factor tailwind"
- Recommendations: maintain genuine alpha sources, hedge or reduce unintended factor bets

**Talking Points**:
- This is the highest-value analysis — separating skill from luck
- Requires multi-tool synthesis, not just data retrieval
- The agent's orchestration workflow manages the complexity automatically

---

## Integration with Other Agents

The Portfolio Manager Co-Pilot agent complements:

- **Portfolio Manager Co-Pilot**: Use attribution insights to inform trading decisions
- **Investment Strategy**: Deep dive into factor exposures and systematic risks
- **Executive Copilot**: Board-ready performance narratives
- **Portfolio Modelling Copilot**: Forward-looking simulation and backtesting

---

### Portfolio Manager Co-Pilot - Yield Curve Context for Rate-Sensitive Attribution

#### Demo Scenario

**User Input**: 
```
How has the yield curve shape changed over the past quarter, and does it explain our rate-sensitive sector attribution?
```

**Tools Used**:
- `treasury_yield_analyzer` (Cortex Analyst) - Yield curve history
- `brinson_analyzer` (Cortex Analyst) - Sector attribution for Utilities, Real Estate, Financials

**Expected Response**:
- Yield curve evolution over the quarter (steepening/flattening)
- Attribution effects for rate-sensitive sectors
- Correlation between yield curve moves and sector performance
- Insight: "The 50bps steepening in the 2Y-10Y spread explains the +0.3% selection effect in Financials"

**Key Features Highlighted**: 
- US Treasury data as attribution context layer
- Multi-tool synthesis (yields + Brinson) for explanatory power
- Rate-regime-aware performance narrative

---

### Portfolio Manager Co-Pilot - Counterfactual What-If Analysis

#### Business Context Setup

**Persona**: Victoria Chen, Chief Investment Officer at Simulated Asset Management  
**Business Challenge**: After reviewing attribution results, the natural question is "what would have happened if we'd made different decisions?" Traditional attribution is purely backward-looking. Counterfactual analysis provides forward-looking decision support by modelling alternative scenarios.  
**Value Proposition**: AI-powered what-if analysis that recalculates attribution under alternative weight scenarios, enabling the investment committee to evaluate the impact of past decisions and inform future allocation choices.

**Agent**: `AM_portfolio_manager_copilot`  
**Data Available**: Multi-level attribution data, counterfactual analysis tool

#### Demo Flow

**Scene Setting**: Victoria has just reviewed the quarterly Brinson attribution. Technology was the largest contributor, but also the most concentrated position. The IC wants to know: "What if we'd held benchmark weights instead of our active overweight?"

##### Step 1: Benchmark Weight Scenario

**User Input**: 
```
What would our returns have been if we had held benchmark weights in all sectors? Run a counterfactual analysis for the Flagship portfolio over the last quarter.
```

**Tools Used**:
- `run_counterfactual` (Stored Procedure) - BENCHMARK_WEIGHTS scenario

**Expected Response**:
- Original active return vs counterfactual active return
- Sector-by-sector comparison showing which active bets added vs detracted value
- Net impact: "Holding benchmark weights would have resulted in X% active return vs the actual Y%"
- Clear identification of the value-add from active management

**Talking Points**:
- Counterfactual analysis answers "was our active management worth it?"
- This is deterministic recalculation, not LLM speculation
- Board members love this because it quantifies the value of the investment team

**Key Features Highlighted**: 
- Stored procedure for deterministic calculation
- Sector-by-sector comparison
- Decision accountability framework

##### Step 2: Weight Cap Scenario

**Presenter Transition**:
> "We know Technology was concentrated at 35%+. What if we had a risk management rule capping any sector at 25%? Would that have helped or hurt?"

**User Input**: 
```
What if no sector exceeded 25% weight? How would that have affected our returns?
```

**Tools Used**:
- `run_counterfactual` (Stored Procedure) - CAP_WEIGHT scenario

**Expected Response**:
- Original weights vs capped weights for each sector
- Redistributed excess weight shown clearly
- Impact on active return
- Whether the cap would have improved or worsened performance

**Talking Points**:
- Risk management rules have performance costs — this quantifies them
- Helps calibrate concentration limits based on evidence, not arbitrary thresholds

#### Scenario Wrap-up

**Business Impact Summary**:
- **Decision Accountability**: Quantify the value added by active management
- **Risk Calibration**: Evidence-based concentration limit setting
- **Forward-Looking**: Inform future allocation decisions based on historical counterfactuals

**Technical Differentiators**:
- **Deterministic Recalculation**: Not LLM speculation — actual Brinson recalculation
- **Multiple Scenario Types**: Benchmark weights, weight caps, with more scenarios extensible
- **Sector-Level Detail**: Shows impact at every level, not just portfolio total

---

### Portfolio Manager Co-Pilot - Cross-Dimension Comparison

#### Business Context Setup

**Persona**: Victoria Chen, Chief Investment Officer at Simulated Asset Management  
**Business Challenge**: The same excess return can be decomposed by sector, country, or industry — and each tells a different story. Understanding which classification lens provides the most useful insight is a key analytical skill.  
**Value Proposition**: Instant comparison of attribution results across different grouping dimensions, revealing whether outperformance is driven by sector bets, geographic exposure, or specific industry selection.

**Agent**: `AM_portfolio_manager_copilot`  
**Data Available**: Multi-level attribution by sector, country, and industry

#### Demo Flow

**Scene Setting**: Victoria has seen sector attribution showing Technology drove performance. But she wants to know if this is really a "US tech" story (geographic) or a broad "technology" story (sector).

##### Step 1: Sector vs Country Comparison

**User Input**: 
```
Compare the sector attribution and country attribution for our Flagship portfolio last quarter. Which lens tells a more useful story?
```

**Tools Used**:
- `brinson_analyzer` (Cortex Analyst) - Queries both grouping_dimension = 'SECTOR' and 'COUNTRY'

**Expected Response**:
- Side-by-side (or sequential) presentation of sector and country attribution
- Key insight: "The 85bps from Technology overweight (sector view) is concentrated in US holdings (country view), suggesting regional tech exposure rather than global tech conviction"
- Identification of where the two views diverge — a sector that performs well may be concentrated in one country

**Talking Points**:
- This is the Rainardi insight: "same data, different classification produces different attribution results"
- In real AM, the classification choice matters — country of incorporation vs country of risk can tell different stories
- AI can synthesise both views and explain the relationship

**Key Features Highlighted**: 
- Multi-level attribution from a single FACT_BRINSON_ATTRIBUTION_DETAIL table
- Agent synthesises cross-dimension insights automatically
- Real-world analytical pattern used by attribution analysts daily

##### Step 2: YTD Linked Comparison

**Presenter Transition**:
> "Let me extend this to the full YTD view using linked attribution — this accounts for compounding effects over the year."

**User Input**: 
```
Show me the YTD linked attribution by sector for Flagship. How do the linked effects compare to the simple sum?
```

**Tools Used**:
- `brinson_analyzer` (Cortex Analyst) - Queries linked_attribution with period_type = 'YTD'

**Expected Response**:
- YTD linked attribution by sector using Frongello base-period adjustment
- Comparison of linked total vs simple sum of monthly effects
- Explanation of why they differ (compounding effects)

**Talking Points**:
- Frongello linking is forward-looking — future market movements don't affect past contributions
- No residuals — the linked effects sum exactly to the compounded active return
- This is the standard that performance teams use for multi-period client reporting

#### Scenario Wrap-up

**Business Impact Summary**:
- **Analytical Depth**: Multiple classification lenses on the same data
- **Compounding Awareness**: Linked attribution correctly handles multi-period effects
- **Client Reporting Ready**: QTD/YTD figures suitable for formal reporting

**Technical Differentiators**:
- **Frongello Base-Period Adjustment**: Industry-standard multi-period linking
- **Cross-Dimension Synthesis**: AI identifies relationships between sector and country views
- **Generalised Data Model**: Single table supports any grouping dimension

---

### Proactive Portfolio Manager Co-Pilot Intelligence (DATA_AGENT_RUN)

#### Business Context Setup

**Persona**: Victoria Chen, CIO + Risk Operations Team  
**Business Challenge**: Attribution analysis is reactive — teams only investigate when someone asks. Critical attribution anomalies, concentration breaches, and style drift can go unnoticed for days until the next board meeting or client call.  
**Value Proposition**: Proactive agent intelligence uses Snowflake Tasks + DATA_AGENT_RUN to run the Portfolio Manager Co-Pilot agent automatically. Daily briefings are generated before the team arrives. Anomaly scans flag HIGH severity issues immediately. Position changes trigger instant breach detection. All insights are stored for historical analysis.

**Agent**: `AM_portfolio_manager_copilot` + `AM_portfolio_manager_copilot`  
**Infrastructure**: Snowflake Tasks (scheduled + stream-triggered), DATA_AGENT_RUN function, FACT_PROACTIVE_INSIGHTS + FACT_PROACTIVE_ALERTS tables

#### Demo Flow

**Scene Setting**: Show the Snowsight Task DAG view (AI schema) to demonstrate the automated pipeline architecture:

```
DAILY_ATTRIBUTION_BRIEFING (cron: 7am Mon-Fri)
    → ANOMALY_ALERT_CHECK (child: runs cross-portfolio risk scan)
        → ANOMALY_ALERT_PROMOTE (child: copies HIGH severity to alerts)

POSITION_CHANGE_INSIGHT (stream-triggered: when new positions arrive)
```

##### Step 1: Show Task Infrastructure

> **User**: "Show me the proactive insights tasks"

```sql
SHOW TASKS IN SAM_DEMO.AI;
```

**Expected**: 4 tasks visible — DAILY_ATTRIBUTION_BRIEFING (root, scheduled), ANOMALY_ALERT_CHECK (child), ANOMALY_ALERT_PROMOTE (child), POSITION_CHANGE_INSIGHT (stream-triggered)

**Talking Point**: These agents run themselves — no human needs to ask. Every morning at 7am, the Portfolio Manager Co-Pilot agent generates a briefing for each portfolio. If it finds HIGH severity anomalies, those get promoted to the alerts table automatically.

##### Step 2: Show Generated Insights (Pre-populated)

> **User**: "What proactive insights have been generated? Any HIGH severity alerts?"

**Skill Activation**: The agent uses `SAM_PROACTIVE_INSIGHTS_VIEW` to query its own historical outputs.

**Expected Response**: Agent queries FACT_PROACTIVE_INSIGHTS showing insight counts by type, any unread items, and HIGH severity alerts requiring attention.

**Talking Point**: The agent can query its own past outputs — this creates a feedback loop where proactive intelligence accumulates over time. You can ask "What did the anomaly scan flag last Tuesday?" and get a precise answer.

##### Step 3: Demo a Live Agent Run

> **User**: "Run a daily briefing for SAM Global Alpha"

This demonstrates DATA_AGENT_RUN calling the attribution agent programmatically:

```sql
SELECT TRY_PARSE_JSON(
    SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
        'SAM_DEMO.AI.AM_portfolio_manager_copilot',
        $${"messages": [{"role": "user", "content": [{"type": "text", "text": "Generate a brief daily attribution update for SAM Global Alpha. Focus on: 1) Most recent month active return, 2) Top 3 sector contributors, 3) Any anomaly flags. Keep under 200 words."}]}], "stream": false}$$
    )
):content[ARRAY_SIZE(TRY_PARSE_JSON(
    SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
        'SAM_DEMO.AI.AM_portfolio_manager_copilot',
        $${"messages": [{"role": "user", "content": [{"type": "text", "text": "Generate a brief daily attribution update for SAM Global Alpha. Focus on: 1) Most recent month active return, 2) Top 3 sector contributors, 3) Any anomaly flags. Keep under 200 words."}]}], "stream": false}$$
    )
):content)-1]:text::VARCHAR AS briefing;
```

**Talking Point**: This is the exact same call that the Task executes at 7am every morning. The agent orchestrates across Brinson attribution, anomaly detection, and factor analysis to generate a comprehensive briefing in ~30 seconds.

##### Step 4: Stream-Triggered Pattern

> **User**: "What happens when new position data arrives?"

**Explanation**: Show the POSITION_CHANGE_STREAM on FACT_POSITION_DAILY_ABOR. When the ABOR system pushes new end-of-day positions, the stream captures the change, the task polls every 5 minutes, and when data is detected it calls the Portfolio Copilot agent to check for concentration breaches.

```sql
SHOW STREAMS IN SAM_DEMO.AI;
-- POSITION_CHANGE_STREAM: ON TABLE SAM_DEMO.CURATED.FACT_POSITION_DAILY_ABOR, APPEND_ONLY
```

**Talking Point**: This is event-driven AI. The agent doesn't wait to be asked — it automatically checks for limit breaches the moment new data arrives. The 5-minute polling means compliance gets alerted within minutes of a potential breach, not days.

#### Scenario Wrap-up

**Business Impact Summary**:
- **Always-On Intelligence**: No human needs to remember to run attribution analysis
- **Time-to-Insight**: From overnight batch to sub-minute event-driven alerts
- **Audit Trail**: Every agent insight is stored with full provenance (prompt, raw response, timestamp)
- **Self-Referential**: Agents can query their own past insights for trend detection

**Technical Differentiators**:
- **DATA_AGENT_RUN**: SQL-callable agent execution — embeddable in any Task, procedure, or pipeline
- **Task DAG Architecture**: Parent-child task chains with conditional alert promotion
- **Stream-Triggered AI**: Append-only stream → automatic breach detection on data arrival
- **Semantic View on Insights**: Agents query their own outputs via SAM_PROACTIVE_INSIGHTS_VIEW


---

## Part 3: Quantitative / Factor Analysis

## Investment Strategy

### Investment Strategy - Multi-Factor Stock Screening Strategy

#### Business Context Setup

**Persona**: Dr. James Chen, Quantitative Analyst at Simulated Asset Management  
**Business Challenge**: Quantitative analysts need to develop systematic multi-factor investment strategies that screen securities based on factor exposures (Value, Quality, Momentum), validate factor signals with fundamental financial data from SEC filings, cross-reference with analyst research for qualitative validation, and review management commentary for strategic confirmation—all while maintaining statistical rigour with significance testing. Traditional quant analysis requires days of factor database queries, manual SEC filing review, spreadsheet modeling, research document searches, and statistical validation—often missing the integration between quantitative signals, fundamental validation, qualitative research, and management perspective that drives robust factor strategies.  
**Value Proposition**: AI-powered comprehensive quantitative intelligence that seamlessly integrates multi-factor screening, SEC filing fundamental validation, broker research consensus, and earnings transcript analysis—delivering statistically validated, fundamentally sound, research-corroborated investment strategies in minutes instead of days.

**Agent**: `investment_strategy`  
**Data Available**: 14,000+ securities with 5 years monthly factor history (7 factors: Market, Size, Value, Growth, Momentum, Quality, Volatility), 28.7M SEC filing records, 500 broker research reports, 300 earnings transcripts

#### Demo Flow

**Scene Setting**: Dr. Chen is developing a new multi-factor equity strategy for Q1 2025 focusing on Value, Quality, and improving Momentum characteristics. The Quantitative Investment Committee meets in 3 days and requires a complete strategy proposal including factor-screened securities, fundamental validation from SEC filings confirming the factor signals, analyst research supporting the investment thesis, management commentary validating strategic quality, and statistical significance testing (R-squared, p-values, t-statistics) demonstrating model robustness. James needs to screen the investment universe for high Value/Quality scores, identify improving Momentum trends, validate with authentic financial fundamentals, cross-check with analyst views, review management commentary, and compile statistically rigorous analysis—all before Thursday for internal review.

##### Step 1: Comprehensive Multi-Factor Strategy Development
**User Input**: 
```
I'm building a multi-factor stock screening strategy focusing on Value, Quality, and improving Momentum. Can you:
1. Screen our investment universe for securities with high Quality and Value factor exposures
2. Within those results, identify companies showing improving Momentum factor trends over the last 6 months
3. Validate the financial fundamentals using SEC filing data - confirm revenue growth, margin expansion, and balance sheet quality
4. Cross-reference with analyst research to see if broker recommendations align with our factor signals
5. Check earnings transcripts for management commentary supporting the quality and growth characteristics
6. Provide a ranked list with factor scores, fundamental validation, analyst views, and statistical significance testing (R-squared, p-values) for the systematic investment strategy
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Multi-factor screening with Value, Quality, Momentum exposures
- `financial_analyzer` (Cortex Analyst) - SEC filing fundamental validation (revenue, margins, balance sheet)
- `search_external_docs` (Cortex Search) - Analyst recommendations and investment thesis
- `search_company_events` (Cortex Search) - Management commentary on quality/growth

**Expected Response**:
- **Multi-Factor Screening Results**:
  - Screening criteria summary (factor thresholds and constraints)
  - Count of securities meeting all criteria
  - Ranked list of top candidates with factor scores
    | Column | Description |
    |--------|-------------|
    | Ticker/Company | Security identifier and name |
    | Sector | GICS sector classification |
    | Factor Z-Scores | Quality, Value, Momentum scores |
    | Combined Score | Aggregate multi-factor ranking |
  
  - **Factor Statistics**: Average factor exposures and significance metrics
    | Metric | Description |
    |--------|-------------|
    | R² | Percentage of return variance explained |
    | P-values | Statistical significance by factor |

- **SEC Filing Fundamental Validation**:
  - Fundamental metrics for top candidates from SEC filings
    | Metric Type | Description |
    |-------------|-------------|
    | Revenue/Earnings | YoY growth trends |
    | Margins | Profitability validation |
    | Balance Sheet | Leverage and quality metrics |
  - Factor validation summary (confirmed/challenged by fundamentals)

- **Analyst Research Validation**:
  - Broker recommendations for top candidates
  - Consensus ratings distribution (Buy/Hold/Sell)
  - Factor alignment assessment (analyst views supporting factor signals)

- **Management Commentary Validation**:
  - Key quotes from earnings calls supporting factor themes
  - Assessment of management focus on quality metrics (ROE, margins, cash flow)
  - Theme alignment between management commentary and factor signals

- **Statistical Significance Testing**:
  - Factor model regression with significance metrics
    | Metric Type | Description |
    |-------------|-------------|
    | Coefficients | Beta and t-statistics by factor |
    | R² | Model explanatory power |
    | P-values | Statistical significance |
  - Factor stability analysis over rolling windows
  - Risk-adjusted performance metrics (Sharpe ratio, Information ratio, drawdown)

- **Final Investment Strategy Recommendation**:
  - Strategy name and investment thesis summary
  - Portfolio construction with sector-diversified allocations
  - Risk characteristics and implementation considerations
    - **Sector Diversification**: 6 sectors represented (maximum 3 securities/sector)
    - **Average Market Cap**: $285B (large-cap focus for liquidity)
  
  * **Expected Portfolio Characteristics**:
    - **Quality Z-Score**: 1.63 (83rd percentile)
    - **Value Z-Score**: 1.35 (79th percentile)
    - **Momentum Trend**: +0.39 SD improvement (6 months)
    - **Weighted Average P/E**: 13.8x vs S&P 500 21.0x (34% valuation discount)
    - **Weighted Average ROE**: 19.2% vs S&P 500 16.1% (+3.1% quality premium)
    - **Dividend Yield**: 2.8% vs S&P 500 1.6% (+120bp income advantage)
  
  * **Risk Characteristics**:
    - **Expected Tracking Error**: 6-8% (active but controlled)
    - **Beta**: 0.92 (slightly defensive)
    - **Factor Tilt**: Quality +1.63 SD, Value +1.35 SD, Momentum +0.39 SD
    - **Max Single Position**: 12% (concentration managed)
  
  * **Implementation Recommendations**:
    1. **Rebalancing**: Quarterly factor score update with systematic rebalancing
    2. **Entry/Exit Rules**: Add securities when factor scores exceed 3.0 threshold, remove when below 2.5
    3. **Position Sizing**: Weight by combined factor score (higher scores = larger weights)
    4. **Monitoring**: Monthly factor exposure tracking, quarterly fundamental validation
    5. **Risk Management**: Maximum 12% single position, maximum 30% single sector
  
  * **Expected Performance** (based on 60-month backtest):
    - **Alpha**: 2.5-3.5% annually vs S&P 500
    - **Sharpe Ratio**: 1.0-1.2 (vs 0.85-0.90 for S&P 500)
    - **Information Ratio**: 0.7-0.9
    - **Win Rate**: 62% (proportion of months outperforming benchmark)

**Talking Points**:
- **Comprehensive Quantitative Intelligence**: Single query orchestrates 4 tools across factor screening, SEC filing validation, analyst research, and management commentary
- **Statistical Rigour**: Complete significance testing (R²=0.67, p<0.001) demonstrates robust systematic strategy
- **Multi-Layer Validation**: Factor signals validated through SEC fundamentals, analyst research consensus, and management strategic focus
- **Systematic Framework**: Replicable, data-driven approach eliminates subjective biases from investment selection
- **Risk-Adjusted Performance**: Backtest shows 14.2% return with 1.12 Sharpe ratio vs S&P 500 11.3%/0.87

**Key Features Highlighted**: 
- **Multi-Factor Analytics**: Cortex Analyst screens 14,000+ securities across Quality, Value, Momentum factors with 60-month history
- **Authentic Financial Validation**: 28.7M SEC filing records provide institutional-grade fundamental confirmation of factor signals
- **Research Consensus Tracking**: Broker research synthesis shows 76% BUY consensus supporting systematic selection
- **Management Strategic Alignment**: Earnings transcript analysis confirms management focus on quality metrics (ROE, margins)
- **Statistical Validation Engine**: Complete significance testing (t-statistics, p-values, R², F-statistic) demonstrates model robustness
- **Backtest Performance**: 60-month historical analysis shows systematic alpha generation with superior risk-adjusted returns

#### Scenario Wrap-up

**Business Impact Summary**:
- **Strategy Development Speed**: Complete multi-factor strategy with validation reduced from 3-5 days to under 20 minutes (99% time savings)
- **Validation Depth**: SEC filing fundamental confirmation, analyst research consensus, management commentary—triple validation vs single-source factor models
- **Statistical Rigour**: Complete significance testing (R², p-values, t-statistics) provides institutional-quality quantitative framework
- **Implementation Readiness**: Specific portfolio construction, position sizes, rebalancing rules, and risk parameters enable immediate deployment

**Technical Differentiators**:
- **Multi-Factor Intelligence**: Integration of factor analytics (7 factors, 5-year history, 14,000+ universe) with fundamental and qualitative validation
- **Authentic Data Foundation**: 28.7M SEC filing records provide institutional-grade financial validation unavailable from factor databases alone
- **Research Consensus Engine**: Systematic aggregation of 115 analyst ratings across 10 securities demonstrates external validation
- **Management Strategic Analysis**: Earnings transcript processing extracts quality-focused commentary supporting systematic factor signals
- **Statistical Validation Framework**: Complete regression analysis with significance testing (R², t-stats, F-statistic) demonstrates model robustness
- **Systematic Alpha Generation**: 60-month backtest shows 2.9% annual alpha with 1.12 Sharpe ratio validating systematic approach

---

### Investment Strategy - Complete Factor Strategy Development (Catch-All)

#### Business Context Setup

**Persona**: Dr. James Chen, Quantitative Analyst at Simulated Asset Management  
**Business Challenge**: Quantitative analysts sometimes need a complete factor strategy package with a single request when preparing for urgent investment committee presentations—requiring the AI to autonomously orchestrate all quantitative tools.  
**Value Proposition**: The Investment Strategy agent demonstrates complete autonomous orchestration by selecting and sequencing all tools from a single comprehensive question, delivering a committee-ready factor strategy without step-by-step guidance.

**Agent**: `investment_strategy`  
**Data Available**: 14,000+ securities with 5-year factor history (7 factors), 28.7M SEC filing records, 500 broker reports, 300 earnings transcripts

#### Demo Flow

**Scene Setting**: Dr. Chen has 15 minutes before an urgent investment committee call. The CIO wants a complete factor-based investment strategy with validation from all available sources.

##### Step 1: Complete Factor Strategy Development (All Tools)

**User Input**: 
```
Develop a complete multi-factor investment strategy screening for Value and Quality factors, validate signals with SEC fundamental data confirming revenue growth and margin expansion, cross-reference with analyst research for consensus validation, review earnings transcripts for management commentary supporting our factor thesis, and provide statistical significance testing with R-squared, p-values, and backtest performance metrics.
```

**Tools Used**:
- `factor_analyzer` (Cortex Analyst) - Multi-factor screening with Value, Quality, Momentum exposures
- `financial_analyzer` (Cortex Analyst) - SEC filing fundamental validation
- `search_external_docs` (Cortex Search) - Analyst recommendations and ratings
- `search_company_events` (Cortex Search) - Management commentary on fundamentals

**Expected Response**:
- **Factor Screening**: Top securities by Value/Quality scores with factor z-scores
- **SEC Validation**: Revenue growth, margin trends, ROE from 10-K/10-Q filings
- **Analyst Consensus**: Buy/Hold/Sell ratings supporting factor thesis
- **Management Commentary**: Earnings call quotes on quality and growth
- **Statistical Testing**: R-squared, p-values, t-statistics for factor significance
- **Investment Recommendation**: Portfolio construction with allocations and risk parameters

**Talking Points**:
- **Autonomous Orchestration**: AI independently selects and sequences all four quantitative tools
- **Single-Query Capability**: Complete factor strategy from one comprehensive question
- **Committee Ready**: Output includes statistical validation for investment committee review

**Key Features Highlighted**: 
- **Multi-Tool AI Orchestration**: Agent autonomously determines tool sequence and synthesis
- **Quantitative + Qualitative Integration**: Factor scores merged with fundamental and research validation
- **Statistical Rigour**: Complete significance testing for institutional-quality presentation

#### Scenario Wrap-up

**Business Impact Summary**:
- **Rapid Response**: Complete factor strategy available in under 5 minutes
- **Multi-Layer Validation**: Factor signals validated through SEC data, analyst views, and management commentary
- **Statistical Confidence**: Complete significance testing supports investment committee decisions

**Technical Differentiators**:
- **Four-Tool Integration**: Demonstrates full Investment Strategy capability in single query
- **Triple Validation**: Factor + Fundamental + Qualitative analysis in single output
- **Autonomous Operation**: True AI agent capability for quantitative strategy development

---

## End-to-End Quantitative Factor Strategy

### Business Context Setup

**Persona**: Dr. James Chen, Quantitative Analyst at Simulated Asset Management
**Business Challenge**: The PM meeting is in 2 hours and the quant desk needs an updated factor view: which factors are working, what's the ML model's current signal, and how should the portfolio be positioned?
**Value Proposition**: ML-powered factor analysis through natural language — factor returns, SHAP-based factor importance, and optimal portfolio weights available in conversation.

**Agent**: `investment_strategy`
**Data Available**: Factor scores (`FACT_FACTOR_SCORES`), factor returns (`FACT_FACTOR_RETURNS`), ML predictions (`FACT_ML_FACTOR_PREDICTIONS`), optimal portfolio (`FACT_OPTIMAL_PORTFOLIO`)

**Prerequisites**: Run `notebooks/factor_discovery.ipynb` first to populate all tables.

### Demo Flow

#### Step 1: Factor Landscape Overview

**User Input**:
```
What are the current factor Sharpe ratios? Which factors have been generating the strongest returns over the past 12 months?
```

**Expected Response**:
- Annualised Sharpe ratio for each factor (Momentum, Value, Quality, Growth, Size, Volatility)
- Factor return trends over the last 12 months
- Statistical significance (t-stats from Fama-MacBeth)

#### Step 2: ML Factor Signals

**Presenter Transition**:
> "The linear model shows which factors worked historically. Let me ask what the ML model currently predicts..."

**User Input**:
```
What does the XGBoost factor model predict for next month? Which factors are most important according to SHAP analysis?
```

**Expected Response**:
- Top stocks by predicted return
- SHAP feature importance ranking (which factors drive the ML signal)
- Comparison of ML ranking vs linear factor model

#### Step 3: Optimal Portfolio

**User Input**:
```
Show me the current optimal portfolio based on the ML factor model. What are the top holdings and their expected returns?
```

**Expected Response**:
- Top 10 holdings with weights and expected returns
- Portfolio-level statistics (expected return, volatility, Sharpe)
- Sector concentration metrics

#### Step 4: Factor Regime Interaction

**User Input**:
```
How does the current market regime affect factor performance? Which factors tend to work best in this regime?
```

**Expected Response**:
- Current market regime (from FACT_REGIME_PREDICTIONS)
- Historical factor returns conditioned on regime
- Regime-specific factor Sharpe ratios

#### Step 5: Model Health Check

**User Input**:
```
How is the factor model performing? Is there any drift in the factor distributions?
```

**Expected Response**:
- Recent IC (information coefficient) trend
- Model Monitor drift metrics (PSI on factor score distributions)
- Any factors showing distribution shifts

---

### Investment Strategy - Risk-Free Rate & Yield Curve Regime

#### Demo Scenario

**User Input**: 
```
What's the current risk-free rate for Sharpe ratio calculations, and how does the yield curve shape inform our factor rotation?
```

**Tools Used**:
- `treasury_yield_analyzer` (Cortex Analyst) - Current rates and yield curve shape
- `quantitative_analyzer` (Cortex Analyst) - Factor exposures

**Expected Response**:
- Current short-term rate (3M T-bill) for risk-free benchmark
- Yield curve shape and term spread
- Implications for Value vs Growth factor timing
- Rate-regime context for factor rotation strategy

**Key Features Highlighted**: 
- Real US Treasury rates for quantitative risk metrics
- Yield curve as factor rotation signal
- Integration with factor model analysis

---

### Investment Strategy - Ad-Hoc Factor Regression with Code Execution

#### Business Context Setup

**Persona**: Dr. James Chen, Quantitative Analyst at Simulated Asset Management  
**Business Challenge**: Standard factor screenings use pre-computed scores and rankings. When a quant needs a custom analysis — a cross-sectional regression with non-standard factor combinations, a rolling information coefficient for a new signal, or a quick PCA decomposition — they traditionally switch to a Jupyter notebook or R script. This context switch breaks the analytical flow and slows hypothesis testing.  
**Value Proposition**: The `code_execution` tool lets the quant analyst agent write and run custom Python (numpy, pandas, scipy) within the conversation, guided by the `factor-model-explorer` skill. Hypothesis testing goes from hours to seconds.

**Agent**: `investment_strategy`  
**Skills Used**: `factor-model-explorer`, `audience-adaptive-narrative`  
**Data Available**: Factor scores (`FACT_FACTOR_SCORES`), factor returns (`FACT_FACTOR_RETURNS`), ML predictions (`FACT_ML_FACTOR_PREDICTIONS`), 14,000+ securities

#### Demo Flow

**Scene Setting**: Dr. Chen is investigating whether a combination of Quality, Momentum, and the hidden AI_EXPOSURE factor predicts forward returns better than the standard model. He needs a quick cross-sectional regression and rolling IC analysis before the PM meeting in 30 minutes.

##### Step 1: Pull Factor Data for Target Universe

**User Input**: 
```
Pull the latest monthly factor scores for Quality, Momentum, and AI_EXPOSURE for all large-cap securities (top 500 by market cap). Include forward 21-day returns.
```

**Tools Used**:
- `factor_model_analyzer` (Cortex Analyst) - Query factor scores and forward returns

**Expected Response**:
- Dataset summary: N securities, date range, factor coverage
- Quick statistics: mean, std, min, max for each factor
- Data readiness confirmation

##### Step 2: Run Cross-Sectional Regression

**Presenter Transition**:
> "Now let me ask the agent to run a custom regression to test my hypothesis about AI_EXPOSURE adding predictive power..."

**User Input**: 
```
Run a cross-sectional regression of forward 21-day returns on Quality, Momentum, and AI_EXPOSURE for the latest month. Show me the coefficients, t-statistics, R-squared, and whether AI_EXPOSURE is statistically significant at the 5% level.
```

**Tools Used**:
- `server_skill` → loads `factor-model-explorer` skill
- `code_execution` — Runs OLS regression using numpy (X'X)^-1 X'y with t-stat calculation

**Expected Response**:
- **Regression Results**:
  | Factor | Coefficient | t-Statistic | p-Value | Significant? |
  |--------|-------------|-------------|---------|-------------|
  | Quality | β | t | p | ✅/❌ |
  | Momentum | β | t | p | ✅/❌ |
  | AI_EXPOSURE | β | t | p | ✅/❌ |
- **Model Fit**: R², Adjusted R², F-statistic
- **Interpretation**: Whether AI_EXPOSURE adds marginal predictive power

**Talking Points**:
- Agent writes and executes OLS regression code in real-time
- Statistical inference (t-stats, p-values) computed live
- No need to switch to a notebook for custom analysis

##### Step 3: Rolling Information Coefficient

**Presenter Transition**:
> "The single-month regression is promising. Let me check if AI_EXPOSURE has been consistently predictive over time..."

**User Input**: 
```
Calculate the rolling 12-month information coefficient (rank IC) for Quality, Momentum, and AI_EXPOSURE. Show the IC time series and average IC with significance.
```

**Tools Used**:
- `factor_model_analyzer` (Cortex Analyst) - Pull 12 months of factor scores + forward returns
- `code_execution` — Compute rolling Spearman rank correlation (IC) per factor per month

**Expected Response**:
- **Rolling IC Summary**:
  | Factor | Avg IC | IC Std | IC IR | % Positive |
  |--------|--------|--------|-------|-----------|
  | Quality | X.XX | X.XX | X.XX | XX% |
  | Momentum | X.XX | X.XX | X.XX | XX% |
  | AI_EXPOSURE | X.XX | X.XX | X.XX | XX% |
- **IC Time Series**: Monthly IC values showing consistency
- **Key Insight**: Whether AI_EXPOSURE IC is stable and positive

**Talking Points**:
- Rolling IC is the gold standard for factor signal evaluation
- IC IR (Information Ratio of IC) measures signal consistency
- Live computation avoids pre-computed staleness

**Key Features Highlighted**: 
- `code_execution` runs scipy.stats.spearmanr for rank IC calculation
- `factor-model-explorer` skill guides the analytical workflow
- Complete statistical framework: regression → IC → significance

#### Scenario Wrap-up

**Business Impact Summary**:
- **Hypothesis Speed**: Factor hypothesis tested in minutes, not hours
- **No Context Switch**: Custom quantitative analysis stays within the agent conversation
- **Statistical Rigour**: Proper t-statistics, p-values, and IC calculations
- **Signal Discovery**: New factors (e.g., AI_EXPOSURE) can be evaluated immediately

**Technical Differentiators**:
- **Code Execution**: numpy/scipy statistical computing within the agent
- **Skill-Guided Analysis**: `factor-model-explorer` provides the analytical framework
- **Live Regression**: OLS with proper inference, not just correlation
- **Rolling IC**: Industry-standard factor evaluation metric computed on demand


---

## Part 4: Thematic Strategy

## Investment Strategy

### Investment Strategy - AI Infrastructure Strategy Development

#### Business Context Setup

**Persona**: Anna, Portfolio Manager (Thematic Focus) at Simulated Asset Management  
**Business Challenge**: Thematic portfolio managers need to systematically identify emerging investment themes, validate with comprehensive research across multiple sources, analyze current portfolio positioning against identified opportunities, and synthesize into actionable investment strategies. Traditional thematic research requires days of manual analysis across broker research, corporate earnings commentary, press releases, and portfolio analytics—often missing the integration between macro themes, corporate positioning, management conviction, and portfolio gaps that drives superior thematic investment decisions.  
**Value Proposition**: AI-powered comprehensive thematic intelligence that seamlessly integrates current portfolio positioning analysis, multi-source broker research synthesis, management strategic commentary from earnings calls, and corporate investment announcements—delivering complete, investment-ready thematic strategies with specific positioning recommendations in minutes instead of days.

**Agent**: `investment_strategy`  
**Data Available**: Portfolio holdings across 10 strategies, 500 broker research reports with thematic analysis, 300 earnings transcripts with strategic commentary, 400 press releases with corporate investment announcements

#### Demo Flow

**Scene Setting**: Anna is preparing the upcoming quarterly thematic investment strategy for presentation to the Investment Committee next week. The committee wants specific recommendations on artificial intelligence infrastructure as a potential new thematic focus. Anna needs to assess current portfolio positioning, validate the theme with comprehensive research, identify specific sub-themes and investment opportunities, understand corporate and management perspectives, and synthesize into a coherent investment strategy with portfolio positioning recommendations—all within 2 days for strategy documentation and committee materials preparation.

##### Step 1: Comprehensive Thematic Strategy Development
**User Input**: 
```
I'm developing our upcoming quarterly thematic investment strategy around artificial intelligence infrastructure. Can you:
1. Analyze our current portfolio exposure to AI and data center themes across all portfolios
2. Find the latest broker research identifying key AI infrastructure sub-themes and investment opportunities
3. Review what major technology company managements are saying in earnings calls about AI spending and data center capacity plans
4. Check recent corporate announcements for AI infrastructure investments and partnerships
5. Synthesize this into a thematic positioning recommendation showing where we're under-positioned relative to the emerging AI infrastructure opportunity
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Analyze current AI/data center portfolio exposure
- `search_external_docs` (Cortex Search) - Find AI infrastructure thematic research and sub-themes
- `search_company_events` (Cortex Search) - Retrieve management commentary on AI spending
- `search_external_docs` (Cortex Search) - Identify corporate AI infrastructure investments

**Expected Response**:
- **Current Portfolio Positioning Analysis**:
  - Thematic exposure by portfolio (AI, data center, cloud allocations)
    | Portfolio | Description |
    |-----------|-------------|
    | Direct AI | Semiconductor and AI software exposure |
    | Data Center | REIT and infrastructure exposure |
    | Cloud | Cloud infrastructure providers |
    | Total Thematic | Combined thematic allocation |
  - Firm-wide exposure summary and concentration analysis

- **Broker Research - AI Infrastructure Sub-Themes**:
  - Identified sub-themes from broker research synthesis
    | Sub-Theme | Description |
    |-----------|-------------|
    | Thesis | Investment rationale |
    | Market Size | TAM and growth projections |
    | Key Players | Leading companies |
    | Risks/Opportunities | Bull/bear perspectives |
  - Tiered conviction recommendations

- **Management Strategic Commentary**:
    - "Data center demand substantially exceeds our supply. Customers are building out AI factories with H100 and H200 GPUs."
    - "Next-generation Blackwell platform seeing unprecedented demand. Multi-year growth cycle ahead."
    - "Infrastructure buildout is just beginning—we're in first inning of AI data center transition."
  
  * **Microsoft CEO Satya Nadella** (recent quarter):
    - "Capital expenditure increasing to $14B quarterly, primarily for AI infrastructure and data center capacity."
    - "Azure AI capacity constraints limiting growth. Building out infrastructure aggressively to meet demand."
    - "AI workloads require fundamentally different infrastructure—higher power density, specialized cooling, advanced networking."
  
  * **Amazon AWS CEO Adam Selipsky** (recent quarter):
    - "AWS investing $50B in data center capacity, with significant portion for AI infrastructure."
    - "Power and cooling becoming critical constraints. Working with utilities on dedicated power solutions."
    - "AI training clusters require different architecture than traditional cloud—impacting entire infrastructure stack."
  
  * **Equinix CEO Adaire Fox-Martin** (recent quarter):
    - "AI-ready data center capacity fully leased 12 months in advance. Expanding AI-capable facilities by 40%."
    - "Customers specifying 50-100kW per rack for AI workloads vs 5-10kW traditional. Infrastructure transformation required."
    - "Power availability, not space, is limiting factor for AI data center expansion."
  
  * **Management Consensus**: Unprecedented AI infrastructure investment cycle, multi-year duration, capacity constraints driving urgency
  
- **Corporate Investment Announcements** (Press Releases - Last 3 months):
  
  * **Microsoft** (recent): "$10B investment in UK AI data center infrastructure over 3 years"
  * **Amazon** (recent): "Securing 5GW of additional data center power capacity across US and Europe"
  * **Google** (recent): "Expanding AI infrastructure with $9B investment in data centers and networking equipment"
  * **Meta** (recent): "Partnership with Microsoft on AI training infrastructure, joint $6B investment"
  * **Equinix** (recent): "$3.2B acquisition of 12 AI-ready data center facilities in strategic markets"
  * **Vertiv** (recent): "Backlog reaches record $8B for AI power and cooling solutions"
  
  * **Investment Activity**: $45B+ announced AI infrastructure investments in 90 days, validating broker research themes
  
- **Integrated Thematic Investment Strategy**:
  
  * **Theme Validation**: ✅ **STRONG**
    - Broker research consensus on multi-year growth opportunity across 4 sub-themes
    - Management commentary confirms unprecedented spending cycle and capacity constraints
    - Corporate investment activity ($45B+ in 90 days) validates conviction with capital deployment
  
  * **Current Positioning vs Opportunity**:
    | Sub-Theme | Broker Priority | Current Exposure | Target Exposure | Gap Analysis |
    |-----------|----------------|------------------|-----------------|--------------|
    | AI Semiconductors | Tier 1 | 18.3% | 15-18% | ✅ Appropriately positioned |
    | Data Center Networking | Tier 1 | 1.8% | 5-7% | 🔴 Significant underweight (-4%) |
    | Physical Infrastructure | Tier 2 | 3.2% | 6-8% | 🟡 Moderate underweight (-4%) |
    | Power & Cooling | Tier 2 | 0.3% | 3-5% | 🔴 Significant underweight (-4%) |
  
  * **Portfolio Gap Analysis**:
    - **Overweight**: AI compute semiconductors (NVIDIA, AMD) well-positioned but valuation-sensitive
    - **Underweight**: Networking infrastructure (Arista, Broadcom), physical data centers, power systems
    - **Opportunity**: Shift allocation toward infrastructure enablers with better valuations and less crowded positioning
  
  * **Investment Recommendations**:
    
    1. **Immediate Actions** (current quarter implementation):
       - **Increase Networking Infrastructure**: Add 3-4% allocation to Arista Networks, Broadcom networking
         * Rationale: Tier 1 theme, critical GPU interconnect, strong pricing power, less crowded (18x vs 45x P/E)
         * Target: $15-20M new positions in SAM Technology & Infrastructure, SAM Global Thematic Growth
       
       - **Add Physical Data Center Exposure**: Increase data center REIT allocation from 3.2% to 6%
         * Rationale: Capacity constraints, multi-year leasing visibility, attractive yields (4-5%)
         * Target: $12-15M incremental positions in Equinix, Digital Realty
       
       - **Initiate Power/Cooling Positions**: Add 3% allocation to infrastructure equipment
         * Rationale: Emerging bottleneck, uncorrelated to semiconductor volatility, defensive characteristics
         * Target: $8-10M new positions in Vertiv, emerging power infrastructure names
    
    2. **Portfolio Composition Target** (next quarter):
       - AI Semiconductors: 15% (reduce from 18.3% via natural appreciation trim)
       - Data Center Networking: 6% (increase from 1.8%)
       - Physical Infrastructure: 6% (increase from 3.2%)
       - Power & Cooling: 3% (increase from 0.3%)
       - **Total AI Infrastructure Theme**: 30% (focused, diversified across value chain)
    
    3. **Risk Management**:
       - Diversify away from pure-play compute semiconductor concentration
       - Add infrastructure exposure with defensive characteristics and lower valuations
       - Position for multi-year theme with reduced sensitivity to near-term semiconductor cycles
    
    4. **Monitoring Metrics**:
       - Quarterly data center capacity utilization and pricing trends
       - Corporate AI infrastructure capex trajectories (Microsoft, Amazon, Google, Meta)
       - Networking equipment demand trends and GPU interconnect adoption
       - Power infrastructure bottleneck severity and utility investment commitments
  
  * **Investment Committee Recommendation**: 
    - **Approve AI Infrastructure as core thematic focus for the next 12 months**
    - **Authorize $35-45M deployment across networking, physical infrastructure, power/cooling over next two quarters**
    - **Target 30% total AI infrastructure allocation with balanced value chain exposure**
    - **Multi-year investment horizon with quarterly positioning adjustments based on capacity trends**

**Talking Points**:
- **Comprehensive Thematic Intelligence**: Single query orchestrates 4 tools across portfolio analytics, broker research, earnings transcripts, and corporate announcements
- **Multi-Source Validation**: Theme validated through quantitative positioning, external research consensus, management commentary, and corporate capital deployment
- **Actionable Strategy Output**: Specific investment recommendations with dollar amounts, target allocations, and implementation timeline
- **Gap Analysis Framework**: Systematic comparison of current positioning vs research-driven opportunity identifies precise investment needs
- **Risk-Aware Positioning**: Diversification recommendations balance opportunity with valuation risk and sector concentration

**Key Features Highlighted**: 
- **Thematic Portfolio Analytics**: Cortex Analyst aggregates holdings across multiple portfolios to calculate theme-specific exposures
- **Multi-Source Research Synthesis**: Cortex Search across 15 broker reports identifies consensus themes and investment opportunities
- **Management Conviction Tracking**: Earnings transcript analysis reveals strategic priorities and capex commitments
- **Corporate Activity Monitoring**: Press release tracking validates themes with real capital deployment ($45B+ investments)
- **Intelligent Orchestration**: AI automatically sequences analysis from current state → research validation → management perspective → corporate activity → recommendations
- **Investment Decision Framework**: Complete workflow from theme identification through portfolio positioning with specific actions

#### Scenario Wrap-up

**Business Impact Summary**:
- **Strategy Development Speed**: Comprehensive thematic strategy reduced from 2-3 days to under 15 minutes (99% time savings)
- **Research Coverage**: Systematic analysis of 15+ broker reports, 8 earnings transcripts, 10+ press releases vs manual 3-5 source review
- **Decision Quality**: Multi-source validation (research + management + corporate activity) eliminates single-source theme risk
- **Portfolio Optimization**: Precise gap analysis identifies $35-45M specific investment opportunities with clear rationale

**Technical Differentiators**:
- **Cross-Portfolio Thematic Analytics**: Aggregates holdings across 10 portfolios to calculate firm-wide theme exposures unavailable in single-portfolio systems
- **Multi-Modal Research Intelligence**: Seamlessly integrates structured portfolio data (Cortex Analyst) with unstructured research documents (Cortex Search across 3 types)
- **Consensus Theme Extraction**: AI synthesizes 15 broker reports into coherent sub-theme framework with investment priorities
- **Strategic Narrative Analysis**: Earnings transcript processing extracts management conviction signals beyond reported financials
- **Corporate Activity Validation**: Press release monitoring provides real-time validation of themes through capital deployment tracking
- **Systematic Gap Identification**: Automated comparison of current positioning vs research opportunity quantifies precise investment needs

---

### Investment Strategy - Complete Thematic Analysis (Catch-All)

#### Business Context Setup

**Persona**: Anna, Portfolio Manager (Thematic Focus) at Simulated Asset Management  
**Business Challenge**: Thematic portfolio managers sometimes need a complete thematic investment analysis with a single request when preparing for urgent investment committee meetings or responding to market developments—requiring the AI to autonomously orchestrate all thematic research tools for any investment theme.  
**Value Proposition**: The Investment Strategy agent demonstrates complete autonomous orchestration by selecting and sequencing all tools from a single comprehensive question, delivering a committee-ready thematic strategy without step-by-step guidance.

**Agent**: `investment_strategy`  
**Data Available**: Portfolio holdings across 10 strategies, 500 broker research reports, 300 earnings transcripts, 400 press releases

#### Demo Flow

**Scene Setting**: Anna has 15 minutes before an urgent investment committee call. The CIO wants a complete thematic analysis on a specific investment theme. There's no time for multi-step conversations.

##### Step 1: Complete Thematic Analysis (All Tools)

**User Input**: 
```
Develop a complete thematic investment strategy for [INVESTMENT THEME] including our current portfolio exposure across all strategies, the latest broker research identifying key sub-themes and investment opportunities, management commentary from earnings calls on strategic priorities and capital deployment, recent corporate announcements and partnerships, and a synthesized positioning recommendation showing where we should increase or decrease exposure.
```

**Note**: Replace `[INVESTMENT THEME]` with any relevant investment theme (e.g., "renewable energy transition", "healthcare innovation", "digital payments", "cybersecurity", "electric vehicles and battery technology").

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Analyze current portfolio thematic exposure
- `search_external_docs` (Cortex Search) - Find thematic research and sub-themes
- `search_company_events` (Cortex Search) - Retrieve management strategic commentary
- `search_external_docs` (Cortex Search) - Identify corporate investments and partnerships

**Expected Response**:
- **Portfolio Positioning**: Current exposure by portfolio with concentration analysis
- **Research Synthesis**: Broker research consensus on sub-themes and investment opportunities
- **Management Perspective**: Strategic commentary from earnings calls validating theme
- **Corporate Activity**: Recent announcements and capital deployment supporting theme
- **Gap Analysis**: Current positioning vs research-driven opportunity
- **Investment Recommendations**: Specific allocation changes with target weights and rationale
- **Committee Summary**: Executive-ready thematic strategy for immediate presentation

**Talking Points**:
- **Autonomous Orchestration**: AI independently selects and sequences all four thematic tools
- **Single-Query Capability**: Complete thematic strategy from one comprehensive question
- **Theme Agnostic**: Works with any investment theme—AI adapts research and analysis accordingly
- **Committee Ready**: Output structured for immediate investment committee presentation

**Key Features Highlighted**: 
- **Multi-Tool AI Orchestration**: Agent autonomously determines tool sequence and synthesis
- **Cross-Portfolio Analysis**: Holdings data merged across all strategies for firm-wide view
- **Multi-Source Validation**: Theme validated through research, management, and corporate activity
- **Actionable Output**: Specific positioning recommendations ready for implementation

#### Scenario Wrap-up

**Business Impact Summary**:
- **Rapid Response**: Complete thematic strategy available in under 5 minutes
- **Theme Flexibility**: Works with any investment theme without pre-configuration
- **Comprehensive Coverage**: Combines portfolio analytics with research across three document types
- **Decision Quality**: Multi-source validation ensures robust thematic investment decisions

**Technical Differentiators**:
- **Four-Tool Integration**: Demonstrates full Investment Strategy capability in single query
- **Intelligent Synthesis**: AI merges quantitative positioning with qualitative research insights
- **Autonomous Operation**: True AI agent capability for thematic investment strategy development
- **Universal Theme Application**: Same workflow applies to any emerging or established investment theme

---

### Investment Strategy - Yield Curve & Rate Regime Analysis

#### Business Context Setup

**Persona**: James, Head of Multi-Asset Strategy at Simulated Asset Management  
**Business Challenge**: Understanding the yield curve shape and interest rate regime is critical for thematic positioning — rate-sensitive themes (real estate, utilities, growth vs value rotation) depend heavily on monetary policy context.  
**Value Proposition**: US Treasury yield curve data integrated into thematic analysis for rate-regime-aware investment strategy.

**Agent**: `investment_strategy`  
**Data Available**: US Treasury yield curve (14 maturities, 1M-30Y, daily)

#### Demo Flow

##### Step 1: Yield Curve Analysis
**User Input**: 
```
What does the current US Treasury yield curve look like? Is it inverted, and what does that signal for growth themes?
```

**Tools Used**:
- `treasury_yield_analyzer` (Cortex Analyst) - Yield curve across all maturities

**Expected Response**:
- Current yield curve shape with rates by maturity
- Inversion analysis (2Y-10Y spread, 3M-10Y spread)
- Implications for growth vs value rotation themes
- Historical context for yield curve signals

**Key Features Highlighted**: 
- Real US Treasury data from Snowflake Public Data
- Yield curve shape as thematic regime indicator
- Integration with macro-driven investment themes


---

## Part 5: Portfolio Modelling

## Financial Advisor

### Portfolio Modelling Copilot - IPS-Driven Portfolio Construction

#### Business Context Setup

**Persona**: Sarah Mitchell, Financial Advisor at Simulated Asset Management  
**Business Challenge**: Financial advisors face the critical challenge of translating Investment Policy Statements (IPS) into optimal portfolio allocations. An IPS defines client goals, risk tolerance, time horizon, and constraints—but bridging the gap between policy document and executable portfolio requires quantitative validation. Traditional approaches require manual spreadsheet analysis, multiple vendor tools, and hours of work to test different allocations, validate risk metrics against IPS limits, and project outcomes over the investment horizon. This often results in suboptimal portfolios or undetected IPS violations.  
**Value Proposition**: AI-powered portfolio construction that tests multiple allocations, runs Monte Carlo projections for each, validates against IPS constraints, and compares results side-by-side—enabling data-driven weight optimisation and IPS compliance verification in minutes instead of hours.

**Agent**: `portfolio_modelling_copilot`  
**Data Available**: Historical returns for 80+ securities (5+ years), Fama-French factor data, methodology documentation, Monte Carlo simulation engine

#### Demo Flow

**Scene Setting**: Sarah has just completed an Investment Policy Statement with her high-net-worth client Dr. James Chen. The IPS specifies: 12% target annual return, maximum 35% volatility, maximum 45% drawdown, 20-year time horizon, and $1M initial investment. Dr. Chen has expressed preference for technology growth exposure but is open to some diversification into quality defensive names. Sarah needs to construct and validate a portfolio recommendation before her afternoon client meeting.

##### Step 1: Review IPS Requirements and Understand Methodology

**User Input**: 
```
I have a client IPS with these requirements: 12% target annual return, maximum 35% volatility, maximum 45% drawdown, 20-year horizon, $1M initial investment. Before I propose an allocation, explain how you measure portfolio volatility and what risk metrics you'll use to validate against these constraints.
```

**Tools Used**:
- `search_internal_docs` (Cortex Search) - Retrieve risk methodology documentation

**Expected Response**:
- **Methodology Overview**: Explanation of volatility calculation (annualised standard deviation of returns)
- **Risk Metrics Defined**: 
  | Metric | Description |
  |--------|-------------|
  | Volatility | Annualised standard deviation of portfolio returns |
  | Maximum Drawdown | Largest peak-to-trough decline during backtest period |
  | Sharpe Ratio | Risk-adjusted return measure (excess return / volatility) |
  | VaR/CVaR | Tail risk measures for downside scenarios |
- **IPS Alignment**: How each metric maps to the client's constraints
- **Validation Approach**: Steps to validate allocation against IPS limits

**Talking Points**:
- AI understands investment methodology and explains it clearly before analysis
- Client requirements are mapped to specific quantitative metrics
- Builds advisor confidence in the analytical framework

**Key Features Highlighted**: 
- Cortex Search retrieves methodology documentation
- Clear explanation of how risk constraints will be validated
- Professional setup before quantitative analysis begins

##### Step 2: Backtest Aggressive Tech-Focused Allocation

**Presenter Transition**:
> "Now that we understand the risk framework, let me test an aggressive allocation that aligns with my client's technology growth preference. This will be our first candidate portfolio..."

*Reasoning: Starting with a tech-heavy allocation demonstrates the client's stated preference. Including Costco adds a quality defensive name while maintaining growth focus. This creates a natural comparison point for a more diversified alternative.*

**User Input**: 
```
Based on my client's technology growth preference, backtest Portfolio A with 40% Apple, 30% Microsoft, 20% NVIDIA, and 10% Costco from 2019 to 2024.
```

**Tools Used**:
- `run_backtest` (Stored Procedure) - Execute historical portfolio backtest

**Expected Response**:
- **Performance Summary**:
  | Metric | Value |
  |--------|-------|
  | Total Return | Portfolio total return over period |
  | Annualised Return | Geometric average annual return |
  | Benchmark Comparison | Performance vs S&P 500 |
- **Risk Metrics**:
  | Metric | Value | IPS Limit | Status |
  |--------|-------|-----------|--------|
  | Volatility | Annualised volatility | <35% | Pass/Fail indicator |
  | Max Drawdown | Largest decline | >-45% | Pass/Fail indicator |
  | Sharpe Ratio | Risk-adjusted return | - | Interpretation |
- **Key Observations**: Analysis of concentration risk, sector exposure, drawdown periods
- **IPS Validation**: Clear comparison to client constraints

**Talking Points**:
- Backtest provides historical evidence for proposed allocation
- Immediate flagging of constraint violations
- Real historical data, not theoretical projections

**Key Features Highlighted**: 
- Stored procedure executes complex backtest calculations server-side
- Automatic validation against IPS constraints
- Professional risk reporting format

##### Step 3: Monte Carlo Projection for Aggressive Portfolio

**Presenter Transition**:
> "The backtest shows strong historical returns, but that concentrated tech allocation looks quite volatile. Let me project forward to see the probability of actually achieving our client's 12% target over the 20-year horizon..."

*Reasoning: Historical performance doesn't guarantee future results. Monte Carlo projection translates historical risk into forward-looking probability of meeting the client's goals.*

**User Input**: 
```
Run a Monte Carlo simulation for Portfolio A over 20 years with the $1M initial investment. What's the probability of achieving at least 12% annualised return and what's the downside risk?
```

**Tools Used**:
- `run_monte_carlo` (Stored Procedure) - Execute Monte Carlo simulation with block bootstrapping

**Expected Response**:
- **Projection Summary**:
  | Percentile | Terminal Value | Multiple |
  |------------|----------------|----------|
  | 5th (downside) | Worst-case outcome | Growth multiple |
  | 25th | Conservative outcome | Growth multiple |
  | 50th (median) | Expected outcome | Growth multiple |
  | 75th | Optimistic outcome | Growth multiple |
  | 95th (upside) | Best-case outcome | Growth multiple |
- **Goal Achievement**:
  | Outcome | Probability |
  |---------|-------------|
  | Achieve 12% target | Probability percentage |
  | Loss (< $1M) | Probability percentage |
  | Double investment | Probability percentage |
- **Risk Assessment**: Interpretation of distribution width and downside scenarios
- **Methodology Note**: Block bootstrapping preserves volatility clustering

**Talking Points**:
- Forward projection complements historical backtest
- Probability metrics enable goal-based planning
- Wide distribution reflects concentrated portfolio risk

**Key Features Highlighted**: 
- 10,000 simulation paths for statistical robustness
- Block bootstrapping preserves real market dynamics
- Probability of meeting specific client goals

##### Step 4: Backtest Diversified Conservative Allocation

**Presenter Transition**:
> "Portfolio A delivers strong returns but concentrates heavily in tech. Let me test a more diversified allocation that adds financials and healthcare exposure to compare the risk-return tradeoff..."

*Reasoning: Demonstrating an alternative allocation shows the advisor's due diligence and enables data-driven comparison. Portfolio B adds sector diversification with JPMorgan (financials) and Eli Lilly (healthcare) while maintaining core tech holdings.*

**User Input**: 
```
Now backtest Portfolio B with a more diversified allocation: 25% Apple, 25% Microsoft, 20% Costco, 15% JPMorgan, and 15% Eli Lilly from 2019 to 2024.
```

**Tools Used**:
- `run_backtest` (Stored Procedure) - Execute historical portfolio backtest

**Expected Response**:
- **Performance Summary**:
  | Metric | Value |
  |--------|-------|
  | Total Return | Portfolio total return over period |
  | Annualised Return | Geometric average annual return |
  | Benchmark Comparison | Performance vs S&P 500 |
- **Risk Metrics**:
  | Metric | Value | IPS Limit | Status |
  |--------|-------|-----------|--------|
  | Volatility | Annualised volatility | <35% | Pass/Fail indicator |
  | Max Drawdown | Largest decline | >-45% | Pass/Fail indicator |
  | Sharpe Ratio | Risk-adjusted return | - | Interpretation |
- **Comparison to Portfolio A**: Brief comparison of key differences
- **IPS Validation**: Clear comparison to client constraints

**Talking Points**:
- Sector diversification adds financials (JPM) and healthcare (LLY) exposure
- Maintains core tech holdings (AAPL, MSFT) while reducing concentration
- Trade-off between growth potential and risk diversification

**Key Features Highlighted**: 
- Same analytical framework applied to different allocation
- Consistent IPS validation approach
- Building comparison dataset for decision-making

##### Step 5: Monte Carlo Projection for Diversified Portfolio

**Presenter Transition**:
> "Portfolio B shows better risk metrics in the historical backtest. Let me run the same Monte Carlo projection to compare the probability of achieving our client's goals with this more diversified allocation..."

*Reasoning: Consistent analysis framework enables apples-to-apples comparison. Monte Carlo for both portfolios allows comparison of goal achievement probabilities.*

**User Input**: 
```
Run the same Monte Carlo simulation for Portfolio B over 20 years with $1M. Compare the probability of achieving 12% return versus Portfolio A.
```

**Tools Used**:
- `run_monte_carlo` (Stored Procedure) - Execute Monte Carlo simulation

**Expected Response**:
- **Portfolio B Projection**:
  | Percentile | Terminal Value | Multiple |
  |------------|----------------|----------|
  | 5th (downside) | Worst-case outcome | Growth multiple |
  | 50th (median) | Expected outcome | Growth multiple |
  | 95th (upside) | Best-case outcome | Growth multiple |
- **Goal Achievement Comparison**:
  | Outcome | Portfolio A | Portfolio B |
  |---------|-------------|-------------|
  | Achieve 12% target | Probability | Probability |
  | Loss (< $1M) | Probability | Probability |
- **Risk Assessment**: Comparison of distribution width and downside scenarios
- **Key Insight**: Which portfolio has better risk-adjusted probability of success

**Talking Points**:
- Side-by-side probability comparison enables informed decision
- Lower volatility may mean higher goal achievement probability
- Tighter distribution reduces uncertainty for client planning

**Key Features Highlighted**: 
- Consistent methodology enables direct comparison
- Goal achievement probability as key decision metric
- Data-driven portfolio selection

##### Step 6: Compare Allocations Against IPS Constraints

**Presenter Transition**:
> "Now I have complete quantitative data for both allocations—historical backtests and forward projections. Let me generate a comprehensive comparison against my client's IPS requirements to determine which portfolio is compliant..."

*Reasoning: This synthesis step brings together all analysis into a clear decision framework. The IPS compliance matrix provides the definitive answer.*

**User Input**: 
```
Compare Portfolio A and Portfolio B against my client's IPS requirements. Which allocation meets the constraints of 12% target return, maximum 35% volatility, and maximum 45% drawdown?
```

**Tools Used**:
- `portfolio_modelling_analyzer` (Cortex Analyst) - Query and synthesise results
- `search_internal_docs` (Cortex Search) - Reference IPS compliance criteria

**Expected Response**:
- **IPS Compliance Matrix**:
  | Metric | Portfolio A | Portfolio B | IPS Limit | A Status | B Status |
  |--------|-------------|-------------|-----------|----------|----------|
  | Annualised Return | Return % | Return % | >12% | ✅/❌ | ✅/❌ |
  | Volatility | Volatility % | Volatility % | <35% | ✅/❌ | ✅/❌ |
  | Max Drawdown | Drawdown % | Drawdown % | >-45% | ✅/❌ | ✅/❌ |
  | P(Achieve Target) | Probability | Probability | - | - | - |
- **Compliance Summary**: Which portfolio passes all constraints
- **Risk-Adjusted Assessment**: Sharpe ratio and goal achievement comparison
- **Trade-off Analysis**: What the client gives up with each option

**Talking Points**:
- Clear visual comparison against IPS requirements
- Compliance status immediately visible
- Data-driven basis for recommendation

**Key Features Highlighted**: 
- Comprehensive IPS compliance validation
- Side-by-side comparison framework
- Professional decision support for advisor

##### Step 7: Finalise IPS-Compliant Recommendation

**Presenter Transition**:
> "Based on the comprehensive analysis, I can now provide my client with a data-driven recommendation. Let me generate a summary suitable for the client meeting..."

*Reasoning: The final step synthesises all analysis into an actionable recommendation with clear rationale. This is what the advisor presents to the client.*

**User Input**: 
```
Summarise your recommendation for my client meeting. Include the key metrics, IPS compliance status, and your rationale for the recommended allocation.
```

**Expected Response**:
- **Executive Summary**: Recommended portfolio allocation with rationale
- **IPS Compliance Confirmation**: All constraints validated
- **Key Evidence**:
  | Analysis Type | Key Finding |
  |---------------|-------------|
  | Historical Backtest | Performance and risk metrics |
  | Monte Carlo Projection | Goal achievement probability |
  | IPS Validation | Compliance status |
- **Recommendation Rationale**: Why this allocation best serves the client's goals
- **Next Steps**: Implementation considerations and monitoring approach
- **Disclaimer**: Standard investment disclaimer

**Talking Points**:
- Complete audit trail from IPS to recommendation
- Quantitative evidence supports every aspect of recommendation
- Professional presentation ready for client meeting

**Key Features Highlighted**: 
- End-to-end portfolio construction workflow
- Policy-to-portfolio bridge demonstrated
- Client-ready output format

#### Scenario Wrap-up

**Business Impact Summary**:
- **Time Savings**: Portfolio construction and validation reduced from hours to minutes
- **Risk Management**: Quantitative validation ensures IPS compliance before implementation
- **Client Confidence**: Data-driven recommendations with clear evidence trail
- **Regulatory Alignment**: Documented process supports fiduciary duty requirements

**Technical Differentiators**:
- **Policy-to-Portfolio Bridge**: AI translates IPS requirements into quantitative validation criteria
- **Multi-Tool Orchestration**: Seamless integration of backtest, Monte Carlo, and analytics tools
- **Weight Optimisation**: Compare multiple allocations systematically with consistent framework
- **Forward + Historical**: Combines backtesting with probabilistic projection for complete picture
- **IPS Compliance Automation**: Automatic validation against client constraints

---

### Portfolio Modelling Copilot - Client Retirement Planning

#### Business Context Setup

**Persona**: James Patterson, Financial Advisor at Simulated Asset Management  
**Business Challenge**: Retirement planning requires projecting portfolio outcomes over long horizons with significant uncertainty. Clients need to understand not just expected outcomes, but the range of possibilities and probability of achieving their retirement income goals. Traditional deterministic projections using average returns fail to capture market uncertainty and can lead to overconfidence in retirement readiness.  
**Value Proposition**: Monte Carlo simulation-based retirement planning that shows clients the full distribution of possible outcomes, probability of meeting retirement goals, and enables comparison of different allocation strategies to find the optimal risk-return balance for their specific situation.

**Agent**: `portfolio_modelling_copilot`  
**Data Available**: Historical returns for 80+ securities, Monte Carlo simulation engine, risk factor data

#### Demo Flow

**Scene Setting**: James is preparing for a retirement planning meeting with the Hendersons, a couple in their mid-40s with $750,000 in retirement savings. They want to understand if their current allocation strategy will support their goal of $2.5M at retirement in 20 years, and whether a more conservative approach might be prudent as they approach retirement.

##### Step 1: Define Retirement Goals and Initial Allocation

**User Input**: 
```
I have clients with $750,000 in retirement savings, targeting $2.5M in 20 years. Their current allocation is 60% equities (30% AAPL, 20% MSFT, 10% GOOGL) and 40% in diversified holdings (15% AMZN, 15% NVDA, 10% TSM). What's the probability of reaching their goal with this allocation?
```

**Tools Used**:
- `run_backtest` (Stored Procedure) - Validate historical performance
- `run_monte_carlo` (Stored Procedure) - Project retirement outcomes

**Expected Response**:
- **Current Allocation Summary**: Weight distribution and risk profile
- **Historical Performance**: Backtest metrics for context
- **Monte Carlo Projection**:
  | Percentile | Terminal Value | Goal Status |
  |------------|----------------|-------------|
  | 5th | Worst-case | Above/below $2.5M |
  | 50th | Median | Above/below $2.5M |
  | 95th | Best-case | Above/below $2.5M |
- **Goal Achievement Probability**: Percentage chance of reaching $2.5M
- **Risk Assessment**: Downside scenarios and probability of loss

**Talking Points**:
- Monte Carlo provides realistic range of outcomes, not single projection
- Goal achievement probability gives clients clear success metric
- Historical context validates allocation behaviour

**Key Features Highlighted**: 
- Goal-based retirement planning with probability metrics
- Client-friendly presentation of complex simulation results

##### Step 2: Stress Test Downside Scenarios

**Presenter Transition**:
> "The median outcome looks promising, but my clients are concerned about downside risk as they approach retirement. Let me examine what happens in pessimistic scenarios..."

*Reasoning: Retirement planning must account for sequence-of-returns risk. Examining downside scenarios helps clients understand worst-case outcomes.*

**User Input**: 
```
What happens in the worst 10% of scenarios? If markets underperform, what's the minimum they could end up with and what's the probability of not reaching $2M?
```

**Tools Used**:
- `run_monte_carlo` (Stored Procedure) - Analyse tail scenarios
- `search_internal_docs` (Cortex Search) - Explain downside risk concepts

**Expected Response**:
- **Downside Analysis**:
  | Scenario | Terminal Value | Probability |
  |----------|----------------|-------------|
  | 5th percentile | Worst-case outcome | 5% |
  | 10th percentile | Pessimistic outcome | 10% |
  | Fail to reach $2M | Below minimum | Probability % |
- **Risk Explanation**: Why these scenarios occur and their characteristics
- **Mitigation Options**: Strategies to reduce downside exposure

**Talking Points**:
- Downside scenarios help clients prepare for adverse outcomes
- Understanding risk enables informed decision-making
- Sets up comparison with more conservative allocation

**Key Features Highlighted**: 
- Tail risk analysis for retirement planning
- Methodology explanation builds client understanding

##### Step 3: Test More Conservative Allocation

**Presenter Transition**:
> "Given my clients' concern about downside risk, let me test a more conservative allocation with lower volatility to see how it affects both the probability of reaching their goal and the downside protection..."

*Reasoning: Comparing allocations helps clients understand the risk-return tradeoff and make informed decisions about their risk tolerance.*

**User Input**: 
```
Test a more conservative Portfolio B: 40% equities (15% AAPL, 15% MSFT, 10% GOOGL) and 60% diversified (20% AMZN, 20% JNJ, 20% PG). Compare the goal achievement probability and downside risk to the original allocation.
```

**Tools Used**:
- `run_backtest` (Stored Procedure) - Backtest conservative allocation
- `run_monte_carlo` (Stored Procedure) - Project retirement outcomes

**Expected Response**:
- **Portfolio B Profile**: Lower volatility, more defensive positioning
- **Comparison Table**:
  | Metric | Portfolio A | Portfolio B |
  |--------|-------------|-------------|
  | Expected Return | Higher | Lower |
  | Volatility | Higher | Lower |
  | P(Reach $2.5M) | Probability | Probability |
  | P(Below $2M) | Probability | Probability |
  | 5th Percentile | Value | Value |
- **Trade-off Analysis**: What clients gain/lose with each approach
- **Risk-Adjusted Assessment**: Which allocation better fits their situation

**Talking Points**:
- Lower volatility may improve goal achievement despite lower returns
- Downside protection becomes more important near retirement
- Data enables informed client decision

**Key Features Highlighted**: 
- Systematic comparison of allocation strategies
- Quantitative risk-return tradeoff analysis

##### Step 4: Recommend Optimal Allocation

**Presenter Transition**:
> "With both scenarios analysed, I can now provide a recommendation based on my clients' specific goals and risk tolerance..."

*Reasoning: Synthesis of analysis into clear recommendation with supporting evidence.*

**User Input**: 
```
Based on the analysis, which allocation do you recommend for the Hendersons given their 20-year horizon and $2.5M goal? Summarise the key factors supporting your recommendation.
```

**Expected Response**:
- **Recommendation**: Recommended allocation with rationale
- **Supporting Evidence**:
  | Factor | Analysis |
  |--------|----------|
  | Goal Achievement | Probability comparison |
  | Downside Protection | Tail risk comparison |
  | Risk-Return Balance | Optimal for client situation |
- **Implementation Guidance**: How to transition to recommended allocation
- **Monitoring Framework**: How to track progress toward goal

**Talking Points**:
- Data-driven recommendation with clear rationale
- Balances client goals with risk tolerance
- Professional retirement planning workflow complete

**Key Features Highlighted**: 
- End-to-end retirement planning workflow
- Quantitative basis for allocation recommendation

#### Scenario Wrap-up

**Business Impact Summary**:
- **Client Understanding**: Probability-based planning enables informed decisions
- **Risk Communication**: Clear visualisation of downside scenarios
- **Confidence**: Data-driven recommendations build client trust
- **Compliance**: Documented suitability analysis supports regulatory requirements

**Technical Differentiators**:
- **Monte Carlo Retirement Planning**: Realistic projection of retirement outcomes
- **Goal-Based Analysis**: Focus on probability of achieving client goals
- **Tail Risk Assessment**: Explicit analysis of downside scenarios
- **Allocation Comparison**: Systematic framework for strategy selection

---

## Chief Investment Officer

### Portfolio Modelling Copilot - Quarterly Performance Attribution

#### Business Context Setup

**Persona**: Victoria Chen, Chief Investment Officer at Simulated Asset Management  
**Business Challenge**: Understanding the sources of portfolio performance is essential for investment oversight, manager evaluation, and strategy refinement. When a portfolio outperforms or underperforms its benchmark, the CIO needs to determine whether this was due to sector allocation decisions, security selection within sectors, or interaction effects. Traditional performance reports often lack this decomposition, making it difficult to identify what's working and what needs adjustment.  
**Value Proposition**: AI-powered performance attribution that decomposes active returns into allocation, selection, and interaction effects at the sector level—enabling precise identification of performance drivers, informed strategy refinement, and evidence-based manager evaluation.

**Agent**: `portfolio_modelling_copilot`  
**Data Available**: Portfolio holdings, benchmark weights, sector returns, Brinson-Fachler attribution engine

#### Demo Flow

**Scene Setting**: Victoria is preparing for the quarterly investment committee meeting. The SAM Growth Equity portfolio outperformed its S&P 500 benchmark by 180 basis points last quarter. Before the meeting, she needs to understand whether this outperformance came from being in the right sectors (allocation), picking the right stocks within sectors (selection), or a combination of both.

##### Step 1: Run Brinson-Fachler Attribution

**User Input**: 
```
Run a Brinson-Fachler attribution analysis for the SAM Growth Equity portfolio versus the S&P 500 for Q4 2024. Decompose the active return into allocation, selection, and interaction effects.
```

**Tools Used**:
- `run_attribution` (Stored Procedure) - Execute Brinson-Fachler attribution

**Expected Response**:
- **Active Return Decomposition**:
  | Component | Contribution |
  |-----------|--------------|
  | Portfolio Return | Quarterly return |
  | Benchmark Return | Quarterly return |
  | Active Return | Excess return |
  | Allocation Effect | Sector weight contribution |
  | Selection Effect | Stock picking contribution |
  | Interaction Effect | Combined effect |
- **Interpretation**: Primary driver of outperformance
- **Methodology Note**: Brinson-Fachler single-period attribution

**Talking Points**:
- Attribution decomposes total outperformance into components
- Identifies whether success came from allocation or selection
- Essential for manager evaluation and strategy refinement

**Key Features Highlighted**: 
- Brinson-Fachler attribution methodology
- Clear decomposition of active return sources

##### Step 2: Analyse Sector-Level Effects

**Presenter Transition**:
> "The aggregate attribution shows selection was the primary driver. Let me drill down to see which specific sectors contributed most to performance..."

*Reasoning: Sector-level detail identifies which allocation and selection decisions added or detracted value.*

**User Input**: 
```
Show me the sector-level attribution breakdown. Which sectors contributed most to the allocation effect and which had the strongest selection effect?
```

**Tools Used**:
- `run_attribution` (Stored Procedure) - Sector-level breakdown
- `portfolio_modelling_analyzer` (Cortex Analyst) - Query sector weights

**Expected Response**:
- **Sector Attribution Table**:
  | Sector | Port Weight | Bench Weight | Allocation | Selection |
  |--------|-------------|--------------|------------|-----------|
  | Technology | Weight % | Weight % | Effect | Effect |
  | Healthcare | Weight % | Weight % | Effect | Effect |
  | Financials | Weight % | Weight % | Effect | Effect |
  | Consumer | Weight % | Weight % | Effect | Effect |
- **Top Contributors**: Sectors with largest positive effects
- **Detractors**: Sectors with negative effects
- **Key Insights**: Explanation of major attribution drivers

**Talking Points**:
- Sector-level detail enables targeted strategy refinement
- Identifies both successful and unsuccessful decisions
- Guides future allocation and selection focus

**Key Features Highlighted**: 
- Granular sector-level attribution
- Identification of top contributors and detractors

##### Step 3: Examine Factor Exposures

**Presenter Transition**:
> "Understanding factor exposures helps explain the systematic sources of outperformance beyond sector allocation..."

*Reasoning: Factor analysis provides additional insight into performance drivers related to systematic risk factors.*

**User Input**: 
```
What were our factor exposures last quarter? Show me the Fama-French factor returns and how our portfolio's factor tilts contributed to performance.
```

**Tools Used**:
- `portfolio_modelling_analyzer` (Cortex Analyst) - Query factor data
- `search_internal_docs` (Cortex Search) - Explain factor concepts

**Expected Response**:
- **Factor Returns**:
  | Factor | Q4 Return | Portfolio Exposure |
  |--------|-----------|-------------------|
  | MKT-RF | Market return | Beta exposure |
  | SMB | Size factor | Small/large tilt |
  | HML | Value factor | Value/growth tilt |
  | MOM | Momentum | Momentum exposure |
- **Factor Contribution**: How factor tilts affected performance
- **Interpretation**: Systematic vs idiosyncratic performance

**Talking Points**:
- Factor analysis complements sector attribution
- Identifies systematic risk exposures
- Helps distinguish skill from factor loading

**Key Features Highlighted**: 
- Fama-French factor analysis
- Integration of factor and sector attribution

##### Step 4: Generate Rebalancing Recommendations

**Presenter Transition**:
> "Based on the attribution analysis, let me generate recommendations for next quarter's positioning..."

*Reasoning: Attribution analysis should drive forward-looking strategy refinement.*

**User Input**: 
```
Based on the attribution analysis, what adjustments should we consider for next quarter? Are there sectors where we should increase or decrease our allocation based on our selection skill?
```

**Expected Response**:
- **Strategy Recommendations**:
  | Action | Sector | Rationale |
  |--------|--------|-----------|
  | Increase | Sector | Strong selection, positive outlook |
  | Maintain | Sector | Consistent performance |
  | Reduce | Sector | Negative selection, reassess |
- **Risk Considerations**: Impact on portfolio risk profile
- **Implementation Notes**: Timing and execution considerations

**Talking Points**:
- Attribution drives forward-looking strategy
- Evidence-based allocation adjustments
- Complete performance-to-action workflow

**Key Features Highlighted**: 
- Attribution-driven strategy refinement
- Actionable recommendations from analysis

#### Scenario Wrap-up

**Business Impact Summary**:
- **Performance Understanding**: Clear decomposition of return sources
- **Manager Evaluation**: Evidence base for assessing investment decisions
- **Strategy Refinement**: Data-driven allocation and selection adjustments
- **Committee Reporting**: Professional attribution for investment oversight

**Technical Differentiators**:
- **Brinson-Fachler Attribution**: Industry-standard performance decomposition
- **Multi-Level Analysis**: Aggregate and sector-level attribution
- **Factor Integration**: Systematic risk factor analysis
- **Actionable Insights**: Recommendations from attribution findings

---

## Financial Advisor

### Portfolio Modelling Copilot - Complete Portfolio Analysis (Catch-All)

#### Business Context Setup

**Persona**: Michael Torres, Financial Advisor at Simulated Asset Management  
**Business Challenge**: Advisors often need comprehensive portfolio analysis combining multiple analytical perspectives—historical performance, forward projections, risk metrics, and methodology explanations—in a single conversation. Traditional workflows require switching between multiple tools and systems, fragmenting the analysis and making it difficult to present a cohesive picture to clients.  
**Value Proposition**: Single-query comprehensive portfolio analysis that orchestrates backtesting, Monte Carlo simulation, risk metrics, and methodology explanation into a complete investment assessment—demonstrating the full capability of AI-powered portfolio analytics.

**Agent**: `portfolio_modelling_copilot`  
**Data Available**: Historical returns, Monte Carlo engine, attribution tools, methodology documentation

#### Demo Flow

**Scene Setting**: Michael has a prospective client meeting in 30 minutes. The client has asked for a comprehensive analysis of a proposed technology-focused portfolio with specific risk constraints. Michael needs to quickly generate a complete portfolio assessment covering historical performance, forward projections, risk validation, and methodology transparency.

##### Comprehensive Single Query

**User Input**: 
```
I need a complete portfolio analysis for a client considering a tech-focused allocation: 35% Apple, 30% Microsoft, 20% NVIDIA, and 15% Costco. The client's IPS requires maximum 35% volatility and minimum 0.6 Sharpe ratio. Please: 1) Backtest from 2019-2024, 2) Run a 15-year Monte Carlo projection with $500K initial investment, 3) Validate against IPS constraints, 4) Explain the key risk metrics used, and 5) Provide your recommendation.
```

**Tools Used**:
- `run_backtest` (Stored Procedure) - Historical performance analysis
- `run_monte_carlo` (Stored Procedure) - Forward projection
- `portfolio_modelling_analyzer` (Cortex Analyst) - Data queries
- `search_internal_docs` (Cortex Search) - Methodology explanation

**Expected Response**:
- **Historical Backtest Results**:
  | Metric | Value |
  |--------|-------|
  | Total Return | Backtest return |
  | Annualised Return | Annual return |
  | Volatility | Risk measure |
  | Sharpe Ratio | Risk-adjusted return |
  | Max Drawdown | Largest decline |
- **Monte Carlo Projection**:
  | Percentile | Terminal Value |
  |------------|----------------|
  | 5th | Downside outcome |
  | 50th | Median outcome |
  | 95th | Upside outcome |
- **IPS Compliance**:
  | Constraint | Actual | Limit | Status |
  |------------|--------|-------|--------|
  | Volatility | Value | <35% | ✅/❌ |
  | Sharpe Ratio | Value | >0.6 | ✅/❌ |
- **Methodology Notes**: Explanation of volatility, Sharpe ratio, and simulation methodology
- **Recommendation**: Overall assessment with supporting rationale

**Talking Points**:
- Single query orchestrates five different analytical tools
- Complete portfolio assessment in one response
- Demonstrates full agent capability

**Key Features Highlighted**: 
- Multi-tool orchestration in single query
- Comprehensive portfolio analysis framework
- IPS validation automation
- Methodology transparency

#### Scenario Wrap-up

**Business Impact Summary**:
- **Efficiency**: Complete analysis in single query vs multiple tool interactions
- **Completeness**: All analytical perspectives in cohesive format
- **Client Ready**: Professional output suitable for immediate presentation
- **Demonstration**: Full agent capability showcase

**Technical Differentiators**:
- **Multi-Tool Orchestration**: Five tools coordinated seamlessly
- **Comprehensive Framework**: Backtest + Monte Carlo + IPS validation + methodology
- **Natural Language Interface**: Complex analysis from single conversational query
- **Professional Output**: Investment-grade analysis format

---

## Financial Advisor

### Portfolio Modelling Copilot - AI-Powered Portfolio Optimisation

#### Business Context Setup

**Persona**: Sarah Mitchell, Financial Advisor at Simulated Asset Management  
**Business Challenge**: Advisors typically propose portfolio weights based on experience and rules of thumb, then validate with backtests. True mathematical optimisation — mean-variance, risk parity, efficient frontier — requires quantitative tooling that most advisors lack. When a client asks "what's the best allocation given my constraints?", the advisor needs an answer grounded in optimisation theory, not intuition.  
**Value Proposition**: AI-powered portfolio optimisation using the `code_execution` tool to run scipy/numpy algorithms in-conversation, guided by the `portfolio-optimizer` skill. The advisor describes constraints in plain English and receives mathematically optimal allocations instantly.

**Agent**: `portfolio_modelling_copilot`  
**Skills Used**: `portfolio-optimizer`, `audience-adaptive-narrative`  
**Data Available**: Historical returns for 80+ securities, covariance matrices, Monte Carlo engine

#### Demo Flow

**Scene Setting**: Sarah is meeting a new institutional client who wants a quantitatively optimised allocation across 6 securities, subject to IPS constraints. The client has explicitly asked for mean-variance optimised weights rather than ad-hoc allocations.

##### Step 1: Define Universe and Pull Historical Data

**User Input**: 
```
I need to build an optimised portfolio across Apple, Microsoft, NVIDIA, Costco, JPMorgan, and Eli Lilly. First, show me the annualised returns and covariance matrix for these securities over the last 3 years.
```

**Tools Used**:
- `portfolio_modelling_analyzer` (Cortex Analyst) - Query historical returns and compute statistics

**Expected Response**:
- **Annualised Returns**: Per-security expected return estimates
- **Covariance Matrix**: 6×6 matrix showing variance and co-movement
- **Risk-Return Scatter**: Quick positioning of each security

**Talking Points**:
- Data retrieval through natural language before any optimisation
- Agent understands the need to compute covariance from raw returns

##### Step 2: Run Mean-Variance Optimisation

**Presenter Transition**:
> "Now that we have the risk-return data, let me ask the agent to find the mathematically optimal allocation..."

**User Input**: 
```
Find the minimum variance portfolio for these 6 securities with no single position exceeding 30%.
```

**Tools Used**:
- `server_skill` → loads `portfolio-optimizer` skill
- `code_execution` — Runs scipy.optimize.minimize with covariance matrix and position constraints

**Expected Response**:
- **Optimal Weights**:
  | Security | Weight | Contribution to Risk |
  |----------|--------|---------------------|
  | AAPL | X% | X% |
  | MSFT | X% | X% |
  | NVDA | X% | X% |
  | COST | X% | X% |
  | JPM | X% | X% |
  | LLY | X% | X% |
- **Portfolio Metrics**: Expected return, volatility, Sharpe ratio
- **Methodology Note**: Mean-variance optimisation using scipy SLSQP

**Talking Points**:
- Agent writes and executes Python optimisation code in real-time
- Mathematical optimisation, not rule-based allocation
- Constraints enforced by the optimiser (max 30% per position, weights sum to 100%)

**Key Features Highlighted**: 
- `code_execution` tool runs numpy/scipy in a Python 3.12 sandbox
- `portfolio-optimizer` skill provides the algorithmic template
- Real-time computation within the conversation

##### Step 3: Compare Optimisation Objectives

**Presenter Transition**:
> "Minimum variance is one approach. Let me compare it with risk parity and maximum Sharpe to give my client options..."

**User Input**: 
```
Now compare three approaches: minimum variance, risk parity, and maximum Sharpe ratio. Show the weights and risk-return profile for each.
```

**Tools Used**:
- `code_execution` — Three optimisation runs (min variance, risk parity, max Sharpe)

**Expected Response**:
- **Comparison Table**:
  | Objective | AAPL | MSFT | NVDA | COST | JPM | LLY | Return | Vol | Sharpe |
  |-----------|------|------|------|------|-----|-----|--------|-----|--------|
  | Min Variance | X% | X% | X% | X% | X% | X% | X% | X% | X.XX |
  | Risk Parity | X% | X% | X% | X% | X% | X% | X% | X% | X.XX |
  | Max Sharpe | X% | X% | X% | X% | X% | X% | X% | X% | X.XX |
- **Trade-Off Analysis**: What the client gains/loses with each approach
- **Efficient Frontier Context**: Where each portfolio sits on the frontier

**Talking Points**:
- Three optimisation objectives compared side-by-side
- Each uses different algorithm (quadratic programming, risk contribution equalisation, Sharpe maximisation)
- Client can make an informed choice based on their risk preference

##### Step 4: Apply IPS Constraints and Finalise

**Presenter Transition**:
> "My client's IPS requires maximum 25% volatility and at least 10% return. Let me add those constraints to the optimisation..."

**User Input**: 
```
Apply my client's IPS constraints: maximum 25% portfolio volatility, minimum 10% expected return, and no single position above 25%. Which objective gives the best result under these constraints?
```

**Tools Used**:
- `code_execution` — Constrained optimisation with IPS limits
- `portfolio_modelling_analyzer` (Cortex Analyst) - Cross-reference with backtest data

**Expected Response**:
- **Constrained Results**: Updated weights and metrics under IPS limits
- **Feasibility Check**: Which objectives are feasible under the constraints
- **Recommendation**: Best allocation given the constraints with rationale
- **IPS Compliance Summary**: All constraints validated

**Talking Points**:
- IPS constraints translate directly into optimiser bounds
- Some objectives may become infeasible under tight constraints
- Data-driven recommendation with full constraint compliance

**Key Features Highlighted**: 
- Constraint handling through mathematical optimisation
- Policy-to-portfolio bridge with quantitative rigour
- Complete audit trail from data to optimised allocation

#### Scenario Wrap-up

**Business Impact Summary**:
- **Quantitative Rigour**: Mathematically optimal allocations replace rule-of-thumb weights
- **Speed**: Portfolio optimisation in minutes instead of requiring a quant team
- **Constraint Compliance**: IPS limits enforced by the optimiser, not manually checked
- **Client Confidence**: Institutional-grade methodology accessible through natural language

**Technical Differentiators**:
- **Code Execution**: Python scipy optimisation runs live within the agent conversation
- **Skill-Guided Optimisation**: `portfolio-optimizer` skill provides algorithmic templates
- **Multi-Objective Comparison**: Min variance, risk parity, max Sharpe side-by-side
- **IPS Integration**: Constraints from policy documents become optimiser bounds

---

## ML-Powered Market Regime Analysis

### Business Context Setup

**Persona**: Sarah Mitchell, Financial Advisor at Simulated Asset Management
**Business Challenge**: Market conditions shift between risk-on, transitional, and risk-off regimes, impacting optimal portfolio positioning. Sarah needs to understand the current market regime and how it affects her clients' portfolios — without interpreting raw VIX data or building her own models.
**Value Proposition**: AI-powered regime detection that automatically classifies market conditions using ML (replacing hardcoded VIX thresholds), enabling regime-aware portfolio decisions through natural language queries.

**Agent**: `portfolio_modelling_copilot`
**Data Available**: ML regime predictions (`FACT_REGIME_PREDICTIONS`), historical VIX, benchmark returns, sector returns

**Prerequisites**: Run `notebooks/market_regime_detection.ipynb` first to populate the prediction table.

### Demo Flow

#### Step 1: Check Current Market Regime

**User Input**:
```
What is the current market regime? Show me the regime classification for the last 30 days with confidence levels.
```

**Expected Response**:
- Current regime label (RISK_ON / TRANSITIONAL / RISK_OFF)
- Confidence (cluster probability)
- Recent regime history (any transitions in last 30 days)
- Key features driving the classification (VIX level, momentum, volatility)

**Talking Points**:
- ML model replaces the old rule-based VIX threshold approach
- Probabilistic output gives confidence — not just a binary label
- The agent accesses regime data directly via semantic view

#### Step 2: Regime Impact on Portfolio

**Presenter Transition**:
> "Now that we know the regime, let me ask how this affects portfolio positioning..."

**User Input**:
```
Given the current regime, how have my portfolios typically performed in similar regimes historically? Which sectors tend to outperform in this regime?
```

**Expected Response**:
- Historical portfolio performance during similar regime periods
- Sector return patterns by regime (risk-on sectors vs defensive sectors)
- Regime duration statistics (how long regimes typically last)

**Talking Points**:
- Regime context turns raw market data into actionable insight
- Historical patterns help set expectations for current positioning

#### Step 3: Regime Transition Awareness

**User Input**:
```
What is the probability of a regime transition in the near term? Are there any early warning signals?
```

**Expected Response**:
- Transition probabilities from current regime
- Recent trend in cluster probabilities (moving toward another regime?)
- Key features showing directional shifts (e.g., VIX trending up, momentum weakening)

**Talking Points**:
- Probabilistic regime model provides forward-looking signals
- Early warning allows proactive portfolio adjustment before regime shift
- This replaces reactive VIX-watching with systematic detection
