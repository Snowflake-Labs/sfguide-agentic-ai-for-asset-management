---
doc_type: earnings_transcripts
linkage_level: security
sector_tags: [Health Care]
master_id: healthcare_earnings_01
word_count_target: 7200
placeholders:
  required:
    - COMPANY_NAME
    - TICKER
    - FISCAL_QUARTER
    - FISCAL_YEAR
    - PUBLISH_DATE
    - CEO_NAME
    - CFO_NAME
  optional:
    - QUARTERLY_REVENUE_BILLIONS
    - QUARTERLY_EPS
    - YOY_GROWTH_PCT
    - OPERATING_MARGIN_PCT
constraints:
  QUARTERLY_REVENUE_BILLIONS: {min: 5, max: 40}
  QUARTERLY_EPS: {min: 0.8, max: 4.0}
disclosure:
  include_disclaimer: true
---

# {{COMPANY_NAME}} {{FISCAL_QUARTER}} {{FISCAL_YEAR}} Earnings Call Transcript

**Date**: {{PUBLISH_DATE}}  
**Participants**: {{CEO_NAME}} (CEO), {{CFO_NAME}} (CFO), Investor Relations

---

## Operator

Good morning, and welcome to {{COMPANY_NAME}}'s {{FISCAL_QUARTER}} {{FISCAL_YEAR}} earnings conference call. All participants are in listen-only mode. After the presentation, we will conduct a question-and-answer session.

I will now turn the call over to Dr. Emily Watson, Vice President of Investor Relations.

## Dr. Emily Watson, VP Investor Relations

Thank you, operator, and good morning, everyone. Welcome to {{COMPANY_NAME}}'s {{FISCAL_QUARTER}} {{FISCAL_YEAR}} earnings call. Joining me today are {{CEO_NAME}}, our Chief Executive Officer, and {{CFO_NAME}}, our Chief Financial Officer.

This call will contain forward-looking statements about our business, pipeline, and financial outlook. These statements involve risks and uncertainties. Please review our SEC filings for detailed risk factors.

We will also reference non-GAAP financial measures. Reconciliations are available in our earnings release on our investor website.

{{CEO_NAME}}, over to you.

## {{CEO_NAME}}, CEO — Prepared Remarks

Thank you, Emily, and good morning.

I'm pleased to report strong {{FISCAL_QUARTER}} results demonstrating the strength of our diversified pharmaceutical portfolio and the progress of our innovation pipeline. Revenue reached ${{QUARTERLY_REVENUE_BILLIONS}} billion, up {{YOY_GROWTH_PCT}}% year-over-year, and earnings per share were ${{QUARTERLY_EPS}}, both exceeding our guidance.

These results reflect strong commercial execution across our marketed products, positive pipeline developments, and operational discipline. I'm particularly encouraged by the performance of our recently launched products, which continue gaining market share and demonstrating strong clinical value to patients and healthcare providers.

Our lead oncology product achieved another quarter of double-digit growth, with expanded indications and geographic rollout driving adoption. Market share in its primary indication increased to {{MARKET_SHARE}}%, and physician feedback remains exceptionally positive regarding efficacy and tolerability profile.

In cardiovascular, our novel anticoagulant continues to penetrate the market with {{CARDIO_GROWTH}}% growth this quarter. Real-world evidence studies are confirming the clinical trial safety advantages, which supports prescriber confidence and payer coverage decisions.

From a pipeline perspective, we achieved several significant milestones during the quarter. Our Phase III diabetes therapy met primary and all secondary endpoints with statistical significance, positioning us for regulatory filing in Q{{FILING_QUARTER}}. If approved, this asset addresses a multi-billion dollar market opportunity with differentiated clinical profile.

Our immunology programme advanced to Phase II with encouraging preliminary data. Patient response rates exceeded expectations, and the safety profile supports continued development. We expect to initiate pivotal Phase III studies in the second half of {{NEXT_YEAR}}.

