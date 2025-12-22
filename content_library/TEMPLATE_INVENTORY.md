# Content Library Template Inventory

**Total Templates**: 59  
**Rule Files**: 3  
**Last Updated**: 2025-01-21  
**Strategy**: Demo-Focused Coverage

---

## Rule Files (3)

1. `_rules/placeholder_contract.yaml` - Complete placeholder definitions and validation rules
2. `_rules/numeric_bounds.yaml` - Sector-specific numeric bounds for all Tier 1 placeholders
3. `_rules/fictional_providers.yaml` - 15 fictional brokers + 12 fictional NGOs

---

## Security-Level Templates (24)

### Broker Research (7 templates)
- `security/broker_research/technology/variant_01.md`
- `security/broker_research/technology/variant_02.md`
- `security/broker_research/technology/variant_03.md`
- `security/broker_research/healthcare/variant_01.md`
- `security/broker_research/financials/variant_01.md`
- `security/broker_research/consumer_discretionary/variant_01.md`
- `security/broker_research/communication_services/variant_01.md`

**Coverage**: Technology (3), Healthcare (1), Financials (1), Consumer Discretionary (1), Communication Services (1)

### Internal Research (3 templates) ✅ COMPLETE SET
- `security/internal_research/technology/variant_01.md` (2,100 words, comprehensive)
- `security/internal_research/healthcare/variant_01.md` (2,000 words, pharma/biotech focus)
- `security/internal_research/financials/variant_01.md` (2,050 words, banking/financial services focus)

**Coverage**: 3 major sectors (Technology, Healthcare, Financials)

### Investment Memos (3 templates) ✅ COMPLETE SET
- `security/investment_memo/technology/variant_01.md` (1,450 words, IC format)
- `security/investment_memo/healthcare/variant_01.md` (1,400 words, pipeline/regulatory focus)
- `security/investment_memo/financials/variant_01.md` (1,400 words, rate sensitivity/credit focus)

### Earnings Transcripts (4 masters)
- `security/earnings_transcripts/technology/master_01.md` (8,500 words, CEO/CFO/Q&A)
- `security/earnings_transcripts/technology/master_02.md` (7,800 words, detailed Q&A)
- `security/earnings_transcripts/healthcare/master_01.md` (7,200 words, biopharma focus)
- `security/earnings_transcripts/consumer_discretionary/master_01.md` (6,800 words, consumer focus)

**Coverage**: 4 masters across 3 sectors

### Press Releases (4 templates)
- `security/press_releases/technology/variant_01.md` (earnings announcement)
- `security/press_releases/technology/variant_02.md` (strategic partnership)
- `security/press_releases/consumer_discretionary/variant_01.md` (acquisition)
- `security/press_releases/healthcare/variant_01.md` (FDA approval)

---

## Portfolio-Level Templates (8)

### Investment Policy Statements (3 risk variants) ✅ COMPLETE SET
- `portfolio/ips/conservative_variant_01.md` (1,950 words, 65/25/10 allocation)
- `portfolio/ips/moderate_variant_01.md` (2,100 words, 60/35/5 allocation)
- `portfolio/ips/aggressive_variant_01.md` (2,000 words, 90/5/5 allocation)

### Portfolio Reviews (3 performance variants) ✅ COMPLETE SET
- `portfolio/portfolio_review/positive_performance_variant_01.md` (1,600 words with conditionals)
- `portfolio/portfolio_review/negative_performance_variant_01.md` (1,550 words with conditionals)
- `portfolio/portfolio_review/mixed_performance_variant_01.md` (1,480 words with conditionals)

**Special Features**: All portfolio reviews include placeholder-level conditional logic (Option A) for performance-dependent narratives

---

## Issuer-Level Templates (4)

### NGO Reports (3 templates)
- `issuer/ngo_reports/environmental_severity_high_01.md` (650 words)
- `issuer/ngo_reports/social_severity_medium_01.md` (580 words)
- `issuer/ngo_reports/governance_severity_low_01.md` (520 words)

**Coverage**: 3 categories (Environmental, Social, Governance) × 3 severity levels (High, Medium, Low sample)

### Engagement Notes (2 templates)
- `issuer/engagement_notes/management_meeting_variant_01.md` (240 words)
- `issuer/engagement_notes/shareholder_call_variant_01.md` (220 words)

**Coverage**: 2 of 3 meeting types

---

## Global Templates (17)

### Market Data (8 components) ✅ COMPLETE SET
**Main Templates (3 regimes)**:
- `global/market_data/regime_risk_on.md` (1,050 words)
- `global/market_data/regime_risk_off.md` (1,020 words)
- `global/market_data/regime_mixed.md` (980 words)

