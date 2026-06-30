# SAM Demo - Research Copilot Scenarios

Complete demo scenarios for the Research Co-Pilot with step-by-step conversations, expected responses, and data flows.

> **Scenario**: `research_copilot`  
> **Agent**: `AM_research_copilot`  
> **Demo Surfaces**: Snowflake Intelligence  
> **Skills**: `pdf-report-generation`, `investment-memo-generation`, `equity-research-report`, `audience-adaptive-narrative`, `earnings-intelligence`, `competitive-intelligence`, `insider-institutional-analysis`  
> **Common Tools**: `server_skill`, `code_execution`, `data_to_chart`

---

## Research Analyst

### Research Copilot - Document Research & Analysis

#### Business Context Setup

**Persona**: David, Research Analyst at Simulated Asset Management  
**Business Challenge**: Research analysts need to combine quantitative financial analysis with qualitative research synthesis across multiple sources (financial data, broker research, earnings calls, press releases) to build comprehensive investment cases. Manual analysis requires hours of data gathering, financial modeling, and document review, often missing critical connections between financial performance and strategic narratives.  
**Value Proposition**: AI-powered research intelligence that seamlessly combines structured financial analysis with unstructured document insights, enabling analysts to build complete investment theses faster and with greater depth than traditional approaches.

**Agent**: `research_copilot`  
**Data Available**: Financial fundamentals & estimates for 14,000+ securities + 100 broker reports, 75 earnings transcripts, 75 press releases

#### Demo Flow

**Scene Setting**: David is preparing a thematic research report on technology sector opportunities and needs to quickly synthesize insights from multiple document sources to identify emerging trends and validate investment themes.

##### Step 1: Multi-Source Research Synthesis
**User Input**: 
```
What is the latest research saying about AI and cloud computing opportunities in technology companies?
```

**Tools Used**:
- `search_external_docs` (Cortex Search) - Search "AI cloud computing technology investment opportunities"
- `search_company_events` (Cortex Search) - Search "AI cloud strategy growth guidance"
- `search_external_docs` (Cortex Search) - Search "AI cloud product launch announcement"

**Expected Response**:
- AI and cloud computing investment themes from broker research (featuring Microsoft, Amazon, Google)
- Management commentary on AI strategy and cloud growth from earnings transcripts
- Corporate AI and cloud developments from press releases
- Synthesized technology sector opportunities with proper citations

**Talking Points**:
- AI automatically searches across multiple document types simultaneously for specific themes
- Intelligent synthesis of AI and cloud computing insights from different source perspectives
- Thematic focus ensures relevant results for technology sector analysis

**Key Features Highlighted**: 
- Multi-source Cortex Search integration
- Intelligent document synthesis and summarization
- Automatic source attribution and citation

##### Step 2: Deep-Dive Company Analysis

**Presenter Transition**:
> "We've identified strong AI and cloud computing themes across several major technology companies. But thematic research alone doesn't tell us which company offers the best investment opportunity. Let me ask the agent to select the strongest candidate and provide a comprehensive deep-dive analysis..."

*Reasoning: Thematic research identifies opportunities broadly; now we need to focus on a specific company to build a complete investment case with financial validation.*

**User Input**: 
```
From those companies mentioned in the AI and cloud research, pick the one with the strongest themes and give me a detailed analysis of their recent performance and strategic positioning
```

**Tools Used**:
- `financial_analyzer` (Cortex Analyst) - Analyze company financial metrics from SAM_SEC_FILINGS_VIEW
- `search_external_docs` (Cortex Search) - Get analyst research and ratings
- `search_company_events` (Cortex Search) - Get management commentary on strategy

**Expected Response**:
- **Company Selection Rationale**: Why this company was chosen based on Step 1 research themes
- **Financial Performance Metrics**: Revenue trends, EPS progression, analyst estimates vs. actuals
- **Earnings Analysis**: Quarterly performance, earnings surprises, financial ratios
- **Management Commentary**: Strategic positioning and forward guidance from earnings calls that align with Step 1 themes
- **Analyst Perspectives**: Research opinions and price targets that connect to AI/cloud opportunities from Step 1
- **Corporate Developments**: Recent strategic announcements that support the themes identified in Step 1
- **Comprehensive Synthesis**: Integration of quantitative performance with the specific qualitative themes from Step 1

**Talking Points**:
- **Contextual Company Selection**: AI automatically identifies the most relevant company from Step 1 research
- **Theme Continuity**: Deep-dive analysis directly builds on the AI/cloud themes from previous research
- **Integrated Intelligence**: Financial analysis validates the qualitative themes identified in Step 1

**Key Features Highlighted**: 
- **Contextual Follow-up**: Automatically selects relevant company based on Step 1 findings
- **Theme-Based Analysis**: Deep-dive specifically addresses themes identified in previous step
- **Integrated Validation**: Financial performance data supports or challenges qualitative research themes

##### Step 3: Competitive Intelligence Gathering

**Presenter Transition**:
> "We now have a strong understanding of our lead candidate's financial performance and strategic positioning. But no investment decision is complete without understanding the competitive landscape. Let me compare their AI strategy against the other technology players we identified in Step 1..."

*Reasoning: Single-company analysis must be contextualised within the competitive environment. This step transforms company research into a comparative investment framework.*

**User Input**: 
```
How does that company's AI strategy compare to what other technology companies mentioned are doing?
```

**Tools Used**:
- `search_external_docs` (Cortex Search) - Search for competitive analysis and market share data
- `search_external_docs` (Cortex Search) - Get competitor strategic announcements
- `financial_analyzer` (Cortex Analyst) - Compare revenue/margins across competitors

**Expected Response**:
- Comparative analysis of AI strategies across the specific companies identified in Steps 1-2
- Management commentary on competitive positioning from earnings calls of the Step 1 companies
- Strategic announcements and partnerships from press releases that connect the Step 1 themes
- Competitive landscape analysis focused on the AI/cloud opportunities from Step 1
- Direct comparison showing how the Step 2 company stacks against Step 1 competitors

