---
doc_type: "ops_procedures"
linkage_level: "global"
word_count_target: 1100
template_name: "Settlement Failure Resolution Procedure"
---


# Settlement Failure Resolution Procedure
**Document Type:** Standard Operating Procedure  
**Procedure ID:** SOP-MO-001  
**Version:** 3.2  
**Effective Date:** 01 January 2024  
**Last Updated:** 15 October 2024  
**Owner:** Middle Office Operations

## Purpose
This procedure defines the standard process for identifying, investigating, and resolving settlement failures for all Simulated Asset Management portfolios.

## Scope
This procedure applies to all settlement failures across equity, fixed income, and FX transactions processed through our custodian network.

## Definitions
- **Settlement Failure:** Any trade that fails to settle on the contractual settlement date
- **Aging Failure:** Settlement failure outstanding beyond T+5
- **Partial Settlement:** Trade settles for less than the contracted quantity
- **Failed Delivery:** Counterparty unable to deliver securities on settlement date
- **Failed Payment:** Payment not received on settlement date

## Roles and Responsibilities

### Operations Analyst
- Monitor daily settlement reports
- Identify and log all failures
- Initiate investigation process
- Contact counterparties and custodians
- Update tracking system

### Middle Office Manager
- Review all aging failures (>T+5)
- Approve escalation to senior management
- Coordinate with Risk and Compliance
- Sign off on resolution actions

### Risk Management
- Assess counterparty risk for repeated failures
- Recommend credit limit adjustments
- Monitor systemic settlement issues

## Procedure Steps

### Step 1: Detection and Logging (Daily, 09:00)
**Timeframe:** Within 1 hour of market open

1. Access custodian settlement reports
   - Log into BNY Mellon Nexen
   - Navigate to Settlement Status dashboard
   - Filter for "Failed" and "Pending" statuses

2. Export failure data
   - Download CSV file of all failures
   - Import into internal tracking system (SmartStream TLM Reconciliation)
   - Generate failure report

3. Categorize failures
   - By asset class (Equity, FI, FX)
   - By age (T+1, T+2, T+3, T+4, T+5+)
   - By portfolio
   - By counterparty

**Output:** Daily Settlement Failure Report

### Step 2: Initial Investigation (Same Day, Before 12:00)

1. Review trade details
   - Trade date and settlement date
   - Counterparty information
   - Settlement instructions used
   - Expected settlement method (DVP, FOP, PvP)

2. Contact custodian
   - Call settlement desk: custody.operations@bnymellon.com
   - Request failure reason code
   - Obtain expected resolution timeframe
   - Document conversation in tracking system

3. Common failure reasons and initial actions:
   - **Insufficient Securities:** Contact selling counterparty
   - **Payment Pending:** Verify cash position and payment instruction
   - **SSI Mismatch:** Review and correct settlement instructions
   - **System Error:** Contact custodian IT desk
   - **Counterparty Delay:** Escalate to counterparty operations

**Output:** Investigation notes in tracking system

### Step 3: Resolution Actions (Same Day)

#### For SSI Mismatches
1. Retrieve correct SSI from master file
2. Verify SSI with counterparty operations
3. Submit corrected SSI to custodian
4. Request settlement retry
5. Confirm new settlement date

#### For Insufficient Securities
1. Contact counterparty operations
2. Determine if securities available next day
3. If unavailable, discuss alternative resolution:
   - Partial settlement
   - Trade cancellation
   - Market purchase (buy-in)
4. Obtain written confirmation of resolution plan

#### For Payment Issues
1. Verify cash availability in settlement currency
2. Check payment instruction status
3. Contact treasury desk if cash shortfall
4. Arrange FX if currency conversion needed
5. Resubmit payment instruction

### Step 4: Monitoring and Follow-up (Daily Until Resolved)

1. Check status of pending resolutions
2. Contact counterparty if no progress
3. Update tracking system with status
4. Escalate if failure aging beyond T+3

**Escalation Triggers:**
- Any failure beyond T+5
- Repeated failures with same counterparty (3+ in month)
- Material failures (>£5M per trade)
- Pattern of failures in specific security or market

### Step 5: Aging Failure Escalation (T+5 and Beyond)

1. Prepare escalation memo including:
   - Trade details and failure reason
   - Investigation summary
   - Resolution attempts to date
   - Recommended action (buy-in, claim, cancellation)
   - Financial impact

2. Submit to Middle Office Manager for review

3. If approved, proceed with resolution:
   - **Buy-in:** Execute market purchase, claim difference from counterparty
   - **Cancellation:** Cancel original trade, adjust portfolio positions
   - **Legal claim:** Refer to Legal and Compliance

### Step 6: Post-Resolution Actions

1. Update tracking system with final resolution
2. Calculate and document financial impact
3. If loss occurred:
   - Submit claim to counterparty
   - Notify Finance for P&L adjustment
   - Escalate to Legal if counterparty refuses claim

4. Root cause analysis
   - Identify systemic issues
   - Document lessons learned
   - Recommend process improvements

## Reporting Requirements

### Daily Reports (Due 11:00)
- Open failures summary
- New failures identified
- Failures resolved
- Aging failures (>T+5)

### Weekly Reports (Due Friday 17:00)
- Settlement failure trends
- Counterparty failure analysis
- Financial impact summary
- Process improvement recommendations

### Monthly Reports (Due 5th Business Day)
- Comprehensive failure statistics
- Counterparty performance scorecard
- Root cause analysis
- Systemic issues identified

## Key Performance Indicators (KPIs)
- Settlement failure rate: Target <0.5% of all trades
- Average resolution time: Target <3 business days
- Aged failures (>T+5): Target <5 outstanding at month-end
- Financial losses: Target <0.01% of trade value

## Regulatory Requirements
FCA reporting requirements met

## System Access Requirements
- BNY Mellon Nexen access
- SmartStream TLM Reconciliation credentials
- Bloomberg terminal
- Internal email and phone directory

## Contact Information
**Operations Desk:** Middle Office Operations Desk  
**Middle Office Manager:** Sarah Mitchell, Head of Middle Office  
**Custodian Settlement Desk:** custody.operations@bnymellon.com  
**After Hours Emergency:** +44 20 7123 4567 (24/7)

## Document Control
**Author:** Middle Office Operations Team  
**Reviewed By:** Head of Middle Office  
**Approved By:** Chief Operating Officer  
**Next Review Date:** 31 March 2025

---

**Document Reference:** SAM-MO-SOP-002-v3.2  
**Related Procedures:** SOP-MO-002 (NAV Calculation), SOP-MO-003 (Reconciliation)

