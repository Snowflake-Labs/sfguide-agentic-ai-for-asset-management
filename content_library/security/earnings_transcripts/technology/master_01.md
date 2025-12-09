---
doc_type: earnings_transcripts
linkage_level: security
sector_tags: [Information Technology]
master_id: tech_earnings_01
word_count_target: 8500
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
    - GROSS_MARGIN_PCT
    - OPERATING_MARGIN_PCT
    - GUIDANCE_REVENUE_LOW
    - GUIDANCE_REVENUE_HIGH
constraints:
  QUARTERLY_REVENUE_BILLIONS: {min: 10, max: 60}
  QUARTERLY_EPS: {min: 1.0, max: 5.0}
  YOY_GROWTH_PCT: {min: 8, max: 25}
disclosure:
  include_disclaimer: true
---

# {{COMPANY_NAME}} {{FISCAL_QUARTER}} {{FISCAL_YEAR}} Earnings Call Transcript

**Date**: {{PUBLISH_DATE}}  
**Participants**: {{CEO_NAME}} (CEO), {{CFO_NAME}} (CFO), Investor Relations Team

---

## Operator

Good afternoon, and welcome to {{COMPANY_NAME}}'s {{FISCAL_QUARTER}} {{FISCAL_YEAR}} earnings conference call. Today's call is being recorded. At this time, all participants are in a listen-only mode. Following management's prepared remarks, we will conduct a question-and-answer session. Instructions for queuing will be provided at that time.

I would now like to turn the call over to Sarah Thompson, Vice President of Investor Relations. Please go ahead.

## Sarah Thompson, VP Investor Relations

Thank you, operator, and good afternoon, everyone. Welcome to {{COMPANY_NAME}}'s {{FISCAL_QUARTER}} {{FISCAL_YEAR}} earnings call. Joining me today are {{CEO_NAME}}, our Chief Executive Officer, and {{CFO_NAME}}, our Chief Financial Officer.

Before we begin, I'd like to remind you that this call will contain forward-looking statements regarding our business outlook, future financial and operating results, and overall business environment. These statements are subject to risks and uncertainties that could cause actual results to differ materially from our current expectations. We encourage you to review the risk factors detailed in our SEC filings.

Additionally, we will discuss certain non-GAAP financial measures. Reconciliations to the most directly comparable GAAP measures are available in our earnings press release and investor presentation, both of which can be found on our investor relations website.

With that, I'll turn the call over to {{CEO_NAME}}.

## {{CEO_NAME}}, Chief Executive Officer — Prepared Remarks

Thank you, Sarah, and thank you all for joining us today. I'm pleased to report another strong quarter for {{COMPANY_NAME}}, with results that demonstrate the strength of our technology platform, the quality of our execution, and the significant opportunities ahead of us.

Let me start with our {{FISCAL_QUARTER}} financial highlights. Revenue reached ${{QUARTERLY_REVENUE_BILLIONS}} billion, representing {{YOY_GROWTH_PCT}}% growth year-over-year. Earnings per share came in at ${{QUARTERLY_EPS}}, exceeding consensus expectations. These results reflect strong performance across all business segments and continued momentum in our strategic growth initiatives.

Our cloud computing platform continues to be the primary driver of our growth story. Cloud revenue grew {{CLOUD_GROWTH}}% this quarter, with increasing adoption from both new customers and expansion within our existing installed base. We're seeing particularly strong traction in enterprise accounts, where customers are consolidating workloads onto our platform for its security, reliability, and comprehensive capabilities.

Artificial intelligence and machine learning capabilities are becoming increasingly central to our customer value proposition. The AI features we've integrated across our product portfolio are driving higher engagement, improved customer outcomes, and expanded use cases. Customer feedback on our AI-powered tools has been exceptionally positive, and we're investing aggressively to maintain our leadership position in this critical area.

Our subscription and recurring revenue model continues to evolve favourably. Approximately 85% of total revenue now comes from subscription-based offerings, providing excellent visibility and predictability. Customer retention rates remain industry-leading at over 95%, and we're seeing healthy expansion in average contract values as customers adopt additional services and upgrade to premium tiers.

From a strategic perspective, we made significant progress on several key initiatives during the quarter. First, we launched three new AI-enhanced products that address specific customer pain points in data analytics, cybersecurity, and workflow automation. Early customer adoption has exceeded our internal targets, and pipeline development for these products is robust.

Second, our international expansion efforts are gaining momentum. Revenue from markets outside North America grew {{INTERNATIONAL_GROWTH}}% year-over-year, with particular strength in Europe and Asia-Pacific. We've invested in local partnerships and go-to-market capabilities that position us well for sustained international growth.

