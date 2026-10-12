# S&P Capital IQ Mapping for the SAM Demo

This document explains how to replace the current **Snowflake Public Data (Free)** structured-data sources in the SAM demo with **S&P Capital IQ** data while preserving the downstream SAM contract where possible.

The design goal is:

- keep the existing SAM-facing tables, views, semantic views, and agents stable where possible
- minimise or eliminate changes to agent definitions, semantic views, and search services
- focus on **structured data only**

---

## Scope

### In Scope

- Structured tables currently sourced from Snowflake Public Data
- Mapping those tables to S&P Capital IQ source tables
- Identifying where a SAM target can be preserved by:
  - rebuilding the table from S&P data, or
  - exposing a compatibility view over S&P tables
- Preserving downstream semantic views and agents where possible

### Out of Scope

- `RAW.COMPANY_EVENT_TRANSCRIPTS_RAW`
- `CURATED.COMPANY_EVENT_TRANSCRIPTS_CORPUS`
- `SAM_COMPANY_EVENTS`
- Rebuilding transcript-backed Cortex Search services from S&P data

Reason: S&P transcript content would need to be copied and reshaped into Snowflake-managed tables before it can be indexed into Cortex Search. That is a materially larger migration than structured-table replacement.

---

## Migration Principle

The preferred migration approach is:

1. Preserve the **SAM target contract** (`MARKET_DATA.*`, selected `CURATED.*` tables)
2. Swap the upstream source from Snowflake Public Data to S&P Capital IQ
3. Keep the current semantic views, search services, and agents unchanged wherever the SAM contract is preserved

For detailed column-level mappings of the first high-value structured targets, see [docs/sp_capital_iq_column_mapping.md](docs/sp_capital_iq_column_mapping.md).

This makes the migration a **source substitution problem**, not a full downstream AI redesign.

---

## Current Structured Targets That Depend on Public Data

These are the most important current SAM tables backed by Snowflake Public Data.

| SAM Target Table | Current Public Source | Consumed By Semantic Views | Used By Agents |
|------------------|----------------------|-----------------------------|----------------|
| `MARKET_DATA.FACT_STOCK_PRICES` | `PUBLIC_DATA_FREE.STOCK_PRICE_TIMESERIES` | `SAM_MARKET_VIEW`, `SAM_PORTFOLIO_MODELLING_VIEW` (via returns), `SAM_PORTFOLIO_VIEW`, `SAM_ATTRIBUTION_VIEW` (transitively) | Portfolio, Risk, Executive, Private Credit |
| `MARKET_DATA.FACT_SEC_FINANCIALS` | `PUBLIC_DATA_FREE.SEC_CORPORATE_REPORT_ATTRIBUTES` | `SAM_RESEARCH_VIEW` | Portfolio, Research, Risk, Sales, Executive, PE, Private Credit |
| `MARKET_DATA.FACT_SEC_SEGMENTS` | `PUBLIC_DATA_FREE.SEC_METRICS_TIMESERIES` | `SAM_RESEARCH_VIEW` | Portfolio, Research, Risk, Sales, Executive, PE, Private Credit |
| `MARKET_DATA.FACT_SEC_FILING_TEXT` | `PUBLIC_DATA_FREE.SEC_REPORT_TEXT_ATTRIBUTES` | Search-only (`SAM_REAL_SEC_FILINGS`) | Portfolio, Research, Risk, PE, Private Credit |
| `MARKET_DATA.FACT_DIVIDENDS` | `PUBLIC_DATA_FREE.SEC_REPORT_TEXT_ATTRIBUTES` + extraction | `SAM_MIDDLE_OFFICE_VIEW` (via `FACT_CORPORATE_ACTIONS`) | Operations |
| `CURATED.DIM_ISSUER` enrichment | `PUBLIC_DATA_FREE.COMPANY_INDEX`, `PUBLIC_DATA_FREE.COMPANY_CHARACTERISTICS` | Almost every semantic view through issuer/security joins | Nearly all agents |
| `CURATED.FACT_INSIDER_TRANSACTIONS` | `PUBLIC_DATA_FREE.SEC_INSIDER_TRADING_SECURITIES_INDEX` | `SAM_RESEARCH_VIEW` | Portfolio, Research, Risk, Sales, Executive, PE, Private Credit |
| `CURATED.FACT_INSTITUTIONAL_HOLDINGS` | `PUBLIC_DATA_FREE.SEC_HOLDING_FILING_ATTRIBUTES`, `PUBLIC_DATA_FREE.SEC_HOLDING_FILING_INDEX` | `SAM_RESEARCH_VIEW` | Portfolio, Research, Risk, Sales, Executive, PE, Private Credit |
| `CURATED.FACT_BENCHMARK_HOLDINGS` | Marketplace benchmark or N-PORT-like holdings feed | `SAM_PORTFOLIO_VIEW`, `SAM_ATTRIBUTION_VIEW` | Portfolio, Risk, Sales, Executive |

