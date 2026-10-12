# S&P Capital IQ Column Mapping Specification

This document is the implementation-grade companion to [docs/sp_capital_iq_mapping.md](docs/sp_capital_iq_mapping.md).

It covers the first five highest-value SAM target tables:

1. `MARKET_DATA.FACT_SEC_FINANCIALS`
2. `MARKET_DATA.FACT_SEC_SEGMENTS`
3. `MARKET_DATA.FACT_ESTIMATE_CONSENSUS`
4. `MARKET_DATA.FACT_ESTIMATE_DATA`
5. `CURATED.DIM_ISSUER`

The goal is to give enough detail that a future implementation can replace the current public-data-backed upstream sources while preserving the SAM target contract and therefore avoiding changes to downstream semantic views and agents where possible.

---

## 1. Identifier Bridging

The current SAM demo is driven by `IssuerID`, `ProviderCompanyID`, `CIK`, and `PrimaryTicker`.

The S&P Capital IQ model is primarily centred on `companyId`, with supporting object types such as `securityId`, `tradingItemId`, and cross-reference records in `ciqSymbolMapping`.

### Recommended Bridge Layer

| SAM Concept | Current SAM Key | S&P Key / Table | Notes |
|-------------|-----------------|-----------------|-------|
| Issuer | `CURATED.DIM_ISSUER.IssuerID` | Derived internal key | Preserve as SAM-side surrogate key |
| External company identity | `CURATED.DIM_ISSUER.ProviderCompanyID` | `BASE.ciqCompany.companyId` | Best replacement for current provider company id |
| Ticker | `CURATED.DIM_ISSUER.PrimaryTicker` | `BASE.ciqSymbolMapping.symbolValue` or `BASE.ciqTradingItem` ticker field | Prefer symbol mapping as canonical bridge |
| Company name | `CURATED.DIM_ISSUER.LegalName` | `BASE.ciqCompany.companyName` | Preserve SAM naming column |
| Security identity | `CURATED.DIM_SECURITY.SecurityID` | Derived internal key | Keep stable in SAM |
| Instrument bridge | `CURATED.DIM_SECURITY.Ticker` | `BASE.ciqSecurity.securityId`, `BASE.ciqTradingItem.tradingItemId` | Needed for estimates and price joins |

### Recommended Rules

1. Keep `CURATED.DIM_ISSUER` and `CURATED.DIM_SECURITY` as the stable SAM-facing identity layer.
2. Use `ciqCompany.companyId` as the replacement for `ProviderCompanyID`.
3. Use `ciqSymbolMapping` as the canonical bridge for ticker/CUSIP/ISIN/SEDOL lookups.
4. Where downstream tables only need issuer-level linkage, anchor on `ProviderCompanyID = ciqCompany.companyId`.
5. Where downstream tables need market/security-level linkage, bridge through `ciqSecurity` and `ciqTradingItem`.

---

## 2. Mapping Template

Each target table section uses the same structure:

- Purpose
- Current SAM Contract
- Recommended S&P Source Tables
- Column Mapping
- Compatibility Strategy
- Downstream Preserved

Status language used in the column tables:
- `Direct mapping`
- `Derived mapping`
- `Requires transformation`
- `No clear equivalent`

---

## 3. `MARKET_DATA.FACT_SEC_FINANCIALS`

### Purpose

`FACT_SEC_FINANCIALS` is the core structured financial statement table feeding `SAM_RESEARCH_VIEW`. It flattens company-period financials into SAM-friendly rows with income statement, balance sheet, cash flow, share count, and derived metrics.

### Current SAM Contract