Third, our sustainability and ESG initiatives continue to advance. We achieved carbon neutrality in our own operations this quarter and are making excellent progress toward our 2030 net-zero commitments. Customers increasingly value our sustainability leadership, and we're seeing ESG considerations influence purchasing decisions, particularly with large enterprise accounts.

Looking at the competitive landscape, we believe we're gaining market share across key categories. Our technology differentiation, combined with superior customer service and comprehensive platform capabilities, is resonating strongly in the market. Whilst competition remains intense, our innovation pace and execution quality provide confidence in our ability to maintain and extend our competitive advantages.

Before turning it over to {{CFO_NAME}} for detailed financial review, I want to thank our global team for their outstanding execution this quarter. The results we're reporting today reflect the dedication, innovation, and customer focus of our people around the world.

With that, I'll hand it over to {{CFO_NAME}}.

## {{CFO_NAME}}, Chief Financial Officer — Financial Review

Thank you, {{CEO_NAME}}, and good afternoon, everyone. I'll provide more detail on our {{FISCAL_QUARTER}} financial results and discuss our outlook for the remainder of {{FISCAL_YEAR}}.

Total revenue for the quarter was ${{QUARTERLY_REVENUE_BILLIONS}} billion, up {{YOY_GROWTH_PCT}}% year-over-year and ahead of our guidance range. This strong performance was driven by cloud platform revenue growth of {{CLOUD_GROWTH}}%, software subscription revenue growth of {{SOFTWARE_GROWTH}}%, and services revenue growth of {{SERVICES_GROWTH}}%.

Breaking down our revenue by segment, our cloud computing platform generated ${{CLOUD_REVENUE}}B in revenue, representing {{CLOUD_PERCENTAGE}}% of total revenue. This segment continues to scale efficiently, with gross margins expanding to {{CLOUD_MARGIN}}% as we benefit from improved infrastructure utilization and more favourable contract mix.

Our software segment delivered ${{SOFTWARE_REVENUE}}B in revenue with {{SOFTWARE_GROWTH}}% year-over-year growth. The shift toward subscription-based licensing continues to progress well, with subscription revenue now representing 78% of total software revenue, up from 68% in the same quarter last year. This transition is temporarily impacting revenue recognition timing but significantly improves long-term revenue quality and visibility.

Professional services and support revenue was ${{SERVICES_REVENUE}}B, growing {{SERVICES_GROWTH}}% year-over-year. Whilst this segment grows more slowly than our cloud and software businesses, it generates attractive margins and strengthens customer relationships, supporting retention and expansion opportunities.

From a profitability perspective, gross profit margin was {{GROSS_MARGIN_PCT}}%, consistent with our expectations and slightly ahead of the prior year period. The improvement reflects favourable product mix shifts toward higher-margin cloud and software revenue, partially offset by infrastructure investments supporting our AI capabilities.

Operating expenses increased {{OPEX_GROWTH}}% year-over-year, reflecting continued investments in R&D, sales capacity, and go-to-market programmes. Operating margin came in at {{OPERATING_MARGIN_PCT}}%, demonstrating our ability to balance growth investments with profitability. We remain committed to operating leverage, targeting margin expansion as revenue scales.

Net income for the quarter was ${{NET_INCOME}}B, and diluted earnings per share was ${{QUARTERLY_EPS}}, representing {{EPS_GROWTH}}% growth year-over-year. Our tax rate for the quarter was {{TAX_RATE}}%, in line with our full-year guidance.

Turning to the balance sheet and cash flow, we ended the quarter with cash and marketable securities of ${{CASH_BALANCE}}B. Operating cash flow for the quarter was ${{OPERATING_CASH_FLOW}}B, and free cash flow was ${{FREE_CASH_FLOW}}B after capital expenditures. Our strong cash generation supports both organic growth investments and capital return to shareholders.

During the quarter, we repurchased ${{BUYBACK_AMOUNT}}B of our shares and paid ${{DIVIDEND_AMOUNT}}M in dividends. Our Board has approved an additional $10B share repurchase authorisation, demonstrating confidence in our business outlook and commitment to shareholder value creation.

Now turning to our guidance for the coming quarter and full year. For Q4, we expect revenue between ${{GUIDANCE_REVENUE_LOW}}B and ${{GUIDANCE_REVENUE_HIGH}}B, representing year-over-year growth of approximately {{GUIDANCE_GROWTH_LOW}}% to {{GUIDANCE_GROWTH_HIGH}}%. We anticipate operating margin of approximately {{GUIDANCE_OPMARGIN}}%, reflecting seasonal patterns and continued strategic investments.

