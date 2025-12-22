# SAM Demo - Client Relations Scenarios

Complete demo scenarios for Client Relations role with step-by-step conversations, expected responses, and data flows.

---

## Client Relations  

### Sales Advisor - Client Investment Strategy Q&A

#### Business Context Setup

**Persona**: James Mitchell, Client Relationship Manager at Snowcrest Asset Management  
**Business Challenge**: Clients frequently ask detailed questions about SAM's investment approach, particularly around ESG integration. Answering these questions requires synthesising information from philosophy documents, policy requirements, and actual portfolio examples—knowledge that traditionally lives across multiple documents and systems.  
**Value Proposition**: AI-powered investment strategy Q&A that combines philosophy, policy, and portfolio evidence to provide comprehensive, well-supported answers to client questions.

**Agent**: `sales_advisor`  
**Data Available**: Investment philosophy documents, ESG policies, portfolio holdings with ESG data

#### Demo Flow

**Scene Setting**: James received an email from a prospective client asking detailed questions about SAM's ESG investment approach. The client wants to understand the philosophy, specific criteria, and evidence of implementation before making an allocation decision.

##### Step 1: ESG Philosophy Overview
**User Input**: 
```
A prospective client is asking about SAM's approach to ESG integration. Explain our ESG investment philosophy and how it differs from simple exclusionary screening.
```

**Tools Used**:
- `search_philosophy_docs` (Cortex Search) - Search ESG investment philosophy

**Expected Response**:
- **Integration vs Exclusion**: SAM's approach as comprehensive ESG integration, not just negative screening
- **Materiality Focus**: Emphasis on financially material ESG factors
- **Active Ownership**: Engagement and proxy voting as key components
- **Long-term Value**: How ESG integration supports long-term returns
- **Competitive Positioning**: What makes SAM's approach distinctive

**Talking Points**:
- **Philosophy Retrieval**: AI quickly surfaces comprehensive philosophy content
- **Consistent Messaging**: Ensures accurate representation of firm's approach
- **Client Education**: Enables informed client decision-making

**Key Features Highlighted**: 
- **SAM_PHILOSOPHY_DOCS**: Comprehensive investment philosophy library
- **Natural Language**: AI explains complex philosophy in client-friendly terms

##### Step 2: ESG Policy Specifics

**Presenter Transition**:
> "The client appreciated the philosophy overview, but now wants specifics. What exactly are our ESG criteria? What do we exclude? Let me pull our actual policy requirements..."

*Reasoning: Philosophy explains the 'why', but clients often need specific policy details—the 'what' and 'how'—to satisfy due diligence requirements.*

**User Input**: 
```
What are our specific ESG screening criteria and exclusion policies? The client wants to know exactly what we include and exclude.
```

**Tools Used**:
- `search_policies` (Cortex Search) - Search ESG policy requirements

**Expected Response**:
- **Exclusion List**: Industries and activities excluded (controversial weapons, thermal coal, etc.)
- **ESG Grade Requirements**: Minimum ESG ratings for inclusion
- **Controversy Thresholds**: How controversies affect eligibility
- **Engagement Criteria**: When engagement is pursued vs exclusion
- **Review Process**: How exclusion list is maintained and updated

**Talking Points**:
- **Policy Specificity**: AI retrieves exact policy requirements for client due diligence
- **Transparency**: Demonstrates SAM's clear, documented ESG criteria
- **Compliance Ready**: Information suitable for client compliance review

**Key Features Highlighted**: 
- **SAM_POLICY_DOCS**: Complete policy library with ESG requirements
- **Due Diligence Support**: Provides documentation-ready policy details

##### Step 3: Portfolio Evidence

**Presenter Transition**:
> "The client now wants proof—show me this philosophy and policy actually working in practice. Let me pull concrete examples from our ESG Leaders portfolio..."

*Reasoning: Philosophy and policy are important, but prospective clients want evidence of implementation. Portfolio examples provide tangible proof of ESG integration.*

**User Input**: 
```
Show me examples from the SAM ESG Leaders Global Equity portfolio that demonstrate our ESG approach in practice. Include holdings with strong ESG scores and explain why they fit our criteria.
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Query ESG Leaders portfolio holdings

**Expected Response**:
- **Top ESG Holdings**: Highest-rated ESG holdings with grades
- **Sector Examples**: ESG leaders across different sectors
- **Selection Rationale**: Why these holdings exemplify ESG approach
- **ESG Score Distribution**: Overall portfolio ESG profile
- **Comparison**: How ESG focus differs from benchmark

**Talking Points**:
- **Evidence-Based**: Concrete portfolio examples support philosophy claims
- **ESG Integration Proof**: Shows ESG scores alongside positions
- **Differentiation**: Demonstrates how ESG focus affects portfolio composition

**Key Features Highlighted**: 
- **SAM_ANALYST_VIEW**: Complete portfolio data including ESG dimensions
- **Portfolio Evidence**: Real holdings support investment philosophy claims

##### Step 4: Comprehensive Response Summary

**Presenter Transition**:
> "I have all the pieces now—philosophy, policy, and evidence. Let me synthesise this into a comprehensive response that the client can review..."

*Reasoning: Prospective clients often need comprehensive answers for internal discussions. A well-structured synthesis supports their due diligence and decision-making.*

**User Input**: 
```
Synthesise a comprehensive response for the prospective client covering our ESG philosophy, specific policies, and portfolio evidence. Structure it clearly for their investment committee discussion.
```

**Tools Used**:
- Synthesis of previous queries

**Expected Response**:
- **Executive Summary**: SAM's ESG approach in brief
- **Philosophy Section**: Detailed integration approach
- **Policy Details**: Specific criteria and exclusions
- **Portfolio Evidence**: Examples demonstrating implementation
- **Differentiation**: How SAM's approach compares to alternatives
- **Next Steps**: Suggested follow-up actions

**Talking Points**:
- **Comprehensive Synthesis**: AI combines philosophy, policy, and evidence
- **Structured Output**: Clear markdown formatting for easy review
- **Sales Enablement**: Supports conversion of prospective clients

**Key Features Highlighted**: 
- **Multi-Source Synthesis**: Combines search and analytics results
- **Professional Formatting**: Creates well-structured markdown responses

##### Step 5: Generate PDF for Committee Review

**Presenter Transition**:
> "This is exactly what the prospect needs. Let me generate a professional PDF they can circulate to their investment committee..."

*Reasoning: Prospective clients need formal documentation for internal approval processes. A branded PDF demonstrates professionalism and supports their decision-making.*

**User Input**: 
```
Generate a professional PDF of this response document for the client's investment committee review
```

**Tools Used**:
- `pdf_generator` (Generic) - Generate branded PDF with `external_client` audience

**Expected Response**:
- **PDF Generation**: Professional branded PDF with Snowcrest logo
- **Client Committee Format**: External client styling with appropriate disclaimers
- **Download Link**: Presigned URL for immediate download
- **Professional Appearance**: Investment-grade document quality

**Talking Points**:
- **Due Diligence Ready**: Professional PDF suitable for committee circulation
- **Brand Excellence**: Snowcrest branding reinforces institutional quality
- **Conversion Support**: Professional documentation supports allocation decision

**Key Features Highlighted**: 
- **GENERATE_PDF_REPORT**: Branded PDF generation for client deliverables
- **Sales Enablement**: Professional materials that support client conversion
- **Complete Workflow**: From Q&A to committee-ready PDF in single session

#### Scenario Wrap-up

**Business Impact Summary**:
- **Response Quality**: Comprehensive, well-supported answers to client questions
- **Response Time**: Complex Q&A addressed in minutes instead of hours
- **Conversion Support**: Better-informed prospects more likely to convert with professional documentation
- **Consistency**: All relationship managers provide consistent philosophy messaging
- **Professional Deliverables**: Committee-ready PDFs accelerate allocation decisions

**Technical Differentiators**:
- **Three-Source Integration**: Philosophy + Policy + Portfolio data combined seamlessly
- **Due Diligence Ready**: Outputs suitable for client compliance review
- **Contextual Synthesis**: AI creates cohesive narrative from multiple sources
- **PDF Generation**: Professional branded documents for client circulation

---

### Sales Advisor - Comprehensive Client Briefing (All Tools)

#### Business Context Setup

**Persona**: James Mitchell, Client Relationship Manager at Snowcrest Asset Management  
**Business Challenge**: Major client briefings require comprehensive preparation combining performance analytics, professional templates, investment philosophy, and compliance requirements. Traditionally this requires coordination across multiple teams—performance reporting, marketing, investment, and compliance—taking days to assemble.  
**Value Proposition**: AI-powered comprehensive briefing preparation that orchestrates all four Sales Advisor tools to create complete, professional, compliant client presentations in a single workflow.

**Agent**: `sales_advisor`  
**Data Available**: Portfolio performance data, sales report templates, investment philosophy documents, compliance policies

#### Demo Flow

**Scene Setting**: James is preparing a comprehensive annual review briefing for SAM's largest institutional client invested in the Technology & Infrastructure portfolio. This requires performance analysis, professional formatting, investment philosophy integration, and full compliance review—a complete demonstration of all Sales Advisor capabilities.

##### Step 1: Performance Foundation
**User Input**: 
```
I need to prepare a comprehensive annual review briefing for our largest client's SAM Technology & Infrastructure portfolio. Start with full performance analysis including annual returns, quarterly breakdown, top holdings, and sector allocation.
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Complete performance analysis