Key columns:
- `IssuerID`
- `CIK`
- `ADSH`
- `PERIOD_END_DATE`
- `PERIOD_START_DATE`
- `COVERED_QTRS`
- `FISCAL_PERIOD`
- `PERIOD_TYPE`
- `FISCAL_YEAR`
- `CURRENCY`
- `REVENUE`
- `NET_INCOME`
- `GROSS_PROFIT`
- `OPERATING_INCOME`
- `EPS_BASIC`
- `EPS_DILUTED`
- `RD_EXPENSE`
- `INTEREST_EXPENSE`
- `INCOME_TAX_EXPENSE`
- `TOTAL_ASSETS`
- `TOTAL_LIABILITIES`
- `TOTAL_EQUITY`
- `CASH_AND_EQUIVALENTS`
- `LONG_TERM_DEBT`
- `GOODWILL`
- `PP_AND_E`
- `CURRENT_ASSETS`
- `CURRENT_LIABILITIES`
- `RETAINED_EARNINGS`
- `OPERATING_CASH_FLOW`
- `INVESTING_CASH_FLOW`
- `FINANCING_CASH_FLOW`
- `CAPEX`
- `DEPRECIATION_AMORTIZATION`
- `SHARE_BASED_COMP`
- `SHARES_OUTSTANDING`
- `EBITDA`
- `FCF`
- `NET_DEBT`
- `ROIC`
- `TAM`
- `ESTIMATED_CUSTOMER_COUNT`
- `ESTIMATED_NRR_PCT`
- `DATA_SOURCE`
- `LOADED_AT`

### Recommended S&P Source Tables

- `BASE.ciqCompany`
- `FINANCIALS.ciqFinPeriod`
- `FINANCIALS.ciqFinInstance`
- `FINANCIALS.ciqFinInstanceToCollection`
- `FINANCIALS.ciqFinCollection`
- `FINANCIALS.ciqFinCollectionData`
- `BASE.ciqDataItem`
- `BASE.ciqDataItemFinancial`

### Column Mapping

| SAM Column | S&P Source Table | S&P Source Column | Join / Filter | Transformation | Status | Notes |
|-----------|------------------|-------------------|---------------|----------------|--------|-------|
| `IssuerID` | `CURATED.DIM_ISSUER` | `IssuerID` | `DIM_ISSUER.ProviderCompanyID = ciqCompany.companyId` | direct join back into SAM identity layer | Direct mapping | Preserve SAM surrogate key |
| `CIK` | `CURATED.DIM_ISSUER` | `CIK` | via issuer bridge | direct | Direct mapping | Prefer SAM identity layer over rebuilding from CIQ |
| `ADSH` | n/a | n/a | — | null or synthetic filing reference | No clear equivalent | S&P does not use SEC `ADSH` equivalently |
| `PERIOD_END_DATE` | `FINANCIALS.ciqFinPeriod` | period end date field | `companyId -> financialPeriodId` | direct | Direct mapping | Confirm exact CIQ column name during implementation |
| `PERIOD_START_DATE` | `FINANCIALS.ciqFinPeriod` | period start date field | same | direct | Direct mapping | Confirm exact CIQ column name during implementation |
| `COVERED_QTRS` | `FINANCIALS.ciqFinPeriod` / `ciqFinInstance` | period metadata | same | derive from period span/type | Derived mapping | Needed to preserve current SAM period classification |
| `FISCAL_PERIOD` | `FINANCIALS.ciqFinPeriod` | fiscal period columns | same | direct or derived | Direct mapping | |
| `PERIOD_TYPE` | `FINANCIALS.ciqFinPeriod` | period type columns | same | map annual / quarterly / cumulative | Requires transformation | |
| `FISCAL_YEAR` | `FINANCIALS.ciqFinPeriod` | fiscal year | same | direct | Direct mapping | |
| `CURRENCY` | `FINANCIALS.ciqFinCollectionData` / collection metadata | currency field | through collection path | normalize to SAM format | Requires transformation | |
| `REVENUE` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | revenue `dataItemId` | filter by data item | Direct mapping | Requires data-item dictionary |
| `NET_INCOME` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | net income item | filter by data item | Direct mapping | |
| `GROSS_PROFIT` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | gross profit item | filter by data item | Direct mapping | |
| `OPERATING_INCOME` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | operating income item | filter by data item | Direct mapping | |
| `EPS_BASIC` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | EPS basic item | filter by data item | Direct mapping | |
| `EPS_DILUTED` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | EPS diluted item | filter by data item | Direct mapping | |
| `RD_EXPENSE` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | R&D item | filter by data item | Direct mapping | |
| `INTEREST_EXPENSE` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | interest expense item | filter by data item | Direct mapping | |
| `INCOME_TAX_EXPENSE` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | tax expense item | filter by data item | Direct mapping | |
| `TOTAL_ASSETS` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | total assets item | filter by data item | Direct mapping | |
| `TOTAL_LIABILITIES` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | total liabilities item | filter by data item | Direct mapping | |
| `TOTAL_EQUITY` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | equity item | filter by data item | Direct mapping | |
| `CASH_AND_EQUIVALENTS` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | cash item | filter by data item | Direct mapping | |
| `LONG_TERM_DEBT` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | debt item | filter by data item | Direct mapping | |
| `GOODWILL` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | goodwill item | filter by data item | Direct mapping | |
| `PP_AND_E` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | PP&E item | filter by data item | Direct mapping | |
| `CURRENT_ASSETS` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | current assets item | filter by data item | Direct mapping | |
| `CURRENT_LIABILITIES` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | current liabilities item | filter by data item | Direct mapping | |
| `RETAINED_EARNINGS` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | retained earnings item | filter by data item | Direct mapping | |
| `OPERATING_CASH_FLOW` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | CFO item | filter by data item | Direct mapping | |
| `INVESTING_CASH_FLOW` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | CFI item | filter by data item | Direct mapping | |
| `FINANCING_CASH_FLOW` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | CFF item | filter by data item | Direct mapping | |
| `CAPEX` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | capex item | filter by data item | Direct mapping | |
| `DEPRECIATION_AMORTIZATION` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | D&A item | filter by data item | Direct mapping | |
| `SHARE_BASED_COMP` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | SBC item | filter by data item | Direct mapping | |
| `SHARES_OUTSTANDING` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | share count item | filter by data item | Direct mapping | |
| `EBITDA` | `FINANCIALS.ciqFinCollectionData` | `dataItemValue` | direct if available, else derived | direct or derived | Requires transformation | |
| `FCF` | derived | derived | OCF - capex | calculate | Derived mapping | |
| `NET_DEBT` | derived | derived | debt - cash | calculate | Derived mapping | |
| `ROIC` | derived | derived | operating profit / invested capital | calculate | Derived mapping | |
| `TAM` | no structured CIQ equivalent obvious | — | — | retain current SAM derivation if needed | No clear equivalent | |
| `ESTIMATED_CUSTOMER_COUNT` | no structured CIQ equivalent obvious | — | — | retain current SAM derivation if needed | No clear equivalent | |
| `ESTIMATED_NRR_PCT` | no structured CIQ equivalent obvious | — | — | retain current SAM derivation if needed | No clear equivalent | |
| `DATA_SOURCE` | constant | constant | — | set to `SP_CAPITAL_IQ_FINANCIALS` | Requires transformation | |
| `LOADED_AT` | system timestamp | current timestamp | — | direct | Derived mapping | |