**Talking Points**:
- **Building Competitive Context**: Uses the specific companies and themes from previous steps
- **Focused Comparison**: Avoids generic analysis by focusing on the companies already identified
- **Strategic Investment Framework**: Builds a complete competitive picture for investment decision-making

**Key Features Highlighted**: 
- **Multi-Step Intelligence**: Integrates findings from Steps 1 and 2 for focused competitive analysis
- **Theme-Based Comparison**: Competitive analysis specifically addresses AI/cloud themes from Step 1
- **Investment Decision Support**: Provides comparative context needed for investment decisions

##### Step 4: Investment Thesis Validation

**Presenter Transition**:
> "We've built a complete picture: thematic opportunities, company fundamentals, and competitive positioning. The final step is validating our investment thesis by comparing management's outlook with analyst expectations—this reveals whether the market has already priced in the opportunity..."

*Reasoning: Before presenting to the investment committee, we need to validate whether management guidance aligns with analyst forecasts. Any disconnects could signal either opportunity or risk.*

**User Input**: 
```
Based on our analysis of the company and its competitive position, compare what management is saying about AI growth prospects versus what analysts are forecasting for this investment opportunity
```

**Tools Used**:
- `search_company_events` (Cortex Search) - Get management outlook and guidance
- `search_external_docs` (Cortex Search) - Get analyst forecasts and price targets
- `financial_analyzer` (Cortex Analyst) - Compare historical vs forecast metrics

**Expected Response**:
- Management outlook and guidance from earnings transcripts specific to the Step 2 company
- Analyst forecasts and price targets from broker research that connect to Step 1 AI/cloud themes
- Strategic initiatives and investments from press releases that support the competitive analysis from Step 3
- Identification of consensus views and potential disconnects specifically for the investment case built in Steps 1-3
- Final investment thesis validation that ties together all previous analysis

**Talking Points**:
- **Complete Investment Case**: Validates the entire research workflow from themes to company to competition
- **Consensus Analysis**: Identifies alignment or disagreement between management and analysts for the specific opportunity
- **Investment Decision Ready**: Provides final validation needed for investment committee presentation

**Key Features Highlighted**: 
- **Multi-Step Synthesis**: Integrates themes (Step 1), company analysis (Step 2), and competitive position (Step 3)
- **Investment Thesis Validation**: Tests the strength of the complete investment case built through previous steps
- **Decision Support**: Provides final consensus analysis needed for investment decisions

#### Scenario Wrap-up

**Business Impact Summary**:
- **Research Efficiency**: Reduced comprehensive company analysis time from days to minutes
- **Analysis Completeness**: Seamless integration of quantitative financial data with qualitative research insights
- **Investment Thesis Quality**: Enhanced ability to build complete investment cases with both numbers and narrative
- **Competitive Intelligence**: Faster identification of financial performance trends and strategic positioning

**Technical Differentiators**:
- **Hybrid Analytics Platform**: Seamless combination of Cortex Analyst (structured data) and Cortex Search (documents)
- **Comprehensive Data Integration**: Financial fundamentals, estimates, and earnings data combined with research documents
- **Intelligent Financial Analysis**: Automated calculation of earnings surprises, trend analysis, and ratio comparisons
- **Multi-Source Research Synthesis**: Unified analysis across financial data, management commentary, and analyst research


### Research Copilot - Earnings Intelligence Extensions

#### Business Context Setup

**Persona**: Sarah, Senior Research Analyst at Simulated Asset Management  
**Business Challenge**: Research analysts need to rapidly analyze quarterly earnings releases, integrate financial data with management commentary, and identify sentiment shifts that could signal investment opportunities or risks.  
**Value Proposition**: AI-powered earnings intelligence that automatically processes financial filings, earnings call transcripts, and press releases to provide instant financial analysis combined with sentiment insights.

**Agent**: `research_copilot`  
**Skill**: `earnings-intelligence` (4-step workflow with stopping point)  
**Data Available**: SEC filings for 14,000+ securities, earnings transcripts, press releases, financial fundamentals

#### Demo Flow

**Scene Setting**: Sarah is analyzing the latest quarterly earnings for a major technology holding and needs to quickly assess the financial performance, understand management sentiment, and identify any shifts in forward guidance.

##### Step 1: Single Prompt — Skill Activates Automatically

**User Input**: 
```
Give me a comprehensive analysis of Microsoft's latest quarterly earnings, including reported financial metrics versus consensus estimates and key management commentary from the earnings call.
```

**Skill Activation**: Agent loads `earnings-intelligence` skill, executes Step 1 (Integrated Earnings Snapshot):
- `financial_analyzer` (Cortex Analyst) — Get reported financials and estimates
- `search_company_events` (Cortex Search) — Key management quotes from earnings call

**Expected Response**:
- Headline: "Microsoft Q[X]: Revenue [beat/missed] by [X]%, EPS [beat/missed] by [X]%"
- Financial summary table (actual vs estimate vs prior quarter)
- Top 3 management quotes with speaker attribution
- Guidance summary: raised / maintained / lowered

**STOPPING POINT** — Agent pauses and offers:
> "Here's the earnings snapshot. I can:
> - **Analyse sentiment and red flags** (tone shifts, hedging language, non-answers)
> - **Track strategic commentary evolution** (how key themes changed vs prior quarters)
> - **Generate an Investment Committee summary** (structured IC-ready format)
> - **Cross-reference with analyst reactions** (broker research post-earnings)
>
> Which would be most useful?"

**Talking Points**:
- The agent gathered data first, then PAUSED — this mirrors how senior analysts work
- The stopping point gives the presenter control over demo direction
- One prompt activated the full workflow; no multi-step setup needed

##### Step 2: Sentiment Analysis (Branch Selection)

**User Input**: 
```
Analyse sentiment and red flags
```

**Skill Branch**: Agent executes Step 2a (Sentiment & Red Flags):
- `search_company_events` (Cortex Search) — Full transcript sentiment analysis
- `search_company_events` (Cortex Search) - Search "Microsoft management tone challenges risks defensive Q&A"

