---
doc_type: "ssi_documents"
linkage_level: "global"
word_count_target: 400
template_name: "Standard Settlement Instructions - Fixed Income"
---


# Standard Settlement Instructions - Fixed Income
**Document Type:** SSI Master Document  
**Asset Class:** Fixed Income Securities (Bonds, Notes, Bills)  
**Effective Date:** 01 January 2024  
**Version:** 3.2  
**Last Updated:** 15 October 2024

## Overview
This document provides standard settlement instructions for fixed income securities traded for Simulated Asset Management portfolios. All bond settlements must follow these procedures.

## Primary Custodian

### BNY Mellon - Fixed Income Settlement
**Account Name:** SAM Technology & Infrastructure  
**Account Number:** SAM-TECH-001  
**SWIFT/BIC:** IRVTGB2X  
**LEI:** 213800D1EI4B9WTWWD28

## Settlement by Security Type

### U.S. Treasury Securities
**Depository:** Federal Reserve Bank of New York  
**Fedwire:** 026009593  
**Settlement Cycle:** T+1  
**DTC Eligible:** Yes  
**Special Instructions:** All Treasury settlements via Fedwire unless otherwise instructed

### U.S. Corporate Bonds
**Depository:** DTC via Goldman Sachs  
**DTC Participant:** Goldman Sachs & Co.  
**Settlement Cycle:** T+2  
**CUSIP Agent:** Computershare Trust Company  
**Special Instructions:** Corporate actions processed automatically

### U.S. Municipal Bonds
**Depository:** DTC Municipal Securities Division  
**Settlement Agent:** BNY Mellon Municipal Securities  
**Settlement Cycle:** T+2  
**Special Requirements:** CUSIP verification required, settle via DTC

### International Government Bonds (IGBs)

#### Euro-denominated Bonds
**Depository:** Euroclear Bank  
**Euroclear Account:** ECL-SAM-001  
**Clearstream Account:** CLR-SAM-001  
**Settlement Cycle:** T+2  

#### UK Gilts
**Depository:** Euroclear UK & International (CREST)  
**CREST Member ID:** CRST-SAM-001  
**Settlement Cycle:** T+1

#### Japanese Government Bonds (JGBs)
**Depository:** Japan Securities Depository Center (JASDEC)  
**Account Details:** JSDA-SAM-001  
**Settlement Cycle:** T+2

## Settlement Type Requirements

### Delivery vs Payment (DVP)
All fixed income settlements must be DVP unless documented exception approved. Standard DVP models:
- **DVP Model 1:** Gross settlement (securities and cash)
- **DVP Model 2:** Gross securities, net cash
- **DVP Model 3:** Net securities and cash

### Free of Payment (FOP)
FOP deliveries require:
1. Dual authorization (Operations + Compliance)
2. Written explanation
3. Same-day reporting to Risk Committee

## Accrued Interest Calculation
Accrued interest calculated on actual/360 basis, paid separately

## Trade Confirmation Requirements
- **Corporate Bonds:** TRACE confirmation within 15 minutes
- **Treasuries:** Fedwire confirmation same day
- **International:** Confirmation per local market rules

## Settlement Failures

### Failure Protocol
Immediate escalation to trading desk and counterparty

### Buy-In Procedures
Counterparty notified on T+3, buy-in executed T+5 if unresolved

## Corporate Actions

### Coupon Payments
Interest paid semi-annually to account on record

### Redemptions and Calls
Redemptions processed T+3, funds via wire transfer

### Tender Offers
Tender offers via voluntary corporate action process

## Margin and Financing

### Repo Transactions
Repo transactions via triparty agent

### Securities Lending
Securities lending via automated platform

## Contact Information
**Fixed Income Operations:** fi.operations@sam-demo.example  
**Settlement Desk:** settlements.desk@sam-demo.example / +44-20-7123-4571  
**After Hours:** +44 20 7123 4567 (24/7 operations line)

---

**Document Owner:** Middle Office Operations  
**Approved By:** Chief Operating Officer  
**Next Review:** 31 March 2025  
**SSI Reference:** SSI-SAM-TECH-EQUITY-001

