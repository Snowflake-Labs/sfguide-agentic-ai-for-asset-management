# SAM Demo - Portfolio Manager Scenarios

Complete demo scenarios for Portfolio Manager role with step-by-step conversations, expected responses, and data flows.

---

## Portfolio Manager

### Portfolio Copilot - Portfolio Insights & Benchmarking

#### Business Context Setup

**Persona**: Anna, Senior Portfolio Manager at Snowcrest Asset Management  
**Business Challenge**: Portfolio managers need instant access to portfolio analytics, holdings information, and supporting research to make informed investment decisions. Traditional systems require multiple tools, manual data gathering, and time-consuming analysis that delays critical investment decisions.  
**Value Proposition**: AI-powered portfolio analytics that combines quantitative holdings data with qualitative research insights in seconds, enabling faster decision-making and better risk management.

**Agent**: `portfolio_copilot`  
**Data Available**: 10 portfolios, 5,000 securities, 2,800 research documents

#### Demo Flow

**Scene Setting**: Anna is preparing for her weekly portfolio review meeting and needs to quickly assess her Technology & Infrastructure portfolio performance, understand current holdings, and identify any emerging risks that require attention.

##### Step 1: Top Holdings Overview
**User Input**: 
```
What are my top 10 holdings by market value in the SAM Technology & Infrastructure portfolio?
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Query portfolio holdings data from SAM_ANALYST_VIEW

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
- `search_broker_research` (Cortex Search) - Search for analyst research on the top 3 companies identified in Step 1

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
- `quantitative_analyzer` (Cortex Analyst) - Analyze sector allocation and concentration risk from SAM_ANALYST_VIEW

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
- `search_policies` (Cortex Search) - Get concentration thresholds from firm policies
- `search_broker_research` (Cortex Search) - Reference research sentiment from Step 2

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
- `search_policies` (Cortex Search) - Reference mandate requirements and approval processes

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

### Portfolio Copilot - Comprehensive Company Analysis

#### Business Context Setup

**Persona**: Anna, Senior Portfolio Manager at Snowcrest Asset Management  
**Business Challenge**: Portfolio managers need to rapidly conduct comprehensive company analysis that integrates quantitative financial performance from SEC filings, qualitative management commentary from earnings calls, external analyst perspectives from broker research, corporate developments from press releases, and portfolio positioning context—all while market-moving events demand immediate assessment. Traditional research workflows require hours of manual data gathering across multiple systems, spreadsheet modeling, document review, and synthesis, often missing critical connections between financial performance, strategic narratives, and investment implications.  
**Value Proposition**: AI-powered comprehensive company intelligence that seamlessly integrates authentic SEC financial data, management commentary, analyst research, corporate announcements, and portfolio exposure in a single query—delivering complete, investment-ready analysis within minutes instead of hours, enabling faster response to market events and higher-quality investment decisions.

**Agent**: `portfolio_copilot`  
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
- `search_earnings_transcripts` (Cortex Search) - Retrieve management commentary from earnings call
- `search_broker_research` (Cortex Search) - Find analyst research and reactions
- `search_press_releases` (Cortex Search) - Check for related corporate announcements
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

**Persona**: Anna, Senior Portfolio Manager at Snowcrest Asset Management  
**Business Challenge**: Portfolio managers need to rapidly assess portfolio exposure when external events occur, including both direct regional/sector exposure and indirect supply chain dependencies. Traditional risk systems can't model multi-hop supply chain relationships or quantify second-order impacts, leaving managers blind to cascading risks.  
**Value Proposition**: AI-powered event risk verification that combines macro event intelligence, direct portfolio exposure analysis, and sophisticated supply chain dependency mapping to quantify both immediate and indirect portfolio impacts in real-time.

**Agent**: `portfolio_copilot`  
**Data Available**: 10 portfolios, supply chain relationships (150+ dependencies), macro events corpus, press releases

#### Demo Flow

**Scene Setting**: Anna receives an external market alert about a recent earthquake in Taiwan affecting semiconductor production. She needs to immediately understand her portfolio's exposure - both direct holdings in affected companies and indirect exposure through supply chain dependencies.

##### Step 1: Event Verification
**User Input**: 
```
I just received an alert about a recent earthquake in Taiwan affecting semiconductor production. Can you verify this event and tell me what sectors are affected?
```

**Tools Used**:
- `search_macro_events` (Cortex Search) - Search for Taiwan earthquake event details and sector impacts

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
- `quantitative_analyzer` (Cortex Analyst) - Query holdings by CountryOfIncorporation='TW' and sector from SAM_ANALYST_VIEW

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
- `supply_chain_analyzer` (Cortex Analyst) - Analyze multi-hop supply chain dependencies from SAM_SUPPLY_CHAIN_VIEW
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
- `search_press_releases` (Cortex Search) - Search for NVIDIA, AMD, Apple Taiwan supply chain statements
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

**Persona**: David Chen, Senior Portfolio Manager at Snowcrest Asset Management  
**Business Challenge**: Portfolio managers must respond quickly to mandate compliance breaches (e.g., ESG downgrades) by identifying suitable replacement securities that maintain portfolio strategy while meeting compliance requirements. Traditional processes involve manual screening, multiple system lookups, and time-consuming committee documentation.  
**Value Proposition**: AI-powered compliance workflow that automatically identifies pre-screened replacement candidates, analyzes their strategic fit, and generates investment committee documentation—reducing breach response time from days to minutes.

**Agent**: `portfolio_copilot`  
**Data Available**: SAM ESG Leaders Global Equity portfolio, compliance alerts, pre-screened replacements, ESG data, financial filings, broker research

#### Demo Flow

**Scene Setting**: David receives a compliance alert that META has been downgraded to ESG grade CCC due to governance concerns, violating the SAM ESG Leaders Global Equity fund's minimum BBB ESG requirement. He needs to identify a suitable replacement that maintains the portfolio's technology/growth focus while meeting all mandate requirements, then document his recommendation for the investment committee.

##### Step 1: Verify Compliance Breach
**User Input**: 
```
I've received an alert that META has been downgraded to ESG grade CCC. Can you verify this breach for the SAM ESG Leaders Global Equity portfolio and show me our current exposure?
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Check META's AI Growth Score and portfolio weight from SAM_ANALYST_VIEW
- `search_policies` (Cortex Search) - Get AI Growth mandate requirements (minimum score 80)

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
Based on that breach, what are our pre-screened replacement candidates that meet the mandate requirements and maintain our technology/growth focus?
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Query pre-screened replacement securities with AI Growth Score >80 from SAM_ANALYST_VIEW

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
- `search_broker_research` (Cortex Search) - Get analyst research on NVDA
- `search_earnings_transcripts` (Cortex Search) - Get management AI strategy commentary

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
- `search_report_templates` (Cortex Search) - Get Investment Committee Memo template
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
- **Multi-View Analytics**: Combines SAM_ANALYST_VIEW, SAM_SEC_FILINGS_VIEW, and Cortex Search
- **Custom Tool Integration**: Python stored procedures for PDF generation
- **Secure Report Storage**: Snowflake stage for governed document management