For the full year {{FISCAL_YEAR}}, we are raising our revenue guidance to reflect our strong year-to-date performance. We now expect full-year revenue growth of {{FULL_YEAR_GROWTH_LOW}}% to {{FULL_YEAR_GROWTH_HIGH}}%, up from our previous guidance. Operating margin for the full year should be approximately {{FULL_YEAR_MARGIN}}%.

In summary, {{FISCAL_QUARTER}} was an excellent quarter demonstrating the strength of our business model and the significant opportunities ahead. We're executing well across all key initiatives whilst maintaining financial discipline and generating strong returns for shareholders.

With that, operator, let's open the line for questions.

## Question and Answer Session

**Operator**: Thank you. We'll now begin the question-and-answer session. Our first question comes from Michael Chen with Northgate Analytics.

**Michael Chen, Northgate Analytics**: Good afternoon, and congratulations on the strong results. My question is on the cloud platform segment. Can you provide more colour on what's driving the acceleration we're seeing? Is it new customer acquisition, existing customer expansion, or both? And how should we think about sustainability of these growth rates?

**{{CEO_NAME}}**: Thanks, Michael. Great question. The cloud acceleration is really being driven by both factors you mentioned. On new customer acquisition, we're seeing very strong demand particularly from mid-market and enterprise segments. Companies are consolidating workloads from multiple cloud providers onto our platform because of the comprehensive capabilities, security features, and cost efficiency we provide.

But equally important is the expansion we're seeing within existing customers. Our dollar-based net retention rate this quarter was {{NET_RETENTION_PCT}}%, which demonstrates that existing customers are significantly growing their spending with us. This is driven by workload migration from on-premises infrastructure, adoption of new services we've launched, and customers moving more mission-critical applications to our platform.

**{{CFO_NAME}}**: I'll add to that, Michael. On sustainability, we feel good about the growth trajectory. The cloud market itself is still growing mid-to-high teens percentage points annually, and we're taking share within that growing market. Our pipeline remains very healthy, and the sales cycles we're seeing are actually shortening as cloud adoption becomes less of a "should we?" question and more of a "how fast can we?" implementation exercise.

**Michael Chen**: That's helpful. And as a follow-up, can you talk about the competitive environment? We're seeing some pricing aggression from competitors. How are you thinking about pricing strategy versus market share?

**{{CEO_NAME}}**: We're definitely aware of competitive pricing dynamics. Our approach has been to lead with value rather than just price. When customers evaluate total cost of ownership — including not just compute costs but also productivity gains, reduced operational overhead, and superior capabilities — we consistently win on value proposition.

That said, we're also innovating on pricing models. Our consumption-based pricing provides customers with flexibility and cost alignment with their actual usage. We've introduced optimization tools that help customers rightsize their deployments, which builds trust and long-term relationships even if it means slightly lower revenue in the near term.

**Operator**: Our next question comes from Jennifer Martinez with Fairmont Capital Insights.

**Jennifer Martinez, Fairmont Capital Insights**: Hi, thank you. I wanted to ask about the AI initiatives you mentioned. Can you quantify how much AI is contributing to growth? And how do you think about monetization of these AI capabilities?

**{{CEO_NAME}}**: Jennifer, AI is becoming embedded across essentially everything we do, so it's challenging to isolate its specific contribution. What I can tell you is that products with AI features have significantly higher adoption rates and customer engagement metrics. We're seeing {{AI_ADOPTION_PCT}}% of our enterprise customers now actively using our AI-powered tools.

From a monetization perspective, we're taking multiple approaches. Some AI capabilities are included in premium tier subscriptions, which helps drive upgrades. Others are offered as add-on modules with separate pricing. And in some cases, AI features reduce our own operational costs, which improves margins.

**{{CFO_NAME}}**: To Jennifer's question on financial impact, whilst we don't break out AI revenue separately, I can share that products launched in the past 18 months with significant AI components are growing revenue at roughly 2x the rate of our legacy products. These newer products also carry higher gross margins, which is contributing to the overall margin expansion we're seeing.

The investment we're making in AI infrastructure and talent is substantial — probably $2-3 billion annually when you include R&D, infrastructure, and strategic partnerships. But we believe this positions us to capture a disproportionate share of the AI-driven market opportunity, which more than justifies the investment.

**Jennifer Martinez**: That's very helpful context. Thank you.