Strategic priorities remain focused on maximizing value from our commercial portfolio whilst advancing the pipeline through disciplined development. We continue to evaluate business development opportunities that strengthen our pipeline or provide complementary capabilities, though our bar for acquisitions remains high.

I'll now turn it over to {{CFO_NAME}} for financial details.

## {{CFO_NAME}}, CFO — Financial Review

Thank you, {{CEO_NAME}}.

{{FISCAL_QUARTER}} revenue was ${{QUARTERLY_REVENUE_BILLIONS}} billion, up {{YOY_GROWTH_PCT}}% year-over-year and {{SEQUENTIAL_GROWTH}}% sequentially. Growth was driven by our key promoted products with minimal contribution from COVID-related sales, which have normalized post-pandemic.

By therapeutic area, oncology revenue was ${{ONCOLOGY_REVENUE}}B, up {{ONCOLOGY_GROWTH}}%. Cardiovascular revenue was ${{CARDIO_REVENUE}}B, up {{CARDIO_GROWTH}}%. Immunology contributed ${{IMMUNO_REVENUE}}B with growth of {{IMMUNO_GROWTH}}%.

Geographic revenue mix: US represented {{US_PCT}}% of revenue, Europe {{EUROPE_PCT}}%, and rest of world {{ROW_PCT}}%. International markets are growing faster than US, reflecting ongoing geographic expansion and product launches in new markets.

Gross profit was ${{GROSS_PROFIT}}B with gross margin of {{GROSS_MARGIN}}%. Operating expenses were ${{OPEX}}B including R&D of ${{RD_SPEND}}B ({{RD_PCT}}% of revenue) and SG&A of ${{SGA_SPEND}}B ({{SGA_PCT}}% of revenue).

Operating income was ${{OPERATING_INCOME}}B with operating margin of {{OPERATING_MARGIN_PCT}}%, expanding {{MARGIN_EXPANSION}}bps year-over-year. Net income was ${{NET_INCOME}}B, and diluted EPS was ${{QUARTERLY_EPS}}.

Cash flow: Operating cash flow was ${{OCF}}B and free cash flow was ${{FCF}}B. We ended the quarter with cash and investments of ${{CASH_BALANCE}}B and total debt of ${{DEBT}}B.

Capital return: We paid ${{DIVIDEND_AMOUNT}}M in dividends and repurchased ${{BUYBACK_AMOUNT}}M of shares.

Guidance: For Q{{NEXT_QUARTER}}, we expect revenue of ${{GUIDANCE_LOW}}B to ${{GUIDANCE_HIGH}}B and EPS of ${{EPS_LOW}} to ${{EPS_HIGH}}. For full year {{FISCAL_YEAR}}, we are raising revenue guidance to {{FY_LOW}}% to {{FY_HIGH}}% growth.

Operator, let's open for questions.

## Q&A Session

**Operator**: First question from Dr. Sarah Chen with Fairmont Capital Insights.

**Dr. Sarah Chen**: Congratulations on the quarter. Can you provide more detail on the Phase III diabetes data? What differentiates your molecule from existing therapies?

**{{CEO_NAME}}**: Thanks, Sarah. The data were quite compelling. We saw {{A1C_REDUCTION}} A1C reduction versus {{PLACEBO_A1C}} for placebo, which is meaningful improvement over standard of care. More importantly, we achieved this with {{WEIGHT_BENEFIT}} weight loss and no increase in hypoglycemic events, addressing two key limitations of existing therapies.

The differentiation comes from our novel mechanism of action. Unlike GLP-1 agonists or SGLT-2 inhibitors, our molecule works through {{MECHANISM}}, which provides complementary benefits with excellent tolerability. We believe this profile creates opportunity both as monotherapy and in combination regimens.

**Dr. Sarah Chen**: And on market opportunity, how large is the addressable population?

**{{CFO_NAME}}**: The Type 2 diabetes market is approximately {{DIABETES_MARKET}}B annually in major markets. Our target population is estimated at {{TARGET_PATIENTS}}M patients globally who inadequately controlled on current therapies. At peak penetration of {{PEAK_SHARE}}% share, this represents several billion in annual revenue opportunity.