**Expected Response**:
- **Sentiment Comparison**: Quantified sentiment scores for prepared remarks vs. Q&A session
- **Tone Analysis**: Description of management confidence levels and any defensive language
- **Key Questions**: Specific analyst questions that triggered defensive responses
- **Risk Indicators**: Areas where management showed uncertainty or provided evasive answers
- **Comparative Context**: How this sentiment compares to previous quarters

**Talking Points**:
- AI quantifies subjective "gut feelings" about earnings call tone into measurable data
- Sentiment delta between prepared remarks and Q&A often reveals management confidence levels
- Early warning system for detecting management pressure before it shows in financial results

**Key Features Highlighted**: 
- Advanced sentiment analysis turning qualitative assessments into quantitative signals
- Comparative analysis across different sections of earnings calls
- Predictive insights from management tone and language patterns

##### Step 3: Strategic Commentary Evolution

**Presenter Transition**:
> "Current quarter sentiment is useful, but the real insight comes from tracking how management messaging evolves over time. Are they becoming more or less confident on key strategic initiatives? Let me trace the evolution of their AI and cloud commentary..."

*Reasoning: Single-quarter sentiment can be noise; multi-quarter strategic narrative evolution reveals genuine shifts in management priorities and confidence levels.*

**User Input**: 
```
How has Microsoft's commentary on cloud computing and AI strategy evolved over the past three quarters? Are there any shifts in their strategic messaging or capital allocation priorities?
```

**Tools Used**:
- `search_company_events` (Cortex Search) - Search across multiple quarters for Microsoft cloud AI strategy evolution
- `financial_analyzer` (Cortex Analyst) - Track capex and R&D trends over quarters from SAM_SEC_FILINGS_VIEW

**Expected Response**:
- **Strategic Theme Evolution**: Changes in management emphasis on cloud computing and AI initiatives
- **Investment Priorities**: Shifts in capital expenditure focus and R&D allocation
- **Competitive Positioning**: How Microsoft's messaging has evolved relative to market dynamics
- **Forward Guidance**: Changes in growth expectations for cloud and AI segments
- **Historical Context**: Comparison with previous quarters' strategic commentary

**Talking Points**:
- Historical analysis reveals strategic shifts that may not be apparent in single-quarter analysis
- AI tracks consistency in management messaging and identifies strategic pivots
- Long-term strategic evolution analysis supports investment thesis development

**Key Features Highlighted**: 
- Multi-quarter analysis tracking strategic narrative evolution
- Cross-document intelligence linking financial data with strategic commentary
- Historical context providing deeper investment insights

##### Step 4: Investment Committee Summary

**Presenter Transition**:
> "We now have a complete earnings intelligence picture: financial metrics, management sentiment, and strategic evolution over time. Let me synthesise all of this into a concise investment committee memo that captures the key insights and investment implications..."

*Reasoning: Complex multi-dimensional analysis must be distilled into actionable intelligence. The memo format ensures the investment committee receives a complete but concise summary for decision-making.*

**User Input**: 
```
Draft a concise investment committee memo summarizing Microsoft's earnings results, highlighting the key financial metrics, sentiment analysis findings, and any strategic shifts that impact our investment thesis.
```

**Tools Used**:
- `financial_analyzer` (Cortex Analyst) - Get comprehensive financial metrics summary
- `search_company_events` (Cortex Search) - Get key management quotes
- `search_external_docs` (Cortex Search) - Get analyst reactions to earnings

**Expected Response**:
- **Executive Summary**: Key financial highlights and performance vs. expectations
- **Sentiment Assessment**: Summary of management confidence and any concerning shifts
- **Strategic Updates**: Notable changes in cloud/AI strategy and capital allocation
- **Investment Implications**: How findings support or challenge current investment thesis
- **Action Items**: Recommended follow-up analysis or portfolio actions
- **Supporting Data**: References to specific SEC filing metrics and transcript quotes

**Talking Points**:
- Automated synthesis of complex earnings analysis into executive-ready format
- Integration of quantitative financial analysis with qualitative sentiment insights
- Professional documentation supporting investment decision-making process

**Key Features Highlighted**: 
- Comprehensive report generation combining multiple data sources and analytical perspectives
- Professional formatting suitable for investment committee review
- Complete audit trail with source citations for compliance and verification

#### Scenario Wrap-up

**Business Impact Summary**:
- **Speed Enhancement**: Earnings analysis reduced from hours to minutes, enabling faster decision-making
- **Analytical Depth**: Combined quantitative and qualitative analysis provides comprehensive investment insights
- **Risk Detection**: Sentiment analysis creates early warning system for management confidence shifts
- **Strategic Intelligence**: Multi-quarter analysis reveals strategic evolution and competitive positioning changes

**Technical Differentiators**:
- **Authentic Data Integration**: Real SEC filings (28.7M records) provide institutional-grade financial analysis
- **Multi-Modal Intelligence**: Seamless combination of structured financial data with unstructured earnings commentary
- **Predictive Sentiment Analysis**: Quantified sentiment scoring creates measurable signals from qualitative management tone
- **Historical Context Engine**: Multi-quarter strategic analysis reveals long-term trends and strategic pivots

---

### Research Copilot - Investment Memo Generation

#### Business Context Setup

**Persona**: David, Senior Research Analyst at Simulated Asset Management  
**Business Challenge**: Investment committees require comprehensive, structured investment memos that combine quantitative financial analysis with qualitative research insights.  
**Value Proposition**: AI-powered investment memo generation with structured stopping points — the analyst stays in control of scope and depth.

**Agent**: `research_copilot`  
**Skill**: `investment-memo-generation` (7-section memo with dual stopping points)  
**Data Available**: SEC filings (28.7M records, 14,000+ securities), broker research, earnings transcripts, press releases

#### Demo Flow

**Scene Setting**: David needs to prepare a comprehensive investment memo for the upcoming investment committee meeting.

##### Step 1: Single Prompt — Skill Activates (STOPPING POINT)