### Compatibility Strategy

Preferred approach: **compatibility view over S&P tables**.

### Downstream Preserved

If the SAM contract is preserved:
- `SAM_RESEARCH_VIEW` can remain unchanged
- Portfolio, Research, Risk, Sales, Executive, PE, and Private Credit agents can remain unchanged for financial-statement access

---

## 4. `MARKET_DATA.FACT_SEC_SEGMENTS`

### Purpose

`FACT_SEC_SEGMENTS` provides issuer-linked business and geographic segment revenue rows used by `SAM_RESEARCH_VIEW`.

### Current SAM Contract

Key columns:
- `SEGMENT_ID`
- `IssuerID`
- `ADSH`
- `PERIOD_START_DATE`
- `PERIOD_END_DATE`
- `FISCAL_PERIOD`
- `FISCAL_YEAR`
- `FREQUENCY`
- `VARIABLE_NAME`
- `TAG`
- `MEASURE`
- `GEOGRAPHY`
- `BUSINESS_SEGMENT`
- `BUSINESS_SUBSEGMENT`
- `CUSTOMER`
- `LEGAL_ENTITY`
- `SEGMENT_REVENUE`
- `CURRENCY`
- `AI_REVENUE_FLAG`
- `DATA_SOURCE`
- `LOADED_AT`

### Recommended S&P Source Tables

- `FINANCIALS.ciqSegment`
- `FINANCIALS.ciqSegCollectStandCmpntData`
- `FINANCIALS.ciqSegmentClassification`
- `FINANCIALS.ciqSegmentClassificationType`
- `BASE.ciqCompany`

### Column Mapping

