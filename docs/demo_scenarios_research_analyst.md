# SAM Demo - Research Analyst Scenarios

Complete demo scenarios for Research Analyst role with step-by-step conversations, expected responses, and data flows.

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
- `search_broker_research` (Cortex Search) - Search "AI cloud computing technology investment opportunities"
- `search_company_events` (Cortex Search) - Search "AI cloud strategy growth guidance"
- `search_press_releases` (Cortex Search) - Search "AI cloud product launch announcement"

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
- `search_broker_research` (Cortex Search) - Get analyst research and ratings
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
- `search_broker_research` (Cortex Search) - Search for competitive analysis and market share data
- `search_press_releases` (Cortex Search) - Get competitor strategic announcements
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
- `search_broker_research` (Cortex Search) - Get analyst forecasts and price targets
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
**Business Challenge**: Research analysts need to rapidly analyze quarterly earnings releases, integrate financial data with management commentary, and identify sentiment shifts that could signal investment opportunities or risks. Traditional earnings analysis requires hours of manual transcription, data extraction, and cross-referencing across multiple documents, often missing subtle but critical sentiment changes.  
**Value Proposition**: AI-powered earnings intelligence that automatically processes financial filings, earnings call transcripts, and press releases to provide instant financial analysis combined with sentiment insights, enabling analysts to detect emerging trends and risks within minutes of earnings releases.

**Agent**: `research_copilot`  
**Data Available**: SEC filings for 14,000+ securities, earnings transcripts, press releases, financial fundamentals

#### Demo Flow

**Scene Setting**: Sarah is analyzing the latest quarterly earnings for a major technology holding and needs to quickly assess the financial performance, understand management sentiment, and identify any shifts in forward guidance that could impact the investment thesis.

##### Step 1: Integrated Earnings Analysis
**User Input**: 
```
Give me a comprehensive analysis of Microsoft's latest quarterly earnings, including reported financial metrics versus consensus estimates and key management commentary from the earnings call.
```

**Tools Used**:
- `fundamentals_analyzer` (Cortex Analyst) - Get reported financials and consensus estimates from SAM_FUNDAMENTALS_VIEW
- `financial_analyzer` (Cortex Analyst) - Get detailed SEC filing metrics from SAM_SEC_FINANCIALS_VIEW
- `search_company_events` (Cortex Search) - Search "Microsoft earnings Q4 guidance commentary"

**Expected Response**:
- **Financial Performance**: Reported revenue, net income, and EPS vs. analyst consensus estimates from SEC filings
- **Key Metrics Analysis**: Margin trends, growth rates, and segment performance from FACT_SEC_FILINGS
- **Management Commentary**: Key quotes and themes from earnings transcript regarding future outlook
- **Guidance Updates**: Forward-looking statements and any revisions to company guidance
- **Document Sources**: Citations from SEC filings, earnings transcript, and press releases

**Talking Points**:
- Instant integration of structured financial data with unstructured earnings commentary
- Automatic comparison of reported results against consensus estimates
- AI-powered extraction of key management insights from lengthy earnings calls

**Key Features Highlighted**: 
- SEC filings integration providing authentic financial data (28.7M records)
- Multi-document synthesis combining quantitative and qualitative analysis
- Real-time financial analysis with management commentary context

##### Step 2: Sentiment Analysis and Red Flags

**Presenter Transition**:
> "The financial metrics look solid, but numbers only tell part of the story. What often matters more is how management talks about those numbers. Let me analyse the tone and sentiment across different sections of the earnings call to detect any concerning shifts..."

*Reasoning: Quantitative earnings data needs qualitative validation. Sentiment analysis reveals management confidence levels that often precede financial results by one or two quarters.*

**User Input**: 
```
Compare the sentiment between Microsoft's prepared remarks and the Q&A session. Are there any concerning shifts or defensive language that could indicate management uncertainty?
```

