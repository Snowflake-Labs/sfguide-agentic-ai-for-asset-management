# SAM Demo - Private Equity Professional Scenarios

Complete demo scenarios for Private Equity Professional role with step-by-step conversations, expected responses, and data flows.

> **Scenario**: `pe_copilot`  
> **Agent**: `AM_pe_copilot`  
> **Demo Surfaces**: Snowflake Intelligence, PM Cockpit (SPCS)  
> **Skills**: `audience-adaptive-narrative`  
> **Common Tools**: `server_skill`, `code_execution`, `data_to_chart`

---

## PE Professional

### PE Deal Sourcing Copilot - Deal Pipeline Analysis & Screening

#### Business Context Setup

**Persona**: Marcus, Investment Director at APX Partners. He manages investments across 4 vintage funds: APX IX (Growth Equity), APX VIII (Buyout), APX Infrastructure V, and APX Infrastructure IV (Harvesting). The cockpit lets him switch between funds to see fund-specific portfolio companies and morning briefings.  
**Business Challenge**: PE deal teams need instant access to deal pipeline analytics, target company valuations, and supporting due diligence materials to make rapid investment decisions. Traditional systems require manual data gathering across multiple databases, spreadsheets, and document repositories—delaying critical deal decisions in competitive auction processes.  
**Value Proposition**: AI-powered deal intelligence that combines quantitative pipeline data with qualitative due diligence insights and expert network perspectives in seconds, enabling faster deal screening and better investment decisions.

**Agent**: `AM_pe_copilot`  
**Data Available**: 4 PE funds, 6 portfolio companies, 25 active deals in pipeline, due diligence reports, expert network transcripts

#### Demo Flow

**Scene Setting**: Marcus is preparing for the Monday morning deal review meeting and needs to quickly assess the current pipeline, identify high-priority opportunities in the Healthcare sector, and understand the competitive landscape for deals approaching final stages.

##### Step 1: Pipeline Overview

**User Input**: 
```
What deals do we have in the pipeline? Show me a summary by stage and sector.
```

**Tools Used**:
- `deal_pipeline_analyzer` (Cortex Analyst) - Query deal pipeline data from SAM_PE_DEAL_PIPELINE_VIEW

**Expected Response**:
- Table showing deal count by stage (Screening, Indicative Offer, Due Diligence, SPA, Signed)
- Breakdown by sector (Healthcare, Technology, Industrials, Consumer)
- Total pipeline value by stage
- Flag deals in advanced stages requiring immediate attention

**Talking Points**:
- Instant pipeline analytics without manual spreadsheet consolidation
- Automatic stage progression tracking
- Real-time deal data from centralized repository

**Key Features Highlighted**: 
- Cortex Analyst semantic understanding of PE deal data
- Multi-dimensional pipeline segmentation
- Natural language to SQL conversion

##### Step 2: Sector Deep-Dive

**Presenter Transition**:
> "We can see our pipeline at a glance. Now let's focus on Healthcare—our strategic priority sector this year. I want to understand our Healthcare opportunities in detail..."

*Reasoning: Pipeline overview sets context; sector focus demonstrates the ability to drill into strategic priorities with targeted analysis.*

**User Input**: 
```
Show me all Healthcare deals with their valuations, stages, and strategic rationale.
```

**Tools Used**:
- `deal_pipeline_analyzer` (Cortex Analyst) - Query Healthcare sector deals with valuation metrics

**Expected Response**:
- Table of Healthcare deals with:
  - Target company name
  - Deal stage
  - Enterprise value (EUR M)
  - EV/EBITDA multiple
  - Revenue growth %
  - Strategic rationale
  - Deal team lead
- Highlight deals with attractive valuations (<10x EBITDA)
- Flag deals with high growth (>15% revenue growth)

**Talking Points**:
- Sector-focused analysis for strategic planning
- Valuation comparisons across opportunities
- Growth metrics for quality assessment

**Key Features Highlighted**: 
- Sector filtering with multiple metrics
- Valuation multiple analysis
- Strategic rationale capture