**User Input**: 
```
Generate a comprehensive investment memo for NVIDIA covering financial health, management outlook, analyst views, competitive position, and key risks. Include a Buy/Hold/Sell recommendation.
```

**Skill Activation**: Agent loads `investment-memo-generation` skill, executes Step 1 (Financial Foundation):
- `segment_analyzer` — Revenue by segment and geography
- `fundamentals_analyzer` + `sec_financials` — Key metrics, analyst estimates, margins

**STOPPING POINT** — Agent presents financial snapshot and offers:
> "I've pulled the financial foundation. Revenue: $[X]B ([+/-X]% YoY), EPS: $[X]. I can:
> - **Continue to qualitative research** (SEC filings, broker research, earnings calls)
> - **Run earnings intelligence first** → loads earnings-intelligence skill
> - **Check competitive positioning** → loads competitive-intelligence skill
>
> How would you like to proceed?"

**Talking Point**: The agent pauses after financials — the analyst can redirect before committing to the full memo workflow.

##### Step 2: Continue to Research → Full 7-Section Memo Generated

**Presenter Transition**:
> "The agent paused after gathering financials. Now we tell it to continue — this triggers the full qualitative research AND memo compilation in a single response."

**User Input**:
```
Continue to qualitative research
```

**What Happens**: The agent executes the remaining workflow end-to-end:
1. **Qualitative Research** — 4 tools:
   - `search_sec_filings` — Risk factors, MD&A from 10-K
   - `search_external_docs` (broker_research) — Analyst views
   - `search_company_events` — Management guidance
   - `search_external_docs` (press_releases) — Recent catalysts
2. **Memo Compilation** — Synthesises all data into the full 7-section format

**Expected Response**: Full 7-section investment memo:
  - Buy/Hold/Sell recommendation with rationale
  - Key financial highlights (revenue growth, margins, FCF)
  - Critical risks and mitigants
  - Near-term catalysts
- **Financial Profile**:
  - Revenue mix and growth trends from SEC filings
  - Margin analysis (gross, operating, net)
  - Cash flow generation and capital allocation
  - Key financial ratios with [FACT] labels
- **Competitive Landscape**:
  - Market position from broker research
  - Competitive moat assessment
  - Direct and indirect competitors
- **Management Outlook**:
  - Forward guidance from earnings transcripts
  - Strategic priorities and capital allocation
  - Key quotes with [FACT] labels
- **Analyst Perspectives**:
  - Consensus rating and price targets
  - Bull/bear case arguments
- **Risk Assessment**:
  - Macro, regulatory, competitive risks
  - Leading indicators for each risk
- **Catalysts**:
  - Near-term events (product launches, earnings)
  - 12-24 month scenarios (bear/base/bull)

**Talking Points**:
- **2-turn conversation**: One initial prompt + "Continue to qualitative research" — produces a complete 7-section investment memo
- The stopping point gave the analyst a chance to redirect (e.g., run earnings intelligence first), but choosing "Continue" triggers the full end-to-end workflow
- AI automatically orchestrates multiple tools to build comprehensive investment analysis
- Structured output follows institutional investment memo standards
- Clear labelling of facts vs. analysis vs. inference for compliance
- Source citations throughout for audit trail

**Key Features Highlighted**: 
- Multi-tool orchestration for comprehensive research synthesis
- Structured investment memo format with executive summary
- Automatic source attribution and fact/analysis labelling
- Professional output ready for investment committee

##### Step 3: Deep-Dive on Specific Section (Optional)

**Presenter Transition**:
> "The investment memo provides a comprehensive overview, but the investment committee often wants to drill deeper on specific sections. Competitive positioning is particularly important for technology companies. Let me expand on the competitive landscape with detailed market share analysis..."

*Reasoning: Executive summaries identify key areas; deep-dives provide the supporting evidence. This demonstrates the agent's ability to refine any section without losing overall context.*

**User Input**: 
```
Expand on the competitive landscape section. How does NVIDIA's AI chip market position compare to AMD and Intel? Include market share data if available.
```

**Tools Used**:
- `search_external_docs` (Cortex Search) - Get competitive analysis and market share estimates
- `search_external_docs` (Cortex Search) - Get recent competitive developments
- `financial_analyzer` (Cortex Analyst) - Compare revenue and margin trends across competitors

**Expected Response**:
- Detailed competitive positioning analysis
- Market share estimates from broker research (labelled as [ANALYST ESTIMATE])
- Product comparison (GPUs, data centre, AI accelerators)
- Competitive moat assessment (CUDA ecosystem, software lock-in)
- Recent competitive developments from press releases
- Financial comparison table (revenue growth, margins) from SEC filings

**Talking Points**:
- Drill-down capability for any section of the investment memo
- Cross-company financial comparison using SEC filing data
- Market share data clearly labelled as analyst estimates
- Competitive moat analysis synthesised from multiple sources

**Key Features Highlighted**: 
- Section-specific deep-dive capability
- Cross-company financial analysis
- Clear data source attribution
- Competitive intelligence synthesis

##### Step 4: Risk Scenario Analysis (Optional)

**Presenter Transition**:
> "Strong competitive positioning is encouraging, but professional investment analysis requires equal attention to risks. Let me build a comprehensive risk framework with monitoring indicators so we can proactively track any thesis-threatening developments..."

*Reasoning: Investment committees require balanced analysis. After understanding the opportunity and competitive position, we must systematically assess what could go wrong and how we'd know.*

**User Input**: 
```
What are the key risks to the investment thesis? For each risk, provide leading indicators we should monitor and potential mitigants.
```

**Tools Used**:
- `search_external_docs` (Cortex Search) - Get analyst risk assessments
- `search_company_events` (Cortex Search) - Get management commentary on risks
- `search_external_docs` (Cortex Search) - Get regulatory and competitive developments

**Expected Response**:
- **Risk Inventory Table**:
  | Risk Category | Risk Description | Leading Indicators | Mitigants |
  |---------------|------------------|-------------------|-----------|
  | Regulatory | China export restrictions | Policy announcements, trade tensions | Geographic diversification |
  | Competitive | AMD/Intel catching up | Market share trends, product launches | R&D investment, CUDA ecosystem |
  | Demand | AI capex slowdown | Cloud provider guidance, order trends | Diversified customer base |
  | Valuation | Premium multiple compression | Interest rates, risk sentiment | Growth sustainability |