**Tools Used**:
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
- `search_broker_research` (Cortex Search) - Get analyst reactions to earnings

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
**Business Challenge**: Investment committees require comprehensive, structured investment memos that combine quantitative financial analysis with qualitative research insights. Creating these memos manually requires hours of data gathering across SEC filings, broker research, earnings calls, and press releases, often resulting in inconsistent formats and missed connections between data sources.  
**Value Proposition**: AI-powered investment memo generation that automatically synthesizes financial fundamentals, analyst perspectives, management commentary, and corporate developments into professional, structured research reports ready for investment committee review.

**Agent**: `research_copilot`  
**Data Available**: SEC filings (28.7M records, 14,000+ securities), broker research (~200 reports), earnings transcripts (~100 documents), press releases (~200 documents)

#### Demo Flow

**Scene Setting**: David needs to prepare a comprehensive investment memo for the upcoming investment committee meeting. The committee requires a structured analysis covering financial health, competitive positioning, management outlook, and risk assessment for a major technology holding.

##### Step 1: Generate Comprehensive Investment Memo
**User Input**: 
```
Generate a comprehensive investment research report for NVIDIA covering financial health, management outlook, analyst views, competitive position, and key risks. Include a Buy/Hold/Sell recommendation.
```

**Tools Used**:
- `financial_analyzer` (Cortex Analyst) - Get revenue, margins, growth rates, and financial ratios from SEC filings
- `search_broker_research` (Cortex Search) - Get analyst ratings, price targets, and competitive analysis
- `search_company_events` (Cortex Search) - Get management guidance and strategic commentary
- `search_press_releases` (Cortex Search) - Get recent corporate developments and catalysts

**Expected Response**:
- **Executive Summary** (8-12 bullets):
  - Investment thesis statement
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
- AI automatically orchestrates multiple tools to build comprehensive investment analysis
- Structured output follows institutional investment memo standards
- Clear labelling of facts vs. analysis vs. inference for compliance
- Source citations throughout for audit trail

**Key Features Highlighted**: 
- Multi-tool orchestration for comprehensive research synthesis
- Structured investment memo format with executive summary
- Automatic source attribution and fact/analysis labelling
- Professional output ready for investment committee

##### Step 2: Deep-Dive on Specific Section

**Presenter Transition**:
> "The investment memo provides a comprehensive overview, but the investment committee often wants to drill deeper on specific sections. Competitive positioning is particularly important for technology companies. Let me expand on the competitive landscape with detailed market share analysis..."

*Reasoning: Executive summaries identify key areas; deep-dives provide the supporting evidence. This demonstrates the agent's ability to refine any section without losing overall context.*

**User Input**: 
```
Expand on the competitive landscape section. How does NVIDIA's AI chip market position compare to AMD and Intel? Include market share data if available.
```

**Tools Used**:
- `search_broker_research` (Cortex Search) - Get competitive analysis and market share estimates
- `search_press_releases` (Cortex Search) - Get recent competitive developments
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

##### Step 3: Risk Scenario Analysis

**Presenter Transition**:
> "Strong competitive positioning is encouraging, but professional investment analysis requires equal attention to risks. Let me build a comprehensive risk framework with monitoring indicators so we can proactively track any thesis-threatening developments..."

*Reasoning: Investment committees require balanced analysis. After understanding the opportunity and competitive position, we must systematically assess what could go wrong and how we'd know.*

**User Input**: 
```
What are the key risks to the investment thesis? For each risk, provide leading indicators we should monitor and potential mitigants.
```

**Tools Used**:
- `search_broker_research` (Cortex Search) - Get analyst risk assessments
- `search_company_events` (Cortex Search) - Get management commentary on risks
- `search_press_releases` (Cortex Search) - Get regulatory and competitive developments

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

##### Step 4: Investment Committee Summary with PDF Generation

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
- **PDF Generation**: Professional branded PDF with Simulated logo
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
- `search_broker_research` (Cortex Search) - Analyst opinions, ratings, price targets
- `search_press_releases` (Cortex Search) - Recent corporate announcements and developments

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
