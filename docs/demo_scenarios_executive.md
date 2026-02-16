# SAM Demo - Executive Leadership Scenarios

Complete demo scenarios for Executive Leadership using the Executive Copilot agent.

---

## Executive Copilot - Holistic Business Performance Review

### Business Context Setup

**Persona**: Sarah Chen, Head of Asset Management at Simulated Asset Management  
**Business Challenge**: Achieving a timely, accurate, and comprehensive "single pane of glass" view across a complex organization often hampered by data silos. Traditional reporting is static, month-old, and requires manual consolidation from multiple systems. Leadership needs to move from "what happened?" to "what's next?" and "what if?" in real-time.  
**Value Proposition**: AI-powered strategic command center providing real-time firm-wide KPIs, dynamic drill-down capabilities into performance drivers, and instant access to client analytics—all through natural conversation without waiting for analyst reports.

**Agent**: `executive_copilot`  
**Data Available**: 
- Firm-wide KPIs (AUM, net flows, performance by strategy)
- Client flow data with 35+ institutional clients
- Strategy performance across 10 portfolios
- Strategic documents (investment philosophy, strategy materials)

### Demo Flow

**Scene Setting**: Sarah is preparing for the monthly management committee meeting. She needs a real-time briefing on firm performance, understanding of key drivers, and context from strategic documents—all in the next 10 minutes before the meeting starts.

##### Step 1: Firm-Wide Performance Overview
**User Input**: 
```
Give me the key performance highlights for the firm as of the latest available data. I want to see overall AUM, net flows, and our top and bottom 5 performing strategies.
```

**Expected Response**:
- Total AUM with month-to-date change percentage
- Net flow summary (inflows vs outflows)
- Table of top 5 performing strategies with returns
- Table of bottom 5 performing strategies with returns
- Key highlights (e.g., strongest franchise, areas of concern)
- Data freshness indicator

**Talking Points**:
- Real-time data aggregation across all portfolios and strategies
- No waiting for monthly reports—instant executive summary
- Combines quantitative performance with strategic context

**Key Features Highlighted**: 
- Cortex Analyst for KPI aggregation
- Multi-source data synthesis
- Executive-level formatting

##### Step 2: Client Flow Drill-Down

**Presenter Transition**:
> "The firm-wide overview shows strong performance in ESG strategies. But as executives, we need to understand whether this success is sustainable or dependent on a single large client. Let me drill down into the client composition driving these flows..."

*Reasoning: Top-level metrics identify areas of interest; client-level analysis reveals concentration risk and validates whether success is broad-based and sustainable.*

**User Input**: 
```
The inflows for ESG look strong. What is driving this? Is it one large client or broad-based demand?
```

**Expected Response**:
- Breakdown of inflows by client count
- Concentration analysis (no single client >10%)
- Client type distribution (institutional, pension, etc.)
- Alignment with sales team strategic focus
- Trend context (quarter-over-quarter comparison)

**Talking Points**:
- Instant drill-down from summary to detail
- Client analytics integrated with fund flows
- Strategic alignment verification in real-time

**Key Features Highlighted**: 
- CRM data integration
- Concentration analysis
- Strategic context synthesis

##### Step 3: Strategic Document Context

**Presenter Transition**:
> "The client demand is broad-based and aligns with our strategic focus—excellent news. But for the management committee, I need to connect this operational success to our stated investment philosophy. Let me retrieve our positioning on sustainable investing..."

*Reasoning: Operational data gains strategic significance when connected to firm philosophy. This demonstrates alignment between execution and stated investment beliefs.*

**User Input**: 
```
What does our investment philosophy say about sustainable investing? How are we positioning this to clients?
```

**Expected Response**:
- Key excerpts from investment philosophy documents
- Sustainable investing positioning statement
- Client communication themes
- Alignment with firm values and ESG commitments
- Source citations with document names and dates

**Talking Points**:
- Unstructured document search for strategic context
- Connecting operational data to firm philosophy
- Instant access to approved messaging

**Key Features Highlighted**: 
- Cortex Search for philosophy documents
- Strategic document synthesis
- Brand consistency verification

