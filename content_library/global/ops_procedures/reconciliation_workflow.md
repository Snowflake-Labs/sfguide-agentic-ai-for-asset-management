---
doc_type: "ops_procedures"
linkage_level: "global"
word_count_target: 1100
template_name: "Daily Reconciliation Workflow Procedure"
---


# Daily Reconciliation Workflow Procedure
**Document Type:** Standard Operating Procedure  
**Procedure ID:** SOP-MO-003  
**Version:** 3.2  
**Effective Date:** 01 January 2024  
**Last Updated:** 15 October 2024  
**Owner:** Middle Office Operations

## Purpose
This procedure defines the daily reconciliation process for portfolio positions, cash balances, and transactions between internal records and custodian reports.

## Scope
All Simulated Asset Management portfolios across all asset classes and custodians.

## Reconciliation Frequency
- **Positions:** Daily
- **Cash:** Daily
- **Transactions:** Daily
- **Pricing:** Daily
- **Corporate Actions:** Event-driven

## Timing Requirements
- **Start Time:** 08:00 (after custodian files received)
- **Completion Target:** 11:00 (before NAV calculation)
- **Escalation Deadline:** 12:00 (for unresolved breaks)

## Roles and Responsibilities

### Reconciliation Analyst
- Execute daily reconciliation process
- Identify and log breaks
- Investigate discrepancies
- Resolve standard breaks
- Escalate material breaks

### Operations Manager
- Review break reports
- Approve break resolutions
- Coordinate with custodians
- Sign off on aged breaks

### Fund Accountant
- Validate accounting entries
- Post reconciliation adjustments
- Maintain audit trail

## Prerequisites

### System Access
- BNY Mellon Nexen - Custodian portal
- SmartStream TLM - Reconciliation tool
- SimCorp Dimension - Fund accounting
- Microsoft Outlook - Communication

### Data Files Required
- Custodian position file (daily, by 07:00)
- Custodian cash statement (daily, by 07:00)
- Custodian transaction file (daily, by 07:00)
- Internal position file (from SimCorp Dimension)
- Internal cash ledger

## Procedure Steps

### Step 1: Position Reconciliation (08:00 - 09:30)

1. **Import Data Files**
   ```
   - Download custodian files from BNY Mellon Nexen
   - Import into SmartStream TLM
   - Load internal positions from SimCorp Dimension
   - Verify file completeness and dates
   ```

2. **Execute Position Match**
   - Match by ISIN/CUSIP
   - Compare quantities
   - Identify breaks

3. **Classify Breaks**
   - **Type A:** Quantity mismatch (Internal ≠ Custodian)
   - **Type B:** Security in internal records only
   - **Type C:** Security in custodian records only
   - **Type D:** Both sides zero but reported differently

4. **Break Prioritization**
   - **Critical:** Variance >10% or >£1M
   - **High:** Variance >5% or >£500K
   - **Medium:** Variance >1% or >£100K
   - **Low:** All other breaks

**Output:** Position break report

### Step 2: Position Break Investigation (09:00 - 10:30)

**Common Break Causes and Resolution:**

#### Pending Trades (Type A - Internal>Custodian)
- **Cause:** Trade executed but not yet settled
- **Resolution:** Verify trade is settling, mark as timing difference
- **Action:** Monitor for settlement

#### Settled Trade Not Booked (Type A - Custodian>Internal)
- **Cause:** Trade settled at custodian but not recorded internally
- **Resolution:** Obtain trade confirmation, post to system
- **Action:** Book trade, investigate booking delay

#### Corporate Action (Type A)
- **Cause:** Stock split, dividend, merger not reflected one side
- **Resolution:** Verify corporate action details
- **Action:** Post corporate action adjustment

#### Failed Settlement (Type B or C)
- **Cause:** Trade failed to settle, only one side adjusted
- **Resolution:** Check settlement status
- **Action:** Follow settlement failure procedure (SOP-MO-001)

#### Data Error (Type A, B, or C)
- **Cause:** Incorrect data entry or file transmission error
- **Resolution:** Validate correct position
- **Action:** Correct error, notify source system owner

### Step 3: Cash Reconciliation (09:00 - 10:00)

1. **Cash Balance Comparison**
   - Match cash by currency
   - Compare opening + movements = closing
   - Identify variances

2. **Cash Movement Analysis**
   - Match custodian transactions to internal ledger
   - Verify:
     - Trade settlements (purchase/sale proceeds)
     - Income (dividends, interest, coupons)
     - Fees (management, custody, transaction)
     - FX conversions

3. **Common Cash Breaks**
   - **Timing differences:** Transaction posted different dates
   - **Income not received:** Expected dividend not paid
   - **Unexpected fees:** Fee charged not accrued
   - **FX differences:** Rate variance on currency conversion

**Resolution Actions:**
- Timing differences: Mark as pending, monitor next day
- Missing income: Contact paying agent, investigate
- Unexpected fees: Verify invoice, post accrual
- FX differences: Recalculate using correct rate

