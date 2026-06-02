# FSI AM Research Agent Builder — Design Document

## Purpose

Enable a Snowflake customer to deploy an investment research Cortex Agent into their own account. The skill discovers what data the customer already has, maps it to the agent's building blocks, creates the required intermediate objects (semantic views, search services, procedures), and assembles a working agent — all without requiring the customer to understand our internal table naming or schema conventions.

---

## Agent Overview

The **Research Agent** is an investment research analyst that combines structured financial data with unstructured document search to produce comprehensive company analysis, investment memos, and equity research reports.

### Agent Capabilities

| Capability | Description | Data Required |
|------------|-------------|---------------|
| Financial statement analysis | Query revenue, margins, EPS, balance sheet, cash flow metrics | Financial Statements |
| Segment revenue analysis | Break down revenue by geography and business unit | Segment Revenue Data |
| Analyst estimate lookup | Consensus estimates, price targets, ratings | Analyst Estimates |
| Regulatory filing search | Full-text search of risk factors, management discussion, disclosures from regulatory filings (SEC, FCA, ESMA, etc.) | Company Filings and Disclosures |
| Earnings call search | Search management commentary by speaker and topic | Earnings Call Transcripts |
| Broker research search | Search analyst opinions, recommendations, sector themes | External Research Documents |
| PDF report generation | Generate branded investment memos from analysis | Procedure (no data dependency) |
| Data visualisation | Charts and tables from any query result | Always available |

### Agent Architecture

```
RESEARCH AGENT
├── Cortex Analyst Tools (structured queries via semantic views)
│   ├── financial_analyzer  → Semantic View → Financial Statements + Company Master
│   ├── sec_financials      → Semantic View → Financial Statements + Company Master
│   ├── fundamentals_analyzer → Semantic View → Financial Statements + Estimates + Analysts/Brokers + Company Master
│   └── segment_analyzer    → Semantic View → Segment Revenue + Company Master
├── Cortex Search Tools (unstructured document retrieval)
│   ├── search_filings         → Search Service → Company Filings corpus
│   ├── search_company_events → Search Service → Earnings Transcript corpus
│   └── search_external_docs  → Search Service → Research Document corpus
├── Custom Tools
│   └── pdf_generator → Stored Procedure (GENERATE_PDF_REPORT)
└── Platform Tools
    └── data_to_chart → Always available (Vega-Lite visualisation)
```

---

## Data Catalogue

Each data source below is described in business terms. A customer maps their own tables/views to these categories. The skill then creates the semantic views, search services, and agent wiring automatically.

### STRUCTURED DATA (queried via Cortex Analyst)

#### DS-1: Financial Statements (REQUIRED)

Standard financial statement data from regulatory filings or a data vendor. Financial data may follow US GAAP, IFRS, or local GAAP standards — the skill adapts to whatever accounting framework is present.

**What it contains:**
- Income statement: revenue, cost of goods sold, gross profit, operating income, net income, EPS (basic and diluted), R&D expense, interest expense, tax expense
- Balance sheet: total assets, total liabilities, stockholders' equity, cash and equivalents, long-term debt, goodwill, PP&E, current assets, current liabilities, retained earnings
- Cash flow statement: operating cash flow, investing cash flow, financing cash flow, capex, depreciation & amortisation, stock-based compensation
- Derived metrics: free cash flow, gross/operating/net margins, ROE, ROA, debt-to-equity ratio, current ratio, revenue growth rate, EBITDA

**Grain:** One row per company per fiscal period (annual FY or quarterly Q1-Q4).

**Required fields:**
- Company identifier (any: ticker, ISIN, LEI, CIK, internal ID)
- Fiscal period (year + quarter or period type)
- Period dates (start and end)
- At minimum: revenue, net income, total assets, total liabilities
- Reporting currency (important for non-USD reporting companies)