##### Step 3: Due Diligence Insights

**Presenter Transition**:
> "HealthData Analytics looks interesting—35% growth and reasonable multiple for an AI-powered healthcare platform. Before I discuss with the IC, I need to understand the due diligence findings and any red flags..."

*Reasoning: Quantitative screening identifies candidates; due diligence review validates investment thesis and identifies risks.*

**User Input**: 
```
What does our due diligence say about HealthData Analytics? Any concerns or red flags?
```

**Tools Used**:
- `search_due_diligence` (Cortex Search) - Search due diligence reports for HealthData Analytics

**Expected Response**:
- Due diligence summary with:
  - Commercial DD findings (market position, customer concentration)
  - Financial DD highlights (revenue quality, EBITDA adjustments)
  - Operational DD observations (management team, scalability)
  - Legal/regulatory considerations
- Red flags identified and mitigation strategies
- Overall recommendation from DD workstream leads

**Talking Points**:
- AI automatically surfaces relevant DD findings
- Integrated view across DD workstreams
- Risk-focused analysis for IC preparation

**Key Features Highlighted**: 
- Document search across DD reports
- Automatic relevance ranking
- Risk identification and flagging

##### Step 4: Expert Network Perspectives

**Presenter Transition**:
> "The DD looks solid. But I want external validation—what are industry experts saying about this market and company? Let me check our expert network calls..."

*Reasoning: Internal DD provides company perspective; expert network adds external market validation and competitive intelligence.*

**User Input**: 
```
Do we have any expert network insights on HealthData Analytics or the healthcare analytics market?
```

**Tools Used**:
- `search_expert_network` (Cortex Search) - Search expert call transcripts for relevant insights

**Expected Response**:
- Expert perspectives on:
  - Market dynamics and competitive positioning
  - Customer feedback on HealthData Analytics products
  - Management reputation in the industry
  - Growth outlook and market trends
- Key quotes from expert calls with dates and expert profiles
- Consensus view across multiple expert perspectives

**Talking Points**:
- External validation beyond company-provided data
- Industry expert perspectives on competitive dynamics
- Management reputation assessment

**Key Features Highlighted**: 
- Expert network transcript search
- Multi-source perspective synthesis
- Citation with expert credentials

#### Scenario Wrap-up

**Business Impact Summary**:
- **Time Savings**: Deal screening reduced from hours to minutes
- **Decision Quality**: Integrated quantitative and qualitative insights
- **Competitive Advantage**: Faster response in competitive auctions
- **Risk Management**: Early identification of deal red flags

**Technical Differentiators**:
- **Semantic Understanding**: Natural language queries on PE deal data
- **Document Intelligence**: AI-powered search across DD reports and expert calls
- **Multi-Modal Analysis**: Structured deal data combined with unstructured documents
- **Real-Time Pipeline**: Live deal data with no batch processing delays

---

### PE Deal Sourcing Copilot - Carve-Out Analysis

#### Business Context Setup

**Persona**: Marcus, Investment Director at APX Partners  
**Business Challenge**: Carve-out transactions require detailed analysis of parent company financials from SEC filings, segment performance data, and understanding of separation complexities. Traditional analysis requires manual SEC filing review, segment data extraction, and cross-referencing with DD materials.  
**Value Proposition**: AI-powered carve-out analysis combining SEC filing intelligence, segment financial data, and expert perspectives on separation complexity.

**Agent**: `AM_pe_copilot`  
**Data Available**: SEC filings with segment data, due diligence reports, expert network transcripts

#### Demo Flow

**Scene Setting**: Marcus is evaluating Industrial Automation GmbH, a potential carve-out from a large industrial conglomerate. He needs to understand the parent's segment performance and separation considerations.

##### Step 1: Parent Company Analysis

**User Input**: 
```
We're looking at Industrial Automation GmbH, a carve-out from Siemens. What do SEC filings show about the parent's performance?
```

**Tools Used**:
- `sec_financials_analyzer` (Cortex Analyst) - Query SEC filings for Siemens segment data
- `search_sec_filings` (Cortex Search) - Search SEC filing text for relevant commentary

