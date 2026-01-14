---
doc_type: "ssi_documents"
linkage_level: "global"
word_count_target: 400
template_name: "Standard Settlement Instructions - Foreign Exchange"
---


# Standard Settlement Instructions - Foreign Exchange
**Document Type:** SSI Master Document  
**Asset Class:** Foreign Exchange (Spot & Forward)  
**Effective Date:** 01 January 2024  
**Version:** 3.2  
**Last Updated:** 15 October 2024

## Overview
This document defines the standard settlement instructions for foreign exchange transactions executed for Simulated Asset Management portfolios. All FX settlements must adhere to these procedures.

## Primary FX Custodian

### BNY Mellon - FX Settlement
**Account Name:** SAM Technology & Infrastructure  
**SWIFT Code:** IRVTGB2X  
**Correspondent Network:** Citi Correspondent Banking Network

## Currency-Specific Settlement Instructions

### USD - United States Dollar
**Correspondent Bank:** JPMorgan Chase Bank N.A. New York  
**ABA/Fedwire:** 026009593  
**CHIPS UID:** UID: 123456  
**Account Number:** US1234567890  
**Settlement Time:** 17:00 EST

### EUR - Euro
**Correspondent Bank:** Deutsche Bank AG Frankfurt  
**SWIFT:** DEUTDEFF  
**IBAN:** DE89370400440532013000  
**TARGET2 Participant:** {{EUR_TARGET2}}  
**Settlement Time:** 14:00 CET

### GBP - British Pound Simulated
**Correspondent Bank:** NatWest Markets Plc  
**Sort Code:** 60-16-13  
**Account Number:** GB29NWBK60161331926819  
**CHAPS:** Sort Code: 60-16-13  
**Settlement Time:** 15:30 GMT

### JPY - Japanese Yen
**Correspondent Bank:** Mitsubishi UFJ Trust and Banking  
**SWIFT:** BOTKJPJT  
**Zengin Code:** 0001-123-4567890  
**Account Number:** JP1234567890  
**Settlement Time:** 15:00 JST

### Other Major Currencies
Contact FX desk for non-standard currencies

## Settlement Timing

### Spot Transactions
- **Trade Date:** T
- **Value Date:** T+2
- **Cut-off Times:** Currency-specific (see above)

### Forward Transactions
- **Trade Date:** T
- **Value Date:** As agreed
- **Confirmation:** Within 24 hours of trade

## CLS (Continuous Linked Settlement)
FX settlements via CLS Bank, value date T+2

## Payment vs Payment (PvP)
All FX settlements should be executed via PvP through CLS Bank when available. Non-CLS currencies require dual authorization.

## Settlement Failures
Notify counterparty T+1, escalate T+3, buy-in T+5

## Margin and Collateral
Margin calls via email by 10:00 daily

## Contact Information
**FX Settlement Desk:** fx.desk@sam-demo.example / +44-20-7123-4568  
**Urgent Settlement Issues:** +44-20-7123-4567 (24/7 emergency line)

---

**Document Owner:** Middle Office Operations  
**Approval:** Chief Operating Officer  
**Review Date:** 31 March 2025  
**SSI Reference:** SSI-SAM-TECH-EQUITY-001