- Management's risk commentary from earnings transcripts
- Analyst risk assessments from broker research
- Recent risk-related developments from press releases

**Talking Points**:
- Structured risk framework with actionable monitoring indicators
- Multi-source risk synthesis (management, analysts, news)
- Clear mitigants for each identified risk
- Investment committee-ready risk assessment

**Key Features Highlighted**: 
- Comprehensive risk framework generation
- Leading indicator identification for proactive monitoring
- Multi-source risk validation
- Actionable risk mitigation strategies

##### Step 5: Investment Committee Summary with PDF Generation (Optional)

**Presenter Transition**:
> "We've completed the full analysis cycle: comprehensive memo, competitive deep-dive, and risk assessment. Now let me distil everything into a one-page brief and generate a professional PDF that the investment committee can act on immediately..."

*Reasoning: Detailed analysis must culminate in actionable recommendations. The one-page format forces prioritisation and the PDF provides a decision-ready document for the committee.*

**User Input**: 
```
Summarise the key points from our analysis into a one-page investment committee brief with clear recommendation and next steps. Generate a professional PDF for the investment committee.
```

**Tools Used**:
- Synthesis of previous analysis
- `pdf_generator` (Generic) - Generate branded PDF with `internal` audience

**Expected Response**:
- **Investment Committee Brief**:
  - **Company**: NVIDIA Corporation (NVDA)
  - **Recommendation**: [Buy/Hold/Sell] with conviction level
  - **Price Target**: Consensus analyst target with range
  - **Key Thesis Points** (3-5 bullets):
    - AI data centre leadership and growth trajectory
    - Competitive moat via CUDA ecosystem
    - Strong financial profile with expanding margins
  - **Key Risks** (3-5 bullets):
    - Regulatory exposure to China
    - Valuation premium vs. peers
    - Customer concentration in hyperscalers
  - **Near-Term Catalysts**:
    - Next earnings release
    - Product launches
    - Industry events
  - **Recommended Action**: Specific portfolio action recommendation
  - **Follow-Up Items**: Additional analysis needed
- **PDF Generation**: Professional branded PDF with SAM logo
- **Download Link**: Presigned URL for immediate access

**Talking Points**:
- One-page executive summary suitable for investment committee
- Clear recommendation with supporting rationale
- Professional branded PDF ready for distribution
- Complete research workflow from analysis to formal deliverable

**Key Features Highlighted**: 
- Executive summary generation from detailed analysis
- Clear, actionable recommendations
- Professional investment committee format with PDF output
- Complete research workflow in single session with formal deliverable

#### Scenario Wrap-up

**Business Impact Summary**:
- **Research Efficiency**: Comprehensive investment memo generated in minutes vs. hours of manual work
- **Analysis Completeness**: Seamless integration of quantitative SEC data with qualitative research insights
- **Consistency**: Standardised memo format ensures all critical sections are covered
- **Audit Trail**: Clear source citations and fact/analysis labelling for compliance
- **Professional Deliverables**: Branded PDF documents ready for investment committee distribution

**Technical Differentiators**:
- **Multi-Tool Orchestration**: Automatic coordination of Cortex Analyst, Cortex Search, and PDF generation
- **Structured Output Generation**: Professional investment memo format with executive summary and PDF output
- **Source Attribution**: Clear labelling of facts, analysis, and inference with citations
- **Iterative Refinement**: Drill-down capability for any section without losing context

---

### Research Copilot - Complete Company Research (Catch-All)

#### Business Context Setup

**Persona**: David, Research Analyst at Simulated Asset Management  
**Business Challenge**: Research analysts sometimes need a complete company research package with a single request when responding to urgent portfolio manager queries or preparing for unexpected meetings—requiring the AI to autonomously orchestrate all available research tools.  
**Value Proposition**: The Research Copilot demonstrates complete autonomous orchestration by selecting and sequencing all tools from a single comprehensive question, delivering investment-ready research without step-by-step guidance.

**Agent**: `research_copilot`  
**Data Available**: SEC financial data for 14,000+ securities, 100+ broker reports, 75+ earnings transcripts, 75+ press releases

#### Demo Flow

**Scene Setting**: David receives an urgent request from a portfolio manager for a complete research package on Microsoft before a 2 PM meeting. He has 15 minutes to deliver comprehensive analysis.

##### Step 1: Complete Company Research (All Tools)

**User Input**: 
```
Create a comprehensive investment research report on Microsoft including SEC financial analysis with revenue trends and margins, earnings call management commentary on AI strategy, broker research perspectives and ratings, and recent corporate developments from press releases.
```

**Tools Used**:
- `financial_analyzer` (Cortex Analyst) - SEC financial metrics, revenue, margins, growth rates
- `search_company_events` (Cortex Search) - Management commentary and strategic guidance
- `search_external_docs` (Cortex Search) - Analyst opinions, ratings, price targets
- `search_external_docs` (Cortex Search) - Recent corporate announcements and developments

**Expected Response**:
- **Financial Analysis**: Revenue trends, margin progression, key financial ratios from SEC filings
- **Management Perspective**: Strategic commentary from earnings calls, AI and cloud guidance
- **Analyst Views**: Broker ratings, price targets, key investment thesis points
- **Corporate Developments**: Recent announcements, product launches, strategic initiatives
- **Investment Summary**: Synthesized view with key takeaways and considerations

**Talking Points**:
- **Autonomous Orchestration**: AI independently selects and sequences all four research tools
- **Single-Query Capability**: Complete research package from one comprehensive question
- **Investment Ready**: Output structured for immediate portfolio manager use

**Key Features Highlighted**: 
- **Multi-Tool AI Orchestration**: Agent autonomously determines tool sequence and synthesis
- **Quantitative + Qualitative Integration**: SEC data merged with research and commentary
- **Professional Research Format**: Output suitable for investment committee or client communication

