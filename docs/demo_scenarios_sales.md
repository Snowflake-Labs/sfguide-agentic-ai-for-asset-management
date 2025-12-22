# SAM Demo - Sales Scenarios

Complete demo scenarios for Sales and Client Relationship Management role with step-by-step conversations, expected responses, and data flows.

---

## Sales Advisor

### Sales Advisor - Quarterly Client Presentation

#### Business Context Setup

**Persona**: Rebecca, Client Relationship Manager at Snowcrest Asset Management  
**Business Challenge**: Client relationship managers need to prepare professional quarterly client presentations that retrieve performance data with benchmark comparisons, follow approved report templates for consistent structure and branding, integrate investment philosophy messaging for differentiation, and include required regulatory disclaimers for compliance. Traditional client reporting requires hours of manual data extraction, Excel formatting, PowerPoint assembly, philosophy document review for messaging, and compliance review for disclaimers—often resulting in inconsistent formatting, missing required sections, and delayed delivery that impacts client satisfaction.  
**Value Proposition**: AI-powered comprehensive client reporting that seamlessly integrates performance analytics, approved template structures, investment philosophy integration, and compliance disclosures—delivering professional, brand-consistent, regulation-compliant client presentations in minutes instead of hours.

**Agent**: `sales_advisor`  
**Data Available**: Portfolio performance across 10 strategies with benchmark data, 15 approved client report templates, investment philosophy documents, compliance disclosure requirements

#### Demo Flow

**Scene Setting**: Rebecca needs to prepare the latest quarterly client presentation for SAM ESG Leaders Global Equity portfolio ahead of next week's client review meetings. Clients expect comprehensive performance analysis versus benchmark, top holdings review, ESG metrics that demonstrate the strategy's sustainability focus, market outlook commentary aligned with SAM's investment philosophy, and all required regulatory disclosures. Rebecca needs to extract the most recent quarter's performance data, follow the approved quarterly report template structure, integrate SAM's ESG investment philosophy for differentiated messaging, and ensure all regulatory disclaimers are included—all within today to allow time for relationship manager review and printing before client meetings begin Monday.