**Nice-to-have fields:**
- Full set of ~30 financial line items listed above
- Derived ratios (margins, leverage, profitability)
- Shares outstanding
- Filing reference (SEC accession number, Companies House filing ID, EDINET document ID)
- Accounting standard (US GAAP, IFRS, local GAAP)

**Typical customer sources:**
- US: SEC EDGAR XBRL
- UK: Companies House iXBRL filings
- EU: ESMA ESEF (inline XBRL), national regulators (BaFin, AMF, CONSOB)
- Japan: EDINET XBRL
- Global vendors: Bloomberg Terminal / Data License, Refinitiv / LSEG Workspace, S&P Capital IQ / Compustat, FactSet
- Snowflake Marketplace: Cybersyn SEC data, S&P Global, Bureau van Dijk (Orbis), etc.

---

#### DS-2: Segment Revenue (OPTIONAL)

Revenue broken down by business segment and/or geography from regulatory filings.

**What it contains:**
- Revenue by business segment (e.g., "Data Center", "Gaming", "Automotive")
- Revenue by geography (e.g., "United States", "Europe", "Asia Pacific")
- Revenue by customer (major customers disclosed in filings)
- Revenue by legal entity / subsidiary

**Grain:** One row per company per segment per fiscal period.

**Required fields:**
- Company identifier
- Fiscal year / quarter
- Segment type (geography, business segment, customer, legal entity)
- Segment name / label
- Revenue value
- Currency

**Typical customer sources:**
- SEC EDGAR XBRL segment data (US)
- IFRS 8 segment disclosures (international companies)
- Bloomberg segment revenue
- S&P Capital IQ segment data
- Manual extraction from annual reports / regulatory filings

---

#### DS-3: Analyst Consensus Estimates (OPTIONAL)

Forward-looking financial estimates aggregated across sell-side analysts.

**What it contains:**
- Consensus mean, low, and high estimates for key metrics (revenue, EPS, EBITDA)
- Number of contributing analysts per estimate
- Estimate target period (future quarter or year)

**Grain:** One row per company per metric per future period.

**Required fields:**
- Company identifier
- Metric type (revenue, EPS, net income, EBITDA)
- Estimate period (year + quarter)
- Consensus mean value

**Nice-to-have fields:**
- Consensus low and high
- Number of estimates
- As-of date (when consensus was calculated)

**Typical customer sources:**
- Bloomberg consensus estimates
- Refinitiv I/B/E/S
- FactSet consensus
- S&P Capital IQ estimates

---

#### DS-4: Individual Analyst Estimates (OPTIONAL, requires DS-3)

Price targets and stock ratings from individual sell-side analysts.

**What it contains:**
- Analyst name and broker firm
- Price target per company
- Stock rating (Buy/Outperform/Hold/Underperform/Sell or numeric scale)
- Estimate date

**Grain:** One row per analyst per company per estimate.

**Required fields:**
- Company identifier
- Analyst name or ID
- Broker firm name or ID
- Price target or rating value
- Estimate date

**Typical customer sources:**
- Bloomberg individual estimates
- Refinitiv StarMine
- FactSet analyst estimates
- TipRanks (via API or Marketplace)

---

#### DS-5: Company Master / Issuer Dimension (REQUIRED)

Master reference table for all companies in scope. Every other data source joins to this.

**What it contains:**
- Company identifiers (ISIN, LEI, ticker, SEDOL, CUSIP, CIK, internal ID)
- Legal name
- Industry classification (GICS sector, SIC code, ICB)
- Country of incorporation / domicile
- Exchange listing

**Grain:** One row per company.

**Required fields:**
- At least one stable identifier (ISIN, LEI, ticker, or internal ID)
- Company name
- Industry/sector classification

**Nice-to-have fields:**
- Multiple identifier types for cross-referencing
- Country
- LEI
- Active/inactive flag
- Corporate hierarchy (parent company)