#### Scenario Wrap-up

**Business Impact Summary**:
- **Rapid Response**: Complete company research available in under 2 minutes
- **Comprehensive Coverage**: Combines financials, management views, analyst opinions, and news
- **Analyst Productivity**: Hours of manual research compressed into single query

**Technical Differentiators**:
- **Four-Tool Integration**: Demonstrates full Research Copilot capability in single query
- **Intelligent Source Synthesis**: AI merges multiple research sources into coherent narrative
- **Autonomous Operation**: True AI agent capability beyond simple document search

---

### Research Copilot - Equity Research Report

#### Business Context Setup

**Persona**: David, Senior Research Analyst at Simulated Asset Management  
**Business Challenge**: Producing institutional-grade equity research reports with scenario analysis takes 2-3 days per company, limiting coverage capacity.  
**Value Proposition**: The `equity-research-report` skill orchestrates 6 tools across a 10-section institutional format with dual stopping points — the analyst controls scope and depth.

**Agent**: `research_copilot`  
**Skill**: `equity-research-report` (10-section format with dual stopping points + cross-skill references)  
**Data Available**: SEC filings (28.7M records, 14,000+ securities), consensus estimates (500 companies), broker research, earnings transcripts, press releases

#### Demo Flow

**Scene Setting**: David has been asked to produce a comprehensive equity research report on NVIDIA for the investment committee.

> **Note on Stopping Points**: The skill defines stopping points after Step 1 (financial foundation) and Step 2 (research gathered). However, when the user's prompt is highly specific and comprehensive (e.g., explicitly requesting "recommendation, financial model, scenario analysis, and risk assessment"), the agent may interpret this as full authorization and generate the complete 10-section report in a single response. To trigger the stopping point behavior, use a more open-ended prompt like "Write a research report on NVIDIA" without specifying all sections.

##### Option A: Full Report in One Shot (Comprehensive Prompt)

**User Input**: 
```
Generate a comprehensive equity research report for NVIDIA with recommendation, financial model, scenario analysis with bull/base/bear cases, and risk assessment.
```

**What Happens**: The agent interprets the explicit request as authorization for the full workflow and delivers the complete 10-section report in a single response, including:
- Buy/Hold/Sell recommendation with price target
- Investment thesis with pillars table
- Financial model with historical + forecast data
- Scenario analysis (Bull/Base/Bear) with probability-weighted return
- Industry analysis and competitive landscape
- Risk assessment matrix
- Catalysts timeline
- Valuation summary
- ESG considerations
- Monitoring plan with validation/invalidation triggers

**Talking Points**:
- One prompt produced a complete institutional-grade equity research report
- Agent autonomously orchestrated 6+ tools (financial data, consensus, SEC filings, broker research, earnings calls, press releases)
- Scenario analysis uses real consensus estimate data (high→Bull, mean→Base, low→Bear)
- [FACT]/[ANALYSIS]/[INFERENCE] labelling throughout for compliance
- Report is immediately IC-ready

##### Option B: Step-by-Step with Stopping Points (Open-Ended Prompt)

**User Input** (alternative, to demonstrate stopping points): 
```
Write a research report on NVIDIA
```

**Skill Activation**: Agent loads `equity-research-report` skill, executes Step 1 (Financial Foundation):
- `fundamentals_analyzer` — Consensus estimates, price targets, analyst ratings
- `segment_analyzer` + `sec_financials` — Revenue segments, margins, 3-year trends

**STOPPING POINT** — Agent presents financial snapshot and offers:
> "I've gathered the financial foundation — fundamentals, segments, and consensus estimates. I can:
> - **Continue to research phase** (SEC filings, broker research, earnings calls, press releases)
> - **Adjust the scope** (focus on specific segments or time periods)
> - **Run competitive analysis first** → loads competitive-intelligence skill
> - **Check insider/institutional ownership** → loads insider-institutional-analysis skill
>
> Which approach works best? (Recommended: Continue to research phase for the full 10-section report)"

**Talking Point**: Two things to highlight — (1) the agent pauses to let the analyst drive, (2) it offers to compose with other skills (competitive analysis, ownership) before committing to the full report.

##### Step 2: Continue to Research → Full 10-Section Report Generated

**Presenter Transition** (only needed if using Option B above):
> "The agent paused after gathering financials. Now we tell it to continue — this triggers the full research gathering AND report compilation in a single response."

**User Input**:
```
Continue to research phase
```

**What Happens**: The agent executes the remaining workflow end-to-end:
1. **Research Gathering** — 4 tools in parallel:
   - `search_sec_filings` — 10-K risk factors, MD&A
   - `search_external_docs` (broker) — Analyst views
   - `search_company_events` — Earnings commentary
   - `search_external_docs` (press) — Recent catalysts
2. **Report Compilation** — Synthesises all gathered data into the full 10-section format

**Expected Response**: Full institutional equity research report with:
- Recommendation (Buy/Hold/Sell) + price target + risk rating
- Scenario Analysis table (Bull 20-25% / Base 50-60% / Bear 20-25%)
- Probability-weighted expected return
- All 10 sections with [FACT]/[ANALYSIS]/[INFERENCE] labelling
- **Industry Analysis**: Market size, competitive landscape, Porter's Five Forces
- **Risk Assessment**: Risk matrix with leading indicators and mitigants
- **Catalysts**: Near/medium/long-term with expected impact
- **Valuation**: DCF summary, relative valuation, historical context
- **ESG Considerations**: Material ESG factors
- **Monitoring Plan**: KPIs, thesis validation/invalidation signposts

**Talking Points**:
- **2-turn conversation**: One initial prompt + "Continue to research phase" — produces a complete institutional research report
- The stopping point gave the analyst a chance to redirect (e.g., run competitive analysis first), but choosing "Continue" triggers the full end-to-end workflow
- Scenario analysis uses real consensus estimate data (bull=high, base=mean, bear=low)
- All seven Research Copilot tools orchestrated automatically for comprehensive coverage
- Financial data sourced from authentic SEC filings and analyst consensus