##### Step 4: Executive Summary Synthesis

**Presenter Transition**:
> "We now have the complete picture: strong performance, diversified client demand, and alignment with our investment philosophy. With three minutes before the meeting, let me synthesise this into the key talking points for the committee..."

*Reasoning: Multi-dimensional analysis must be distilled into executive-ready talking points. This final synthesis transforms raw analysis into meeting-ready communication.*

**User Input**: 
```
Summarize the key points I should highlight in the management committee meeting about our sustainable investing success.
```

**Expected Response**:
- 3-5 bullet executive summary
- Key metrics to cite (AUM, flows, client count)
- Strategic narrative connecting performance to philosophy
- Suggested talking points for committee discussion
- Areas requiring committee attention

**Talking Points**:
- AI-generated executive briefing
- Connects quantitative performance to qualitative strategy
- Meeting-ready format in seconds

**Key Features Highlighted**: 
- Multi-source synthesis
- Executive communication formatting
- Strategic narrative generation

### Scenario Wrap-up

**Business Impact Summary**:
- **Time Savings**: From hours of report consolidation to minutes of conversation
- **Data Currency**: Real-time insights vs month-old static reports
- **Strategic Alignment**: Instant connection between operations and philosophy
- **Decision Quality**: Comprehensive view enabling informed committee discussions

**Technical Differentiators**:
- **Cortex Analyst**: Real-time KPI aggregation across firm-wide data
- **Cortex Search**: Strategic document retrieval and synthesis
- **Multi-Tool Orchestration**: Seamless combination of quantitative and qualitative analysis
- **Executive Formatting**: Professional output ready for C-suite consumption

---

## Executive Copilot - Strategic Competitor Analysis & M&A Simulation

### Business Context Setup

**Persona**: Sarah Chen, Head of Asset Management at Simulated Asset Management  
**Business Challenge**: A news headline about a competitor potentially selling their European division has just broken. Leadership needs immediate assessment of the opportunity—size, performance, strategic fit—without waiting days for corporate strategy team analysis. If promising, a preliminary financial model is needed to determine if it meets acquisition criteria.  
**Value Proposition**: AI-powered competitive intelligence and M&A simulation enabling real-time strategic opportunity assessment. Transform breaking news into actionable analysis within minutes, equipping leadership with data-driven insights for rapid strategic decision-making.

**Agent**: `executive_copilot`  
**Data Available**: 
- SEC filings for competitor analysis
- Industry benchmarks and market data
- Firm-specific M&A assumptions (cost synergies, integration costs)
- Strategic document templates for executive memos

### Demo Flow

**Scene Setting**: During the management committee meeting, Sarah receives a news alert: "[Competitor X] potentially selling their European division." She needs to quickly assess whether this represents a strategic opportunity worth pursuing.

##### Step 1: Competitor Intelligence Gathering
**User Input**: 
```
I saw a headline about BlackRock potentially selling their European division. What do we know about the size and performance of that business from their SEC filings?
```

**Expected Response**:
- European revenue from SEC filings (~$6 billion annually based on geographic segment data)
- Quarterly European revenue trends ($1.4B - $1.8B per quarter)
- Comparison to Americas and Asia Pacific segments
- Year-over-year growth in European business
- Recent strategic commentary from filings
- Source citations with filing dates

**Talking Points**:
- Real SEC geographic segment data from 10-K/10-Q filings
- No waiting for analyst research—real-time data extraction from regulatory filings
- Combines quantitative metrics with strategic context

**Key Features Highlighted**: 
- SEC filings semantic view with geographic segment breakdowns
- FACT_SEC_SEGMENTS data for regional revenue analysis
- Competitor data extraction from regulatory filings

##### Step 2: Strategic Fit Assessment

**Presenter Transition**:
> "We now have a clear picture of the target's size and performance. But size alone doesn't make a good acquisition—we need to understand strategic fit. Let me analyse how their European footprint would complement or overlap with our current geographic presence..."

*Reasoning: Financial metrics determine if a target is interesting; strategic fit analysis determines if it's the right opportunity for SAM specifically.*