**Expected Response**:
- **Annual Performance**: Full year returns vs benchmark
- **Quarterly Breakdown**: Quarter-by-quarter performance attribution
- **Top Holdings**: Largest positions with weights and returns
- **Sector Allocation**: Technology sector breakdown
- **Risk Metrics**: Volatility, tracking error, key risk indicators
- **Concentration Analysis**: Positions flagged above thresholds

**Talking Points**:
- **Comprehensive Analytics**: Complete performance picture for annual review
- **Multi-Period Analysis**: Annual and quarterly perspectives combined
- **Risk Integration**: Risk metrics alongside return data

**Key Features Highlighted**: 
- **SAM_ANALYST_VIEW**: Complete portfolio analytics for institutional reporting
- **Automated Analysis**: Complex multi-period analysis in seconds

##### Step 2: Professional Template Structure

**Presenter Transition**:
> "Now I have comprehensive performance data. For our largest client's annual review, this needs to be in our most professional format—the annual client presentation template with full executive structure..."

*Reasoning: Major client briefings require premium presentation quality. Template integration ensures consistent, professional formatting that reflects SAM's institutional standards.*

**User Input**: 
```
Format this into a professional annual client presentation using our executive briefing template with proper sections, charts placeholders, and SAM branding guidelines.
```

**Tools Used**:
- `search_sales_templates` (Cortex Search) - Executive briefing template

**Expected Response**:
- **Executive Structure**: Annual review presentation format
- **Section Organisation**: Performance, Attribution, Outlook, Philosophy sections
- **Chart Placeholders**: Recommended visualisations for each section
- **Branding Elements**: SAM visual identity and formatting standards
- **Appendix Structure**: Supporting data and disclosures organisation

**Talking Points**:
- **Executive Quality**: Premium template for major client relationship
- **Visual Guidance**: Chart recommendations for professional presentation
- **Brand Excellence**: Consistent institutional presentation standards

**Key Features Highlighted**: 
- **SAM_SALES_TEMPLATES**: Complete template library including executive formats
- **Presentation Intelligence**: AI adapts content to professional structures

##### Step 3: Investment Philosophy Integration

**Presenter Transition**:
> "The structure looks excellent. Now let me integrate our investment philosophy—particularly our technology innovation thesis and forward-looking views—to make this compelling, not just informative..."

*Reasoning: Annual reviews should reinforce the investment partnership, not just report numbers. Philosophy integration transforms reports into relationship-building communications.*

**User Input**: 
```
Integrate SAM's technology and innovation investment philosophy, including our forward-looking views on artificial intelligence and digital transformation themes.
```

**Tools Used**:
- `search_philosophy_docs` (Cortex Search) - Technology investment philosophy

**Expected Response**:
- **Technology Philosophy**: SAM's approach to technology investing
- **Innovation Themes**: AI, digital transformation, cloud computing views
- **Forward-Looking Perspective**: Outlook on technology sector opportunities
- **Portfolio Alignment**: How current holdings reflect these themes
- **Competitive Positioning**: SAM's differentiation in technology investing

**Talking Points**:
- **Thought Leadership**: Philosophy content positions SAM as experts
- **Forward Narrative**: Not just backward-looking performance, but future vision
- **Relationship Deepening**: Content that stimulates strategic conversation

**Key Features Highlighted**: 
- **SAM_PHILOSOPHY_DOCS**: Comprehensive investment philosophy library
- **Thematic Integration**: AI weaves philosophy into performance context

##### Step 4: Compliance and Regulatory Requirements

**Presenter Transition**:
> "We have compelling content with professional formatting. Before this goes to our largest client, it must pass our most rigorous compliance review. Let me add all required disclosures and fiduciary language..."

*Reasoning: Major client communications require comprehensive compliance review. For the largest client, this means full regulatory disclosure and fiduciary language.*

**User Input**: 
```
Add complete regulatory compliance including all required disclosures, performance disclaimers, risk warnings, and fiduciary language appropriate for our largest institutional relationship.
```

**Tools Used**:
- `search_policies` (Cortex Search) - Compliance and regulatory requirements

**Expected Response**:
- **Performance Disclaimers**: Standard and enhanced disclosure language
- **Risk Disclosures**: Comprehensive risk warning language
- **Fiduciary Standards**: Institutional-grade fiduciary language
- **Regulatory Compliance**: All required regulatory disclosures
- **Conflict Disclosures**: Any relevant conflict of interest statements

**Talking Points**:
- **Institutional Standards**: Compliance language for sophisticated clients
- **Regulatory Excellence**: Complete adherence to regulatory requirements
- **Fiduciary Care**: Demonstrates SAM's commitment to client protection

**Key Features Highlighted**: 
- **SAM_POLICY_DOCS**: Complete compliance and regulatory library
- **Institutional Compliance**: AI applies highest compliance standards

##### Step 5: Complete Client Briefing Document with PDF Generation

