# SAM Demo - Client Relations Scenarios

Complete demo scenarios for Client Relations role with step-by-step conversations, expected responses, and data flows.

---

## Client Relations  

### Sales Advisor - Client Reporting & Template Formatting

#### Business Context Setup

**Persona**: James Mitchell, Client Relationship Manager at Snowcrest Asset Management  
**Business Challenge**: Client relationship managers need to produce professional, compliant, and compelling client reports that integrate performance data with approved messaging templates and investment philosophy. Traditional processes require manual data gathering, template formatting, compliance review, and brand alignment, consuming significant time and introducing formatting inconsistencies.  
**Value Proposition**: AI-powered client reporting that automatically combines portfolio analytics with approved templates, investment philosophy, and compliance language to generate professional, relationship-building client communications in minutes.

**Agent**: `sales_advisor`  
**Data Available**: Portfolio performance data, sales report templates, investment philosophy documents, compliance policies, brand messaging guidelines

#### Demo Flow

**Scene Setting**: James needs to prepare a monthly client report for a key institutional client with their SAM Technology & Infrastructure portfolio, ensuring professional presentation with proper compliance language and brand messaging.

##### Step 1: Portfolio Performance Foundation
**User Input**: 
```
Generate a client report for the SAM Technology & Infrastructure portfolio showing quarterly performance, top holdings, and sector allocation
```

**Tools Used**:
- `quantitative_analyzer` (Cortex Analyst) - Query performance, holdings, and sector data from SAM_ANALYST_VIEW

**Expected Response**:
- **Performance Summary**: Quarterly returns vs benchmark with multiple time periods
- **Top Holdings Table**: Largest positions with weights and contribution to performance
- **Sector Allocation**: Technology sector breakdown with allocation percentages
- **Performance Attribution**: Key contributors and detractors to portfolio performance
- **Concentration Warnings**: Flag any positions >6.5% with "⚠️ CONCENTRATION WARNING"
- **Professional Structure**: Executive summary format with clear data presentation

**Talking Points**:
- **Comprehensive Analytics**: AI instantly gathers all required portfolio data for client reporting
- **Professional Formatting**: Automatically structures data in client-appropriate format
- **Risk Highlighting**: Proactive flagging of concentration risks for client transparency

**Key Features Highlighted**: 
- **SAM_ANALYST_VIEW**: Complete portfolio analytics for client reporting foundation
- **Automated Formatting**: AI structures complex portfolio data for client presentation
- **Risk Management**: Automatic concentration warning and risk disclosure

##### Step 2: Template Integration and Professional Formatting
**User Input**: 
```
Format this into a professional monthly client report using our approved template structure with proper sections and branding
```

**Tools Used**:
- `search_sales_templates` (Cortex Search) - Get "monthly client report template structure branding"

**Expected Response**:
- **Template Structure**: Monthly Client Report format with standardised sections
- **Executive Summary**: Key performance highlights and market commentary section
- **Performance Analysis**: Detailed returns analysis with benchmark comparison
- **Holdings Overview**: Portfolio composition and changes section
- **Market Commentary**: Template-guided market outlook section
- **Professional Layout**: Consistent formatting with SAM branding elements
- **Section Headers**: Clear, template-compliant section organisation

**Talking Points**:
- **Template Compliance**: AI automatically applies approved report templates for consistency
- **Brand Standards**: Ensures all client communications follow SAM brand guidelines
- **Professional Presentation**: Client-ready formatting that enhances relationship value

**Key Features Highlighted**: 
- **SAM_SALES_TEMPLATES**: Comprehensive template library for consistent client communications
- **Automated Formatting**: AI applies professional structure and branding consistently
- **Template Intelligence**: Smart adaptation of content to template requirements

##### Step 3: Investment Philosophy and Brand Integration
**User Input**: 
```
Integrate our ESG investment philosophy and technology innovation messaging to align the report with SAM's strategic positioning
```

**Tools Used**:
- `search_philosophy_docs` (Cortex Search) - Search "ESG investment philosophy technology innovation approach"
- `search_sales_templates` (Cortex Search) - Get branded messaging guidelines