**Expected Response**:
- Segment revenue and profitability from SEC filings
- MD&A commentary on automation business unit
- Geographic revenue breakdown
- Growth trends and strategic commentary

**Talking Points**:
- Real SEC geographic segment data from regulatory filings
- No waiting for analyst research—direct data extraction
- Combines quantitative metrics with strategic context

**Key Features Highlighted**: 
- SEC filings semantic view with segment breakdowns
- FACT_SEC_SEGMENTS data for regional revenue analysis
- Competitor data extraction from regulatory filings

##### Step 2: Separation Complexity Assessment

**Presenter Transition**:
> "The segment performance looks strong. Now I need to understand the carve-out complexity—what are the key separation considerations..."

*Reasoning: Financial performance determines attractiveness; separation complexity determines execution risk and timeline.*

**User Input**: 
```
Search expert calls for views on carve-out complexity and typical separation costs for industrial carve-outs.
```

**Tools Used**:
- `search_expert_network` (Cortex Search) - Search expert transcripts for carve-out perspectives
- `search_due_diligence` (Cortex Search) - Search DD docs for TSA considerations

**Expected Response**:
- Expert perspectives on carve-out complexity factors
- Typical TSA duration and cost benchmarks
- Key separation workstreams (IT, HR, finance, supply chain)
- Risk factors specific to industrial carve-outs

**Talking Points**:
- Expert insights on practical execution challenges
- Benchmarking data for financial modeling
- Risk identification for investment thesis

**Key Features Highlighted**: 
- Cross-referencing SEC data with expert perspectives
- Carve-out complexity assessment
- TSA and separation considerations

#### Scenario Wrap-up

**Business Impact Summary**:
- **Analysis Speed**: Carve-out assessment reduced from days to hours
- **Data Quality**: Real SEC filing data vs. management presentations
- **Risk Awareness**: Early identification of separation complexities
- **Valuation Precision**: Better understanding of one-time costs

**Technical Differentiators**:
- **SEC Filings Integration**: Real-time segment data from regulatory filings
- **Expert Network Intelligence**: Industry perspectives on execution complexity
- **Multi-Source Synthesis**: Combines regulatory, DD, and expert sources

---

### PE Portfolio Monitor - Portfolio Company Performance & Value Creation

#### Business Context Setup

**Persona**: Sarah, Portfolio Director at APX Partners  
**Business Challenge**: PE portfolio teams need to monitor portfolio company performance, track value creation initiatives, and prepare for board meetings with comprehensive analysis. Traditional processes require consolidating data from multiple portfolio companies, manual board pack preparation, and time-consuming performance reviews.  
**Value Proposition**: AI-powered portfolio intelligence that combines financial KPIs, value creation plan tracking, and board pack analysis in a unified interface, enabling proactive portfolio management and better board engagement.

**Agent**: `AM_pe_copilot`  
**Data Available**: 8 portfolio companies, 24 value creation initiatives, monthly board pack metrics

#### Demo Flow

**Scene Setting**: Sarah is preparing for quarterly portfolio reviews and needs to understand which companies are on track, which value creation initiatives need attention, and what the key discussion points should be for upcoming board meetings.

##### Step 1: Portfolio Overview

**User Input**: 
```
Give me an overview of our portfolio company performance. Which companies are on track and which need attention?
```

**Tools Used**:
- `value_creation_analyzer` (Cortex Analyst) - Query portfolio metrics from SAM_PE_VALUE_CREATION_VIEW

**Expected Response**:
- Portfolio summary showing:
  - Company name, fund, sector
  - Current EBITDA vs budget variance
  - Revenue growth YoY
  - Leverage ratio (Net Debt/EBITDA)
  - Overall status (On Track, Attention Needed, Outperforming)
- Flag companies with negative budget variance (>5%)
- Highlight outperformers exceeding targets

**Talking Points**:
- Single view across entire portfolio
- Automatic performance flagging
- Budget variance tracking