| SAM Column | S&P Source Table | S&P Source Column | Join / Filter | Transformation | Status | Notes |
|-----------|------------------|-------------------|---------------|----------------|--------|-------|
| `SEGMENT_ID` | derived | row_number | after flattening | generate surrogate key | Derived mapping | |
| `IssuerID` | `CURATED.DIM_ISSUER` | `IssuerID` | `ProviderCompanyID = ciqCompany.companyId` | direct join | Direct mapping | |
| `ADSH` | n/a | n/a | — | null or synthetic filing reference | No clear equivalent | |
| `PERIOD_START_DATE` | financial period tables | period start | company -> period -> collection | direct | Direct mapping | |
| `PERIOD_END_DATE` | financial period tables | period end | same | direct | Direct mapping | |
| `FISCAL_PERIOD` | financial period tables | fiscal period | same | direct/derived | Direct mapping | |
| `FISCAL_YEAR` | financial period tables | fiscal year | same | direct | Direct mapping | |
| `FREQUENCY` | financial period tables | period frequency/type | same | normalise to SAM values | Requires transformation | |
| `VARIABLE_NAME` | `BASE.ciqDataItem` | data item name | via segment financial item join | direct | Direct mapping | |
| `TAG` | `BASE.ciqDataItem` | data item identifier | same | direct | Direct mapping | |
| `MEASURE` | `BASE.ciqDataItem` | description / measure label | same | direct | Direct mapping | |
| `GEOGRAPHY` | `FINANCIALS.ciqSegmentClassification` | geography classification | `segmentId` + classification type | flatten | Requires transformation | |
| `BUSINESS_SEGMENT` | `FINANCIALS.ciqSegment` / classification | segment name | `segmentId` | flatten | Direct mapping | |
| `BUSINESS_SUBSEGMENT` | `FINANCIALS.ciqSegmentClassification` | subtype/classification detail | same | flatten | Requires transformation | |
| `CUSTOMER` | `FINANCIALS.ciqSegmentClassification` | customer-type classification | same | flatten | Requires transformation | |
| `LEGAL_ENTITY` | `FINANCIALS.ciqSegmentClassification` | legal-entity classification | same | flatten | Requires transformation | |
| `SEGMENT_REVENUE` | `FINANCIALS.ciqSegCollectStandCmpntData` | `dataItemValue` | segment revenue rows | direct | Direct mapping | |
| `CURRENCY` | segment financial data / collection metadata | currency field | through collection path | normalize | Requires transformation | |
| `AI_REVENUE_FLAG` | derived | derived | business segment text heuristic | calculate | Derived mapping | |
| `DATA_SOURCE` | constant | constant | — | set to `SP_CAPITAL_IQ_SEGMENTS` | Requires transformation | |
| `LOADED_AT` | system timestamp | current timestamp | — | direct | Derived mapping | |

### Compatibility Strategy

Preferred approach: **compatibility view over S&P segment tables**.

### Downstream Preserved

If the SAM contract is preserved:
- `SAM_RESEARCH_VIEW` remains unchanged
- Portfolio, Research, Risk, Sales, Executive, PE, and Private Credit agents remain unchanged for segment analysis

---

## 5. `MARKET_DATA.FACT_ESTIMATE_CONSENSUS`

### Purpose

`FACT_ESTIMATE_CONSENSUS` provides forward-looking consensus metrics at issuer, year, quarter, and data-item grain.

### Current SAM Contract

Key columns:
- `CONSENSUS_ID`
- `IssuerID`
- `ESTIMATE_YEAR`
- `FISCAL_QUARTER`
- `DATA_ITEM_ID`
- `ESTIMATE_TYPE`
- `CONSENSUS_MEAN`
- `CONSENSUS_LOW`
- `CONSENSUS_HIGH`
- `NUM_ESTIMATES`
- `AS_OF_DATE`
- `LAST_UPDATED`

### Recommended S&P Source Tables

- `ESTIMATES.ciqEstimatePeriod`
- `ESTIMATES.ciqEstimateConsensus`
- `ESTIMATES.ciqEstimateNumericData`
- `BASE.ciqDataItemEstimate`
- `BASE.ciqDataItem`

### Column Mapping

