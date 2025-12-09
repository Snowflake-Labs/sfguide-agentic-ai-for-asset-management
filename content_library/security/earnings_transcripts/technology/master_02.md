---
doc_type: earnings_transcripts
linkage_level: security
sector_tags: [Information Technology]
master_id: tech_earnings_02
word_count_target: 7800
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
  QUARTERLY_REVENUE_BILLIONS: {min: 10, max: 60}
  QUARTERLY_EPS: {min: 1.0, max: 5.0}
disclosure:
  include_disclaimer: true
---

# {{COMPANY_NAME}} {{FISCAL_QUARTER}} {{FISCAL_YEAR}} Earnings Conference Call

**Date**: {{PUBLISH_DATE}}  
**Time**: 14:00 PT / 17:00 ET  
**Participants**: Executive Leadership and Investor Relations

---

## Operator Introduction

Good afternoon. Thank you for standing by, and welcome to the {{COMPANY_NAME}} {{FISCAL_QUARTER}} {{FISCAL_YEAR}} earnings conference call. All participants are currently in listen-only mode. Following the prepared remarks, we will open the call for your questions. As a reminder, this conference call is being recorded.

I will now turn the conference over to James Mitchell, Head of Investor Relations for {{COMPANY_NAME}}. Please go ahead, sir.

## James Mitchell, Head of Investor Relations

Thank you, operator, and good afternoon, everyone. Welcome to {{COMPANY_NAME}}'s {{FISCAL_QUARTER}} {{FISCAL_YEAR}} earnings call.

Joining me today are {{CEO_NAME}}, our Chief Executive Officer, and {{CFO_NAME}}, our Chief Financial Officer. Our earnings release, financial tables, and supplemental slides are available on our investor relations website.

During this call, we will make forward-looking statements about our business, results, and financial position. These statements involve risks and uncertainties, and actual results may differ materially. Please review the Safe Harbor statement in our press release and the risk factors in our SEC filings.

We will also discuss non-GAAP financial measures today. Reconciliations to GAAP metrics are in our press release and supplemental materials.

I'll now turn the call over to {{CEO_NAME}}.

## {{CEO_NAME}}, CEO — Prepared Remarks

Thanks, James, and thanks to everyone for joining us.

I'm pleased to report another excellent quarter for {{COMPANY_NAME}}. We delivered revenue of ${{QUARTERLY_REVENUE_BILLIONS}} billion, up {{YOY_GROWTH_PCT}}% year-over-year, and earnings per share of ${{QUARTERLY_EPS}}, both exceeding our guidance ranges and consensus expectations.

These results reflect strong execution across our business, continued momentum in our strategic initiatives, and the significant value our platform creates for customers worldwide. I'm particularly proud of how our team has navigated this dynamic environment whilst maintaining our focus on innovation, customer success, and operational excellence.

Let me share some highlights from the quarter. Our cloud infrastructure platform achieved another record quarter with revenue growth accelerating to {{CLOUD_GROWTH}}% year-over-year. We added thousands of new customers while expanding significantly within our existing base. Dollar-based net retention remained above {{NET_RETENTION}}%, demonstrating that our customers are growing their usage of our platform as they migrate more workloads and adopt additional services.

The AI products we've launched over the past year are exceeding expectations. Customer adoption is strong, use cases are expanding beyond initial applications, and we're seeing measurable improvements in customer outcomes. Enterprises are actively deploying AI to enhance productivity, improve decision-making, and create better customer experiences. We're positioned at the centre of this transformation with both enabling infrastructure and application-layer capabilities.

On the innovation front, we announced several significant product releases during the quarter. Our new AI-powered developer tools are helping customers build applications faster with fewer resources. Early feedback has been phenomenal, and we're seeing rapid adoption from both individual developers and enterprise teams.

From a strategic perspective, our focus remains on three key priorities. First, continuing to strengthen our position in cloud infrastructure through technology innovation and customer success. Second, capitalising on the AI opportunity by integrating AI capabilities across our platform and launching new AI-centric products. Third, expanding internationally to capture the global opportunity.

International expansion is progressing well. Revenue from outside North America grew {{INTL_GROWTH}}% this quarter, faster than overall company growth. We've made strategic investments in local infrastructure, partnerships, and go-to-market capabilities that are beginning to pay dividends. The international market represents a massive long-term opportunity where we're still relatively under-penetrated.

Before turning to {{CFO_NAME}}, I want to thank our global team. The results we're reporting today are the outcome of exceptional work by talented people committed to our mission and our customers' success.