**Key Features Highlighted**: 
- Multi-company portfolio analytics
- KPI threshold monitoring
- Status categorization

##### Step 2: Value Creation Tracking

**Presenter Transition**:
> "I see TechCorp Europe is flagged as needing attention. Let me understand what's happening with their value creation plan..."

*Reasoning: Portfolio overview identifies issues; value creation tracking diagnoses root causes and initiative status.*

**User Input**: 
```
What's the status of TechCorp Europe's value creation initiatives? Are there any at-risk workstreams?
```

**Tools Used**:
- `value_creation_analyzer` (Cortex Analyst) - Query value creation plan status for TechCorp Europe

**Expected Response**:
- Value creation initiative summary:
  - Initiative name and category (Revenue, Cost, Digital, ESG)
  - Status (On Track, At Risk, Behind, Completed)
  - Baseline → Target → Current values
  - Expected EBITDA impact (EUR M)
  - Owner and timeline
- At-risk initiatives highlighted with specific concerns
- Overall value creation progress vs plan

**Talking Points**:
- Granular initiative tracking
- Early warning on at-risk workstreams
- EBITDA impact quantification

**Key Features Highlighted**: 
- Value creation plan analytics
- RAG status tracking
- Impact measurement

##### Step 3: Board Pack Analysis

**Presenter Transition**:
> "The cost optimization initiative is behind schedule. Before the board meeting, I need to understand the full financial picture from their latest board pack..."

*Reasoning: Value creation tracking shows initiative status; board pack analysis provides complete financial context for board discussion.*

**User Input**: 
```
What are the key metrics from TechCorp Europe's latest board pack? How are they trending vs budget and prior year?
```

**Tools Used**:
- `value_creation_analyzer` (Cortex Analyst) - Query board pack metrics
- `search_board_packs` (Cortex Search) - Search board pack documents for context

**Expected Response**:
- Board pack metrics summary:
  - Revenue: Actual vs Budget vs Prior Year
  - EBITDA and EBITDA margin trends
  - Net debt and leverage ratio
  - Key operational KPIs (NRR, headcount, customer count)
  - Cash position and runway
- Variance analysis with explanations
- Management commentary on key variances

**Talking Points**:
- Comprehensive board pack synthesis
- Budget and YoY comparisons
- Management narrative integration

**Key Features Highlighted**: 
- Board pack data aggregation
- Multi-period comparison
- Document search for context

##### Step 4: Investment Thesis Validation

**Presenter Transition**:
> "Revenue is tracking but costs are the issue. Let me step back and assess whether the original investment thesis is still intact..."

*Reasoning: Current performance analysis must be viewed against original investment thesis to assess whether the deal is on track for planned returns.*

**User Input**: 
```
Is TechCorp Europe's investment thesis still valid? How does current performance compare to our entry assumptions?
```

**Tools Used**:
- `value_creation_analyzer` (Cortex Analyst) - Compare current metrics to entry assumptions
- `search_board_packs` (Cortex Search) - Search for strategic updates and thesis validation

**Expected Response**:
- Investment thesis assessment:
  - Entry thesis summary and key assumptions
  - Current performance vs entry model
  - EBITDA bridge: Entry → Current (organic growth, initiatives, headwinds)
  - Multiple progression: Entry EV/EBITDA vs implied current multiple
  - Exit readiness assessment
- Strategic developments supporting/challenging thesis
- Recommended discussion points for board

**Talking Points**:
- Investment thesis validation framework
- Value creation attribution
- Exit planning perspective

**Key Features Highlighted**: 
- Entry vs current comparison
- Value bridge analysis
- Strategic assessment

#### Scenario Wrap-up

**Business Impact Summary**:
- **Portfolio Visibility**: Real-time performance across all portfolio companies
- **Proactive Management**: Early warning on at-risk initiatives
- **Board Effectiveness**: Comprehensive preparation in minutes
- **Value Creation Focus**: Clear tracking of EBITDA impact