These are lower-priority current public-data-backed targets that are usually better left on their current source unless the customer has a preferred replacement:

| SAM Target Table | Current Public Source | Recommendation |
|------------------|----------------------|----------------|
| `MARKET_DATA.FACT_FX_RATES` | `PUBLIC_DATA_FREE.FX_RATES_TIMESERIES` | Keep current source |
| `MARKET_DATA.FACT_TREASURY_YIELDS` | `PUBLIC_DATA_FREE.US_TREASURY_TIMESERIES` + attributes | Keep current source |
| `MARKET_DATA.FACT_POLICY_RATES` | `PUBLIC_DATA_FREE.BANK_FOR_INTERNATIONAL_SETTLEMENTS_TIMESERIES` + attributes | Keep current source |
| `MARKET_DATA.FACT_ECONOMIC_INDICATORS` | `PUBLIC_DATA_FREE.FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES` + attributes | Keep current source |
| `MARKET_DATA.FACT_COUNTRY_EMISSIONS` | `PUBLIC_DATA_FREE.CLIMATE_WATCH_TIMESERIES` + attributes | Keep current source |

---

## Recommended S&P Capital IQ Replacement Mapping

This is the main migration table.

| SAM Target Table | Current Public Source | Recommended S&P Source Table(s) | Join Path / Key | Implementation Pattern | Compatibility Outcome |
|------------------|----------------------|----------------------------------|-----------------|------------------------|-----------------------|
| `MARKET_DATA.FACT_STOCK_PRICES` | `STOCK_PRICE_TIMESERIES` | `BASE.ciqTradingItem`, `BASE.ciqCompany`, `BASE.ciqSymbolMapping`, S&P market price/history tables (customer feed dependent) | ticker / symbol mapping -> `companyId` / `tradingItemId` | Rebuild physical SAM table from S&P | No downstream changes expected |
| `MARKET_DATA.FACT_SEC_FINANCIALS` | `SEC_CORPORATE_REPORT_ATTRIBUTES` | `FINANCIALS.ciqFinPeriod`, `FINANCIALS.ciqFinInstance`, `FINANCIALS.ciqFinInstanceToCollection`, `FINANCIALS.ciqFinCollection`, `FINANCIALS.ciqFinCollectionData`, `BASE.ciqDataItem` | `companyId` -> `financialPeriodId` -> `financialInstanceId` -> `financialCollectionId` | Compatibility view over S&P is preferred | No downstream changes if SAM column contract is preserved |
| `MARKET_DATA.FACT_SEC_SEGMENTS` | `SEC_METRICS_TIMESERIES` | `FINANCIALS.ciqSegment`, `FINANCIALS.ciqSegCollectStandCmpntData`, `FINANCIALS.ciqSegmentClassification`, `FINANCIALS.ciqSegmentClassificationType` | `companyId` / `segmentId` | Compatibility view over S&P is preferred | No downstream changes if segment grain is preserved |
| `MARKET_DATA.FACT_ESTIMATE_DATA` | public-data estimate generation | `ESTIMATES.ciqEstimatePeriod`, `ESTIMATES.ciqEstimateConsensus`, `ESTIMATES.ciqEstimateNumericData`, `ESTIMATES.ciqEstimateCoverage`, `BASE.ciqDataItem` | `companyId` -> `estimatePeriodId` -> `estimateConsensusId` | Compatibility view or physical rebuild | No downstream changes if current estimate columns are preserved |
| `MARKET_DATA.FACT_ESTIMATE_CONSENSUS` | public-data consensus generation | `ESTIMATES.ciqEstimateConsensus`, `ESTIMATES.ciqEstimateNumericData`, `BASE.ciqDataItemEstimate` | `estimateConsensusId`, `dataItemId`, current/open consensus filters | Compatibility view or physical rebuild | No downstream changes if current consensus columns are preserved |
| `MARKET_DATA.FACT_SEC_FILING_TEXT` | `SEC_REPORT_TEXT_ATTRIBUTES` | `FILINGS.filingRef`, `FILINGS.filingData`, `FILINGS.filingInstitutionRel`, filing type/reference tables | `companyId` / `fileVersionId` | Rebuild physical SAM table or compatibility view over filing text | Search service can stay unchanged if `FACT_SEC_FILING_TEXT` shape is preserved |
| `MARKET_DATA.FACT_DIVIDENDS` | filing text extraction | likely derived from S&P filing text plus extraction logic, or alternative corporate actions package if licensed | `fileVersionId` / filing text extraction | Non-trivial; may keep current logic/source | Gap / custom design likely |
| `CURATED.DIM_ISSUER` enrichment | `COMPANY_INDEX`, `COMPANY_CHARACTERISTICS` | `BASE.ciqCompany`, `BASE.ciqSymbolMapping`, `BASE.ciqSecurity`, `BASE.ciqTradingItem` | `companyId` and symbol bridge | Compatibility view or reload into issuer table | No downstream changes expected |
| `CURATED.FACT_INSIDER_TRANSACTIONS` | `SEC_INSIDER_TRADING_SECURITIES_INDEX` | no clear equivalent in the explored S&P schema bundle | unknown | Keep current source unless customer licenses equivalent data | Gap / keep current source |
| `CURATED.FACT_INSTITUTIONAL_HOLDINGS` | `SEC_HOLDING_FILING_*` | no clear equivalent in the explored S&P schema bundle | unknown | Keep current source unless customer has ownership package | Gap / keep current source |
| `CURATED.FACT_BENCHMARK_HOLDINGS` | benchmark / fund holdings feed | no clear direct equivalent in explored bundle | benchmark mapping needed | Keep current source or redesign benchmark pipeline | Gap / keep current source |