**Presenter Transition**:
> "All components are ready—performance, template, philosophy, compliance. Let me synthesise everything into the final, complete client briefing document and generate a professional PDF ready for delivery..."

*Reasoning: The final synthesis combines all four tool outputs into a cohesive, professional document that represents SAM's best capabilities, with PDF generation for formal client delivery.*

**User Input**: 
```
Create the complete annual review client briefing document synthesising all elements—performance analysis, executive formatting, investment philosophy, and full compliance—and generate a professional PDF ready for client delivery.
```

**Tools Used**:
- All 4 tools synthesis
- `pdf_generator` (Generic) - Generate branded PDF with `external_client` audience

**Expected Response**:
- **Executive Summary**: Key highlights and messages
- **Performance Section**: Complete annual performance review
- **Investment Outlook**: Philosophy-informed forward perspective
- **Compliance Section**: All required disclosures and warnings
- **Professional Format**: Executive presentation structure
- **PDF Generation**: Branded PDF with Snowcrest logo and client-appropriate formatting
- **Download Link**: Presigned URL for immediate client delivery

**Talking Points**:
- **Complete Orchestration**: All five Sales Advisor tools working together
- **Professional Excellence**: Institutional-quality client communication
- **Immediate Deliverable**: Branded PDF ready for client distribution
- **Efficiency**: What took days now completed in minutes with formal PDF output

**Key Features Highlighted**: 
- **Five-Tool Integration**: Complete demonstration of Sales Advisor capabilities including PDF generation
- **End-to-End Workflow**: From raw data to branded, client-ready PDF document
- **AI Orchestration**: Seamless combination of analytics, templates, philosophy, compliance, and PDF generation

#### Scenario Wrap-up

**Business Impact Summary**:
- **Time Savings**: Annual review preparation reduced from 2-3 days to under 30 minutes
- **Quality Consistency**: Institutional-grade output every time
- **Compliance Assurance**: Comprehensive regulatory compliance automated
- **Relationship Value**: Premium communications strengthen major client relationships
- **Professional Deliverables**: Branded PDF documents ready for immediate client distribution

**Technical Differentiators**:
- **Five-Tool Orchestration**: Complete demonstration of all Sales Advisor capabilities including PDF generation
- **End-to-End Automation**: From raw data to branded, compliant, client-ready PDF
- **Institutional Quality**: AI produces outputs matching internal team quality standards
- **Workflow Integration**: Single conversation replaces multi-team coordination with formal deliverable

---

### Sales Advisor - Client-Specific Reporting

#### Business Context Setup

**Persona**: James Mitchell, Client Relationship Manager at Snowcrest Asset Management  
**Business Challenge**: Preparing for quarterly client reviews requires gathering client-specific data including flow history, relationship tenure, and AUM trends—information that traditionally lives in separate CRM and accounting systems requiring manual consolidation.  
**Value Proposition**: AI-powered client-specific analytics that combines client relationship data with portfolio performance and flow history to prepare personalised client review materials in minutes.

**Agent**: `sales_advisor`  
**Data Available**: 75 institutional clients, 12 months flow history, client types, AUM data, portfolio performance

#### Demo Flow

**Scene Setting**: James is preparing for a quarterly review with Meridian Capital Partners, one of SAM's largest pension clients in North America. He needs to understand their recent flow activity, total relationship value, and prepare talking points for the meeting.

##### Step 1: Client Relationship Overview

**User Input**: 
```
Show me the complete relationship profile for Meridian Capital Partners including their AUM with SAM, client type, and relationship history
```

**Tools Used**:
- `client_analyzer` (Cortex Analyst) - Query SAM_EXECUTIVE_VIEW for client data

**Expected Response**:
- Client Name, Type (Pension), Region
- Total AUM with SAM
- Primary Contact / Relationship Manager
- Portfolios invested in
- Relationship tenure

**Talking Points**:
- Single source of truth for client relationship data
- Instant access to complete client profile

**Key Features Highlighted**: 
- SAM_EXECUTIVE_VIEW client dimension
- Relationship context for personalised communications

##### Step 2: Flow History Analysis

**Presenter Transition**:
> "Now I have the relationship overview. Let me look at their recent activity to understand if they've been adding or reducing their allocation..."

*Reasoning: Understanding recent flow activity is critical for quarterly review preparation—it shows whether the relationship is growing or at risk.*

**User Input**: 
```
What has been Meridian Capital Partners' flow activity over the past 12 months? Show me subscriptions and redemptions by quarter.
```

**Tools Used**:
- `client_analyzer` (Cortex Analyst) - Query flow history from FACT_CLIENT_FLOWS

**Expected Response**:
- Quarterly flow summary (subscriptions vs redemptions)
- Net flow trend (growing/declining)
- Largest individual flows with dates
- Flow by portfolio/strategy

**Talking Points**:
- Immediate visibility into client behaviour patterns
- Trend analysis without manual data gathering

**Key Features Highlighted**: 
- Client flow analytics
- Time-series analysis capabilities

##### Step 3: Portfolio Performance Context

**Presenter Transition**:
> "Their flows have been positive—they've been adding to their ESG allocation. Let me check the performance of the portfolios they're invested in to prepare talking points..."

*Reasoning: Connecting flow decisions to portfolio performance helps explain client behaviour and prepare for performance discussions.*

**User Input**: 
```
Show me the performance of the portfolios that Meridian Capital Partners is invested in, with sector allocation and top holdings
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Portfolio performance from SAM_ANALYST_VIEW

**Expected Response**:
- Performance summary for client's portfolios
- Sector allocation breakdown
- Top holdings with weights
- Benchmark comparison

**Talking Points**:
- Cross-tool integration for complete client picture
- Performance context for flow discussions

**Key Features Highlighted**: 
- Multi-tool orchestration (client_analyzer + quantitative_analyzer)
- Client-specific portfolio analysis

##### Step 4: Client Meeting Preparation Summary

**Presenter Transition**:
> "I have all the data I need. Let me create a meeting preparation summary that combines relationship context, flow history, and performance..."

*Reasoning: Synthesising all information into a meeting-ready document completes the preparation workflow.*

**User Input**: 
```
Create a quarterly client review preparation summary for Meridian Capital Partners including relationship overview, flow activity highlights, portfolio performance, and recommended talking points
```

**Tools Used**:
- Synthesis of client_analyzer and quantitative_analyzer results
- `search_sales_templates` (Cortex Search) - Client meeting template format

**Expected Response**:
- **Relationship Summary**: Client profile and relationship tenure
- **Flow Activity**: Net flows trend with key transactions
- **Performance Highlights**: Portfolio returns and attribution
- **Talking Points**: 3-5 key messages for the meeting
- **Follow-up Actions**: Recommended next steps

**Talking Points**:
- Complete meeting preparation in under 5 minutes
- Personalised client materials automatically generated

**Key Features Highlighted**: 
- Multi-source synthesis
- Professional document generation

#### Scenario Wrap-up

**Business Impact Summary**:
- **Preparation Time**: Client review prep reduced from 2+ hours to 10 minutes
- **Personalisation**: Client-specific data integrated into all communications
- **Relationship Intelligence**: Complete visibility into client behaviour and trends
- **Proactive Service**: Identify at-risk relationships through flow pattern analysis

**Technical Differentiators**:
- **Client Analytics Integration**: SAM_EXECUTIVE_VIEW provides unified client relationship data
- **Cross-View Orchestration**: Seamless combination of client data (SAM_EXECUTIVE_VIEW) with portfolio analytics (SAM_ANALYST_VIEW)
- **Flow Trend Analysis**: Time-series client flow analysis for relationship health monitoring
- **Personalised Synthesis**: AI creates client-specific materials from multiple data sources

---

### Sales Advisor - RFP Response Preparation

#### Business Context Setup

**Persona**: James Mitchell, Client Relationship Manager at Snowcrest Asset Management  
**Business Challenge**: Responding to institutional RFPs is time-intensive, requiring coordination across investment, operations, compliance, and client service teams to compile firm capabilities, track record, and team information. Traditional RFP responses take 2-3 weeks and consume significant senior resources.  
**Value Proposition**: AI-powered RFP response preparation that gathers firm capabilities, performance data, investment process details, and compliance information to accelerate RFP turnaround from weeks to days.

**Agent**: `sales_advisor`  
**Data Available**: Portfolio performance data, investment philosophy documents, sales templates (RFP template), compliance policies, product catalog

#### Demo Flow

**Scene Setting**: James received an RFP from a large pension fund seeking a Global ESG Equity mandate. The response is due in 10 days and he needs to prepare a comprehensive proposal.

##### Step 1: Firm Capabilities and Track Record

**User Input**: 
```
I need to prepare an RFP response for a Global ESG Equity mandate. Start by gathering our firm capabilities, ESG track record, and available performance history for the SAM ESG Leaders Global Equity strategy.
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Query ESG Leaders performance from SAM_ANALYST_VIEW
- `search_sales_templates` (Cortex Search) - Get RFP response template structure