**Operator**: Our next question comes from David Park with Sterling Wharf Intelligence.

**David Park, Sterling Wharf Intelligence**: Good afternoon. Question on operating margins. You delivered {{OPERATING_MARGIN_PCT}}% this quarter, which is impressive. But you're also investing heavily in growth. How do you think about the right balance between growth investment and margin expansion? And where do you see margins trending longer term?

**{{CFO_NAME}}**: David, this is the key strategic question we wrestle with each quarter. Our philosophy has been to invest aggressively when we see high-return opportunities, but we also want to demonstrate operating leverage to shareholders. The framework we use is to ensure that incremental investments are generating appropriate returns, typically targeting 3-5x return on invested capital for new initiatives.

This quarter, we expanded operating margins by {{MARGIN_EXPANSION_BPS}} basis points year-over-year whilst increasing R&D spending by {{RD_GROWTH}}%. That demonstrates we can do both — invest for growth and improve profitability through scale efficiencies and operational improvements.

Longer term, we see a path to 35-40% operating margins over the next 3-5 years, up from {{OPERATING_MARGIN_PCT}}% today. The key drivers will be revenue scale, particularly in high-margin cloud and software segments, continued automation of customer support and operations, and infrastructure efficiency improvements.

**{{CEO_NAME}}**: I'd just add that we're not managing the business to hit specific margin targets in any given quarter. If we see compelling investment opportunities that will drive long-term shareholder value, we'll pursue them even if they create near-term margin headwinds. But structurally, this business model has significant operating leverage, and shareholders should expect to see that materialise over time.

**Operator**: Our next question comes from Rebecca Foster with Granite Peak Advisory.

**Rebecca Foster, Granite Peak Advisory**: Hi there. I wanted to ask about the enterprise versus SMB customer mix. Are you seeing different growth rates or margin profiles between these segments? And how does your go-to-market strategy differ?

**{{CEO_NAME}}**: Rebecca, we're seeing strong growth in both segments but with somewhat different dynamics. Enterprise customers represent about {{ENTERPRISE_PCT}}% of revenue and are growing {{ENTERPRISE_GROWTH}}% year-over-year. These are typically longer sales cycles but much larger contract values and excellent expansion characteristics once we land the initial workload.

SMB customers are growing slightly faster at {{SMB_GROWTH}}% year-over-year, driven by our self-service and digital channels. Contract values are obviously smaller, but the sales efficiency is much higher, and we can serve these customers at scale with largely automated onboarding and support processes.

From a margin perspective, both segments are attractive. Enterprise has higher gross margins due to contract structure and infrastructure efficiency at scale. But SMB has very low customer acquisition costs through our digital channels, so the unit economics work well for both.

**{{CFO_NAME}}**: I'll add that strategically, we see both segments as critical to our long-term success. Enterprise customers provide stability, large revenue scale, and often act as reference customers for broader market adoption. SMB customers provide volume, diversification, and a proving ground for new products before we take them upmarket to enterprise.

**Operator**: Our next question comes from Thomas Lee with Ashfield Partners.

**Thomas Lee, Ashfield Partners**: Thank you. Question on international markets. You mentioned strong international growth. Can you break down the regional performance? And are you seeing any macro headwinds in specific geographies?

**{{CFO_NAME}}**: Sure, Thomas. International revenue was ${{INTL_REVENUE}}B, growing {{INTL_GROWTH}}% year-over-year and now representing {{INTL_PCT}}% of total company revenue. Europe remains our largest international market with solid mid-teens growth despite some macroeconomic uncertainty. We're seeing particular strength in the UK, Germany, and Nordics.

Asia-Pacific is our fastest-growing region at {{APAC_GROWTH}}% year-over-year, though from a smaller base. Japan, Australia, and Singapore are performing exceptionally well. We're also seeing accelerating adoption in India, which we view as a massive long-term opportunity.

On macro headwinds, we're certainly monitoring global economic conditions closely. We have seen some elongation of deal cycles in certain European markets where economic uncertainty is higher. But overall, demand for our solutions remains strong because customers view technology infrastructure as strategic and essential rather than discretionary.

**{{CEO_NAME}}**: I'd emphasise that our international opportunity is still in early innings. We're under-indexed in international markets relative to the global revenue opportunity. The investments we're making in local partnerships, data centre infrastructure, and go-to-market capabilities are setting us up for sustained international growth over many years.

**Operator**: Our next question comes from Amanda Rodriguez with Bluehaven Capital Research.