**Typical customer sources:**
- Internal security master / reference data system
- GLEIF (Global LEI Foundation) — LEI registry
- Bloomberg FIGI / OpenFIGI
- Refinitiv PermID
- ANNA DSB (ISIN allocation)
- US: SEC EDGAR company index (CIK)
- UK: FCA register, Companies House
- EU: ESMA registers, national regulators
- Snowflake Marketplace: Cybersyn COMPANY_INDEX, Bureau van Dijk (Orbis)

---

### UNSTRUCTURED DATA (searched via Cortex Search)

#### DS-6: Company Filings and Disclosures (OPTIONAL)

Narrative text from mandatory regulatory filings — annual reports, interim reports, and material event disclosures. The specific filing types and section names vary by jurisdiction, but the business purpose is the same everywhere: searchable access to the qualitative narrative sections of company regulatory filings.

**What it contains:**

The narrative sections of regulatory filings contain risk factors, management discussion, business descriptions, governance statements, and forward-looking disclosures. Filing types vary by jurisdiction:

| Jurisdiction | Regulator | Annual Filing | Interim Filing | Event Filing | Governance / Proxy |
|-------------|-----------|---------------|----------------|--------------|-------------------|
| US | SEC | 10-K | 10-Q | 8-K | DEF 14A |
| UK | FCA / Companies House | Annual Report & Accounts | Half-year Report | RNS Announcement | Annual Report (governance section) |
| EU | ESMA / National regulators | ESEF Annual Report | Half-year Report (Transparency Directive) | Ad-hoc Disclosure (MAR) | Management Report |
| Japan | FSA / EDINET | Yuho (Annual Securities Report) | Shihanki Hokokusho (Quarterly Report) | Extraordinary Report | Yuho (governance section) |
| Hong Kong | HKEX | Annual Report | Interim Report | Announcement | Annual Report (CG Report) |
| Australia | ASX / ASIC | Annual Report + Appendix 4E | Half-year Report + Appendix 4D | Market Announcement | Annual Report (Remuneration Report) |
| Canada | CSA / SEDAR+ | AIF + Annual MD&A | Interim MD&A | Material Change Report | Information Circular |

Section names also vary across jurisdictions:

| Content | US (SEC) | UK (FCA) | EU (ESMA) |
|---------|----------|----------|-----------|
| Risk discussion | Risk Factors | Principal Risks and Uncertainties | Risk Report |
| Management narrative | MD&A | Strategic Report | Management Report |
| Business overview | Business Description | Business Review | Activity Report |
| Governance | DEF 14A (Proxy) | Corporate Governance Statement | Corporate Governance Statement |
| Forward guidance | Forward-Looking Statements | Viability Statement | Going Concern Assessment |

**Grain:** One row per filing section chunk (long sections split into ~4000 character chunks).

**Required fields:**
- Company identifier (ticker, ISIN, CIK, or internal ID)
- Filing / report type (e.g., annual report, interim report, event disclosure)
- Filing text content
- Fiscal year / period

**Nice-to-have fields:**
- Section name (e.g., "Risk Factors", "Strategic Report", "MD&A")
- Filing date / period end date
- Regulatory filing reference (accession number, RNS ID, EDINET code)
- Company name (denormalised for search)
- Sector (denormalised for search filtering)
- Document title (human-readable)
- Jurisdiction / regulatory body
- Language (important for non-English filings)

**Typical customer sources:**
- US: SEC EDGAR full-text feeds, Snowflake Marketplace (Cybersyn SEC text), Calcbench
- UK: Companies House filings, FCA RNS feed, London Stock Exchange
- EU: ESMA ESEF filings, national regulators (BaFin, AMF, CONSOB, CNMV)
- Japan: EDINET (FSA), Tokyo Stock Exchange TDnet
- Hong Kong: HKEX news / e-Disclosure
- Australia: ASX announcements platform, ASIC
- Canada: SEDAR+ filings
- Global: S&P Capital IQ filings, Bloomberg filings, Refinitiv filings, FactSet
- Internal: Compliance feeds, document management systems

---

#### DS-7: Earnings Call Transcripts (OPTIONAL)