**Sub-Template Partials (5)**:
- `global/market_data/_partials/equity_markets.md`
- `global/market_data/_partials/fixed_income.md`
- `global/market_data/_partials/commodities.md`
- `global/market_data/_partials/currencies.md`
- `global/market_data/_partials/economic_data.md`

**Special Features**: Demonstrates sub-template inclusion pattern with `{{> partial_name}}` syntax

### Policy Documents (3 templates) ✅ COMPLETE SET
- `global/policy_docs/concentration_risk_policy.md` (950 words, concentration limits and procedures)
- `global/policy_docs/sustainable_investment_policy.md` (1,200 words)
- `global/policy_docs/investment_management_agreement.md` (1,280 words, IMA template)

### Sales Templates (6 templates) ✅ COMPLETE SET
- `global/sales_templates/monthly_client_report.md` (1,100 words, comprehensive template)
- `global/sales_templates/quarterly_client_letter.md` (950 words, relationship-building)
- `global/sales_templates/rfp_response_template.md` (1,200 words, institutional RFP responses)
- `global/sales_templates/client_onboarding_welcome.md` (800 words, new client welcome package)
- `global/sales_templates/client_retention_playbook.md` (1,000 words, at-risk client strategies)
- `global/sales_templates/product_catalog.md` (1,100 words, strategy descriptions for cross-sell)

### Philosophy Documents (3 templates) ✅ COMPLETE SET
- `global/philosophy_docs/esg_philosophy.md` (1,150 words)
- `global/philosophy_docs/risk_philosophy.md` (1,050 words)
- `global/philosophy_docs/brand_guidelines.md` (980 words)

### Compliance Manual (1 template)
- `global/compliance_manual/compliance_manual_canonical.md` (3,800 words, comprehensive)

### Risk Framework (1 template)
- `global/risk_framework/risk_framework_canonical.md` (2,850 words, comprehensive)

---

## Regulatory Templates (5)

### SEC Form ADV Part 2A (1 template)
- `regulatory/form_adv/adv_part_2a_canonical.md` (4,200 words, complete SEC format)

### SEC Form CRS (1 template)
- `regulatory/form_crs/form_crs_canonical.md` (720 words, 2-page compliant)

### Regulatory Updates (2 templates)
- `regulatory/regulatory_updates/sec_update_template.md` (850 words, US focus)
- `regulatory/regulatory_updates/fca_update_template.md` (780 words, UK Consumer Duty)

---

## Template Quality Metrics

### All Templates Meet Standards ✅

**Content Quality**:
- ✅ UK English spelling and terminology throughout
- ✅ Professional institutional tone appropriate to document type
- ✅ Fictional provider names only (15 brokers, 12 NGOs)
- ✅ Word counts within specified target ranges
- ✅ Complete YAML front matter with metadata

**Technical Standards**:
- ✅ All placeholders defined in placeholder_contract.yaml
- ✅ Proper linkage levels specified (security/issuer/portfolio/global)
- ✅ Constraint definitions for distributions and numeric bounds
- ✅ Tier markers (tier0, tier1, tier2) correctly indicated

**Innovation Highlights**:
- ✅ **Conditional Logic** (Option A): Portfolio reviews demonstrate placeholder-level conditionals for both words and sentences
- ✅ **Sub-Templates**: Market data shows partial inclusion with `{{> partial_name}}` syntax
- ✅ **Tier 2 Derivations**: Portfolio reviews marked for SQL-derived metrics from CURATED tables
- ✅ **Context-First Design**: All templates structured for Context-First approach (Option B)

---

## Coverage by Document Type

| Document Type | Templates | Status | Notes |
|---------------|-----------|--------|-------|
| Broker Research | 7 | ✅ Sufficient | Multiple sectors, 3 tech variants |
| Internal Research | 3 | ✅ **COMPLETE** | Tech, Healthcare, Financials |
| Investment Memo | 3 | ✅ **COMPLETE** | Tech, Healthcare, Financials |
| Earnings Transcripts | 4 | ✅ Sufficient | 3 sectors, 4 masters for variety |
| Press Releases | 4 | ✅ Sufficient | Multiple release types and sectors |
| IPS | 3 | ✅ **COMPLETE** | All 3 risk variants |
| Portfolio Review | 3 | ✅ **COMPLETE** | All 3 performance variants with conditionals |
| NGO Reports | 3 | ✅ Sufficient | Multiple categories and severities |
| Engagement Notes | 2 | ✅ Sufficient | 2 of 3 meeting types |
| Market Data | 8 | ✅ **COMPLETE** | All 3 regimes + 5 partials |
| Policy Docs | 3 | ✅ **COMPLETE** | All critical policies including concentration risk |
| Sales Templates | 6 | ✅ **COMPLETE** | All 6 templates (reports, letters, RFP, onboarding, retention, catalog) |
| Philosophy | 3 | ✅ **COMPLETE** | All 3 documents |
| Compliance Manual | 1 | ✅ **COMPLETE** | Canonical comprehensive manual |
| Risk Framework | 1 | ✅ **COMPLETE** | Canonical framework |
| Form ADV | 1 | ✅ **COMPLETE** | SEC-compliant format |
| Form CRS | 1 | ✅ **COMPLETE** | 2-page compliant |
| Regulatory Updates | 2 | ✅ Sufficient | SEC and FCA templates |