**Key Features Highlighted**: 
- **Stopping point with branching**: Agent pauses once, giving analyst control — then delivers the full report on "Continue"
- Full report format with all 10 standard sections
- Consensus-driven scenario analysis (bull/base/bear) from real analyst data
- Multi-tool orchestration combining structured and unstructured data
- Investment committee-ready output

##### Step 3: Deep-Dive Scenario Analysis (Optional)

**Presenter Transition**:
> "The report provides a strong overview with scenario analysis based on consensus estimates. But the investment committee will want to understand the specific assumptions behind each scenario. Let me expand the bull, base, and bear cases with detailed driver analysis..."

*Reasoning: Scenario analysis tables summarise outcomes, but investment committees need to understand the underlying assumptions and sensitivity to key variables to make informed decisions.*

**User Input**: 
```
Expand on the scenario analysis. For each case (bull, base, bear), detail the specific assumptions about AI revenue growth, data centre demand, margin trajectory, and competitive dynamics. What would need to happen for each scenario to materialise?
```

**Tools Used**:
- `fundamentals_analyzer` (Cortex Analyst) - Get detailed consensus estimate breakdowns
- `search_external_docs` (Cortex Search) - Get analyst bull/bear case arguments
- `search_company_events` (Cortex Search) - Get management guidance on key growth drivers

**Expected Response**:
- **Bull Case Detailed Assumptions**: Specific growth rates, margin targets, market share gains, AI adoption acceleration
- **Base Case Detailed Assumptions**: Expected trajectory, consensus growth path, industry-average dynamics
- **Bear Case Detailed Assumptions**: Specific risk materialisation, competitive share loss, margin compression drivers
- **Sensitivity Analysis**: Key variables that swing outcomes between scenarios
- **Probability Assessment**: What signals would shift probability weights between scenarios
- **Monitoring Triggers**: Specific data points that would confirm or deny each scenario

**Talking Points**:
- Scenario analysis goes beyond simple high/low ranges to explain what drives each outcome
- Consensus estimates provide the quantitative foundation; qualitative research explains the "why"
- Sensitivity analysis helps the committee understand which variables matter most

**Key Features Highlighted**: 
- Detailed scenario decomposition with specific assumptions
- Integration of quantitative consensus data with qualitative analyst perspectives
- Actionable monitoring triggers for each scenario

##### Step 4: Competitive Position and Industry Context (Optional)

**Presenter Transition**:
> "Understanding the scenario drivers is critical, but we also need to contextualise the investment within the broader industry. The competitive landscape directly impacts which scenario is most likely to materialise. Let me assess the industry dynamics and competitive positioning..."

*Reasoning: Scenario probabilities depend on competitive dynamics. Industry analysis validates or challenges the assumptions in each scenario.*

**User Input**: 
```
How does the company's competitive position support or threaten our base case assumptions? Include market share trends, competitive moat assessment, and any industry dynamics that could shift the scenario probabilities.
```

**Tools Used**:
- `search_external_docs` (Cortex Search) - Get competitive analysis and market share data
- `search_external_docs` (Cortex Search) - Get competitive developments and strategic announcements
- `sec_financials` (Cortex Analyst) - Compare financial performance vs competitors

**Expected Response**:
- Competitive moat assessment (network effects, switching costs, scale advantages)
- Market share trends and competitive dynamics
- Industry structural analysis (growth rates, consolidation, regulation)
- Impact on scenario probabilities based on competitive position
- Comparison table: company vs key competitors on financial metrics

**Talking Points**:
- Competitive analysis directly informs scenario probability weighting
- Industry dynamics can shift the likelihood of bull vs bear outcomes
- Cross-company financial comparison validates competitive positioning claims

**Key Features Highlighted**: 
- Competitive moat framework applied with real data
- Industry dynamics linked to scenario analysis outcomes
- Cross-company financial comparison from SEC filings

##### Step 5: Generate Professional PDF Report (Optional)

**Presenter Transition**:
> "We now have a complete equity research report with detailed scenario analysis and competitive context. Let me generate a professional PDF with SAM branding that the investment committee can review and distribute..."

*Reasoning: The final step transforms the comprehensive analysis into a formal, branded deliverable suitable for investment committee distribution and institutional record-keeping.*

**User Input**: 
```
Generate a professional PDF of the complete equity research report including all sections we've discussed: recommendation, thesis, financial model, scenario analysis, industry analysis, risks, valuation, and monitoring plan.
```

**Tools Used**:
- Synthesis of all previous analysis
- `pdf_generator` (Generic) - Generate branded PDF with `internal` audience

**Expected Response**:
- **Complete Equity Research Report PDF** with all 10 sections:
  - Recommendation with price target and rating
  - Investment thesis with supporting pillars
  - Financial model with revenue/margin/EPS tables
  - Scenario analysis table (bull/base/bear) with probability-weighted return
  - Industry analysis with competitive landscape
  - Risk matrix with monitoring indicators
  - Catalyst timeline
  - Valuation summary
  - ESG considerations
  - Monitoring plan with signposts
- **Professional Formatting**: SAM logo, brand colours, section headers
- **Download Link**: Presigned URL for immediate access

**Talking Points**:
- Complete equity research report produced in minutes vs days
- Professional branded PDF suitable for investment committee distribution
- All financial data sourced from authentic SEC filings and consensus estimates
- Scenario analysis with quantitative foundation from real analyst consensus

**Key Features Highlighted**: 
- Professional PDF generation with institutional branding
- Complete research workflow from data gathering to formal deliverable
- Investment committee-ready format with all standard sections

#### Scenario Wrap-up

**Business Impact Summary**:
- **Research Efficiency**: Complete equity research report generated in minutes vs 2-3 days
- **Scenario Analysis Quality**: Bull/base/bear cases built on real consensus estimates, not assumptions
- **Coverage Capacity**: Analysts can produce 5-10x more research reports, expanding coverage universe
- **Consistency**: Standardised 10-section format ensures all critical analysis areas are covered
- **Professional Output**: Branded PDF suitable for investment committee distribution