| SAM Column | S&P Source Table | S&P Source Column | Join / Filter | Transformation | Status | Notes |
|-----------|------------------|-------------------|---------------|----------------|--------|-------|
| `CONSENSUS_ID` | `ciqEstimateConsensus` | `estimateConsensusId` | issuer/trading item join | direct or rekey | Direct mapping | |
| `IssuerID` | `CURATED.DIM_ISSUER` | `IssuerID` | `ProviderCompanyID = ciqEstimatePeriod.companyId` | direct join | Direct mapping | |
| `ESTIMATE_YEAR` | `ciqEstimatePeriod` | estimate period year | company -> estimate period | direct | Direct mapping | |
| `FISCAL_QUARTER` | `ciqEstimatePeriod` | quarter / period field | same | direct/derived | Direct mapping | |
| `DATA_ITEM_ID` | `ciqEstimateNumericData` / `ciqDataItemEstimate` | `dataItemId` | same | direct | Direct mapping | |
| `ESTIMATE_TYPE` | `BASE.ciqDataItem` | item name | data item join | direct | Direct mapping | |
| `CONSENSUS_MEAN` | `ciqEstimateNumericData` | `dataItemValue` | current/open consensus filter | direct | Direct mapping | |
| `CONSENSUS_LOW` | `ciqEstimateNumericData` | numeric value | low-estimate item / variant | direct or derived | Requires transformation | |
| `CONSENSUS_HIGH` | `ciqEstimateNumericData` | numeric value | high-estimate item / variant | direct or derived | Requires transformation | |
| `NUM_ESTIMATES` | `ciqEstimateCoverage` or support rows | coverage/count field | consensus join | direct or derived | Requires transformation | |
| `AS_OF_DATE` | `ciqEstimateNumericData` | `effectiveDate` | filter to current estimate row | direct | Direct mapping | |
| `LAST_UPDATED` | system timestamp or source date | timestamp | — | direct/derived | Derived mapping | |

### Compatibility Strategy

Preferred approach: **compatibility view over S&P estimates tables**.

### Downstream Preserved

If the SAM contract is preserved:
- `SAM_RESEARCH_VIEW` remains unchanged
- all estimate-consuming agents remain unchanged

---

## 6. `MARKET_DATA.FACT_ESTIMATE_DATA`

### Purpose

`FACT_ESTIMATE_DATA` holds more atomic estimate outputs such as price targets and ratings by analyst and broker.

### Current SAM Contract

Key columns:
- `ESTIMATE_ID`
- `IssuerID`
- `ANALYST_ID`
- `BROKER_ID`
- `DATA_ITEM_ID`
- `DATA_VALUE`
- `ESTIMATE_DATE`
- `LAST_UPDATED`

### Recommended S&P Source Tables

- `ESTIMATES.ciqEstimateCoverage`
- `ESTIMATES.ciqEstimateConsensus`
- `ESTIMATES.ciqEstimateNumericData`
- `BASE.ciqDataItemEstimate`
- `BASE.ciqTradingItem`

### Column Mapping

| SAM Column | S&P Source Table | S&P Source Column | Join / Filter | Transformation | Status | Notes |
|-----------|------------------|-------------------|---------------|----------------|--------|-------|
| `ESTIMATE_ID` | derived or source row id | estimate row key | coverage / consensus join | direct or generated | Derived mapping | |
| `IssuerID` | `CURATED.DIM_ISSUER` | `IssuerID` | via `companyId` bridge | direct join | Direct mapping | |
| `ANALYST_ID` | `ciqEstimateCoverage` | analyst id | issuer/trading item join | direct | Direct mapping | |
| `BROKER_ID` | `ciqEstimateCoverage` | broker id | same | direct | Direct mapping | |
| `DATA_ITEM_ID` | `ciqEstimateNumericData` | `dataItemId` | same | direct | Direct mapping | |
| `DATA_VALUE` | `ciqEstimateNumericData` | `dataItemValue` | same | direct | Direct mapping | |
| `ESTIMATE_DATE` | `ciqEstimateNumericData` | `effectiveDate` | same | direct | Direct mapping | |
| `LAST_UPDATED` | system timestamp or source date | timestamp | — | direct/derived | Derived mapping | |

### Compatibility Strategy

Preferred approach: **compatibility view over S&P estimate tables**.

### Downstream Preserved