**Expected Response**:
- **Firm Overview**: SAM capabilities and AUM
- **Strategy Performance**: ESG Leaders returns vs benchmark (QTD, YTD available; longer-term history requires supplemental data)
- **ESG Characteristics**: Portfolio ESG ratings and sustainability metrics
- **RFP Template Structure**: Recommended sections and format

**Note**: The semantic model provides QTD and YTD returns. For longer-term performance (1Y, 3Y, Since Inception), the agent will note data availability limitations—this is realistic as demo data is anchored to recent market data.

**Talking Points**:
- **Instant Access**: Performance data immediately available without manual compilation
- **Template Guidance**: AI provides RFP structure to ensure completeness
- **Compliance Ready**: Data formatted for institutional due diligence

**Key Features Highlighted**: 
- **SAM_ANALYST_VIEW**: Complete portfolio analytics for RFP evidence
- **SAM_SALES_TEMPLATES**: RFP response template with standard sections

##### Step 2: Investment Process and Philosophy

**Presenter Transition**:
> "We have the track record data. Now I need to articulate our investment process and ESG integration methodology—the 'how' behind our performance..."

*Reasoning: RFPs require detailed investment process descriptions. Philosophy documents provide the structured content needed for process sections.*

**User Input**: 
```
Provide our ESG investment process, integration methodology, and active ownership approach for the investment process section of the RFP.
```

**Tools Used**:
- `search_philosophy_docs` (Cortex Search) - Search ESG investment philosophy and process

**Expected Response**:
- **Investment Process**: Multi-stage ESG integration approach
- **ESG Methodology**: Proprietary ESG rating framework
- **Active Ownership**: Engagement and proxy voting approach
- **Exclusion Policy**: Industries and practices excluded
- **Integration Examples**: How ESG factors influence investment decisions

**Talking Points**:
- **Process Documentation**: AI retrieves structured investment process content
- **Differentiation**: Highlights SAM's unique ESG approach
- **Due Diligence Ready**: Content suitable for institutional evaluation

**Key Features Highlighted**: 
- **SAM_PHILOSOPHY_DOCS**: Comprehensive investment philosophy library
- **Contextual Retrieval**: AI finds relevant process content for RFP sections

##### Step 3: Compliance and Risk Management

**Presenter Transition**:
> "The investment process section is complete. Now I need compliance and risk management content to address operational due diligence requirements..."

*Reasoning: Institutional RFPs include extensive operational and compliance sections. Policy documents provide the required content.*

**User Input**: 
```
Gather our compliance framework, risk management policies, and regulatory disclosures for the operational due diligence section of the RFP.
```

**Tools Used**:
- `search_policies` (Cortex Search) - Get compliance and risk management policies

**Expected Response**:
- **Compliance Framework**: Regulatory registrations and compliance infrastructure
- **Risk Management**: Investment risk limits and monitoring approach
- **Concentration Policy**: Position and sector limit framework
- **Regulatory Disclosures**: Standard required disclosures
- **Conflict Management**: Conflict of interest policies

**Talking Points**:
- **Comprehensive Coverage**: All operational due diligence areas addressed
- **Policy Consistency**: Ensures RFP responses align with actual policies
- **Institutional Standards**: Content meets pension fund requirements

**Key Features Highlighted**: 
- **SAM_POLICY_DOCS**: Complete compliance and policy library
- **Operational DD Content**: Covers all standard RFP operational sections

##### Step 4: Complete RFP Response Draft

**Presenter Transition**:
> "I have all the components. Let me synthesise everything into a complete RFP response document following our approved template..."

*Reasoning: Synthesising all components into a cohesive response document demonstrates the complete RFP workflow.*

**User Input**: 
```
Create a complete RFP response draft for the Global ESG Equity mandate combining our track record, investment process, and compliance content in our standard RFP format.
```

**Tools Used**:
- Synthesis of previous queries
- `search_sales_templates` (Cortex Search) - RFP template for final formatting

**Expected Response**:
- **Executive Summary**: Key highlights and value proposition
- **Firm Overview Section**: Capabilities and track record
- **Investment Process Section**: ESG methodology and philosophy
- **Performance Section**: Returns and risk metrics
- **Operational Section**: Compliance and risk management
- **Team Section**: Key personnel placeholder
- **Fee Section**: Standard fee schedule format

**Talking Points**:
- **Complete Draft**: Comprehensive RFP response in single workflow
- **Template Compliant**: Follows institutional RFP standards
- **Review Ready**: Draft prepared for senior review and customisation

**Key Features Highlighted**: 
- **Multi-Source Synthesis**: Combines analytics, philosophy, and policy content
- **Professional Format**: Institutional-quality RFP response
- **Accelerated Timeline**: What took weeks now takes hours

#### Scenario Wrap-up

**Business Impact Summary**:
- **Time Savings**: RFP response preparation reduced from 2-3 weeks to 2-3 days
- **Consistency**: Standardised responses across all RFPs
- **Quality**: Comprehensive coverage of all RFP requirements
- **Win Rate**: Better-prepared proposals improve competitive positioning

**Technical Differentiators**:
- **Multi-Source Integration**: Combines performance data, philosophy, and policies seamlessly
- **Template Intelligence**: AI applies institutional RFP standards automatically
- **Due Diligence Ready**: Output meets pension fund evaluation requirements

---

### Sales Advisor - Client Onboarding Package

#### Business Context Setup