**Technical Differentiators**:
- **Multi-Company Analytics**: Unified view across diverse portfolio
- **Value Creation Framework**: Structured initiative tracking with impact measurement
- **Board Pack Intelligence**: AI-powered synthesis of financial and operational data
- **Investment Thesis Tracking**: Automated comparison to entry assumptions

---

### PE Portfolio Monitor - 100-Day Plan Review

#### Business Context Setup

**Persona**: Sarah, Portfolio Director at APX Partners  
**Business Challenge**: Deal team leads need to monitor value creation initiatives during the critical first 100 days post-close, identifying at-risk workstreams before they impact EBITDA targets.  
**Value Proposition**: AI-powered 100-day plan tracking that surfaces at-risk initiatives, calculates total EBITDA impact at risk, and recommends management interventions.

**Agent**: `AM_pe_copilot`  
**Data Available**: Value creation initiatives with status tracking, EBITDA impact projections

#### Demo Flow

**Scene Setting**: Sarah is reviewing the 100-day plans across recent acquisitions to ensure value creation is on track and identify any initiatives requiring intervention.

##### Step 1: At-Risk Initiative Scan

**User Input**: 
```
Which value creation initiatives are at risk or behind schedule?
```

**Tools Used**:
- `value_creation_analyzer` (Cortex Analyst) - Query initiatives with Status = 'At Risk' or 'Behind'

**Expected Response**:
- Structured list with Company, Initiative, Status, Target vs Current
- Calculation of total EBITDA impact at risk
- Recommendation for management discussion
- Number of initiatives at risk by company
- Initiative categories most affected

**Talking Points**:
- Proactive identification of at-risk initiatives
- Quantified EBITDA impact at risk
- Early warning for management intervention

**Key Features Highlighted**: 
- Status-based filtering
- EBITDA impact calculation
- Priority recommendations

##### Step 2: Initiative Deep-Dive

**Presenter Transition**:
> "Several initiatives are flagged. Let me understand the specific issues with the NordicTech Cloud Infrastructure Optimization..."

*Reasoning: Overview identifies at-risk items; deep-dive provides context for management intervention.*

**User Input**: 
```
What is NordicTech's Cloud Infrastructure Optimization issue? Search board packs for management update on at-risk initiatives.
```

**Tools Used**:
- `value_creation_analyzer` (Cortex Analyst) - Get initiative details
- `search_board_packs` (Cortex Search) - Search for management commentary

**Expected Response**:
- Initiative details: baseline, target, current, timeline
- Management explanation from board pack
- Root cause analysis
- Recommended corrective actions
- Impact if initiative fails

**Talking Points**:
- Combines quantitative status with management narrative
- Root cause identification
- Actionable recommendations

**Key Features Highlighted**: 
- Cross-referencing structured and unstructured data
- Management commentary integration
- Action planning support

#### Scenario Wrap-up

**Business Impact Summary**:
- **Risk Visibility**: Early warning on value creation risks
- **EBITDA Protection**: Quantified impact enables prioritization
- **Management Focus**: Clear guidance on where to intervene

**Technical Differentiators**:
- **Initiative Tracking**: Structured value creation monitoring
- **Impact Quantification**: EBITDA at risk calculation
- **Document Integration**: Board pack context for analysis

---

### PE Portfolio Monitor - KPI Health Check

#### Business Context Setup

**Persona**: Sarah, Portfolio Director at APX Partners  
**Business Challenge**: ESG leads and operating partners need to monitor operational KPIs across the portfolio, identifying Red status items requiring intervention.  
**Value Proposition**: AI-powered KPI monitoring with automatic flagging of Red status items, trend analysis, and prioritization recommendations.

**Agent**: `AM_pe_copilot`  
**Data Available**: Portfolio company KPIs with RAG status, historical trends

#### Demo Flow

**Scene Setting**: Sarah is conducting a portfolio health check to identify operational issues before they escalate.

##### Step 1: Red KPI Scan

**User Input**: 
```
Show me all Red status KPIs across the portfolio.
```

**Tools Used**:
- `value_creation_analyzer` (Cortex Analyst) - Query KPI data filtered by Status = 'Red'

