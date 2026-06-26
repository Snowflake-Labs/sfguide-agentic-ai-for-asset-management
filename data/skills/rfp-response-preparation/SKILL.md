---
name: rfp-response-preparation
description: Use this skill when the user asks to "prepare an RFP response", "draft an RFP", "respond to an RFP", or needs to compile firm capabilities, track record, investment process, and compliance content for a proposal. Also use when the user mentions "Request for Proposal", "mandate proposal", "tender response", or "client proposal".
---

# RFP Response Preparation

## When to Activate

Trigger when user asks for: "RFP response", "prepare RFP", "respond to RFP", "mandate proposal", "tender response", "client proposal", "draft proposal for [mandate]", "RFP for [strategy]"

## Workflow

### Step 1: Confirm Mandate Details

**⚠️ MANDATORY STOPPING POINT**: Do NOT proceed until user responds.

Before presenting options, query `portfolio_analyzer` for "List all available portfolio names" to get the current strategy list. Use the results to populate the strategy options.

Present the user with structured questions:

1. **Strategy**: Options from the portfolio list above (filter to those relevant to the user's stated mandate type if possible)
2. **Regulatory framework**: SFDR Article 8 / SFDR Article 9 / TCFD / UK Stewardship Code / FCA SDR / MiFID
3. **Client type**: UK DB Pension Scheme / UK DC Pension Scheme / EU IORP / occupational pension / Public / local government scheme / Foundation / Insurance / Sovereign Wealth
4. **Sections to emphasise**: ESG integration methodology / Active ownership / engagement / Climate metrics / Performance track record / Team and governance / Fees and operations

Once the user selects their options, proceed through all remaining steps without further interruption.

### Step 2: Firm Capabilities and Track Record

Tool: `portfolio_analyzer` (SAM_PORTFOLIO_VIEW)
Query: "Latest performance summary for SAM [strategy] including returns, AUM, sector allocation, and top holdings"

Tool: `portfolio_analyzer` (SAM_PORTFOLIO_VIEW)
Query: "Total AUM across all portfolios" — use this for the Firm Overview section (total firm AUM)

Tool: `search_internal_docs` (filter: DOCUMENT_TYPE = 'sales_templates')
Query: "RFP response template"

Extract:
- Total firm AUM (sum across all portfolios — do NOT mark as [TO COMPLETE])
- Strategy AUM and inception date
- Performance vs benchmark (QTD, YTD where available)
- Top holdings and sector positioning
- RFP template structure for formatting

Visualisation: Include a line chart showing strategy performance vs benchmark over time.

### Step 3: Investment Process and Philosophy

Tool: `search_internal_docs` (filter: DOCUMENT_TYPE = 'philosophy_docs')
Query: "Investment process methodology for [mandate type]"

For ESG mandates, additional query:
Query: "ESG integration methodology and active ownership approach"

Extract:
- Investment process description (multi-stage)
- Philosophy and differentiation
- For ESG: integration framework, exclusion policy, engagement approach
- Team structure and decision-making governance

### Step 4: Compliance and Risk Management

Tool: `search_internal_docs` (filter: DOCUMENT_TYPE = 'policy_docs')
Query: "Compliance framework and risk management policies"

Tool: `search_regulations` (SAM_REGULATORY_DOCS)
Query: "[Relevant regulation] disclosure requirements for [mandate type]"
(e.g., "SFDR Article 8 disclosure" for ESG, "UCITS risk limits" for regulated funds)

Extract:
- Regulatory registrations and compliance infrastructure
- Risk management framework and limits
- Relevant regulatory disclosures
- Conflict of interest management

### Step 5: Synthesise Complete RFP Response

Combine all gathered content into a structured RFP document following the template from Step 2. Use the [RFP_TEMPLATE.md](RFP_TEMPLATE.md) structure as the framework.

Include `[TO COMPLETE]` markers for sections requiring manual input (e.g., specific fee proposal, named team biographies).

End with a "Sections Requiring Manual Review" checklist summarising what still needs human attention.

## Multi-Section Handling

Make SEPARATE tool calls for each section. Never combine different content types in a single query.

## Date Handling

ALWAYS request "latest" or "most recent" data. Never use specific future dates.

## Mandate-Specific Adaptations

| Mandate Type | Philosophy Focus | Regulatory Focus | Additional Content |
|-------------|-----------------|-----------------|-------------------|
| ESG / Sustainable | ESG integration, exclusions, engagement | SFDR Art. 8/9, TCFD, UK Stewardship | Carbon metrics, ESG ratings |
| Global Equity | Factor approach, stock selection | MiFID, UCITS | Style characteristics |
| Fixed Income | Credit analysis, duration management | Prudent person, IORP II | Yield metrics, credit quality |
| Multi-Asset | Asset allocation, risk budgeting | FCA COLL, AIFMD | Diversification stats |

## Error Handling

- **Strategy not found**: "Portfolio not found. Available SAM strategies: [list from portfolio_analyzer]. Did you mean one of these?"
- **Template not found**: "RFP template not found in internal documents. I'll format using the standard institutional RFP structure from RFP_TEMPLATE.md."
- **Regulation not found**: "No specific regulatory content found for [framework]. I'll include a placeholder for regulatory disclosures that your compliance team can complete."

## Output Format

- Produce as a written document in markdown with clear section headers
- NEVER produce slide-deck format
- Include `[TO COMPLETE]` markers ONLY for information that cannot be retrieved from available tools (e.g., named team biographies, specific fee schedules). Never mark AUM, performance, or portfolio data as [TO COMPLETE] — always query it.
- Include data tables where quantitative evidence supports claims
- Do NOT generate PDF unless the user explicitly requests it

Visualisation rules:
- Include a line chart showing strategy performance vs benchmark over time
- Include a pie chart for sector allocation — do NOT present sector allocation as a table
- Do NOT include full monthly return tables — show the chart and state "Full monthly performance series available on request"

Table rules:
- Do NOT repeat the strategy/portfolio name in every row of a table — state it once in the section header and omit from the table body
- Keep tables clean: only include columns that vary across rows

## Cross-Skill References

- "What SFDR requirements apply?" -> `regulatory-lookup` skill
- "Adapt for board/prospect audience?" -> `audience-adaptive-narrative` skill
- "Generate PDF?" -> `pdf-report-generation` skill (only when explicitly requested)

## Stopping Points

- Before Step 2: Confirm mandate details, strategy, and any specific requirements
- After Step 5 (draft complete): Present for review. Do NOT generate PDF unless explicitly requested.
