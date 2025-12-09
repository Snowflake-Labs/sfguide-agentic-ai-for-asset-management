---
doc_type: earnings_transcripts
linkage_level: security
sector_tags: [Consumer Discretionary]
master_id: consumer_earnings_01
word_count_target: 6800
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
  QUARTERLY_REVENUE_BILLIONS: {min: 3, max: 100}
  QUARTERLY_EPS: {min: 0.5, max: 3.0}
disclosure:
  include_disclaimer: true
---

# {{COMPANY_NAME}} {{FISCAL_QUARTER}} {{FISCAL_YEAR}} Earnings Call

**Date**: {{PUBLISH_DATE}}  
**Participants**: {{CEO_NAME}} (CEO), {{CFO_NAME}} (CFO)

---

## Operator

Good afternoon, and welcome to the {{COMPANY_NAME}} {{FISCAL_QUARTER}} {{FISCAL_YEAR}} earnings conference call. All participants are in listen-only mode. Following the presentation, we will conduct a question-and-answer session.

I would now like to turn the conference over to Robert Martinez, Vice President of Investor Relations. Please go ahead.

## Robert Martinez, VP Investor Relations

Thank you, operator, and good afternoon, everyone. Welcome to {{COMPANY_NAME}}'s {{FISCAL_QUARTER}} {{FISCAL_YEAR}} earnings call.

Joining me are {{CEO_NAME}}, our Chief Executive Officer, and {{CFO_NAME}}, our Chief Financial Officer.

Before we begin, please note that this call contains forward-looking statements about our business outlook and future performance. These statements involve risks and uncertainties. Please review our SEC filings for detailed risk factors.

We will also discuss non-GAAP financial measures. Reconciliations to GAAP are in our earnings release.

{{CEO_NAME}}, over to you.

## {{CEO_NAME}}, CEO — Prepared Remarks

Thank you, Robert, and thank you all for joining.

I'm pleased to report excellent {{FISCAL_QUARTER}} results with revenue of ${{QUARTERLY_REVENUE_BILLIONS}} billion, up {{YOY_GROWTH_PCT}}% year-over-year, and diluted EPS of ${{QUARTERLY_EPS}}. These results exceeded our guidance and consensus expectations, demonstrating strong consumer demand, effective execution, and the power of our brands.

Our performance this quarter reflects the strength of our digital transformation, the resilience of consumer spending in our categories, and our team's ability to navigate a complex operating environment. We're seeing healthy consumer engagement across both physical retail and digital channels, with e-commerce representing an increasing share of total sales.

Digital sales grew {{DIGITAL_GROWTH}}% this quarter and now represent {{DIGITAL_PCT}}% of total revenue. Our omnichannel strategy is working, with customers seamlessly moving between online browsing, mobile app engagement, and in-store experiences. Data integration across channels enables personalized marketing and improved customer lifetime value.

Product innovation remains central to our strategy. We launched {{NEW_PRODUCTS}} new products this quarter, with particularly strong reception for our {{PRODUCT_CATEGORY}} offerings. Innovation allows us to command premium pricing whilst meeting evolving consumer preferences around sustainability, functionality, and design.

International expansion delivered strong results with non-US revenue growing {{INTL_GROWTH}}% year-over-year. We're seeing particular strength in Europe and Asia-Pacific markets where brand awareness is increasing and distribution is expanding. International represents {{INTL_PCT}}% of revenue, up from {{INTL_PRIOR_PCT}}% a year ago.

From a brand perspective, we made strategic marketing investments this quarter that are driving measurable results. Brand awareness metrics improved {{BRAND_AWARENESS}}ppts, and consumer sentiment scores increased {{SENTIMENT_IMPROVEMENT}}%. These brand investments support pricing power and customer acquisition efficiency.

Supply chain performance was solid despite ongoing global logistics challenges. We've diversified our supplier base, improved inventory management, and strengthened relationships with logistics partners. In-stock rates remained above {{INSTOCK_PCT}}%, and delivery times met customer expectations.

Before turning to {{CFO_NAME}}, I want to thank our global team for their outstanding execution and our customers for their continued loyalty to our brands.

{{CFO_NAME}}.

## {{CFO_NAME}}, CFO — Financial Review

Thank you, {{CEO_NAME}}.

{{FISCAL_QUARTER}} revenue was ${{QUARTERLY_REVENUE_BILLIONS}} billion, representing {{YOY_GROWTH_PCT}}% growth year-over-year. Growth was balanced across our major product categories and geographies.

By channel, retail revenue was ${{RETAIL_REVENUE}}B, up {{RETAIL_GROWTH}}%, whilst digital direct-to-consumer revenue was ${{DTC_REVENUE}}B, up {{DTC_GROWTH}}%. Wholesale revenue was ${{WHOLESALE_REVENUE}}B with growth of {{WHOLESALE_GROWTH}}%.

Gross profit was ${{GROSS_PROFIT}}B with gross margin of {{GROSS_MARGIN}}%, expanding {{MARGIN_EXPANSION}}bps year-over-year. Margin improvement reflects favorable channel mix toward higher-margin direct business, pricing realization, and supply chain efficiencies.

