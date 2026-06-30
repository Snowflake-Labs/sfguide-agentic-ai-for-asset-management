---
name: regulatory-lookup
description: Routes regulatory framework queries to the correct search filters and provides structured regulatory analysis. Use when the user asks about SFDR, EU Taxonomy, MiFID II, FCA SDR, FCA Consumer Duty, AIFMD, UCITS, SEC rules, or IFRS standards. Supports cross-jurisdiction comparison.
---

# Regulatory Lookup

## When to Activate

Trigger when user mentions:
- Any regulation by name: SFDR, EU Taxonomy, MiFID II, FCA SDR, FCA Consumer Duty, AIFMD, UCITS, DORA, EMIR, SEC Marketing Rule, SEC Investment Advisers Act, IFRS 7, IFRS 9
- Regulatory concepts: "sustainability disclosure", "anti-greenwashing", "suitability requirements", "investor protection"
- Cross-jurisdiction questions: "how does EU compare to UK?", "what are the US equivalents?"

## Regulation-to-Filter Mapping

When searching `search_regulations` (SAM_REGULATORY_DOCS), use these filters:

| Regulation | REGULATION_ID Filter | JURISDICTION |
|-----------|---------------------|-------------|
| SFDR | eu_sfdr | EU |
| EU Taxonomy | eu_taxonomy | EU |
| MiFID II | eu_mifid_ii | EU |
| UCITS | eu_ucits | EU |
| AIFMD II | eu_aifmd_ii | EU |
| DORA | eu_dora | EU |
| EMIR III | eu_emir_iii | EU |
| FCA Consumer Duty | fca_consumer_duty | UK |
| FCA SDR / Anti-Greenwashing | fca_sdr_anti_greenwashing | UK |
| SEC Marketing Rule | sec_marketing_rule | US |
| SEC Private Fund Rules | sec_private_fund_rules | US |
| SEC Investment Advisers Act | sec_investment_advisers_act | US |
| IFRS 9 | ifrs_9 | International |
| IFRS 7 | ifrs_7 | International |

## Cross-Jurisdiction Comparison Workflow

When the user asks to compare regulations across jurisdictions:

1. Search for the EU regulation (filter by JURISDICTION = 'EU')
2. Search for the UK equivalent (filter by JURISDICTION = 'UK')
3. Search for the US equivalent (filter by JURISDICTION = 'US')
4. Present as a comparison table:

| Aspect | EU | UK | US |
|--------|----|----|-----|
| Regulation | [Name] | [Name] | [Name] |
| Scope | [Who it applies to] | ... | ... |
| Key Requirements | [Summary] | ... | ... |
| Effective Date | [Date] | ... | ... |

## Citation Format

Always cite regulations with:
- Full regulation name
- Article/Section number where applicable
- Effective date
- Example: "Regulation (EU) 2019/2088 (SFDR), Article 6 — Transparency of sustainability risk integration, effective 10 March 2021"

## Stopping Points

- After retrieving regulation text: present findings for user review before synthesising cross-jurisdiction comparison
- This skill is often invoked as part of a larger workflow; inherit stopping points from the calling context

## Output

Structured regulatory analysis with proper citations following the Citation Format above. For cross-jurisdiction queries, a comparison table.
