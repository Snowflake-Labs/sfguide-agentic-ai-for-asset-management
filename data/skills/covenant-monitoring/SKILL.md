---
name: covenant-monitoring
description: Use this skill when the user asks about covenant compliance, covenant breaches, covenant headroom, watchlist borrowers, equity cures, waiver requests, or credit committee recommendations on covenant issues. Also use for "any covenants at risk", "which borrowers are in breach", "covenant deep-dive on [borrower]", or "credit committee summary".
---

# Covenant Monitoring & Breach Investigation

## When to Activate

Trigger when user asks: "covenant breach", "covenant compliance", "covenant headroom", "watchlist", "which borrowers are at risk", "equity cure", "waiver", "covenant deep-dive", "credit committee recommendation", "covenant status", "tight covenants", "breach investigation"

## Workflow

### Step 1: Covenant Breach Detection

Tool: `credit_portfolio_analyzer`
Query: All borrowers with covenant breaches, headroom below 10%, or active waivers. Include leverage covenant, coverage covenant, and any financial maintenance tests.

Present:
- Headline: "[X] borrowers with covenant issues ([Y] in breach, [Z] with tight headroom)"
- Breach summary table:

| Borrower | Covenant | Threshold | Actual | Headroom | Status |
|----------|----------|-----------|--------|----------|--------|
| [Name] | Leverage | [X]x | [Y]x | [Z]% | BREACH |
| [Name] | DSCR | [X]x | [Y]x | [Z]% | TIGHT |

- Flag any borrowers with headroom below 10% as "TIGHT"
- Note any active waivers or equity cure usage

### STOPPING POINT

Present the breach summary, then offer:
"I've identified [X] covenant issues across the portfolio. I can:
- **Deep-dive a specific borrower** (full covenant history, financial trends, leverage trajectory)
- **Review cure provisions** (credit agreement terms for equity cure, waiver, and amendment)
- **Check management commentary** (latest compliance certificate narrative and outlook)
- **Generate credit committee summary** (structured severity assessment with recommended actions)

Which would be most useful?"

### Step 2a: Borrower Deep-Dive (if user selects a borrower)

Tool: `credit_portfolio_analyzer`
Query: Full financial history for the selected borrower — quarterly leverage, coverage ratios, revenue, EBITDA trends over 8+ quarters

Present:
- Financial trend table (quarterly)
- Leverage trajectory chart data (is it improving or deteriorating?)
- Key inflection points: "Leverage crossed covenant threshold in Q[X] when EBITDA declined [Y]%"
- Context: sector performance, rate impact on coverage

### Step 2b: Cure Provisions (if user chooses cure review)

Tool: `search_credit_agreements`
Query: Credit agreement for the breached borrower — equity cure provisions, waiver terms, amendment procedures, PIK triggers

Present:
- Cure mechanism: "Equity cure available: [Yes/No], max [X] cures in [Y] months, max amount $[Z]M"
- Waiver terms: notice period, lender consent threshold
- Amendment provisions: supermajority requirements, fee structure
- PIK trigger: "PIK activates if leverage exceeds [X]x for [Y] consecutive quarters"

### Step 2c: Management Commentary (if user chooses compliance review)

Tool: `search_compliance_certs`
Query: Latest compliance certificate for the flagged borrower — management narrative, outlook, remediation plans

Present:
- Management explanation for covenant pressure
- Remediation plan (if any): cost reduction, asset sales, equity injection
- Forward outlook: management confidence level
- Comparison to prior quarter commentary (improving or worsening narrative)

### Step 2d: Credit Committee Summary (if user chooses CC summary)

Synthesise all available data into structured format:

```
## Covenant Issue: [Borrower]

**Severity**: [Critical / Elevated / Watch] | **Trend**: [Deteriorating / Stable / Improving]

### Breach Summary
| Covenant | Threshold | Actual | Headroom | Quarters in Breach |
|----------|-----------|--------|----------|--------------------|
| [Type] | [X] | [Y] | [Z]% | [N] |

### Root Cause
[FACT] [What financial metrics drove the breach]
[ANALYSIS] [Whether the issue is cyclical or structural]

### Available Remedies
- Equity cure: [Available / Exhausted] ([X] of [Y] used)
- Waiver: [Requested / Not yet requested]
- Amendment: [In discussion / Not applicable]

### Recommended Action
[INFERENCE] [Credit committee recommendation with rationale]
```

## Audience-Specific Presentation

- **Credit Committee**: Full Step 1 + Step 2d summary for each flagged borrower
- **PM/Analyst**: Full workflow with stopping point and all branch options
- **Client/Investor**: Step 1 headline only — "[X] borrowers on watchlist, [Y] under active remediation"

## Output Template

```
## Covenant Monitoring Report

**Portfolio**: [Fund Name] | **As of**: [Date]
**Borrowers in Breach**: [X] | **Tight Headroom (<10%)**: [Y] | **On Watchlist**: [Z]

| Borrower | Covenant | Status | Headroom | Remedy | Severity |
|----------|----------|--------|----------|--------|----------|
| [Name] | [Type] | [Status] | [X]% | [Remedy] | [Severity] |

### Key Concern
[Most critical borrower situation in 2-3 sentences]

### Recommended Actions
1. [Action for highest severity borrower]
2. [Action for next priority]
```

## Stopping Points

- After Step 1 (breach detection): Offer 4 branching options
- After any Step 2 branch: "Would you like to investigate another borrower, or shall I compile the full credit committee report?"