**Amanda Rodriguez, Bluehaven Capital Research**: Hi, thanks for taking my questions. On free cash flow, it came in a bit lighter than we modeled. Can you walk through the working capital dynamics? And how should we think about free cash flow trajectory for the remainder of the year?

**{{CFO_NAME}}**: Good question, Amanda. Free cash flow of ${{FREE_CASH_FLOW}}B was down slightly sequentially, primarily due to timing of collections and some seasonal working capital movements. The specific drivers were accounts receivable, which increased due to strong revenue performance and some larger enterprise contracts with slightly extended payment terms, and infrastructure CapEx investments supporting our AI and cloud capacity expansion.

Looking forward, we expect free cash flow to accelerate in Q4, as typically happens with our seasonal patterns. Collections usually pick up significantly in the fourth quarter, and CapEx should moderate slightly. For the full year, we continue to target free cash flow conversion of approximately {{FCF_CONVERSION}}% of operating cash flow.

It's worth noting that our CapEx this year is elevated due to strategic investments in AI infrastructure and data centre expansion. These investments have very attractive returns and are critical to supporting our growth. But they do create a temporary headwind to free cash flow in the current year that reverses as the capacity we're building comes online and generates revenue.

**Amanda Rodriguez**: That makes sense. And just quickly, any changes to capital allocation priorities given the strong business momentum?

**{{CFO_NAME}}**: No changes to our overall framework. Priority one is always investing in the business — R&D, sales capacity, infrastructure — where we see compelling returns. Priority two is maintaining a strong balance sheet with ample liquidity. And priority three is returning capital to shareholders through a combination of dividends and share repurchases.

We increased our dividend {{DIVIDEND_INCREASE}}% earlier this year, and as I mentioned, the Board just approved an additional $10B buyback authorization. We'll continue to be opportunistic on buybacks, but you should expect us to be active return of capital to shareholders whilst maintaining financial flexibility for organic investments or potential strategic M&A.

**Operator**: Our final question comes from Kevin Walsh with Regent Square Analytics.

**Kevin Walsh, Regent Square Analytics**: Good afternoon. My question is on the competitive moat. What do you see as the most important sustainable competitive advantages? And how are you defending against both traditional competitors and new entrants?

**{{CEO_NAME}}**: Kevin, I think our competitive moat has several components. First and most important is our technology lead. We invest ${{RD_BILLIONS}}B+ annually in R&D, which is amongst the highest in our industry. That investment pace is difficult for smaller competitors to match, and it allows us to continuously extend our technology differentiation.

Second is our customer relationships and installed base. With millions of customers running mission-critical workloads on our platform, we have deep integrations and switching costs that create natural stickiness. Our 95%+ retention rate reflects this dynamic.

Third is our ecosystem and partner network. We've built out extensive partnerships with systems integrators, ISVs, and technology partners that make our platform more valuable to customers. This network effect strengthens over time as more participants join the ecosystem.

Fourth is brand and trust. Particularly in enterprise markets, our reputation for security, reliability, and customer support matters enormously. That trust is earned over many years and isn't easily replicated.

To defend these advantages, we're focused on innovation velocity, customer success, and strategic investments in emerging technologies like AI where we can establish early leadership. We're also cognizant of potential disruption and actively invest in areas that could threaten our core business, ensuring we're either the disruptor or the fast follower.

**{{CFO_NAME}}**: I'll just add that we measure ourselves constantly against both traditional technology competitors and emerging challengers. We track detailed competitive metrics across product categories, win rates, pricing dynamics, and customer satisfaction. This data-driven approach to competitive intelligence helps us stay ahead of market shifts and adjust our strategy dynamically.

## {{CEO_NAME}} — Closing Remarks

Before we close, I want to reiterate a few key points. First, {{COMPANY_NAME}} delivered another quarter of strong financial performance and strategic progress. Second, the long-term growth opportunities in front of us — in cloud computing, AI, international markets, and emerging technologies — are substantial and expanding. Third, we have the right strategy, team, and financial resources to capitalize on these opportunities whilst delivering value to shareholders.

Thank you all for your time today and your continued interest in {{COMPANY_NAME}}. We look forward to updating you on our progress next quarter.

**Operator**: This concludes today's {{COMPANY_NAME}} {{FISCAL_QUARTER}} {{FISCAL_YEAR}} earnings conference call. Thank you for participating. You may now disconnect.

---

**Forward-Looking Statements**: This transcript contains forward-looking statements involving risks and uncertainties. Actual results may differ materially from those discussed today. Please refer to our SEC filings for detailed risk factors.

*SAM Demo Content. Company details and figures are illustrative for demonstration purposes.*