Transcripts of company events segmented by speaker.

**What it contains:**
- Earnings call prepared remarks and Q&A
- Annual general meeting discussions
- Investor day presentations
- Capital markets day presentations
- Speaker identification (CEO, CFO, analyst asking questions)

**Note:** For non-English-speaking markets (Japan, continental Europe, Latin America, etc.), transcripts may be in the local language. If translation is needed, Cortex `AI_TRANSLATE` can be used as a preprocessing step before indexing.

**Grain:** One row per speaker turn chunk (long speaker turns split into chunks).

**Required fields:**
- Company identifier (ticker or name)
- Event date
- Transcript text content

**Nice-to-have fields:**
- Event type (Earnings Call, AGM, Investor Day)
- Speaker name
- Speaker role (CEO, CFO, VP, Analyst)
- Sector (denormalised for filtering)
- Document title
- Chunk/segment index

**Typical customer sources:**
- Refinitiv / LSEG transcripts
- S&P Capital IQ transcripts
- FactSet transcripts
- Bloomberg transcripts
- Snowflake Marketplace: Cybersyn transcript data
- Japan: Tokyo Stock Exchange TDnet disclosure service, EDINET
- Hong Kong: HKEX news
- Internal meeting notes / recordings (transcribed via speech-to-text)

---

#### DS-8: External Research Documents (OPTIONAL)

Broker research, press releases, and other external analysis documents parsed into searchable text.

**What it contains:**
- Broker/sell-side research reports (investment recommendations, sector analysis)
- Press releases (corporate announcements, product launches, M&A)
- NGO reports, ESG assessments, industry white papers

**Grain:** One row per document chunk (PDFs parsed and chunked).

**Required fields:**
- Document text content
- Document type / category

**Nice-to-have fields:**
- Company ticker / name (linked)
- Publish date
- Document title
- Sector
- Language
- Source / author

**Typical customer sources:**
- Internal research database / knowledge management system
- Bloomberg research
- Refinitiv research
- Broker portals (Goldman, JPMorgan, Morgan Stanley, etc.)
- PR Newswire / Business Wire feeds
- SharePoint / document management systems
- Email archives (parsed)

---

### CUSTOM PROCEDURE

#### DS-9: PDF Report Generator (OPTIONAL)

A stored procedure that accepts markdown content and produces a formatted PDF.

**What it does:** Takes three inputs — markdown content, report title, document audience — and returns a PDF file on a Snowflake stage.

**Dependencies:** Only needs a Snowflake stage for output. No data tables required.

**Customer alternative:** Skip this tool entirely if PDF generation is not needed. The agent works without it — reports are returned as formatted markdown in the chat.

---

## Data Source Priority

| Priority | Data Source | Impact if Missing |
|----------|-----------|-------------------|
| REQUIRED | DS-1: Financial Statements | No structured financial queries at all |
| REQUIRED | DS-5: Company Master | Cannot join any data sources together |
| HIGH | DS-6: Company Filings and Disclosures | No regulatory filing narrative search |
| HIGH | DS-7: Earnings Transcripts | No management commentary search |
| MEDIUM | DS-8: Research Documents | No broker research / press release search |
| MEDIUM | DS-2: Segment Revenue | No geographic/business segment breakdown |
| LOW | DS-3: Consensus Estimates | No forward-looking estimate queries |
| LOW | DS-4: Individual Estimates | No analyst-level price targets/ratings |
| OPTIONAL | DS-9: PDF Generator | Reports returned as markdown instead of PDF |

**Minimum viable agent:** DS-1 (Financial Statements) + DS-5 (Company Master) = one Cortex Analyst tool + data_to_chart. Functional but limited to structured financial queries.

**Recommended minimum:** DS-1 + DS-5 + at least one of DS-6/DS-7/DS-8 = structured queries + document search. This enables the multi-tool synthesis workflow that makes the agent genuinely useful.

---

## Skill Workflow (Proposed)

### Phase 1: Data Discovery and Mapping