---

## Compatibility View Strategy

Where possible, preserve the current SAM contract by implementing views over S&P Capital IQ tables instead of rebuilding downstream logic.

| SAM Object | Candidate S&P Base Tables | Why a View May Work | Key Filters / Transformations | Downstream Preserved |
|------------|---------------------------|---------------------|-------------------------------|----------------------|
| `MARKET_DATA.FACT_SEC_FINANCIALS` | `ciqFinPeriod`, `ciqFinInstance`, `ciqFinInstanceToCollection`, `ciqFinCollection`, `ciqFinCollectionData`, `ciqDataItem` | Current SAM consumers need a flattened statement table, not raw CIQ hierarchy | filter latest instance, annual/quarterly periods, map CIQ `dataItemId` values to SAM financial fields | `SAM_RESEARCH_VIEW`, all consuming agents |
| `MARKET_DATA.FACT_SEC_SEGMENTS` | `ciqSegment`, `ciqSegCollectStandCmpntData`, `ciqSegmentClassification`, `ciqSegmentClassificationType` | Current SAM consumers need flattened business/geographic segment outputs | map segment classifications to SAM segment dimensions, preserve issuer/security linkages | `SAM_RESEARCH_VIEW`, all consuming agents |
| `MARKET_DATA.FACT_ESTIMATE_DATA` | `ciqEstimatePeriod`, `ciqEstimateConsensus`, `ciqEstimateNumericData`, `ciqEstimateCoverage` | Current SAM estimate tables are already synthetic/derived abstractions | flatten consensus and estimate points into current SAM shape, preserve ticker/company alignment | `SAM_RESEARCH_VIEW`, all consuming agents |
| `MARKET_DATA.FACT_ESTIMATE_CONSENSUS` | same as above | Consensus table is a natural fit for a view | filter current/open consensus (`toDate = 2079-06-06` pattern if used), aggregate by data item and period | `SAM_RESEARCH_VIEW`, all consuming agents |
| `MARKET_DATA.FACT_SEC_FILING_TEXT` | `filingRef`, `filingData`, `filingInstitutionRel` | Search service only needs the flattened filing text table | filter filing types of interest, preserve text/body and company/ticker fields | `SAM_REAL_SEC_FILINGS`, Portfolio/Research/Risk/PE/Private Credit agents |
| `CURATED.DIM_ISSUER` enrichment | `ciqCompany`, `ciqSymbolMapping`, `ciqSecurity`, `ciqTradingItem` | Current issuer/security layer can likely be preserved with identifier bridging | map `companyId` to ticker/CUSIP/ISIN and populate current issuer columns | nearly all semantic views and agents |

Recommendation: use compatibility views first for financials, segments, estimates, and filing text. Rebuild physical SAM tables only when performance or operational requirements make views impractical.

---

## Keep vs Replace Decisions