**Output:** Cash break report

### Step 4: Transaction Reconciliation (09:30 - 10:30)

1. **Trade Matching**
   - Match executed trades to custodian confirmations
   - Compare:
     - Trade date
     - Settlement date
     - Security
     - Quantity
     - Price
     - Counterparty

2. **Identify Mismatches**
   - Price differences
   - Quantity differences
   - Settlement date discrepancies
   - Missing confirmations

3. **Resolution Steps**
   - Price/quantity: Verify with trading desk, correct if error
   - Settlement date: Confirm correct date, adjust if needed
   - Missing confirmation: Request from custodian

**Output:** Transaction break report

### Step 5: Pricing Reconciliation (10:00 - 10:30)

1. **Price Comparison**
   - Match security prices from:
     - Internal pricing vendor (Bloomberg)
     - Custodian pricing
     - Third-party source (validation)

2. **Variance Analysis**
   - Calculate price difference percentage
   - Flag variances >±0.5% tolerance for pricing validation%

3. **Price Break Resolution**
   - Small variance (<1%): Accept internal price
   - Medium variance (1-5%): Verify with secondary source
   - Large variance (>5%): Escalate to Pricing Committee

**Output:** Pricing variance report

### Step 6: Break Resolution and Documentation (10:30 - 11:00)

1. **Resolve Standard Breaks**
   - Post timing differences as pending items
   - Book missing trades
   - Correct data errors
   - Update SmartStream TLM

2. **Document Complex Breaks**
   - Create investigation note (SOP reference)
   - Assign to specialist (if needed)
   - Set resolution deadline
   - Escalate if material

3. **System Updates**
   - Post reconciliation adjustments to SimCorp Dimension
   - Update break tracking log
   - Clear resolved items
   - Age unresolved items

**Output:** Reconciliation summary for NAV team

### Step 7: Reporting and Escalation (11:00 - 11:30)

1. **Daily Reconciliation Report**
   Contents:
   - Total break count
   - Breaks by type and severity
   - Resolved vs unresolved
   - Aged breaks (>T+2)
   - Material breaks (>£100K)

2. **Escalation Triggers**
   - Any break >£1M
   - Aged breaks >5 days
   - Repeated breaks same security/portfolio
   - Systemic issues affecting multiple portfolios

3. **Distribution**
   - NAV team (for NAV calculation)
   - Operations Manager (for review)
   - Fund Accountant (for adjustments)
   - Portfolio Managers (if material to portfolio)

## Break Tolerance Thresholds

| Asset Class | Quantity Tolerance | Value Tolerance |
|-------------|-------------------|-----------------|
| Equities    | 0.1% or 10 shares | £10,000        |
| Bonds       | 0.1% or £10,000   | £25,000        |
| FX          | 0.01%             | £5,000         |
| Cash        | £1,000            | £1,000         |

## Aged Break Management

### T+1 to T+2
- Standard investigation
- Daily monitoring

### T+3 to T+5
- Enhanced investigation
- Custodian escalation
- Manager notification

### T+5+
- Formal escalation memo
- Senior management notification
- Root cause analysis required
- Process improvement review

## Quality Controls

### Peer Review
- All material adjustments (>£100K) require dual approval
- Month-end reconciliations independently verified

### Audit Trail
- All breaks logged with resolution notes
- System adjustments documented
- Approval signatures retained

## Contingency Procedures

### Late Custodian Files
1. Contact custodian operations
2. Use prior day + known movements
3. Complete reconciliation when received
4. Note timing in NAV report

### System Unavailability
1. Use manual reconciliation spreadsheet
2. Follow same matching logic
3. Implement additional checks
4. Post results when system restored

## Reporting Requirements

### Daily Reports (11:00)
- Reconciliation summary
- Open break listing
- Material items

### Weekly Reports (Friday 17:00)
- Trend analysis
- Aged break status
- Process improvements

### Monthly Reports (5th business day)
- Comprehensive statistics
- Root cause analysis
- Quality metrics

## Key Performance Indicators
- Breaks identified: <1% of positions
- Breaks resolved same day: >95%
- Aged breaks (>T+5): <5 outstanding
- Material breaks: <1 per month
- Reconciliation completion: 100% by 11:00

## Contact Information
**Reconciliation Team:** reconteam@sam-demo.example  
**Operations Manager:** Sarah Mitchell  
**Custodian Reconciliation Desk:** Daily reconciliation via automated feed

## Document Control
**Author:** Middle Office Operations Team  
**Reviewed By:** Head of Middle Office  
**Approved By:** Chief Operating Officer  
**Next Review Date:** 31 March 2025

---

**Document Reference:** SAM-MO-SOP-002-v3.2  
**Related Procedures:** SOP-MO-001 (Settlement Failures), SOP-MO-002 (NAV Calculation)