Operating expenses totaled ${{OPEX}}B. Marketing and advertising was ${{MARKETING}}B or {{MARKETING_PCT}}% of revenue. General and administrative expenses were ${{GA}}B. Total operating expenses grew {{OPEX_GROWTH}}%, slower than revenue growth, demonstrating operating leverage.

Operating income was ${{OPERATING_INCOME}}B with operating margin of {{OPERATING_MARGIN_PCT}}%. Net income was ${{NET_INCOME}}B, and diluted EPS was ${{QUARTERLY_EPS}}, up {{EPS_GROWTH}}% year-over-year.

Cash flow: Operating cash flow was ${{OCF}}B and free cash flow was ${{FCF}}B. We ended with cash of ${{CASH}}B.

Capital return: We paid dividends of ${{DIVIDENDS}}M and repurchased ${{BUYBACKS}}B of shares.

Guidance: Q{{NEXT_Q}} revenue ${{Q_NEXT_LOW}}B to ${{Q_NEXT_HIGH}}B, EPS ${{EPS_LOW}} to ${{EPS_HIGH}}. Full year revenue growth {{FY_GROWTH_LOW}}% to {{FY_GROWTH_HIGH}}%.

Operator, questions please.

## Q&A Session

**Operator**: First question from Amanda Foster with Kingswell Securities Research.

**Amanda Foster**: Congratulations. Can you talk about consumer health? Are you seeing any trade-down behavior or spending caution?

**{{CEO_NAME}}**: Amanda, consumer health remains generally good in our categories. We're a premium brand, so we watch for trading down carefully. What we're seeing is consumers prioritizing value — they're still willing to pay premium prices but expect premium products and experiences in return.

Our brand strength helps during uncertain times. Customers trust our quality and have emotional connections to our products. That loyalty provides resilience. We're not seeing meaningful trade-down to lower-priced alternatives.

That said, we're being thoughtful about pricing. We've taken selective price increases to offset cost inflation, but we're ensuring price increases are justified by value delivered. Maintaining customer trust is more important than maximizing short-term pricing.

**Operator**: Question from David Park with Crescent Point Analytics.

**David Park**: On digital growth, how sustainable is the {{DIGITAL_GROWTH}}% rate? And what's the margin difference between digital and retail?

**{{CFO_NAME}}**: Digital growth should remain strong though likely moderating from current peak rates. We see long-term structural shift toward online purchasing, particularly in younger demographics. Our digital channel can sustain 15-20% growth for several more years as we gain share and the overall market expands.

On margins, direct digital sales have gross margins {{DIGITAL_MARGIN_PREMIUM}}ppts higher than wholesale and {{DIGITAL_VS_RETAIL}}ppts higher than our own retail stores when you include occupancy costs. The margin advantage makes digital growth particularly valuable from profitability perspective.

That said, digital requires marketing spend to drive traffic and customer acquisition costs can be high. On a full P&L basis, digital and retail have comparable profitability, though digital scales better with growth.

**Operator**: Question from Lisa Thompson with Sterling Wharf Intelligence.

**Lisa Thompson**: Can you discuss inventory levels and any discounting or promotional activity?

**{{CFO_NAME}}**: Inventory management has been excellent this quarter. We ended with ${{INVENTORY}}B in inventory, representing {{INVENTORY_DAYS}} days, which is healthy and appropriate for our seasonal patterns. We're not sitting on excess inventory requiring heavy markdowns.

Promotional activity was in line with historical norms for the quarter. We ran planned promotions during key shopping events but didn't see need for elevated discounting to move product. Sell-through rates were strong, and margin realization was good.

**{{CEO_NAME}}**: I'd add that our inventory planning and demand forecasting have improved significantly through data analytics and AI. We're better at predicting demand, aligning production, and minimizing excess stock situations. This drives both margin improvement and working capital efficiency.

**Operator**: Final question from Thomas Richardson with Northgate Analytics.

**Thomas Richardson**: On sustainability, can you update us on ESG initiatives and whether consumers are rewarding sustainable products with higher purchase intent?

**{{CEO_NAME}}**: Sustainability is core to our strategy. We're making good progress toward our 2030 targets including {{SUSTAINABILITY_METRIC}}. This quarter we launched our first product line using {{SUSTAINABLE_MATERIAL}}% recycled materials, and consumer response has been very positive.

On purchase intent, we're definitely seeing sustainability influence decisions, particularly with younger consumers. Products marketed with sustainability attributes have {{SUSTAINABLE_PREMIUM}}% price premium and growing category share. This validates our sustainability investments both from brand and business perspectives.

We view sustainability as both responsibility and opportunity. Doing right thing for environment creates long-term business value through brand differentiation and operational efficiency.

---

## {{CEO_NAME}} — Closing

Thank you all for your time today. {{FISCAL_QUARTER}} was an excellent quarter demonstrating our brand strength, operational excellence, and growth opportunities. We're excited about our momentum and look forward to updating you on progress next quarter.

**Operator**: This concludes the {{COMPANY_NAME}} earnings call. Thank you for participating.

---

**Safe Harbor**: Forward-looking statements subject to risks. See SEC filings.

*SAM Demo*