1. Ask customer for target database, schema, warehouse
2. Present the data catalogue (DS-1 through DS-9) and ask which categories they have
3. For each category the customer has, ask them to identify their source table(s)
4. Validate the mapping: run `DESCRIBE TABLE` on each nominated table and confirm columns match the required fields
5. Record which data sources are available and which are missing

### Phase 2: Object Creation

For each mapped data source, create the required intermediate objects:

**Structured (DS-1 through DS-5):**
1. Create semantic view(s) over the customer's tables — adapting column references to match their schema
2. Semantic view definitions are generated dynamically based on discovered columns

**Unstructured (DS-6 through DS-8):**
1. Validate corpus table has required columns (text content, identifiers)
2. Create Cortex Search service over the corpus table
3. Configure indexed/filterable columns based on what exists

**Custom (DS-9):**
1. Create PDF generator procedure (or skip if customer doesn't want it)

### Phase 3: Agent Assembly

1. Generate tool specifications — only for enabled data sources
2. Generate tool descriptions — inspecting actual semantic views and search services
3. Generate instructions — adapted to reference only available tools
4. Calculate budget based on tool count
5. Execute `CREATE AGENT` SQL
6. Register with Snowflake Intelligence
7. Grant access to specified roles

### Phase 4: Verification

1. Test with a sample question appropriate to available tools
2. Validate response uses correct tools and returns sensible data

---

## Semantic View Templates

Each semantic view needs to be generated dynamically based on the customer's actual column names. The skill maintains a template for each that maps business concepts to customer columns.

### Template: Financial Statements View

Maps DS-1 (Financial Statements) + DS-5 (Company Master) into a semantic view for Cortex Analyst.

**Required joins:** Financial table joined to company master on a shared identifier.

**Entities:**
- Company dimension: name, ticker, sector, country
- Financial facts: revenue, net income, EPS, margins (whatever columns exist)
- Time dimension: fiscal year, quarter, period dates

**Metrics to expose:** All numeric financial columns found in the customer's table, plus any derived ratios.

### Template: Segment Revenue View

Maps DS-2 + DS-5. Revenue by segment/geography joined to company master.

### Template: Fundamentals View

Maps DS-1 + DS-3 + DS-4 + DS-5. Financial statements + estimates + analyst data joined to company master.

---

## Search Service Templates

### Template: Regulatory Filing Search

Source table must have: text content column, company identifier, filing/report type.
Optional: fiscal year, section name, filing date, jurisdiction, language.
Text column → vector index (searchable). Type/year/company/jurisdiction → filterable attributes.

### Template: Transcript Search

Source table must have: text content column, company identifier, event date.
Optional: event type, speaker name, speaker role.
Text column → vector index. Event type/speaker/company → filterable attributes.

### Template: Research Document Search

Source table must have: text content column, document type/category.
Optional: company identifier, publish date, title.
Text column → vector index. Doc type/company/date → filterable attributes.

---

## Open Questions

1. **Semantic view generation complexity**: ~~Should we use a template-based approach or a more intelligent inspection approach?~~ **RESOLVED**: Use YAML-based definitions with `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML`. The skill generates YAML dynamically, validates with `verify_only=TRUE`, then deploys. See `python/ai/yaml_loader.py` for the template engine pattern used in the SAM demo.

2. **Data transformation**: What if the customer's data isn't in the right shape? E.g., their financial data is in EAV format (metric name + value columns) rather than pivoted. Should the skill handle this or require pre-transformation?

3. **Corpus preparation**: Unstructured data often needs chunking before it can be indexed by Cortex Search. Should the skill include a chunking step, or require the customer to have pre-chunked corpus tables?

4. **Multi-agent**: Should the skill only build the Research Agent, or should it be extensible to other agent types (Portfolio, Executive, Compliance) using the same dependency-driven pattern?

5. **Update workflow**: When the customer adds new data sources later, how do they update the agent? Rerun the skill? Manual SQL?