**Persona**: James Mitchell, Client Relationship Manager at Snowcrest Asset Management  
**Business Challenge**: New client onboarding requires creating welcome materials, establishing reporting preferences, introducing key contacts, and ensuring smooth operational setup. Traditional onboarding takes 4-6 weeks with multiple coordination touchpoints.  
**Value Proposition**: AI-powered onboarding package generation that creates comprehensive welcome materials, checklists, and setup documentation to accelerate client integration and demonstrate service excellence from day one.

**Agent**: `sales_advisor`  
**Data Available**: Client profile data, portfolio performance data, sales templates (onboarding welcome), investment philosophy documents

#### Demo Flow

**Scene Setting**: James just closed a new mandate with Midwest Community Foundation, a foundation client allocating $62 million to SAM ESG Leaders Global Equity. He needs to prepare their onboarding package.

##### Step 1: Client Profile and Portfolio Overview

**User Input**: 
```
I need to prepare an onboarding welcome package for our new client Midwest Community Foundation. They're investing in SAM ESG Leaders Global Equity. Start with their client profile and portfolio overview.
```

**Tools Used**:
- `client_analyzer` (Cortex Analyst) - Query new client profile from SAM_EXECUTIVE_VIEW
- `quantitative_analyzer` (Cortex Analyst) - Query ESG Leaders portfolio overview

**Expected Response**:
- **Client Profile**: Midwest Community Foundation, Foundation type, North America
- **Relationship Details**: Recent onboarding date, primary contact
- **Portfolio Overview**: SAM ESG Leaders strategy, performance, top holdings
- **ESG Characteristics**: Portfolio ESG ratings and sustainability metrics

**Talking Points**:
- **Unified View**: Client profile and portfolio data combined instantly
- **Relationship Context**: New client status identified for appropriate service level
- **ESG Focus**: Sustainability metrics highlighted for foundation client

**Key Features Highlighted**: 
- **SAM_EXECUTIVE_VIEW**: Client relationship data including new client status
- **Cross-View Integration**: Client and portfolio data combined seamlessly

##### Step 2: Welcome Package Structure

**Presenter Transition**:
> "Now I have the client and portfolio context. Let me retrieve our onboarding template to structure the welcome package appropriately..."

*Reasoning: Onboarding templates ensure consistent, professional welcome experiences for all new clients.*

**User Input**: 
```
Retrieve our client onboarding welcome template and customize it for Midwest Community Foundation as a foundation client.
```

**Tools Used**:
- `search_sales_templates` (Cortex Search) - Get client onboarding welcome template

**Expected Response**:
- **Welcome Letter**: Personalised welcome message structure
- **Key Contacts**: Relationship manager, portfolio manager, operations contacts
- **Onboarding Checklist**: Administrative, investment, and reporting setup items
- **First 90 Days Roadmap**: Week-by-week integration timeline
- **Reporting Preferences**: Available report types and frequencies

**Talking Points**:
- **Consistent Experience**: All clients receive professional onboarding
- **Clear Expectations**: Roadmap sets expectations for integration timeline
- **Self-Service Guidance**: Checklist empowers client to track progress

**Key Features Highlighted**: 
- **SAM_SALES_TEMPLATES**: Comprehensive onboarding template library
- **Client-Centric Design**: Materials focused on client experience

##### Step 3: Investment Philosophy Introduction

**Presenter Transition**:
> "The welcome structure is set. Let me add investment philosophy content to help them understand our ESG approach—critical for a foundation client with mission alignment needs..."

*Reasoning: Foundation clients often have values-based mandates. Philosophy content helps them understand alignment with their mission.*

**User Input**: 
```
Include our ESG investment philosophy and sustainable investing approach in the welcome package, emphasizing alignment with foundation values.
```

**Tools Used**:
- `search_philosophy_docs` (Cortex Search) - Get ESG investment philosophy

**Expected Response**:
- **ESG Philosophy**: SAM's approach to sustainable investing
- **Mission Alignment**: How ESG integration supports foundation values
- **Impact Reporting**: Available sustainability and impact metrics
- **Active Ownership**: Engagement approach and proxy voting policy
- **Exclusion Policy**: Industries excluded from portfolios

**Talking Points**:
- **Values Alignment**: Content demonstrates SAM-foundation mission fit
- **Transparency**: Clear articulation of ESG approach from day one
- **Reporting Expectations**: Sets foundation for sustainability reporting

**Key Features Highlighted**: 
- **SAM_PHILOSOPHY_DOCS**: Investment philosophy library with ESG focus
- **Client-Specific Messaging**: Content tailored for foundation audience

##### Step 4: Complete Onboarding Package

**Presenter Transition**:
> "I have all components ready. Let me synthesize the complete onboarding package for Midwest Community Foundation..."

*Reasoning: A complete, professional onboarding package demonstrates service excellence and accelerates client integration.*

**User Input**: 
```
Create the complete onboarding welcome package for Midwest Community Foundation combining their portfolio overview, welcome materials, and ESG philosophy content.
```

**Tools Used**:
- Synthesis of previous queries

**Expected Response**:
- **Welcome Letter**: Personalised welcome from relationship manager
- **Client Summary**: Profile, portfolio, and key contacts
- **Onboarding Checklist**: Complete setup tracking
- **90-Day Roadmap**: Integration timeline and milestones
- **Investment Philosophy**: ESG approach and mission alignment
- **Reporting Guide**: Available reports and preferences
- **Next Steps**: Immediate action items

**Talking Points**:
- **First Impression**: Professional package demonstrates service commitment
- **Complete Materials**: Everything client needs for successful integration
- **Efficiency**: Onboarding package created in minutes

**Key Features Highlighted**: 
- **Multi-Source Synthesis**: Combines client data, templates, and philosophy
- **Professional Presentation**: Institutional-quality onboarding materials
- **Accelerated Integration**: Faster time-to-full-service for new clients

#### Scenario Wrap-up

**Business Impact Summary**:
- **Time Savings**: Onboarding package preparation reduced from days to minutes
- **Consistency**: Professional experience for every new client
- **Client Satisfaction**: Comprehensive materials accelerate integration
- **Retention**: Strong start builds foundation for long-term relationship

**Technical Differentiators**:
- **Client-Portfolio Integration**: New client data combined with portfolio analytics
- **Template Customisation**: Onboarding materials adapted to client type
- **Mission Alignment**: Philosophy content matched to foundation values

---

### Sales Advisor - At-Risk Client Analysis

#### Business Context Setup

**Persona**: James Mitchell, Client Relationship Manager at Snowcrest Asset Management  
**Business Challenge**: Identifying clients at risk of redemption before they leave requires analyzing flow patterns, performance satisfaction, and relationship health. Traditional monitoring relies on delayed reporting and reactive responses after redemption notices are received.  
**Value Proposition**: AI-powered at-risk client identification that combines flow trend analysis, performance context, and retention strategies to enable proactive relationship management before clients decide to leave.

**Agent**: `sales_advisor`  
**Data Available**: Client flow history, portfolio performance data, sales templates (retention playbook), philosophy documents

#### Demo Flow

**Scene Setting**: James is reviewing his client book for Q4 planning and wants to identify any relationships showing signs of potential redemption risk.

##### Step 1: Client Flow Analysis