**Expected Response**:
- **ESG Integration**: SAM's sustainable investment approach woven into performance narrative
- **Technology Focus**: Innovation leadership messaging aligned with technology portfolio theme
- **Investment Philosophy**: Core beliefs about ESG and technology investing naturally integrated
- **Brand Messaging**: Competitive differentiators and unique capabilities highlighted
- **Strategic Positioning**: SAM's forward-thinking, technology-enhanced approach emphasised
- **Value Proposition**: Clear articulation of why SAM's approach benefits clients

**Talking Points**:
- **Philosophy Alignment**: Seamlessly integrates SAM's investment beliefs into client communications
- **Brand Consistency**: Ensures all client touchpoints reinforce strategic positioning
- **Relationship Building**: Enhances client understanding of SAM's unique value proposition

**Key Features Highlighted**: 
- **SAM_PHILOSOPHY_DOCS**: Comprehensive investment philosophy and brand messaging library
- **Natural Integration**: AI weaves philosophy into performance narrative without appearing promotional
- **Strategic Messaging**: Consistent reinforcement of SAM's competitive differentiators

##### Step 4: Compliance Review and Final Document
**User Input**: 
```
Complete the compliance review by adding all required regulatory disclosures, risk warnings, and fiduciary language for final client delivery
```

**Tools Used**:
- `search_policies` (Cortex Search) - Get "client communication compliance regulatory disclosure requirements"
- `search_sales_templates` (Cortex Search) - Get disclaimer and risk warning templates

**Expected Response**:
- **Regulatory Disclosures**: All mandatory disclaimers and risk warnings included
- **Performance Disclaimers**: "Past performance does not guarantee future results" and appropriate caveats
- **Fiduciary Language**: Professional standard disclaimers for investment advice
- **Risk Warnings**: Market risk, concentration risk, and investment limitation disclosures
- **Compliance Standards**: Full regulatory compliance for client communication
- **Final Document**: Complete, compliance-ready client report for immediate delivery

**Talking Points**:
- **Regulatory Compliance**: AI ensures all client communications meet regulatory standards
- **Risk Management**: Comprehensive risk disclosure protects both client and firm
- **Fiduciary Excellence**: Professional-grade compliance language maintains highest standards

**Key Features Highlighted**: 
- **SAM_POLICY_DOCS**: Complete compliance manual and regulatory requirements library
- **Compliance Automation**: AI automatically includes all required disclosures and warnings
- **Professional Standards**: Ensures client communications meet institutional investment standards

#### Scenario Wrap-up

**Business Impact Summary**:
- **Productivity Gains**: Client report generation reduced from hours to minutes, enabling more client interaction time
- **Consistency Assurance**: Automated template and brand compliance ensures professional standard across all client communications
- **Compliance Excellence**: Comprehensive regulatory disclosure automation reduces compliance risk and review time
- **Relationship Enhancement**: Professional, compelling reports strengthen client relationships and demonstrate institutional capabilities

**Technical Differentiators**:
- **Multi-Source Integration**: Seamlessly combines portfolio data, templates, philosophy, and compliance requirements in single workflow
- **Template Intelligence**: AI-powered formatting that adapts content to professional report structures while maintaining brand consistency
- **Compliance Automation**: Comprehensive regulatory disclosure integration ensures client communications meet institutional standards
- **Brand Integration**: Natural weaving of investment philosophy and strategic messaging into performance narratives

---

## Future Enhancement: Client-Specific Analytics

### DIM_CLIENT Now Available

The Executive Copilot implementation has introduced new client data tables that can enhance Sales Advisor capabilities:

**New Data Available**:
- `DIM_CLIENT`: 75 institutional client entities with client type, region, AUM, and relationship history
- `FACT_CLIENT_FLOWS`: 12 months of client-level subscription/redemption data
- `SAM_EXECUTIVE_VIEW`: Semantic view for client analytics queries

**Potential Sales Advisor Enhancements**:
These new tables enable client-specific reporting capabilities:

```
"Show me the flow history for [Client Name] to prepare for our quarterly review"
"Which clients in the pension segment have increased allocations this year?"
"Prepare a client-specific report for [Client Name] including their flow history"
"What's the relationship tenure and AUM trend for our top 10 clients?"
```

**Implementation Note**: The Sales Advisor agent can be enhanced to include the `executive_kpi_analyzer` tool (SAM_EXECUTIVE_VIEW) for client-specific analytics, enabling more personalized client communications with flow history and relationship context.

See [Executive Leadership Scenarios](demo_scenarios_executive.md) for examples of client flow analytics in action.

