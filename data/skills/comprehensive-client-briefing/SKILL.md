---
name: comprehensive-client-briefing
description: Use this skill when the user asks for a comprehensive client briefing, annual review briefing, institutional client presentation, full client review pack, or complete client briefing that combines performance analysis, template structure, investment philosophy, and compliance disclosures in one workflow.
---

# Comprehensive Client Briefing

## When to Activate

Trigger when user asks for: "comprehensive client briefing", "annual review briefing", "institutional client presentation", "full client review pack", "complete client briefing", "annual client review", "client annual review pack", or a large-client review that combines performance, positioning, and compliance in one deliverable.

## Workflow

### Step 1: Confirm Client and Portfolio Scope

If the client, portfolio, or review period is ambiguous, confirm the exact scope before proceeding.

Use `client_analyzer` to retrieve the client relationship context:
- relationship tenure
- current AUM with SAM
- recent flow history
- client type / institutional profile

If the user already supplied a precise client and portfolio, proceed directly.

### Step 2: Build the Performance Foundation

Tool: `portfolio_analyzer`

Make separate calls as needed for:
- full-year returns versus benchmark
- quarterly performance breakdown
- top holdings at year-end or latest date requested
- sector allocation
- risk metrics and concentration flags

Tool: `client_analyzer`

Use when helpful to connect the portfolio review to the client relationship:
- client allocation across SAM portfolios
- recent flows into or out of the reviewed strategy

Present a concise factual foundation before moving to the narrative layers.

### STOPPING POINT

After the performance foundation, confirm that the correct client, portfolio, and review framing have been captured before assembling the full briefing.

### Step 3: Retrieve the Professional Briefing Structure

Tool: `search_internal_docs`

Query for:
- annual review template
- executive briefing template
- relevant sales template structure

Extract:
- section order
- presentation structure
- branding and formatting guidance
- recommended appendix or disclosure placement

### Step 4: Integrate Investment Philosophy and Positioning

Tool: `search_internal_docs`

Query for:
- strategy philosophy
- portfolio theme positioning
- forward-looking market or investment narrative relevant to the reviewed strategy

Extract:
- philosophy statements
- strategic positioning points
- forward-looking themes suitable for a client conversation
- links between current holdings / sector positioning and the stated philosophy

### Step 5: Add Compliance and Regulatory Disclosures

Tool: `search_internal_docs`

Query for:
- disclosure language
- performance disclaimers
- risk warnings
- fiduciary or policy language for institutional communications

Tool: `search_regulations`

Query for:
- MiFID II disclosure requirements
- FCA disclosure requirements
- any other framework explicitly requested by the user

Extract:
- required disclosure language
- risk and performance disclaimers
- client-appropriate fiduciary framing
- any relevant conflict or suitability language

### Step 6: Synthesise the Complete Client Briefing

Combine the outputs from Steps 2-5 into a single written markdown document.

The briefing should include:
- executive summary
- performance review
- portfolio positioning and outlook
- investment philosophy alignment
- compliance / disclosure section
- talking points for the relationship manager

Keep it in written-report format. Do not produce slide-deck output.

### Step 7: Generate PDF Only If Explicitly Requested

Tool: `pdf_generator`

Only call this step when the user explicitly asks for a PDF, client-ready document, or formal downloadable version.

## Output Format

- Produce a written markdown briefing with clear section headers
- NEVER produce slide-deck format
- Use tables for performance summaries and holdings where useful
- Use concise relationship-manager talking points near the end
- Include disclaimers and required disclosure language in a distinct section

## Boundaries

- This skill is for full client briefing assembly, not simple meeting prep
- For narrower meeting prep without full template/compliance synthesis, prefer `client-review-preparation`
- For periodic portfolio letters, prefer `quarterly-client-letter`
- For proposal / tender workflows, prefer `rfp-response-preparation`
- Do not generate PDF unless explicitly requested

## Return Figures (mandatory)

- Quote portfolio, benchmark and active (excess) returns exactly as the query returns them; never recompute them yourself (no subtraction, summing or compounding by hand, no bash or code_execution arithmetic). If a figure is missing, query for it.
- For quarters and other multi-month periods use the linked (compounded) figures from attribution data rather than adding monthly numbers.
- When quoting allocation, selection or interaction effects, take all of them and the active return from ONE linked portfolio-total row (the `attribution_analyzer` linked Brinson effects query in bps with its reconciliation check column). Verify the effects sum to the active return before quoting; if not, re-query. Never derive selection by subtraction or from summed sector rows.

## Stopping Points

- After Step 2: confirm the factual foundation and scope
- After Step 6: present the completed draft for review before PDF generation or distribution