**User Input**: 
```
Analyze client flow patterns to identify any clients showing redemption trends or declining engagement over the past 6 months.
```

**Tools Used**:
- `client_analyzer` (Cortex Analyst) - Query client flow trends from SAM_EXECUTIVE_VIEW

**Expected Response**:
- **At-Risk Clients Identified**: Pacific Coast Pension Fund, Alpine University Endowment, Metropolitan Insurance Group
- **Flow Patterns**: Net redemptions over multiple consecutive months
- **Trend Severity**: Percentage of AUM redeemed, acceleration trends
- **Client Context**: Client type, relationship tenure, total AUM

**Talking Points**:
- **Early Detection**: AI identifies declining patterns before formal notice
- **Prioritised List**: Clients ranked by redemption risk severity
- **Actionable Intelligence**: Clear data for proactive outreach

**Key Features Highlighted**: 
- **SAM_EXECUTIVE_VIEW**: Client flow analytics with trend detection
- **Pattern Recognition**: AI identifies concerning flow sequences

##### Step 2: Performance Context

**Presenter Transition**:
> "I've identified several at-risk clients. Let me check if performance issues might be driving their redemptions..."

*Reasoning: Understanding performance context is essential for retention conversations. Poor relative performance often drives redemption decisions.*

**User Input**: 
```
Show me which portfolios Pacific Coast Pension Fund has invested in historically, including their complete flow history and any remaining positions. Then show the performance of those portfolios.
```

**Tools Used**:
- `client_analyzer` (Cortex Analyst) - Get Pacific Coast portfolio allocations and flow history (without positive-only filter for at-risk clients)
- `quantitative_analyzer` (Cortex Analyst) - Get portfolio performance

**Expected Response**:
- **Portfolio Flow History**: All portfolios Pacific Coast has invested in with gross inflows/outflows
- **Current Position Status**: Which portfolios still have positions vs fully redeemed
- **Performance Summary**: Returns vs benchmark for relevant portfolios
- **Attribution**: Key drivers of performance (positive and negative)

**Note**: At-risk clients may have zero or negative cumulative positions due to redemptions. The agent will show complete flow history rather than filtering to positive positions only.

**Talking Points**:
- **Context Understanding**: Performance data informs retention strategy
- **Honest Assessment**: Clear view of any performance challenges
- **Preparation**: Data for addressing performance questions

**Key Features Highlighted**: 
- **Cross-View Analysis**: Client flow history linked to portfolio performance
- **At-Risk Client Handling**: Shows full history including redeemed positions

##### Step 3: Retention Strategy

**Presenter Transition**:
> "I understand the performance context. Now let me pull our retention playbook for recommended engagement strategies..."

*Reasoning: Structured retention approaches increase success rates. Playbook content provides proven tactics for at-risk client engagement.*

**User Input**: 
```
Retrieve retention strategies and engagement tactics for an at-risk pension fund client concerned about performance.
```

**Tools Used**:
- `search_sales_templates` (Cortex Search) - Get client retention playbook

**Expected Response**:
- **Early Warning Response**: Recommended actions for at-risk indicators
- **Engagement Framework**: Conversation structure for retention discussions
- **Performance Discussion**: How to address underperformance concerns
- **Value Demonstration**: Ways to highlight non-performance value
- **Escalation Path**: When to involve senior leadership

**Talking Points**:
- **Structured Approach**: Proven framework for retention conversations
- **Tactical Guidance**: Specific actions to take with at-risk clients
- **Escalation Clarity**: When to bring in senior support

**Key Features Highlighted**: 
- **SAM_SALES_TEMPLATES**: Client retention playbook with tactical guidance
- **Best Practices**: Institutional retention strategies

##### Step 4: At-Risk Client Action Plan

**Presenter Transition**:
> "I have performance context and retention strategies. Let me create a specific action plan for Pacific Coast Pension Fund..."

*Reasoning: A specific action plan with timeline and talking points prepares relationship managers for effective retention engagement.*

**User Input**: 
```
Create an action plan for retaining Pacific Coast Pension Fund including talking points, value demonstration, and recommended next steps.
```

**Tools Used**:
- Synthesis of previous queries
- `search_philosophy_docs` (Cortex Search) - Get value proposition content

**Expected Response**:
- **Client Summary**: Pacific Coast profile and relationship history
- **Risk Assessment**: Flow trend analysis and severity
- **Performance Context**: Portfolio returns and benchmark comparison
- **Retention Strategy**: Recommended approach based on playbook
- **Talking Points**: Key messages for retention conversation
- **Action Timeline**: Recommended outreach schedule
- **Success Metrics**: How to measure retention progress

**Note on Value Proposition Content**: The `search_philosophy_docs` tool will return documents including "Snowcrest Asset Management — Brand Messaging Guidelines" which contains comprehensive value proposition content under the "Core Value Propositions" section, covering Innovation Leadership, ESG Excellence, and Performance Focus messaging.

**Talking Points**:
- **Proactive Management**: Act before formal redemption notice
- **Prepared Approach**: Specific strategy tailored to client situation
- **Relationship Investment**: Demonstrates commitment to partnership

**Key Features Highlighted**: 
- **Comprehensive Synthesis**: Flow data, performance, and strategy combined
- **Action-Oriented Output**: Clear next steps and timeline
- **Retention Focus**: Materials designed to preserve relationship

#### Scenario Wrap-up

**Business Impact Summary**:
- **Early Detection**: Identify at-risk clients 3-6 months earlier
- **Proactive Response**: Engage before clients make redemption decisions
- **Retention Rate**: Improved client retention through structured approach
- **AUM Preservation**: Reduced redemptions from better relationship management

**Technical Differentiators**:
- **Flow Pattern Analysis**: AI detects concerning redemption trends
- **Cross-View Intelligence**: Client flows linked to portfolio performance
- **Retention Integration**: Playbook strategies embedded in analysis

---

### Sales Advisor - Product Cross-Sell Opportunity

#### Business Context Setup

**Persona**: James Mitchell, Client Relationship Manager at Snowcrest Asset Management  
**Business Challenge**: Identifying cross-sell opportunities requires understanding each client's current allocations, investment preferences, and which additional SAM products might fit their needs. Traditional approaches rely on relationship manager intuition without systematic analysis.  
**Value Proposition**: AI-powered cross-sell identification that analyzes client profiles, current holdings, and product suitability to recommend additional SAM strategies that align with client objectives.

**Agent**: `sales_advisor`  
**Data Available**: Client profile and allocations, portfolio performance data, product catalog, investment philosophy documents

#### Demo Flow

**Scene Setting**: James is preparing for his quarterly business development review and wants to identify cross-sell opportunities across his client book.

##### Step 1: Client Portfolio Analysis

**User Input**: 
```
Show me clients with single-product relationships who might be good cross-sell opportunities. Include their current SAM product allocation and AUM.
```

**Tools Used**:
- `client_analyzer` (Cortex Analyst) - Query client allocations from SAM_EXECUTIVE_VIEW

**Expected Response**:
- **Single-Product Clients**: Clients investing in only one SAM strategy
- **Current Allocations**: Which SAM product each client holds
- **Client Profiles**: Client type (Pension, Endowment, Foundation, etc.)
- **AUM by Client**: Relationship size for prioritisation

