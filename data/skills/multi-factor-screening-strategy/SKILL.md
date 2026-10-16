---
name: multi-factor-screening-strategy
description: Use this skill when the user asks to build a multi-factor stock screening strategy, rank factor candidates, screen for Value and Quality with improving Momentum, or assemble a quant strategy proposal that combines factor signals with fundamental and qualitative validation.
---

# Multi-Factor Screening Strategy

## When to Activate

Trigger when user asks for: "multi-factor screening", "multi-factor stock screening strategy", "build a factor strategy", "screen for value quality momentum", "rank factor candidates", "quant strategy proposal", or requests a factor-screened shortlist with validation.

## Workflow

### Step 1: Initial Factor Screen

Tool: `factor_model_analyzer`

Query for the latest available factor scores across the investment universe, focusing on the requested factor profile.

Typical objective:
- high Value score
- high Quality score
- improving or favorable Momentum score

Default Step 1 method:
- Use the latest available `month_date` first.
- Filter out securities with NULL Value, Quality, or Momentum scores before ranking.
- Treat "improving Momentum" as current Momentum score versus a fixed recent lookback, defaulting to a 3-month comparison unless the user requests another window.
- Prefer a percentile/rank-based shortlist for the initial pass rather than hard raw-score thresholds.
- Use a composite ranking that favours Value and Quality first, then favorable Momentum and positive Momentum improvement.
- If raw factor distributions are sparse, compressed, or uneven, continue with percentile ranking instead of trying multiple threshold-debugging passes in the visible response.

Default percentile recipe:
- Rank Value and Quality in descending percentile terms within the latest month.
- Rank current Momentum and Momentum improvement separately.
- Use a weighted composite that emphasizes Value and Quality more heavily than Momentum level and Momentum improvement.
- Prefer top-decile / top-quartile style percentile cutoffs for the initial shortlist when a cutoff is needed, rather than absolute z-score cutoffs.
- Treat percentile ranking as the standard fallback, not an exceptional recovery path.

Return:
- screening criteria summary
- number of securities meeting thresholds
- ranked shortlist with factor scores and combined ranking logic
- the ranking method used, especially if percentile ranking was used as the default fallback

Do not include hidden chain-of-thought or tool-selection rationale in the user-facing response.

Step 1 response discipline:
- Keep the initial screen concise and decision-oriented.
- Do not narrate exploratory threshold tuning, score-distribution debugging, join debugging, or null-behavior analysis unless the user explicitly asks for methodology details.
- Once a workable shortlist is produced, stop and present the shortlist rather than continuing into refinement or validation automatically.
- If the first ranking approach returns no names, switch quietly to the default percentile-based method and present the shortlist without exposing intermediate debugging steps.
- Mention methodology caveats in one short note only when they materially affect interpretation.

### ESG-Constrained Screens and Replacement Candidates

Apply this gate whenever the screen is for an ESG-labelled portfolio, must "meet the mandate", or is proposing replacements for a name being exited on ESG grounds. It runs before the shortlist is presented.

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

### STOPPING POINT

After the initial screen, present the shortlist and offer:
- continue to SEC fundamental validation
- tighten or relax the factor thresholds
- compare with another factor recipe
- backtest the screened basket

Do not proceed into Step 2 or later validation steps until the user explicitly chooses one of those follow-up paths.

### Step 2: Trend and Refinement Layer

Tool: `factor_model_analyzer`

Refine the shortlist using recent factor trend information, especially for Momentum or requested changes over time.

Use Step 2 only after the user asks to refine, compare, or validate the initial shortlist.

Return:
- which names have improving trend characteristics
- any names where the factor mix is unstable or deteriorating

### Step 3: Fundamental Validation

Tool: `research_analyzer`

Validate top candidates with structured fundamentals from SEC-derived data.

Check for:
- revenue growth
- margin expansion or stability
- balance sheet quality
- profitability / quality support

Return a validation summary showing whether the fundamental evidence confirms or challenges the factor signal.

### Step 4: Analyst Research Validation

Tool: `search_external_docs`

Check whether broker research broadly aligns with the shortlisted candidates.

Return:
- recent report titles and dates
- broad rating direction or consensus framing
- any analyst concerns that contradict the factor thesis

### Step 5: Management Commentary Validation

Tool: `search_company_events`

Review earnings transcript commentary for management statements supporting quality, growth, execution discipline, or strategic momentum.

Return:
- key supporting or contradicting management quotes
- management alignment with the factor thesis

### STOPPING POINT

After fundamental and qualitative validation, present the validated shortlist and offer:
- synthesize the full strategy proposal
- backtest the basket
- compare against another screened basket
- turn the shortlist into a portfolio-construction workflow

### Step 6: Synthesize Strategy Recommendation

Combine the screened shortlist, factor evidence, SEC fundamentals, analyst views, and management commentary into a committee-ready strategy proposal.

Include:
- strategy thesis summary
- ranked candidates
- validation status
- implementation considerations
- risk notes and concentration constraints

### Step 7: Statistical Validation and Backtest Branch

If the user asks for statistical significance, historical validation, or performance testing:
- use `factor_model_analyzer` for available factor-model statistics such as R-squared and factor-return context
- use `historical-backtest` or `run_backtest` for basket performance validation when a specific candidate basket or weighting is requested

If notebook-populated ML tables are unavailable, state that clearly and degrade gracefully to the non-ML factor-screening workflow.

## Data Readiness Rules

- Confirm factor-screening data is available before promising the full workflow.
- If `SAM_FACTOR_MODEL_VIEW` data is present but ML-derived tables are unpopulated, continue with factor screening and validation, but clearly state that ML-specific or notebook-derived outputs are unavailable.
- Do not imply that full ML or backtest outputs exist unless the underlying data is present.

## Boundaries

- For ad hoc factor analytics like IC, correlations, or rolling Sharpe, prefer `factor-model-explorer`.
- For explicit historical validation requests, branch to `historical-backtest`.
- For portfolio implementation or weight construction, branch to `portfolio-construction` or `portfolio-optimizer`.

## Output Format

- Produce a written markdown strategy brief
- Use tables for ranked candidates and validation summaries
- Keep the initial screen concise, then deepen only after the stopping point
- Clearly separate factor evidence, fundamental validation, analyst validation, and management validation
- In Step 1, show only the screening recipe, shortlist size, ranked candidates, and brief next-step options

## Stopping Points

- After Step 1: present shortlist and threshold options
- After Step 5: present validated shortlist before full synthesis or backtest branch