---
doc_type: "ops_procedures"
linkage_level: "global"
word_count_target: 1100
template_name: "Net Asset Value (NAV) Calculation Procedure"
---


# Net Asset Value (NAV) Calculation Procedure
**Document Type:** Standard Operating Procedure  
**Procedure ID:** SOP-MO-002  
**Version:** 3.2  
**Effective Date:** 01 January 2024  
**Last Updated:** 15 October 2024  
**Owner:** Middle Office Operations

## Purpose
This procedure defines the daily process for calculating and publishing Net Asset Value (NAV) for all Simulated Asset Management portfolios.

## Scope
Applies to all fund NAV calculations including equity, fixed income, multi-asset, and alternative investment portfolios.

## Calculation Frequency
- **Daily NAV:** All open-ended funds
- **Weekly NAV:** Certain alternative strategies
- **Monthly NAV:** Private market funds

## Timing Requirements
- **Market Close:** 16:00 (London), 21:00 (New York)
- **Data Complete:** T+2 hours after market close
- **NAV Calculation:** Complete by T+3 hours
- **NAV Publication:** By T+4 hours (20:00 London / 01:00 New York)

## Roles and Responsibilities

### NAV Analyst
- Execute daily NAV calculation
- Reconcile positions and cash
- Identify and investigate anomalies
- Prepare NAV report
- Submit for approval

### NAV Manager
- Review NAV calculations
- Approve or reject NAV
- Investigate material variances
- Authorize publication
- Sign off on month-end NAV

### Fund Accountant
- Verify expense accruals
- Review income postings
- Confirm corporate actions processed
- Validate pricing sources

## Prerequisites

### Data Requirements
1. **Position Data**
   - Settled positions from custodian
   - Pending trades (T to T+3)
   - Corporate action adjustments

2. **Pricing Data**
   - Security prices from Bloomberg
   - FX rates as of 16:00 London (WM/Reuters)
   - Fair value prices for illiquid securities

3. **Cash Balances**
   - Custodian cash statements
   - Pending cash movements
   - Income receivables

4. **Expense Accruals**
   - Management fees
   - Performance fees
   - Operating expenses

## Procedure Steps

### Step 1: Data Collection and Validation (T+0 to T+2 hours)

1. **Import Custodian Data**
   - Download position files from BNY Mellon Nexen
   - Import into NAV system (SimCorp Dimension)
   - Verify record counts match expected

2. **Import Pricing Data**
   - Load prices from Bloomberg
   - Import FX rates from WM/Reuters
   - Flag securities without prices

3. **Reconcile Positions**
   - Match custodian positions to internal records
   - Investigate breaks >100 shares or 0.01%
   - Document reconciliation items

4. **Validate Cash Balances**
   - Reconcile cash by currency
   - Verify pending settlements
   - Confirm income receipts

**Quality Checks:**
- Position count within expected range
- Total market value within 5% of prior day
- No missing prices for material holdings (>1%)
- Cash balances reconciled

**Output:** Reconciliation report, exception list

### Step 2: NAV Calculation (T+2 to T+3 hours)

1. **Calculate Gross Asset Value (GAV)**
   ```
   GAV = (Securities Market Value) + (Cash) + (Receivables) - (Payables)
   ```

2. **Calculate Accrued Expenses**
   - Daily management fee accrual = (AUM × Annual Fee Rate) / 365
   - Performance fee accrual (if applicable)
   - Audit and custody fee accruals

3. **Calculate Net Asset Value (NAV)**
   ```
   NAV = GAV - Accrued Expenses - Other Liabilities
   ```

4. **Calculate NAV per Share**
   ```
   NAV per Share = NAV / Shares Outstanding
   ```

5. **Calculate Returns**
   - Daily return = (NAV per Share today / NAV per Share yesterday) - 1
   - MTD return
   - YTD return

**Validation Checks:**
- NAV variance vs prior day within expected range
- Expense accruals calculated correctly
- Share count matches registry
- Returns calculation verified

### Step 3: Anomaly Detection and Investigation (T+2.5 to T+3 hours)