**Note**: With updated data generation, approximately 20% of clients will have single-product relationships, making them natural cross-sell targets.

**Talking Points**:
- **Portfolio View**: Complete picture of client allocations
- **Opportunity Identification**: Single-product clients highlighted
- **Prioritisation**: Focus on high-AUM clients with expansion potential

**Key Features Highlighted**: 
- **SAM_EXECUTIVE_VIEW**: Client-product allocation data
- **Gap Analysis**: Identifies single-product relationships

##### Step 2: Product Catalog Review

**Presenter Transition**:
> "I can see several clients with single-product relationships. Let me review our product catalog to identify suitable cross-sell options..."

*Reasoning: Understanding the full product suite enables matching client needs to available strategies.*

**User Input**: 
```
Retrieve our SAM product catalog with strategy descriptions, target clients, and suitability criteria for cross-sell analysis.
```

**Tools Used**:
- `search_sales_templates` (Cortex Search) - Get product catalog

**Expected Response**:
- **Product Overview**: All SAM strategies with descriptions
- **Target Clients**: Ideal client profile for each product
- **Key Characteristics**: Risk profile, expected returns, investment approach
- **Cross-Sell Matrix**: Natural product combinations

**Talking Points**:
- **Complete Catalog**: Full view of SAM product suite
- **Suitability Guidance**: Clear criteria for product recommendations
- **Natural Pairs**: Identify complementary product combinations

**Key Features Highlighted**: 
- **SAM_SALES_TEMPLATES**: Comprehensive product catalog
- **Suitability Criteria**: Client matching guidance

##### Step 3: Client-Product Matching

**Presenter Transition**:
> "Now let me match specific clients to products that align with their investment objectives and existing allocations. I'll pick one of the single-product clients from our list..."

*Reasoning: Specific client-product recommendations require understanding both client profile and product fit. Use a client identified in Step 1.*

**User Input**: 
```
For [CLIENT_NAME from Step 1], who currently holds [THEIR CURRENT PRODUCT], recommend additional SAM products that would complement their portfolio and align with their [CLIENT_TYPE] objectives.
```

**Note**: Replace `[CLIENT_NAME from Step 1]` with an actual single-product client from Step 1 results, and `[THEIR CURRENT PRODUCT]` and `[CLIENT_TYPE]` with their actual data. This makes the demo dynamic and realistic.

**Tools Used**:
- `client_analyzer` (Cortex Analyst) - Get client profile and current holdings
- `search_philosophy_docs` (Cortex Search) - Get product philosophy alignment

**Expected Response**:
- **Current Allocation**: Client's single SAM product position
- **Client Profile**: Client type, region, investment focus
- **Recommended Products**: 2-3 complementary SAM strategies based on client type
  - For pension funds: Income or liability-matching strategies
  - For foundations: ESG/sustainable strategies
  - For family offices: Thematic or growth strategies
- **Alignment Rationale**: Why each product fits the client's objectives
- **AUM Opportunity**: Potential allocation size

**Talking Points**:
- **Tailored Recommendations**: Products matched to specific client needs
- **Strategic Rationale**: Clear explanation of product fit
- **Relationship Deepening**: Cross-sell strengthens client partnership

**Key Features Highlighted**: 
- **Client-Product Matching**: AI identifies suitable additional products
- **Philosophy Alignment**: Recommendations grounded in investment approach

##### Step 4: Cross-Sell Action Plan

**Presenter Transition**:
> "I have recommendations for this client. Let me create a complete cross-sell proposal..."

*Reasoning: A structured proposal with messaging and next steps prepares relationship managers for effective cross-sell conversations.*

**User Input**: 
```
Create a cross-sell proposal for [CLIENT_NAME from Step 1] with product recommendations, key messaging, and suggested next steps.
```

**Note**: Use the same client from Step 3 to maintain continuity.

**Tools Used**:
- Synthesis of previous queries

**Expected Response**:
- **Client Summary**: Meridian relationship overview
- **Current Holdings**: Existing SAM allocation
- **Recommended Products**: SAM Renewable & Climate, SAM Multi-Asset Income
- **Value Proposition**: Benefits of each recommendation
- **Key Messages**: Talking points for client conversation
- **Next Steps**: Proposed meeting agenda and timeline

**Talking Points**:
- **Prepared Approach**: Complete proposal for client conversation
- **Value-Led Messaging**: Focus on client benefits
- **Relationship Growth**: Cross-sell as partnership deepening

**Key Features Highlighted**: 
- **Comprehensive Proposal**: Complete cross-sell materials
- **Action-Oriented**: Clear next steps and timeline

#### Scenario Wrap-up

**Business Impact Summary**:
- **Revenue Growth**: Increased AUM through existing relationships
- **Relationship Depth**: Multi-product clients have higher retention
- **Efficiency**: Systematic identification vs. ad-hoc intuition
- **Client Value**: Better-matched portfolios to client objectives

**Technical Differentiators**:
- **Client-Product Analysis**: AI identifies cross-sell opportunities systematically
- **Suitability Matching**: Recommendations aligned to client profiles
- **Proposal Automation**: Complete cross-sell materials generated automatically

---

### Sales Advisor - Client Segmentation and Prioritisation

#### Business Context Setup

**Persona**: James Mitchell, Client Relationship Manager at Snowcrest Asset Management  
**Business Challenge**: Relationship managers serve diverse client books but have limited time. Determining which clients to prioritise for outreach, which need attention, and how to allocate time effectively requires systematic analysis of client value, engagement, and relationship health.  
**Value Proposition**: AI-powered client segmentation that analyzes AUM, flow trends, relationship tenure, and engagement patterns to help relationship managers prioritise their time and focus on highest-impact activities.

**Agent**: `sales_advisor`  
**Data Available**: Client profile data, client flow history, portfolio allocations

#### Demo Flow

**Scene Setting**: James is planning his Q1 client engagement calendar and wants to prioritise his client outreach based on relationship value and health.

##### Step 1: Client Book Overview

**User Input**: 
```
Give me an overview of my client book segmented by AUM tier and client type, including total relationship value.
```

**Tools Used**:
- `client_analyzer` (Cortex Analyst) - Query client book from SAM_EXECUTIVE_VIEW

**Expected Response**:
- **Total Clients**: Number of institutional clients
- **Total AUM**: Aggregate assets under management
- **AUM Tiers**: Segmentation by size (>$200M, $100-200M, <$100M)
- **Client Types**: Distribution by type (Pension, Endowment, Foundation, etc.)
- **Regional Distribution**: Geographic breakdown

**Talking Points**:
- **Complete View**: Full client book at a glance
- **Segmentation**: Clear tiers for prioritisation
- **Balance Assessment**: Distribution across segments

**Key Features Highlighted**: 
- **SAM_EXECUTIVE_VIEW**: Comprehensive client analytics
- **Segmentation Capability**: Multiple dimensions of analysis

##### Step 2: Relationship Health Analysis

**Presenter Transition**:
> "I have the AUM view. Now let me analyze relationship health based on flow trends and engagement patterns..."

*Reasoning: AUM alone doesn't indicate relationship health. Flow trends reveal which relationships are growing, stable, or declining.*