**Technical Differentiators**:
- **Consensus-Driven Scenarios**: Bull/base/bear analysis uses real analyst consensus data (high/mean/low estimates and price targets)
- **Seven-Tool Orchestration**: Autonomous coordination of financial data, consensus estimates, SEC filings, broker research, earnings transcripts, press releases, and PDF generation
- **Institutional Format**: Standard equity research report structure recognised by professional investors
- **End-to-End Workflow**: From data gathering through scenario analysis to branded PDF in a single session

---

### Research Copilot - Insider Trading & Institutional Ownership Analysis

#### Business Context Setup

**Persona**: David, Research Analyst at Simulated Asset Management  
**Business Challenge**: Understanding insider sentiment and institutional ownership changes provides crucial signals for investment decisions, but manually tracking Form 4 and 13F filings is time-consuming.  
**Value Proposition**: The `insider-institutional-analysis` skill combines both data sources into a unified ownership picture with actionable smart money signals.

**Agent**: `research_copilot`  
**Skill**: `insider-institutional-analysis` (3-step workflow with stopping point)  
**Data Available**: SEC Form 4 insider transactions + SEC 13F institutional holdings

#### Demo Flow

**Scene Setting**: David is building an investment case for Apple and wants to understand ownership signals.

##### Step 1: Single Prompt — Skill Activates

**User Input**: 
```
What's the insider and institutional ownership picture for Apple?
```

**Skill Activation**: Agent loads `insider-institutional-analysis` skill, executes Steps 1 + 2:
- `insider_trading_analyzer` — Recent Form 4 filings, insider sentiment
- `institutional_holdings_analyzer` — Top holders, quarterly changes, concentration

**Expected Response**:
- Insider sentiment: Net [buying/selling] with transaction summary table
- Top 10 institutional holders with quarterly change
- Ownership concentration metrics

**STOPPING POINT** — Agent offers:
> "Here's the complete ownership picture. I can:
> - **Cross-reference with price action** (correlate insider trades with stock moves)
> - **Compare to sector peers** (ownership concentration vs industry norms)
> - **Generate ownership summary for IC** (structured format)
>
> Which would be most useful?"

**Talking Points**:
- Two specialised tools combined into one unified view
- Real SEC data (Form 4 + 13F) from Snowflake Public Data
- Stopping point lets analyst choose depth — quick check vs full IC analysis

##### Step 2: Branch Selection

**User Input**: 
```
Generate ownership summary for IC
```

**Expected Response**: Structured IC format with Insider Sentiment (Bullish/Neutral/Bearish), Institutional Conviction (High/Medium/Low), and Smart Money Signal synthesis.

**Talking Points**:
- One prompt activated the full workflow, one follow-up generated IC output
- The skill composed insider + institutional signals into an actionable recommendation
- Smart money flow analysis for investment validation
- Combines with insider data for complete ownership picture

**Key Features Highlighted**: 
- Real SEC filing data (Form 4 + 13F) integrated into research workflow
- Insider sentiment + institutional ownership = complete ownership intelligence
- Seamless tool orchestration between insider and holdings analyzers

---

### Research Copilot - Competitive Intelligence (Skill-Driven)

#### Business Context Setup

**Persona**: David, Research Analyst evaluating a new investment opportunity  
**Business Challenge**: Understanding competitive positioning requires cross-company financial comparison, broker research synthesis, and SEC filing analysis across multiple peers.  
**Value Proposition**: The `competitive-intelligence` skill identifies peers, compares financials, and offers moat assessment in a structured workflow.

**Agent**: `research_copilot`  
**Skill**: `competitive-intelligence`  
**Data Available**: SEC financials + segment data for 14,000+ securities + broker research

#### Demo Flow

##### Step 1: Single Prompt

**User Input**:
```
Compare NVDA to its main competitors
```

**Skill Activation**: Agent loads `competitive-intelligence` skill:
- `segment_analyzer` pulls NVDA's segment and geographic data
- `search_external_docs` finds broker research mentioning competitors
- `fundamentals_analyzer` compares financials across the peer set

**Expected Response**: Peer set identified (AMD, INTC, AVGO) + financial comparison table + positioning verdict

**STOPPING POINT** — Agent offers:
> - **Deep-dive a specific competitor**
> - **Analyse market share trends**
> - **Assess competitive moat**
> - **Generate competitive positioning summary**

##### Step 2: Branch into Moat Assessment

**User Input**:
```
Assess the competitive moat
```

**Expected Response**: Moat assessment (Wide/Narrow/None) with sources of advantage, risk factors from 10-K, and analyst consensus on durability.

**Talking Point**: The agent composed 5 different tools across structured data and unstructured documents to build a competitive picture — then let the analyst choose where to go deeper.

---

### Research Copilot - Ownership Intelligence (Skill-Driven)

#### Business Context Setup

**Persona**: David, Research Analyst validating an investment thesis  
**Business Challenge**: Smart money signals — insider buying clusters, institutional accumulation/distribution — provide valuable thesis confirmation but require manual SEC filing analysis.  
**Value Proposition**: The `insider-institutional-analysis` skill combines Form 4 and 13F data into a unified ownership picture with actionable signals.

**Agent**: `research_copilot`  
**Skill**: `insider-institutional-analysis`

#### Demo Flow

##### Step 1: Single Prompt

**User Input**:
```
What's the insider and institutional ownership picture for Apple?
```

**Skill Activation**: Agent loads `insider-institutional-analysis` skill:
- `insider_trading_analyzer` scans recent Form 4 filings
- `institutional_holdings_analyzer` pulls 13F data

**Expected Response**: Insider sentiment (Bullish/Neutral/Bearish) + top institutional holders + net quarterly flows

**STOPPING POINT** — Agent offers:
> - **Cross-reference with price action**
> - **Compare to sector peers**
> - **Generate ownership summary for IC**

**Talking Point**: Two specialised tools, one unified ownership picture, with branching options for deeper analysis. The stopping point lets the analyst decide if they need more or have enough.