{{CFO_NAME}}, over to you.

## {{CFO_NAME}}, CFO — Financial Details

Thank you, {{CEO_NAME}}, and good afternoon.

I'll provide additional detail on our financial results and discuss our guidance for the coming quarter.

Q{{QUARTER_NUM}} revenue was ${{QUARTERLY_REVENUE_BILLIONS}} billion, representing {{YOY_GROWTH_PCT}}% year-over-year growth. This exceeded the high end of our guidance range and consensus estimates. All product categories contributed to the outperformance with cloud infrastructure, software subscriptions, and professional services all coming in ahead of plan.

Breaking down revenue by category, subscription and support revenue was ${{SUBSCRIPTION_REVENUE}}B, up {{SUBSCRIPTION_GROWTH}}% year-over-year. This represents {{SUBSCRIPTION_PCT}}% of total revenue, continuing the favorable mix shift toward recurring revenue streams. Subscription revenue provides excellent visibility and grows more predictably than transaction-based revenue.

Professional services and other revenue was ${{SERVICES_REVENUE}}B, growing {{SERVICES_GROWTH}}% year-over-year. Services margins improved sequentially as utilization rates increased and we achieved better leverage on our services organization.

From a geographic perspective, US revenue was ${{US_REVENUE}}B, up {{US_GROWTH}}% year-over-year. International revenue was ${{INTL_REVENUE}}B, up {{INTL_GROWTH}}% year-over-year, or {{INTL_CONSTANT_GROWTH}}% in constant currency. International now represents {{INTL_PCT}}% of total revenue, up from {{INTL_PRIOR_PCT}}% a year ago.

Gross profit was ${{GROSS_PROFIT}}B with gross margin of {{GROSS_MARGIN_PCT}}%. The slight margin expansion year-over-year reflects improved infrastructure efficiency and favorable revenue mix toward higher-margin software and services. We continue to invest in infrastructure capacity to support future growth, which creates some near-term gross margin headwind but positions us well for scale.

Operating expenses totaled ${{OPEX}}B, up {{OPEX_GROWTH}}% year-over-year. The increase primarily reflects higher R&D and sales spending supporting our growth initiatives. R&D was ${{RD_SPEND}}B or {{RD_PCT}}% of revenue. Sales and marketing was ${{SALES_SPEND}}B or {{SALES_PCT}}% of revenue. Both are growing slower than revenue, demonstrating the operating leverage in our model.

Operating income was ${{OPERATING_INCOME}}B with operating margin of {{OPERATING_MARGIN_PCT}}%, expanding {{MARGIN_EXPANSION}} basis points year-over-year. This demonstrates our ability to balance growth investments with profitability improvement.

Net income was ${{NET_INCOME}}B, and diluted EPS was ${{QUARTERLY_EPS}}, up {{EPS_GROWTH}}% year-over-year. Our tax rate for the quarter was {{TAX_RATE}}%, consistent with our guidance.

Turning to cash flow and balance sheet, operating cash flow was ${{OCF}}B and free cash flow was ${{FCF}}B. Free cash flow margin was {{FCF_MARGIN}}%, demonstrating strong cash generation characteristics of the business. We ended the quarter with ${{CASH}}B in cash, cash equivalents, and marketable securities.

During the quarter, we returned ${{CAPITAL_RETURN}}B to shareholders through share repurchases and dividends. Share repurchases totaled ${{BUYBACK}}B and we paid dividends of ${{DIVIDEND}}M. Our capital return demonstrates confidence in our outlook whilst maintaining balance sheet strength.

Now for guidance. For Q{{NEXT_QUARTER}}, we expect revenue between ${{Q_NEXT_LOW}}B and ${{Q_NEXT_HIGH}}B, representing year-over-year growth of approximately {{Q_NEXT_GROWTH_LOW}}% to {{Q_NEXT_GROWTH_HIGH}}%. We expect operating margin of approximately {{Q_NEXT_MARGIN}}%.

For the full fiscal year {{FISCAL_YEAR}}, based on our strong performance year-to-date, we are raising our outlook. We now expect full-year revenue growth of {{FY_GROWTH_LOW}}% to {{FY_GROWTH_HIGH}}%, and operating margin of approximately {{FY_MARGIN}}%.

With that, let's open for questions.

## Q&A Session

**Operator**: Our first question comes from Sarah Johnson with Kingswell Securities Research.