**User Input**: 
```
Analyze relationship health across my client book based on flow trends over the past 12 months. Identify growing, stable, and declining relationships.
```

**Tools Used**:
- `client_analyzer` (Cortex Analyst) - Query flow trends from SAM_EXECUTIVE_VIEW

**Expected Response**:
- **Growing Relationships**: Clients with net positive flows
- **Stable Relationships**: Clients with neutral flow patterns
- **Declining Relationships**: Clients with net redemptions
- **Flow Metrics**: Net flows by client with trend direction
- **At-Risk Alerts**: Clients requiring immediate attention

**Talking Points**:
- **Health Assessment**: Clear view of relationship trajectories
- **Priority Identification**: Declining relationships flagged for attention
- **Growth Recognition**: Identify momentum for expansion opportunities

**Key Features Highlighted**: 
- **Flow Trend Analysis**: 12-month pattern recognition
- **Health Categorisation**: Automatic relationship health scoring

##### Step 3: Prioritised Client List

**Presenter Transition**:
> "Now I can see relationship health. Let me create a prioritised client list combining AUM value and relationship health for next quarter planning..."

*Reasoning: Effective prioritisation balances client value (AUM) with relationship health (flow trends) and opportunity (growth potential).*

**User Input**: 
```
Create a prioritised client engagement list for the upcoming quarter combining AUM value and relationship health, with recommended action for each segment.
```

**Tools Used**:
- Synthesis of previous queries

**Expected Response**:
- **Priority 1 - Protect**: High-AUM declining relationships (immediate attention)
- **Priority 2 - Grow**: High-AUM growing relationships (expansion opportunity)
- **Priority 3 - Develop**: Mid-AUM stable relationships (engagement opportunity)
- **Priority 4 - Monitor**: Lower-AUM stable relationships (standard service)
- **Recommended Actions**: Specific engagement approach for each segment
- **Time Allocation**: Suggested focus percentage by segment

**Talking Points**:
- **Strategic Prioritisation**: Data-driven client focus
- **Action Guidance**: Clear recommendations for each segment
- **Time Optimisation**: Maximise impact of limited time

**Key Features Highlighted**: 
- **Multi-Factor Segmentation**: AUM + Health combined scoring
- **Action-Oriented Output**: Specific recommendations by segment
- **Planning Ready**: Directly usable for calendar planning

#### Scenario Wrap-up

**Business Impact Summary**:
- **Time Optimisation**: Focus on highest-impact client activities
- **Risk Reduction**: At-risk clients identified for proactive management
- **Growth Capture**: Growing relationships prioritised for expansion
- **Portfolio Management**: Balanced attention across client book

**Technical Differentiators**:
- **Multi-Dimensional Segmentation**: AUM, flows, tenure, and type combined
- **Relationship Health Scoring**: Automatic health categorisation
- **Actionable Prioritisation**: Clear recommendations for each segment

---

### Sales Advisor - Complete Client Intelligence (Catch-All)

#### Business Context Setup

**Persona**: James Mitchell, Client Relationship Manager at Snowcrest Asset Management  
**Business Challenge**: Relationship managers sometimes need a complete client intelligence package with a single request when preparing for urgent client calls—requiring the AI to autonomously orchestrate all available tools including client analytics.  
**Value Proposition**: The Sales Advisor demonstrates complete autonomous orchestration by selecting and sequencing all five tools from a single comprehensive question, producing a client-ready document with relationship context.

**Agent**: `sales_advisor`  
**Data Available**: Portfolio performance data, client flow history, sales report templates, investment philosophy documents, compliance policies

#### Demo Flow

**Scene Setting**: James has 5 minutes before an unexpected call from a key pension client and needs complete preparation immediately.

##### Step 1: Complete Client Intelligence (All Tools)

**User Input**: 
```
Prepare complete meeting materials for Meridian Capital Partners including their relationship profile and AUM, recent flow activity and trends, performance of their invested portfolios with holdings and sector allocation, proper report formatting from our templates, investment philosophy context for their allocation, and relevant policy information for any questions they might have.
```

**Tools Used**:
- `client_analyzer` (Cortex Analyst) - Client relationship and flow data
- `quantitative_analyzer` (Cortex Analyst) - Portfolio performance and holdings
- `search_sales_templates` (Cortex Search) - Report template structure
- `search_philosophy_docs` (Cortex Search) - Investment philosophy
- `search_policies` (Cortex Search) - Policy information

**Expected Response**:
- **Client Profile**: Relationship overview, AUM, client type, tenure
- **Flow Analysis**: Recent subscriptions/redemptions, net flow trend
- **Performance Summary**: Portfolio returns, sector allocation, top holdings
- **Professional Format**: Template-compliant structure with proper sections
- **Philosophy Integration**: ESG and investment approach messaging
- **Policy Context**: Relevant compliance and mandate information
- **Meeting Ready Document**: Complete package for immediate client engagement

**Note on Sector Allocation**: When the agent shows sector allocation, weights are summed across all holdings in that sector. For example, if a portfolio has 5 Technology holdings each at 8%, the Technology sector allocation would show 40%. Individual position weights always sum to 100% per portfolio; sector aggregations can exceed 100% if presented as cumulative sector totals rather than percentages.

**Talking Points**:
- **Five-Tool Orchestration**: AI independently selects and sequences all Sales Advisor tools
- **Single-Query Capability**: Complete client intelligence from one comprehensive question
- **Relationship-Aware**: Output includes client-specific context and history

**Key Features Highlighted**: 
- **Multi-Tool AI Orchestration**: Agent autonomously determines tool sequence and synthesis
- **Client + Portfolio Integration**: Relationship data merged with performance analytics
- **Production Ready**: Output quality matches manual multi-team coordination

#### Scenario Wrap-up

**Business Impact Summary**:
- **Emergency Response**: Complete client packages available in under 2 minutes
- **Relationship Context**: Client-specific data automatically incorporated
- **Quality Assurance**: AI maintains institutional standards with personalisation

**Technical Differentiators**:
- **Five-Tool Integration**: Demonstrates full enhanced Sales Advisor capability
- **Cross-View Orchestration**: SAM_EXECUTIVE_VIEW + SAM_ANALYST_VIEW in single query
- **Autonomous Orchestration**: True AI agent capability for client relationship management

---

## Client-Specific Analytics

### DIM_CLIENT Integration Complete

The Sales Advisor has been enhanced with comprehensive client analytics capabilities:

**Available Scenarios**:
- **Client-Specific Reporting**: Flow history and relationship analytics
- **At-Risk Client Analysis**: Identify and retain declining relationships
- **Product Cross-Sell Opportunity**: Recommend additional SAM products
- **Client Segmentation and Prioritisation**: Optimise relationship manager time

**Key Tools**:
- `client_analyzer` tool using SAM_EXECUTIVE_VIEW
- Client relationship profiles and flow history
- At-risk client identification with redemption pattern detection
- Cross-view orchestration with portfolio analytics

**New Demo Clients**:
- **At-Risk Clients**: Pacific Coast Pension Fund, Alpine University Endowment, Metropolitan Insurance Group (declining flow patterns)
- **New Clients**: Midwest Community Foundation, Nordic Heritage Family Office (onboarding scenarios)

See individual scenarios above for detailed demo flows.