**User Input**: 
```
How would their European business complement our current geographic presence? What overlaps or gaps would this address?
```

**Expected Response**:
- Current SAM geographic exposure analysis
- Overlap assessment with competitor's European presence
- Gap analysis (markets/products we don't currently cover)
- Strategic fit summary
- Potential synergy areas

**Talking Points**:
- Strategic fit analysis combining internal and external data
- Geographic and product line complementarity assessment
- Instant strategic context for M&A evaluation

**Key Features Highlighted**: 
- Multi-source strategic analysis
- Portfolio geographic analytics
- Competitive positioning synthesis

##### Step 3: M&A Financial Simulation

**Presenter Transition**:
> "The strategic fit looks compelling—they fill gaps we've been wanting to address. But before taking this to the board, we need to understand the financial impact. Let me run a preliminary M&A simulation using our firm's standard assumptions..."

*Reasoning: Strategic rationale must be backed by financial analysis. The EPS accretion model provides the quantitative case for advancing the opportunity.*

**User Input**: 
```
Let's model this. Run a high-level simulation of us acquiring that $50 billion AUM business. Use the revenue figures you found and apply our firm's standard assumptions for cost synergies. What is the projected impact on our earnings per share in the first year?
```

**Expected Response**:
- Input assumptions clearly stated:
  - Acquired AUM: $50B
  - Revenue: $200M (from SEC filings)
  - Cost synergy rate: 20% (firm standard)
  - Integration costs: $30M (firm standard)
- EPS accretion calculation
- First-year projected impact (e.g., ~5% accretive)
- Key sensitivities and assumptions
- Caveats and limitations

**Talking Points**:
- Custom M&A simulation tool with firm-specific assumptions
- Instant financial modeling without spreadsheet work
- Professional output suitable for strategic discussions

**Key Features Highlighted**: 
- Custom M&A simulation tool
- Firm-specific assumption library
- Financial modeling automation

##### Step 4: Executive Memo Generation with PDF

**Presenter Transition**:
> "The numbers are compelling—5% EPS accretion in year one. This opportunity warrants further investigation. Let me draft a confidential memo to the Chief Strategy Officer and generate a formal PDF document..."

*Reasoning: Analysis without action is incomplete. The executive memo transforms a real-time opportunity assessment into a formal request for deeper investigation, with a professional PDF for distribution.*

**User Input**: 
```
That's a compelling number. Draft a confidential memo to the Chief Strategy Officer. Title it 'Project Europa: Preliminary Analysis.' Summarize the opportunity, our key findings, the potential EPS accretion, and ask them to prepare a more detailed analysis for us to review next week. Generate a professional PDF for my signature.
```

**Tools Used**:
- Synthesis of previous queries
- `pdf_generator` (Generic) - Generate branded PDF with `internal` audience

**Expected Response**:
- Professionally formatted confidential memo
- Clear title and classification
- Executive summary of opportunity
- Key findings with supporting data
- Financial highlights (EPS accretion)
- Recommended next steps
- Request for detailed analysis with timeline
- **PDF Generation**: Branded internal document with Simulated logo
- **Download Link**: Presigned URL for immediate access

**Talking Points**:
- AI-generated executive communication with formal PDF output
- Professional memo formatting with all key elements
- Seamless transition from analysis to action with deliverable document
- Internal document styling appropriate for confidential memo

**Key Features Highlighted**: 
- Executive memo generation with PDF output
- Professional document formatting
- Strategic communication synthesis
- GENERATE_PDF_REPORT with internal audience styling

### Scenario Wrap-up

**Business Impact Summary**:
- **Speed to Insight**: From news headline to actionable analysis in minutes
- **Strategic Agility**: Rapid assessment of M&A opportunities
- **Decision Quality**: Data-driven preliminary analysis for informed decisions
- **Resource Efficiency**: Executive-level analysis without analyst bottleneck
- **Professional Deliverables**: Formal PDF memos ready for executive signature

**Technical Differentiators**:
- **SEC Filings Integration**: Real-time competitor intelligence from regulatory filings
- **Custom M&A Tool**: Firm-specific financial modeling with standard assumptions
- **Multi-Source Synthesis**: Combining external data with internal strategic context
- **Executive Communication**: Professional memo generation with PDF output for C-suite workflow

---

### Executive Copilot - Complete Executive Briefing (Catch-All)

#### Business Context Setup

**Persona**: Sarah Chen, Head of Asset Management at Simulated Asset Management  
**Business Challenge**: Executives sometimes need a complete firm briefing with a single request when preparing for board meetings or urgent stakeholder calls—requiring the AI to autonomously orchestrate all available executive tools.  
**Value Proposition**: The Executive Copilot demonstrates complete autonomous orchestration by selecting and sequencing all tools from a single comprehensive question, delivering a board-ready briefing without step-by-step guidance.

**Agent**: `executive_copilot`  
**Data Available**: 
- Firm-wide KPIs including FIRM_AUM (authoritative from holdings) and TOTAL_CLIENT_AUM (client-reported)
- Strategy performance metrics (QTD/YTD returns by strategy)
- Client flow data with 75+ institutional clients
- Investment philosophy documents

**Important AUM Distinction**:
- **FIRM_AUM**: Authoritative figure calculated from actual portfolio holdings (~£12.5B). Use this for board and executive reporting.
- **TOTAL_CLIENT_AUM**: Sum of client-reported AUM with SAM. May differ from FIRM_AUM due to reporting timing.

#### Demo Flow

**Scene Setting**: Sarah has 5 minutes before a surprise call from the board chairman requesting an update on firm performance. She needs a complete executive briefing immediately.

##### Step 1: Complete Executive Briefing with PDF (All Tools)

**User Input**: 
```
Prepare a complete executive briefing for the board covering firm-wide AUM and performance across all strategies, client flow analysis with any concentration concerns, our top and bottom performing strategies with context, and relevant investment philosophy positioning that explains our current strategic direction. Generate a professional PDF for board distribution.
```

**Tools Used**:
- `executive_kpi_analyzer` (Cortex Analyst) - FIRM_AUM, strategy performance (QTD/YTD), net flows, client analytics
- `search_strategy_docs` (Cortex Search) - Investment philosophy and strategic positioning
- `pdf_generator` (Generic) - Generate branded PDF with `internal` audience for board briefing

**Expected Response**:
- **Headline KPIs**:
  - Total Firm AUM (from holdings, authoritative): ~£12.5B
  - Net Flows MTD with gross inflows and outflows
  - Active Client Count: 75 institutional investors

- **Strategy Performance Table**:
  | Strategy | AUM | QTD Return | YTD Return | Net Flows MTD |
  |---|---|---|---|---|
  | [Top performers first, sorted by performance] |

- **Top and Bottom Performers**:
  - Top 3 strategies by QTD/YTD return with context
  - Bottom 3 strategies with explanation

- **Client Flow Analysis**:
  - Flow trends by client type
  - Concentration check (no single client >10%)
  - Key segments driving flows

- **Strategic Context**:
  - Investment philosophy alignment
  - Strategic positioning summary

- **Key Messages for Board**:
  - 3-5 executive talking points

- **PDF Generation**:
  - Professional branded PDF with Simulated logo
  - Internal document styling (INTERNAL DOCUMENT badge)
  - Download link for immediate board distribution

**Talking Points**:
- **Authoritative AUM**: Uses FIRM_AUM calculated from actual holdings for accurate board reporting
- **Autonomous Orchestration**: AI independently selects and sequences executive tools including PDF generation
- **Single-Query Capability**: Complete board briefing with formal PDF from one comprehensive question
- **Strategy Performance Integration**: QTD/YTD returns now available directly from executive view
- **Board-Ready Deliverable**: Professional PDF ready for governance distribution

**Key Features Highlighted**: 
- **Multi-Tool AI Orchestration**: Agent autonomously determines tool sequence and synthesis including PDF generation
- **Holdings-Based AUM**: FIRM_AUM provides accurate, authoritative figure from portfolio data
- **Strategy Performance Metrics**: QTD/YTD returns calculated from weighted holdings performance
- **Board-Ready Format**: Professional executive summary with formal PDF suitable for governance reporting

#### Scenario Wrap-up

**Business Impact Summary**:
- **Rapid Response**: Complete executive briefing with PDF available in under 2 minutes
- **Comprehensive View**: Combines firm KPIs, strategy performance, client analytics, and strategic context
- **Data Accuracy**: Authoritative FIRM_AUM from holdings eliminates reporting discrepancies
- **Executive Productivity**: Hours of briefing preparation compressed into single query
- **Professional Deliverables**: Branded PDF ready for immediate board distribution

**Technical Differentiators**:
- **Multi-Tool Integration**: Demonstrates full Executive Copilot capability including PDF generation in single query
- **Holdings-Based Metrics**: FIRM_AUM and strategy performance calculated from actual portfolio data
- **Strategic Synthesis**: AI merges quantitative performance with qualitative positioning
- **Autonomous Operation**: True AI agent capability for executive decision support with formal deliverables

---

## Tools Used by Executive Copilot

| Tool | Type | Purpose |
|------|------|---------|
| `executive_kpi_analyzer` | Cortex Analyst | FIRM_AUM, strategy performance (QTD/YTD), net flows, client analytics |
| `quantitative_analyzer` | Cortex Analyst | Portfolio holdings detail, sector allocation |
| `financial_analyzer` | Cortex Analyst | Consolidated SEC financial metrics (total revenue, net income, EPS, balance sheet) |
| `sec_segments_analyzer` | Cortex Analyst | Geographic and business segment revenue from SEC filings (European division, regional breakdowns) |
| `implementation_analyzer` | Cortex Analyst | Client mandate requirements and constraints |
| `search_strategy_docs` | Cortex Search | Investment philosophy and strategy documents |
| `search_press_releases` | Cortex Search | Competitor news and M&A announcements |
| `ma_simulation` | Custom Tool | M&A financial modeling with firm assumptions |
| `pdf_generator` | Custom Tool | Professional branded PDF reports for board memos and executive briefings |

## Data Requirements

### Semantic Views
- `SAM_EXECUTIVE_VIEW`: FIRM_AUM (from holdings), STRATEGY_AUM, strategy performance (QTD/YTD/MTD returns), net flows, client analytics
- `SAM_SEC_FINANCIALS_VIEW`: Consolidated SEC financial metrics (total revenue, net income, EPS, balance sheet)
- `SAM_SEC_SEGMENTS_VIEW`: Geographic and business segment revenue from SEC filings (regional breakdowns, divisional performance)
- `SAM_ANALYST_VIEW`: Portfolio analytics for holdings detail (existing)
- `SAM_IMPLEMENTATION_VIEW`: Client mandate requirements (existing)

### Key Metrics in SAM_EXECUTIVE_VIEW
- **FIRM_AUM**: Authoritative firm AUM calculated from portfolio holdings
- **TOTAL_CLIENT_AUM**: Client-reported AUM (may differ from FIRM_AUM)
- **STRATEGY_AUM**: AUM by strategy/portfolio
- **STRATEGY_QTD_RETURN**: Quarter-to-date return by strategy
- **STRATEGY_YTD_RETURN**: Year-to-date return by strategy
- **STRATEGY_MTD_RETURN**: Month-to-date return by strategy
- **FUND_NET_FLOWS**: Net flows at strategy level
- **CLIENT_COUNT**: Number of institutional clients

### Search Services
- `SAM_STRATEGY_DOCUMENTS`: Strategic planning and philosophy documents
- `SAM_PRESS_RELEASES`: Market news and competitor announcements

### Custom Tools
- `ma_simulation`: Python UDF for M&A EPS accretion modeling

### Data Tables
- `FACT_STRATEGY_PERFORMANCE`: Strategy-level AUM and performance metrics (NEW)
- `FACT_CLIENT_FLOWS`: Client-level flow data with institutional detail
- `FACT_FUND_FLOWS`: Aggregated fund-level flows by strategy
- `DIM_CLIENT`: Client dimension with type, AUM, relationship history