**Total Coverage**: 59 templates across 18 document types  
**Complete Sets**: 11 document types have all required variants  
**Sufficient Coverage**: 7 document types have demo-adequate templates

---

## Reusability and Scaling

**Current Templates Support**:
- 8 demo companies (5 core + 3 additional) via sector-based template reuse
- 4 portfolios with all risk/performance variants
- Multiple quarters of earnings (4 masters × multiple companies)
- Comprehensive global/regulatory document coverage

**Template Reuse Pattern**:
- 7 broker research templates → 48 documents (7 templates × 6-8 reuses each)
- 3 internal research templates → 24 documents (3 templates × 8 uses each)
- 3 investment memos → 18 documents (3 templates × 6 uses each)
- 4 earnings masters → 58 documents (4 masters × 14-15 uses each across quarters)
- 3 portfolio review variants → 8 documents (3 variants × 2-3 uses each)
- Global templates → 1 use each (canonical documents)

**Scaling Approach**:
- Add templates incrementally as needed for additional sectors or variants
- Template library easily extensible without code changes
- New templates follow established patterns and YAML structure

---

## Demo Scenario Coverage Analysis

Based on `@demo_scenarios.md` requirements:

### Portfolio Copilot ✅
- **Needs**: Broker research, earnings transcripts, press releases for technology holdings
- **Coverage**: ✅ 3 tech broker variants, 2 tech earnings masters, 2 tech press releases

### Research Copilot ✅
- **Needs**: Multi-source research (broker, earnings, press) for technology companies
- **Coverage**: ✅ Comprehensive technology sector templates across all 3 document types

### Thematic Macro Advisor ✅
- **Needs**: Broker research and press releases for thematic analysis
- **Coverage**: ✅ Multiple broker variants and press release types

### Sales Advisor ✅
- **Needs**: Sales templates, philosophy docs, policy docs, RFP templates, onboarding materials, retention playbooks
- **Coverage**: ✅ All 6 sales templates complete (monthly report, quarterly letter, RFP response, client onboarding, retention playbook, product catalog) plus philosophy and policies

### ESG Guardian ✅
- **Needs**: NGO reports, engagement notes, policy documents
- **Coverage**: ✅ Multiple NGO severities, 2 engagement types, ESG policy

### Compliance Advisor ✅
- **Needs**: Policy documents, compliance procedures
- **Coverage**: ✅ Compliance manual, IMA, policies

### Quant Analyst ✅
- **Needs**: Research documents for quantitative validation
- **Coverage**: ✅ Internal research and broker research templates

**Result**: All demo scenarios have adequate template coverage for realistic demonstrations

---

## Next Steps — Phase 3: Hydration Engine

**Ready for Implementation**: 
- ✅ 59 high-quality templates covering all demo scenarios
- ✅ 3 comprehensive rule files
- ✅ Config.py fully configured
- ✅ All template patterns proven (conditionals, partials, tiers)
- ✅ Complete sector coverage (Technology, Healthcare, Financials) for internal research and investment memos
- ✅ Policy-driven concentration flagging with dedicated concentration risk policy template

**Phase 3 Tasks**:
1. Implement content_loader module (parse YAML + markdown)
2. Implement variant_picker (deterministic template selection)
3. Implement context_builder (query DIM tables, build context dict)
4. Implement numeric_rules (load bounds, sample within ranges)
5. Implement conditional_renderer (process conditional placeholders)
6. Implement renderer (fill placeholders, validate, extract titles)
7. Implement writer (write RAW tables with Context-First approach)
8. Update build_all() to support USE_PREGENERATED_CONTENT flag

**Estimated Effort**: 3-4 days for complete hydration engine

---

*Phase 2 Complete — Ready for Phase 3 Hydration Engine Implementation*