**Operator**: Next question from Michael Torres with Granite Peak Advisory.

**Michael Torres**: Question on the oncology franchise. You've had strong growth, but several biosimilars are approaching patent expiry dates. How are you thinking about defending against biosimilar competition?

**{{CEO_NAME}}**: Important question. We have patent protection on our lead oncology asset through {{PATENT_EXPIRY}}, which provides several more years of exclusivity. During that period, we're advancing next-generation formulations with improved dosing convenience and combination studies that could extend lifecycle.

More broadly, our approach to biosimilar defence emphasizes clinical evidence demonstrating superior outcomes, physician relationships, and patient support programmes. We'll compete on value delivered to healthcare system, not just on price.

We're also advancing earlier-stage oncology pipeline assets that could become the next-generation products. {{PIPELINE_ASSET}} shows promise in Phase II with encouraging response rates in difficult-to-treat tumour types.

**{{CFO_NAME}}**: From a financial planning perspective, we've modelled biosimilar impact conservatively. Even with {{EROSION_PCT}}% erosion over 3-4 years post-loss of exclusivity, the franchise generates substantial cash supporting both pipeline investment and capital returns.

**Operator**: Question from Rachel Martinez with Brookline Advisory Group.

**Rachel Martinez**: On the immunology programme in Phase II, what's the competitive landscape? And what would success criteria be for advancing to Phase III?

**{{CEO_NAME}}**: The immunology market is competitive but validated, with multiple companies pursuing different mechanisms. Our asset's differentiation is the clean safety profile we're observing. Many immunology therapies face safety concerns that limit use. Our data suggest we may avoid those issues whilst delivering efficacy.

Success criteria for Phase III advancement include demonstrating clinical response rates above {{RESPONSE_THRESHOLD}}% in our target indications and maintaining the favorable safety profile we've seen to date. If we hit those criteria, we'd initiate Phase III in mid-{{NEXT_YEAR}}.

The commercial opportunity is substantial if successful. Severe immunologic conditions affect millions of patients globally with current treatment options providing incomplete disease control. A safer, more effective therapy would address significant unmet need.

**Operator**: Final question from Jennifer Lee with Ashfield Partners.

**Jennifer Lee**: Can you discuss capital allocation priorities? How do you balance R&D investment, business development, and shareholder returns?

**{{CFO_NAME}}**: Our capital allocation framework is clear and consistent. Priority one is funding organic R&D to advance our pipeline. We're currently investing ${{RD_ANNUAL}}B+ annually in R&D, which is amongst the highest in our peer group on a percentage of revenue basis.

Priority two is business development — licensing or acquiring pipeline assets or companies that accelerate our strategy. We evaluate numerous opportunities but maintain discipline. Deals must be strategically aligned, financially attractive, and executable from integration perspective.

Priority three is returning capital to shareholders through dividends and buybacks. We increased our dividend {{DIV_INCREASE}}% this year and have been consistently active in share repurchases. This quarter we returned ${{TOTAL_RETURN}}B total.

The balance sheet provides flexibility to do all of these simultaneously. Strong cash generation, investment-grade credit rating, and access to capital markets give us strategic and financial flexibility.

**{{CEO_NAME}}**: I'd add that we take a long-term view on capital allocation. We're willing to invest aggressively in high-potential pipeline assets even if it creates near-term earnings headwind. The nature of drug development is that returns come over many years, so patience and discipline are critical.

---

## Closing Remarks

**{{CEO_NAME}}**: Thank you all for joining today. {{FISCAL_QUARTER}} was a strong quarter reflecting commercial execution and pipeline progress. We're excited about our marketed products, upcoming milestones, and long-term growth opportunities. We look forward to updating you next quarter.

**Operator**: This concludes today's conference call. Thank you for participating.

---

**Forward-Looking Statements**: This transcript contains forward-looking statements involving significant risks and uncertainties. Actual results may differ materially. See SEC filings for risk factors.

*SAM Demo Content*