##### Step 1: Comprehensive Client Report Generation
**User Input**: 
```
I need to prepare a quarterly client presentation for our SAM ESG Leaders Global Equity portfolio. Can you:
1. Get the most recent quarter's performance data including portfolio returns vs benchmark, top holdings, sector allocation, and ESG metrics
2. Retrieve our quarterly client report template to follow the approved structure and formatting
3. Find our ESG investment philosophy documentation to integrate our differentiated approach and sustainable development beliefs
4. Get the required regulatory disclaimers and risk warnings from compliance policies
5. Generate a professional client-ready quarterly report that combines performance data, investment philosophy, and compliance disclosures in the approved template format
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Extract Q4 performance data and portfolio analytics
- `search_sales_templates` (Cortex Search) - Retrieve quarterly client report template
- `search_philosophy_docs` (Cortex Search) - Find ESG investment philosophy messaging
- `search_policy_docs` (Cortex Search) - Get regulatory disclaimers and risk warnings

**Expected Response**:
- **Performance Data Retrieved**:
  - Quarterly and annual returns vs benchmark with relative performance
  - Performance attribution by factor (sector allocation, stock selection, currency)
    | Data Type | Description |
    |-----------|-------------|
    | Returns | Portfolio vs benchmark returns by period |
    | Attribution | Factor contributions to relative performance |
    | Holdings | Top positions with weights and ESG ratings |
    | Allocation | Sector and geographic breakdown vs benchmark |
  - ESG metrics comparison (ratings, carbon intensity, controversies)
  - Portfolio characteristics (holdings count, active share, turnover)

- **Template Retrieved**:
  - Approved quarterly report template structure with required sections
  - Formatting guidelines (fonts, colours, chart types)
  - ESG-specific section requirements

- **Philosophy Documents Retrieved**:
  - Core ESG investment philosophy messaging
  - ESG integration approach (exclusions, screening, engagement)
  - Differentiation messaging vs competitors

- **Compliance Disclosures Retrieved**:
  - Mandatory regulatory disclaimers (past performance, risk warnings)
  - ESG methodology disclosures
  - Benchmark and regulatory status statements

- **Generated Report**:
  - Professional quarterly client report combining all retrieved elements
  - Executive summary with performance highlights and ESG leadership
  - Detailed sections following template structure
  - All required regulatory disclosures included

**Talking Points**:
- **Comprehensive Client Intelligence**: Single query orchestrates 4 tools across performance data, report templates, philosophy documents, and compliance requirements
- **Brand Consistency**: Approved template structure ensures consistent formatting, messaging, and professional presentation across all client communications
- **Philosophy Integration**: SAM's differentiated ESG investment approach naturally woven throughout report for client education and retention
- **Compliance Automation**: All required regulatory disclaimers, risk warnings, and fiduciary disclosures automatically included per FCA requirements
- **Speed to Client**: Professional quarterly report generated in under 5 minutes vs 2-3 hours manual preparation

**Key Features Highlighted**: 
- **Portfolio Analytics**: Cortex Analyst extracts comprehensive Q4 performance, holdings, sector allocation, and ESG metrics from portfolio database
- **Template Intelligence**: Cortex Search retrieves approved quarterly report structure ensuring brand consistency and required sections
- **Philosophy Integration**: Investment philosophy messaging automatically incorporated for differentiated positioning vs competitors
- **Compliance Automation**: Regulatory disclaimers from policy documents ensure FCA compliance and fiduciary standards
- **Professional Formatting**: Template guidelines (fonts, colors, charts, tables) applied for institutional-quality client deliverable
- **ESG Differentiation**: Superior sustainability metrics (AA vs A rating, 58% carbon reduction) clearly presented to demonstrate strategy value proposition

#### Scenario Wrap-up

**Business Impact Summary**:
- **Preparation Speed**: Quarterly client report generation reduced from hours to minutes
- **Brand Consistency**: Template-driven approach ensures professional formatting and messaging consistency across all clients
- **Client Education**: Philosophy integration in every report strengthens client understanding of SAM's differentiated approach
- **Compliance Efficiency**: Automated regulatory disclosure inclusion eliminates compliance review cycles and approval delays

**Technical Differentiators**:
- **Multi-Source Client Intelligence**: Integration of portfolio analytics, approved templates, philosophy documents, and compliance requirements in unified workflow
- **Template-Driven Consistency**: Approved formatting, structure, and branding guidelines automatically applied for professional deliverables
- **Philosophy-Aware Messaging**: Investment beliefs and differentiated approach naturally integrated without appearing promotional
- **Compliance-by-Design**: FCA-required disclaimers, risk warnings, and fiduciary language automatically included per regulatory standards
- **ESG Metrics Integration**: Sophisticated sustainability analytics (carbon intensity, controversy tracking, SDG alignment) presented in client-friendly format
- **Professional Report Generation**: Institutional-quality quarterly reports suitable for immediate client distribution without manual formatting

---

### Sales Advisor - Complete Client Package (Catch-All)

#### Business Context Setup

**Persona**: Rebecca, Client Relationship Manager at Snowcrest Asset Management  
**Business Challenge**: Relationship managers sometimes need a complete client package with a single request when preparing for urgent client meetings or responding to unexpected calls—requiring the AI to autonomously orchestrate all Sales Advisor tools to deliver comprehensive client intelligence.  
**Value Proposition**: The Sales Advisor demonstrates complete autonomous orchestration by selecting and sequencing all tools from a single comprehensive question, delivering a client-ready package without step-by-step guidance.

**Agent**: `sales_advisor`  
**Data Available**: Portfolio performance across 10 strategies, 75 institutional clients with flow history, 15 approved client report templates, investment philosophy documents, compliance policies

#### Demo Flow

**Scene Setting**: Rebecca has 10 minutes before an unexpected call from a key client who wants a complete update on their relationship with SAM. There's no time for multi-step conversations.

##### Step 1: Complete Client Package (All Tools)

**User Input**: 
```
Prepare complete meeting materials for [CLIENT NAME] including their relationship profile with AUM and investment history, recent flow activity and trends, performance of their invested portfolios with holdings and sector allocation, proper report formatting from our approved templates, investment philosophy context for their allocation, and relevant compliance disclosures and policy information for any questions they might have.
```

**Note**: Replace `[CLIENT NAME]` with any client name from the database (e.g., "Meridian Capital Partners", "Pacific Coast Pension Fund", "Midwest Community Foundation").

**Tools Used**:
- `client_analyzer` (Cortex Analyst) - Client relationship and flow data
- `quantitative_analyzer` (Cortex Analyst) - Portfolio performance and holdings
- `search_sales_templates` (Cortex Search) - Report template structure
- `search_philosophy_docs` (Cortex Search) - Investment philosophy
- `search_policies` (Cortex Search) - Compliance disclosures and policies

**Expected Response**:
- **Client Profile**: Relationship overview, AUM, client type, tenure
- **Flow Analysis**: Recent subscriptions/redemptions, net flow trend
- **Performance Summary**: Portfolio returns, sector allocation, top holdings
- **Professional Format**: Template-compliant structure with proper sections
- **Philosophy Integration**: ESG and investment approach messaging
- **Policy Context**: Relevant compliance and regulatory disclosures
- **Meeting Ready Document**: Complete package for immediate client engagement

**Talking Points**:
- **Five-Tool Orchestration**: AI independently selects and sequences all Sales Advisor tools
- **Single-Query Capability**: Complete client package from one comprehensive question
- **Relationship-Aware**: Output includes client-specific context and history
- **Compliance Integrated**: Required regulatory disclosures automatically included

**Key Features Highlighted**: 
- **Multi-Tool AI Orchestration**: Agent autonomously determines tool sequence and synthesis
- **Client + Portfolio Integration**: Relationship data merged with performance analytics
- **Template Compliance**: Professional formatting following approved guidelines
- **Production Ready**: Output quality matches multi-team coordination

#### Scenario Wrap-up

**Business Impact Summary**:
- **Emergency Response**: Complete client packages available in under 5 minutes
- **Relationship Context**: Client-specific data automatically incorporated
- **Quality Assurance**: AI maintains institutional standards with personalisation
- **Compliance Coverage**: Regulatory disclosures included without manual review

**Technical Differentiators**:
- **Five-Tool Integration**: Demonstrates full Sales Advisor capability in single query
- **Cross-View Orchestration**: Client data + portfolio analytics in single response
- **Relationship Intelligence**: Personalised output based on client profile and history
- **Autonomous Operation**: True AI agent capability for client relationship management