**Expected Response**:
- KPI heatmap by company/category
- Context (actual vs budget vs prior year)
- Trends (improving/declining)
- Action priority recommendations
- Which companies have the most Red KPIs

**Talking Points**:
- Portfolio-wide KPI visibility
- Automatic severity flagging
- Trend context for prioritization

**Key Features Highlighted**: 
- RAG status monitoring
- Multi-company aggregation
- Priority recommendations

##### Step 2: Trend Analysis

**Presenter Transition**:
> "Several HR-related KPIs are flagged. Let me check the trend for Employee NPS across the portfolio..."

*Reasoning: Point-in-time Red flags need trend context to understand if situation is improving or deteriorating.*

**User Input**: 
```
What is the trend for Employee NPS across portfolio? Search board packs for HR initiatives addressing turnover.
```

**Tools Used**:
- `value_creation_analyzer` (Cortex Analyst) - Query NPS trends
- `search_board_packs` (Cortex Search) - Search for HR initiatives

**Expected Response**:
- NPS trend by company (6-month view)
- Companies with improving vs declining trends
- HR initiatives from board packs
- Correlation between initiatives and NPS improvement

**Talking Points**:
- Trend analysis reveals trajectory
- Initiative correlation shows what's working
- Portfolio-wide benchmarking

**Key Features Highlighted**: 
- Time-series analysis
- Cross-company benchmarking
- Initiative effectiveness tracking

#### Scenario Wrap-up

**Business Impact Summary**:
- **Operational Visibility**: Real-time KPI monitoring across portfolio
- **Early Intervention**: Red flags identified before escalation
- **Trend Intelligence**: Understanding of improving vs deteriorating situations

**Technical Differentiators**:
- **RAG Status Framework**: Automatic severity classification
- **Trend Analysis**: Historical context for point-in-time flags
- **Initiative Correlation**: Linking actions to outcomes

---

### PE Portfolio Monitor - Fund-Level Summary

#### Business Context Setup

**Persona**: Sarah, Portfolio Director at APX Partners  
**Business Challenge**: Fund CFOs preparing LP updates need consolidated fund-level performance including portfolio metrics and exit performance.  
**Value Proposition**: AI-powered fund summary combining active portfolio performance, value creation progress, and exit metrics.

**Agent**: `AM_pe_copilot`  
**Data Available**: Fund-level aggregations, exit performance metrics (MOIC, IRR)

#### Demo Flow

**Scene Setting**: Sarah is preparing materials for the quarterly LP update and needs a consolidated fund summary.

##### Step 1: Fund Performance Summary

**User Input**: 
```
Give me a summary of APX IX portfolio performance including any recent exits.
```

**Tools Used**:
- `value_creation_analyzer` (Cortex Analyst) - Query portfolio by Fund = 'APX IX'

**Expected Response**:
- Active portfolio overview with aggregate metrics
- Total value and EBITDA across fund
- Exit performance (MOIC, IRR for completed exits)
- Aggregate value creation progress
- Fund-level highlights and concerns

**Talking Points**:
- Consolidated fund view for LP communication
- Exit performance tracking
- Value creation attribution at fund level

**Key Features Highlighted**: 
- Fund-level aggregation
- Exit metrics (MOIC, IRR)
- LP-ready summary format

#### Scenario Wrap-up

**Business Impact Summary**:
- **LP Communication**: Fund-level summary ready for investor updates
- **Exit Tracking**: Clear visibility on realized returns
- **Portfolio Context**: Active investments alongside exits

**Technical Differentiators**:
- **Fund Segmentation**: Portfolio filtering by fund
- **Exit Metrics**: MOIC and IRR calculation
- **Aggregation Intelligence**: Roll-up across portfolio companies

---

> **Note**: Both PE scenarios use specialized semantic views (SAM_PE_DEAL_PIPELINE_VIEW, SAM_PE_VALUE_CREATION_VIEW) and Cortex Search services (SAM_PE_DUE_DILIGENCE, SAM_PE_EXPERT_NETWORK, SAM_PE_BOARD_PACKS) tailored for private equity workflows.