**Sarah Johnson**: Congratulations on the quarter. Can you talk about what you're seeing in enterprise spending? Any changes in customer buying behavior or deal cycles?

**{{CEO_NAME}}**: Thanks, Sarah. Enterprise demand remains healthy. We're not seeing meaningful elongation of sales cycles or budget compression. If anything, AI and cloud migration have elevated technology spending priority for most CIOs. Customers view these as strategic imperatives rather than discretionary projects.

Deal sizes are growing. Average contract value was up {{ACV_GROWTH}}% year-over-year. Customers are starting larger, doing broader deployments, and committing to multi-year agreements. This reflects confidence in our platform and desire to consolidate onto fewer vendors.

**{{CFO_NAME}}**: I'd add that our pipeline remains very strong, both in terms of new logo opportunity and expansion within existing accounts. Win rates are stable to improving. Customer success metrics show high satisfaction. We feel good about enterprise demand sustainability.

**Operator**: Next question from Mark Stevens with Crescent Point Analytics.

**Mark Stevens**: Question on AI monetization. How are you pricing AI capabilities? And what's the revenue contribution so far?

**{{CEO_NAME}}**: We're taking multiple monetization approaches for AI. Some AI features are embedded in existing products, enhancing value proposition and supporting pricing power. Others are priced as add-on modules or separate SKUs. And in some cases, AI improves our own efficiency, which helps margins.

Revenue contribution is still relatively small percentage of total, but growing very rapidly. Products with meaningful AI components launched in last 12-18 months are now contributing several hundred million dollars quarterly and growing triple digits year-over-year. As these products mature and we launch additional AI offerings, contribution will increase materially.

**Operator**: Question from Lisa Anderson with Brookline Advisory Group.

**Lisa Anderson**: Can you discuss competition? Are you seeing pricing pressure or market share shifts?

**{{CEO_NAME}}**: Competition is always intense in technology. We compete with large platforms, specialized point solutions, and emerging startups. Our differentiation comes from comprehensive capabilities, proven enterprise scale, and integration depth.

We're not seeing broad-based pricing pressure. Some specific product categories are competitive on price, but our value proposition usually wins on total cost of ownership. When customers consider not just license costs but implementation, operations, productivity gains, and innovation pace, we compete very effectively.

Market share data shows we're gaining in most categories. Our cloud infrastructure share is expanding, particularly in enterprise segment. Software categories are growing share steadily. We're winning more competitive evaluations than we're losing.

**{{CFO_NAME}}**: I'd note our revenue growth of {{YOY_GROWTH_PCT}}% is well above overall market growth rates, which by definition means share gain. And we're doing that whilst maintaining or expanding margins, which suggests we're winning on value not just price.

**Operator**: Final question from Robert Chen with Whitestone Equity Research.

**Robert Chen**: Thanks. Question on capital allocation. How are you thinking about M&A versus organic investment versus shareholder returns?

**{{CFO_NAME}}**: Our capital allocation framework remains consistent. Priority one is organic investment in the business where we see compelling returns. R&D, infrastructure, go-to-market — these drive our long-term growth and competitive position.

We're always evaluating M&A for capabilities, technology, or talent that accelerates our strategy. The bar is high. Acquisitions must be strategically aligned, financially attractive, and executable from integration perspective. We've done several smaller acquisitions this year adding specific capabilities, and we'll continue that pattern.

On shareholder returns, we increased our dividend {{DIV_INCREASE}}% this year and remain committed to growing it over time. Buybacks are opportunistic but substantial. We returned ${{CAPITAL_RETURN}}B this quarter and expect to be active returning capital whilst maintaining balance sheet strength.

**{{CEO_NAME}}**: I'll just add that we have financial flexibility to do all of these things simultaneously. Strong cash generation, solid balance sheet, and access to capital markets give us strategic flexibility. We can invest organically, pursue M&A when it makes sense, and return meaningful capital to shareholders.

## Closing

**{{CEO_NAME}}**: Thanks, everyone, for joining today. Q{{QUARTER_NUM}} was an outstanding quarter reflecting strong customer demand, excellent execution, and significant opportunity ahead. We're excited about our product pipeline, market position, and long-term growth prospects. We look forward to updating you next quarter.

**Operator**: This concludes the {{COMPANY_NAME}} {{FISCAL_QUARTER}} {{FISCAL_YEAR}} earnings call. Thank you for participating.

---

**Safe Harbor**: Forward-looking statements subject to risks and uncertainties. See SEC filings for risk factors.

*SAM Demo Content*