If the SAM contract is preserved:
- `SAM_RESEARCH_VIEW` remains unchanged
- downstream analyst / broker / rating use cases remain unchanged

---

## 7. `CURATED.DIM_ISSUER`

### Purpose

`DIM_ISSUER` is the central issuer master in the SAM demo and anchors almost every downstream join into semantic views and agents.

### Current SAM Contract

Key columns:
- `IssuerID`
- `UltimateParentIssuerID`
- `ProviderCompanyID`
- `CIK`
- `PrimaryTicker`
- `LegalName`
- `SIC_DESCRIPTION`
- `GICS_SECTOR`
- `CountryOfIncorporation`
- `LEI`
- `Tier`

### Recommended S&P Source Tables

- `BASE.ciqCompany`
- `BASE.ciqSecurity`
- `BASE.ciqTradingItem`
- `BASE.ciqSymbolMapping`
- `BASE.ciqCompanyData` and related company reference tables where needed

### Column Mapping

| SAM Column | S&P Source Table | S&P Source Column | Join / Filter | Transformation | Status | Notes |
|-----------|------------------|-------------------|---------------|----------------|--------|-------|
| `IssuerID` | derived | row number / persisted SAM key | after bridge build | preserve existing SAM surrogate key | Derived mapping | Should remain SAM-owned |
| `UltimateParentIssuerID` | parent-company relationship table if available | parent company id | company relationship join | map to SAM issuer key if used | Requires transformation | may remain null if not essential |
| `ProviderCompanyID` | `BASE.ciqCompany` | `companyId` | primary company row | direct | Direct mapping | critical bridge key |
| `CIK` | `BASE.ciqSymbolMapping` or company reference data | CIK-like symbol value | filter symbol type | direct if available | Requires transformation | verify actual CIQ source |
| `PrimaryTicker` | `BASE.ciqSymbolMapping` or `BASE.ciqTradingItem` | ticker symbol | primary trading item / ticker mapping | direct | Direct mapping | |
| `LegalName` | `BASE.ciqCompany` | `companyName` | primary company row | direct | Direct mapping | |
| `SIC_DESCRIPTION` | company classification reference | industry description | company join | direct/derived | Requires transformation | depends on available CIQ taxonomy |
| `GICS_SECTOR` | company classification reference | sector field | company join | direct/derived | Requires transformation | may require taxonomy mapping |
| `CountryOfIncorporation` | `BASE.ciqCompany` / company data | country field | company join | direct | Direct mapping | |
| `LEI` | company reference data | LEI field | company join | direct | Direct mapping | if available in licensed package |
| `Tier` | current SAM company seed | tier field | keep current SAM seed logic | retain current value | No clear equivalent | SAM demo construct, not an S&P construct |

### Compatibility Strategy

Preferred approach: **preserve `DIM_ISSUER` physically as the SAM bridge table**, populated from S&P company master data plus current SAM seed logic where needed (`Tier`).

### Downstream Preserved

If `DIM_ISSUER` is preserved:
- almost all semantic views remain join-compatible
- `DIM_SECURITY` can continue to derive from the same issuer contract
- downstream agents remain unchanged for issuer/company identity handling

---

## 8. Cross-Table Caveats

| Topic | Guidance |
|-------|----------|
| Latest financial instance | Use the S&P latest/current instance logic rather than blindly taking all filings |
| Annual vs quarterly periods | Preserve current SAM annual/quarterly semantics explicitly in the compatibility layer |
| Current/open consensus | Define one canonical filter for current consensus rows and reuse it across estimate views |
| Segment classifications | Business, geography, customer, and legal entity classifications may need flattening into SAM-style columns |
| Derived SAM metrics | `TAM`, `ESTIMATED_CUSTOMER_COUNT`, and `ESTIMATED_NRR_PCT` likely remain SAM-side derived fields |
| Missing fields | If no clean S&P equivalent exists, document it explicitly instead of forcing a weak mapping |

---

## 9. What This Enables

With this document plus the overview in `docs/sp_capital_iq_mapping.md`, a future implementation task should be able to:

1. decide whether a target is best rebuilt physically or exposed as a compatibility view
2. map the first five highest-value structured SAM targets onto S&P Capital IQ
3. preserve `SAM_RESEARCH_VIEW` and the major agents that depend on it without changing their definitions