| Domain | Recommendation | Reason |
|--------|----------------|--------|
| Company master / identifiers | Replace with S&P | S&P provides strong company/security/symbol structure |
| Financial statements | Replace with S&P | Strong direct fit via premium financials |
| Segment financials | Replace with S&P | Strong direct fit via segment tables |
| Analyst estimates / consensus | Replace with S&P | Strong direct fit via estimates package |
| Filing text / metadata | Replace with S&P | Filing tables are a good structured replacement for SEC filing text |
| Prices | Replace with S&P if customer has the price/history package | High-value and foundational to returns/attribution |
| Dividends / corporate actions | Evaluate separately | Current implementation uses filing-text extraction; direct like-for-like replacement is less obvious |
| Insider transactions | Keep current source unless customer has an equivalent package | No clear replacement in explored bundle |
| Institutional holdings | Keep current source unless customer has an equivalent package | No clear replacement in explored bundle |
| Benchmark holdings | Keep current source or redesign separately | Not clearly covered by explored S&P package |
| FX / Treasury / BIS / macro / climate | Keep current source | These are not the natural strength of the explored S&P equity-research package |
| Company event transcripts / transcript search | Out of scope for this document | Requires document-copy/search redesign, not just table substitution |

---

## Downstream Preservation

If the SAM target contract is preserved, these downstream AI surfaces remain unchanged.

| SAM Target Table / View | Semantic Views Preserved | Search Services Preserved | Agents Preserved |
|-------------------------|--------------------------|---------------------------|------------------|
| `MARKET_DATA.FACT_STOCK_PRICES` | `SAM_MARKET_VIEW`, `SAM_PORTFOLIO_VIEW`, `SAM_PORTFOLIO_MODELLING_VIEW`, attribution and regime dependencies | none directly | Portfolio, Risk, Executive, Private Credit |
| `MARKET_DATA.FACT_SEC_FINANCIALS` | `SAM_RESEARCH_VIEW` | none directly | Portfolio, Research, Risk, Sales, Executive, PE, Private Credit |
| `MARKET_DATA.FACT_SEC_SEGMENTS` | `SAM_RESEARCH_VIEW` | none directly | Portfolio, Research, Risk, Sales, Executive, PE, Private Credit |
| `MARKET_DATA.FACT_ESTIMATE_DATA` | `SAM_RESEARCH_VIEW` | none directly | Portfolio, Research, Risk, Sales, Executive, PE, Private Credit |
| `MARKET_DATA.FACT_ESTIMATE_CONSENSUS` | `SAM_RESEARCH_VIEW` | none directly | Portfolio, Research, Risk, Sales, Executive, PE, Private Credit |
| `MARKET_DATA.FACT_SEC_FILING_TEXT` | none directly | `SAM_REAL_SEC_FILINGS` | Portfolio, Research, Risk, PE, Private Credit |
| `CURATED.DIM_ISSUER` enrichment | almost all semantic views through issuer/security joins | none directly | nearly all agents |

This is the main preservation story for customers: if these SAM-facing tables stay stable, the semantic views and agents can remain unchanged.

---

## Identifier Bridging

The current SAM demo is heavily ticker/CIK-centric. S&P Capital IQ is centred on `companyId` and related identifiers.

Recommended bridge objects:
- `BASE.ciqCompany`
- `BASE.ciqSecurity`
- `BASE.ciqTradingItem`
- `BASE.ciqSymbolMapping`

Recommended bridging strategy:

1. Map current SAM issuer identity into `companyId`
2. Preserve ticker/CUSIP/ISIN access through `ciqSymbolMapping`
3. Preserve SAM `DIM_ISSUER` / `DIM_SECURITY` as the stable identifier layer used by semantic views
4. Build S&P-backed financial/estimate/filing views keyed through that same SAM identifier layer

This is the single most important design step if the goal is to avoid downstream agent and semantic-view changes.

---

## Suggested Migration Sequence

1. Bridge identifiers from S&P (`companyId`, `ciqSecurity`, `ciqTradingItem`, `ciqSymbolMapping`) into the SAM issuer/security model
2. Replace or view-wrap `MARKET_DATA.FACT_STOCK_PRICES`
3. Replace or view-wrap `MARKET_DATA.FACT_SEC_FINANCIALS`
4. Replace or view-wrap `MARKET_DATA.FACT_SEC_SEGMENTS`
5. Replace or view-wrap `MARKET_DATA.FACT_ESTIMATE_DATA` and `FACT_ESTIMATE_CONSENSUS`
6. Replace or view-wrap `MARKET_DATA.FACT_SEC_FILING_TEXT`
7. Rebuild any dependent calculated SAM tables if required
8. Validate semantic views remain unchanged
9. Validate agents remain unchanged

---

## Notes and Gaps

- Transcript replacement is intentionally excluded from scope
- Some public-data-backed domains are better left on their current source rather than forced into S&P
- The exact price-history replacement depends on which S&P market data package the customer licenses
- Dividend/corporate action equivalence may require either a custom extraction pattern or a separate corporate-actions feed
- Insider holdings / institutional holdings may require additional licensed S&P datasets beyond the explored schema bundle