**Anomaly Thresholds:**
- NAV per share change >2% (typical: 2%)
- Total return outside 1.5× market index return
- Unexplained cash movement >£100,000
- Position break >£50,000

**Investigation Process:**
1. Identify anomaly type (price, position, cash, expense)
2. Check for corporate actions on anomaly date
3. Review large trades or redemptions
4. Verify pricing sources for material holdings
5. Confirm calculation formulas
6. Document findings

**Resolution:**
- If explainable: Document explanation, proceed to approval
- If data error: Correct data, recalculate NAV
- If pricing issue: Obtain fair value price, recalculate
- If unexplainable: Escalate to NAV Manager, do not publish

### Step 4: NAV Review and Approval (T+3 to T+3.5 hours)

1. **NAV Analyst Review**
   - Verify all checks completed
   - Confirm anomalies investigated
   - Prepare NAV approval memo

2. **NAV Manager Approval**
   - Review calculation summary
   - Check variance explanations
   - Verify material items
   - Approve or reject NAV

**Approval Criteria:**
- All reconciliation breaks resolved or documented
- Anomalies investigated and explained
- Pricing validated for material holdings
- Returns reasonable vs market and peers

### Step 5: NAV Publication (T+3.5 to T+4 hours)

1. **System Updates**
   - Post NAV to SimCorp Dimension
   - Update fund accounting system
   - Upload to administrator platform

2. **External Distribution**
   - Publish to pricing services (Bloomberg, Refinitiv)
   - Post to investor portal
   - Send to fund administrator
   - Update company website

3. **Internal Distribution**
   - Email NAV summary to:
     - Portfolio managers
     - Client services
     - Risk management
     - Senior management

4. **Regulatory Reporting**
   - Submit to FCA (if required)
   - Post to fund website (UCITS requirement)

### Step 6: Month-End Procedures (Monthly, T+5 hours)

Additional month-end requirements:
- Full expense reconciliation
- Performance fee calculation (if applicable)
- Audit trail documentation
- Board reporting package
- Investor statement preparation

## Quality Controls

### Dual Review
- All NAVs >£100M require dual approval
- Month-end NAVs require CFO sign-off
- Quarter-end NAVs reviewed by audit committee

### Exception Reporting
Document and escalate:
- NAV calculations not completed by deadline
- Unresolved anomalies
- Repeated pricing issues
- Systemic data problems

## Contingency Procedures

### Delayed Data
If custodian data delayed:
1. Use prior day positions with today's prices
2. Adjust for known trades
3. Note estimation in NAV report
4. Recalculate when data available

### Pricing Failures
If prices unavailable:
1. Use prior day price (if market closed)
2. Use broker quote (if liquid security)
3. Use model price (if available)
4. Escalate to valuation committee if material

### System Failures
If NAV system unavailable:
1. Activate manual calculation spreadsheet
2. Follow same calculation steps
3. Implement additional dual checks
4. Document manual calculation reason

## Reporting Requirements

### Daily Reports
- NAV summary by portfolio
- Daily return calculations
- Anomaly explanations
- Reconciliation status

### Weekly Reports
- NAV trend analysis
- Pricing quality metrics
- Anomaly summary

### Monthly Reports
- Comprehensive NAV pack
- Performance attribution
- Expense analysis
- Audit documentation

## Key Performance Indicators
- NAV published on time: Target 100%
- NAV restatements: Target <1 per year per fund
- Pricing coverage: Target >99% of holdings
- Reconciliation breaks: Target <0.1% of positions

## Contact Information
**NAV Team:** nav.team@sam-demo.example  
**NAV Manager:** Sarah Mitchell  
**After Hours:** +44 20 7123 4567 (24/7 operations line)

## Document Control
**Author:** Middle Office Operations Team  
**Reviewed By:** Head of Middle Office  
**Approved By:** Chief Operating Officer  
**Next Review Date:** 31 March 2025

---

**Document Reference:** SAM-MO-SOP-002-v3.2  
**Related Procedures:** SOP-MO-001 (Settlement Failures), SOP-MO-003 (Reconciliation)

