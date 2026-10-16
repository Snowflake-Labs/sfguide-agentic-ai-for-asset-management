---
name: esg-mandate-compliance
description: Use this skill when the user asks about ESG mandate compliance, ESG grade breaches, SFDR Article 8/9 requirements, or ESG portfolio screening. Detects breaches, checks engagement history, and generates remediation plans.
---

# ESG Mandate Compliance

## When to Activate

Trigger when user asks about: "ESG mandate breach", "ESG compliance check", "ESG grade monitoring", "SFDR classification", "Article 8 compliance", "sustainability disclosure"

## 5-Step Mandate Breach Detection

### Step 1: Retrieve Mandate

Tool: `search_internal_docs` or `search_regulations`

Search: "ESG mandate requirements" or "minimum ESG grade policy"

Extract: Minimum ESG grade (typically BBB), exclusion lists, SFDR classification

### Step 2: Check Current Grades

Tool: `portfolio_analyzer`

Query: "Current ESG grades for all holdings in SAM [portfolio]"

Extract: ESG grade per security, overall portfolio ESG score

### Step 3: Identify Breaches

Compare each holding's ESG grade against mandate minimum:
- Grade < BBB for ESG-labelled portfolios = BREACH
- Grade downgrade from previous quarter = FLAG

### Step 4: Check Engagement History

Tool: `search_internal_docs`

Search: "engagement notes [company name]" (filter DOCUMENT_TYPE = 'engagement_notes')

Extract: Prior engagement attempts, management responsiveness, timeline commitments

### Step 5: Generate Remediation Plan

Synthesise into remediation report:

| Security | Current Grade | Mandate Min | Gap | Engagement Status | Recommendation |
|----------|--------------|-------------|-----|-------------------|---------------|
| [Ticker] | BB | BBB | -1 notch | 2 prior engagements | Escalate / Divest |

**Remediation Timeline**:
- Immediate (T+0): Notify Investment Committee
- Short-term (30 days): Escalated engagement with company management
- Medium-term (90 days): If no improvement, begin orderly divestment
- Ongoing: Monitor for grade recovery

### Step 6: Replacement Candidates (when asked for replacements or a divestment redeployment)

Tool: `portfolio_analyzer` (one candidate query, filters applied in SQL)

Query: "Replacement candidates for SAM [portfolio]: latest ESG grade, sector and weight, with no esg_controversies row where controversy_is_active = TRUE and controversy_severity is High or Medium, ESG grade BBB or better, excluding [name being replaced]". The controversy exclusion is a hard WHERE filter on the `esg_controversies` logical table (dimensions `controversy_severity`, `controversy_is_active`, metric `active_controversy_count`) inside the candidate query; the view's ESG_REPLACEMENT_CANDIDATES verified query is the template, never a post-filter applied after the results come back.

Tool: `portfolio_analyzer` (second query, for transparency only)

Query: "Names in the same candidate universe with an active High or Medium esg_controversies row or ESG grade below BBB, with severity and grade". These are the excluded names; list them separately and never as eligible.

Optional: `search_external_docs` (DOCUMENT_TYPE = 'ngo_reports') only to cite the NGO source and date for an excluded name; it does not decide eligibility.

Rules (all mandatory):
- Eligible candidates come only from the filtered query. Do not re-add a name the filter removed, and do not drop the filter if it returns few rows.
- Exclude the name being replaced and any name sharing its controversy.
- If fewer than three candidates remain, say so rather than relaxing the filter.
- Present the eligible shortlist, then a separate "Excluded and why" table (ticker, controversy severity or grade).

## SFDR Classification Requirements

- **Article 6**: Basic sustainability risk integration
- **Article 8**: Promotes environmental/social characteristics (minimum screening required)
- **Article 9**: Sustainable investment objective (all holdings must meet sustainability criteria)

For SFDR-specific queries, use the `regulatory-lookup` skill for detailed regulation text.

## Stopping Points

- After Step 2 (breach detection complete): present breaches for review before checking engagement history
- After Step 4 (remediation plan drafted): present for approval before finalising

## Output

An ESG compliance report with breach table, engagement history context, and remediation timeline.
