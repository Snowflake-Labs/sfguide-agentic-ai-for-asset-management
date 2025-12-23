# Prompt Discrepancies Between am_ai_demo and sfguide

This document tracks all identified discrepancies between the prompts in am_ai_demo docs and the sfguide README.md.

## Portfolio Copilot

### ✅ Scenario 1: Portfolio Insights & Benchmarking
**Status**: Missing 1 prompt (Step 4)

**am_ai_demo has 5 steps:**
1. Top 10 holdings ✅
2. Latest broker research ✅  
3. Sector concentration risk ✅
4. **Which positions need attention** ❌ **MISSING FROM SFGUIDE**
5. Implementation plan ✅

**Missing Prompt (Step 4)**:
```
Based on our concentration analysis and research findings, which of our largest positions need attention and what actions should we consider?
```

---

### ❌ Scenario 2: Real-Time Event Impact & Supply Chain Risk
**Status**: Missing 1 prompt (Step 4)

**am_ai_demo has 4 steps:**
1. Event verification ✅
2. Direct exposure ✅
3. Supply chain dependencies ✅
4. **TSMC statements** ❌ **MISSING FROM SFGUIDE**

**Missing Prompt (Step 4)**:
```
Do we have any statements from TSMC or their customers about the Taiwan earthquake impact and supply chain resilience?
```

---

### ❌ Scenario 3: AI-Assisted Mandate Compliance & Security Replacement
**Status**: Incorrect wording in Step 2

**Issue**: 
- am_ai_demo (line 547): "maintain our **AI growth focus**"
- sfguide (line 228): "maintain our **technology/growth focus**"

**Correct Prompt (Step 2)**:
```
Based on that breach, what are our pre-screened replacement candidates that meet the mandate requirements and maintain our AI growth focus?
```

---

### ✅ Scenario 4: Comprehensive Company Analysis
**Status**: OK - matches am_ai_demo

---

## Executive Copilot  

### ✅ All scenarios verified and fixed in previous commit
- Scenario 1: 4 prompts ✅
- Scenario 2: 4 prompts ✅
- Scenario 3: 1 prompt ✅

---

## Research Copilot
**Status**: NEEDS VERIFICATION

---

## Thematic Macro Advisor
**Status**: NEEDS VERIFICATION

---

## ESG Guardian
**Status**: NEEDS VERIFICATION

---

## Sales Advisor
**Status**: NEEDS VERIFICATION

---

## Quant Analyst
**Status**: NEEDS VERIFICATION

---

## Compliance Advisor
**Status**: NEEDS VERIFICATION

---

## Middle Office Copilot
**Status**: NEEDS VERIFICATION

---

## Summary

### Immediate Fixes Needed:
1. **Portfolio Copilot Scenario 1**: Add missing Step 4 prompt
2. **Portfolio Copilot Scenario 2**: Add missing Step 4 prompt  
3. **Portfolio Copilot Scenario 3**: Fix wording from "technology/growth" to "AI growth"

### Remaining Work:
- Verify all other 6 agents against am_ai_demo docs
- Total prompts in am_ai_demo: **124**
- Total prompts verified so far: **~20** (Executive + Portfolio partial)