---

### Portfolio Copilot - Event-Driven Risk Assessment & Response

#### Business Context Setup

**Persona**: Anna, Senior Portfolio Manager at Snowcrest Asset Management  
**Business Challenge**: Portfolio managers need to rapidly assess portfolio exposure when external events occur, including both direct regional/sector exposure and indirect supply chain dependencies, then validate findings with financial analysis and research, retrieve policy guidance, and document formal recommendations. Traditional risk systems can't model multi-hop supply chain relationships, integrate qualitative research with quantitative risk metrics, or generate audit-ready documentation—leaving managers blind to cascading risks and unable to respond with comprehensive, documented action plans within required timeframes.  
**Value Proposition**: AI-powered comprehensive event risk assessment that seamlessly integrates macro event verification, direct portfolio exposure, supply chain dependency mapping, financial health analysis, management commentary, analyst research, policy compliance, and formal documentation generation—delivering complete, actionable, audit-ready risk assessment within minutes instead of days.

**Agent**: `portfolio_copilot`  
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
- `search_macro_events` (Cortex Search) - Verify Taiwan earthquake and identify affected sectors
- `quantitative_analyzer` (Cortex Analyst) - Calculate direct Taiwan technology exposure by portfolio
- `supply_chain_analyzer` (Cortex Analyst) - Map indirect exposures through multi-hop supply chain dependencies
- `search_policies` (Cortex Search) - Retrieve concentration limits and event response procedures
- `financial_analyzer` (Cortex Analyst) - Analyze financial health of exposed companies using SEC filings
- `search_earnings_transcripts` (Cortex Search) - Find management commentary on supply chain resilience
- `search_broker_research` (Cortex Search) - Get analyst recommendations on semiconductor exposure
- `search_report_templates` (Cortex Search) - Retrieve Investment Committee memo template
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

> **Note**: For comprehensive thematic investment strategy scenarios using the `thematic_macro_advisor` agent, see [demo_scenarios_thematic_advisor.md](demo_scenarios_thematic_advisor.md).

---

### Portfolio Copilot - Complete Investment Analysis (Catch-All)

#### Business Context Setup

**Persona**: Anna, Senior Portfolio Manager at Snowcrest Asset Management  
**Business Challenge**: Portfolio managers sometimes need a complete investment analysis with a single request when preparing for urgent meetings or responding to time-sensitive situations—requiring the AI to autonomously orchestrate all available tools.  
**Value Proposition**: The Portfolio Copilot demonstrates complete autonomous orchestration by selecting and sequencing all tools from a single comprehensive question, delivering a full investment picture without step-by-step guidance.

**Agent**: `portfolio_copilot`  
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
- `search_broker_research` (Cortex Search) - Latest analyst research on major holdings
- `search_earnings_transcripts` (Cortex Search) - Management commentary and guidance
- `search_press_releases` (Cortex Search) - Recent corporate developments
- `search_policies` (Cortex Search) - Concentration and mandate policy thresholds

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

