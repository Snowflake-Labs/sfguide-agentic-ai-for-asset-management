# SAM Demo - Demo Scenario Documentation Standards

Complete guide for documenting demo scenarios following the established structure and format. This rule ensures consistency when adding new scenarios or steps to existing demo flows.

## Overview

Demo scenarios must follow a standardized structure that provides clear business context, structured demo flows, and compelling wrap-ups. This format ensures professional presentations with consistent messaging and technical differentiation.

**Required Structure for All Scenarios:**
1. **Business Context Setup** - Persona, challenge, and value proposition
2. **Demo Flow** - Scene setting and structured steps with talking points
3. **Scenario Wrap-up** - Business impact and technical differentiators

## Scenario Documentation Template

### Document Structure (Role-Based Organization)

**Critical Heading Hierarchy:**
```
## {Role Name}                           ← Level 2: Role section
### {Role Name} - {Scenario Title}       ← Level 3: Scenario header
#### Business Context Setup              ← Level 4: Major sections
#### Demo Flow                           ← Level 4: Major sections
##### Step 1: {Step Title}               ← Level 5: Individual steps
##### Step 2: {Step Title}               ← Level 5: Individual steps
#### Scenario Wrap-up                    ← Level 4: Major sections
```

**Complete Template:**
```markdown
# SAM Demo - Scenario Scripts

## Available Scenarios by Role

### {Role Name}
**Agent: {Agent Name}**
- {Scenario Name} ✅ **IMPLEMENTED** or ❌ **NOT IMPLEMENTED**

### {Role Name}
**Agent: {Agent Name}**
- {Scenario Name} ✅ **IMPLEMENTED** or ❌ **NOT IMPLEMENTED**
- {Additional Scenario} ✅ **IMPLEMENTED** or ❌ **NOT IMPLEMENTED**

---

## {Role Name}

### {Role Name} - {Scenario Title}

#### Business Context Setup

**Persona**: {Full Name}, {Title} at Simulated Asset Management  
**Business Challenge**: {Detailed description of the specific business problem that traditional systems struggle with. Include pain points, inefficiencies, and risks of current manual processes.}  
**Value Proposition**: {Clear articulation of how AI solves the challenge. Focus on speed, accuracy, integration, and business outcomes.}

**Agent**: `{agent_name}`  
**Data Available**: {Brief description of data scope and document counts}

#### Demo Flow

**Scene Setting**: {Context-setting narrative that explains why the persona needs to perform these tasks now. Include business urgency, meeting preparation, or decision deadlines.}

##### Step 1: {Step Title}
**User Input**: 
```
"{Exact query to demonstrate - use realistic business language}"
```

**Tools Used**:
- `tool_name` (Tool Type) - Brief description of what the tool retrieves

**Expected Response**:
- **{Category}**: Description of data type returned (no specific values)
  | Column Type | Description |
  |-------------|-------------|
  | Example | Shows format without specific values |
- **{Category}**: Brief description of what will be shown
- **Flagging**: Description of any warnings or flags that should appear

**Presenter Transition** (REQUIRED for Steps 2+):
> "[Quote explaining why moving to next step - presenter speaks this]"

*Reasoning: [Brief explanation of demo logic and why this transition makes sense]*

**Talking Points**:
- {Key message about AI capability demonstrated}
- {Business value or efficiency gain highlighted}
- {Technical sophistication or integration shown}

**Key Features Highlighted**: 
- {Specific Snowflake capability showcased}
- {Technical differentiator emphasized}
- {Integration or AI feature demonstrated}

##### Step 2: {Step Title}

**Presenter Transition**:
> "[Quote explaining transition from Step 1]"

*Reasoning: [Why this step follows logically]*

**User Input**: 
```
"{Query that builds on Step 1 results}"
```

{Repeat remaining structure for each step}

##### Step 3: {Step Title}
{Repeat structure with Presenter Transition}

##### Step 4: {Step Title}
{Repeat structure with Presenter Transition}

#### Scenario Wrap-up

**Business Impact Summary**:
- **{Impact Category}**: {Quantified business benefit with specific outcomes}
- **{Impact Category}**: {Quantified business benefit with specific outcomes}
- **{Impact Category}**: {Quantified business benefit with specific outcomes}
- **{Impact Category}**: {Quantified business benefit with specific outcomes}

**Technical Differentiators**:
- **{Technical Capability}**: {Unique technical advantage that competitors can't match}
- **{Technical Capability}**: {Unique technical advantage that competitors can't match}
- **{Technical Capability}**: {Unique technical advantage that competitors can't match}
- **{Technical Capability}**: {Unique technical advantage that competitors can't match}
```

### Documentation Organization Standards

**Role-Based Structure Requirements:**
- Group scenarios by business role (Portfolio Manager, Research Analyst, etc.)
- Each role section contains multiple agent types
- Each agent can have multiple scenarios
- Status tracking only in "Available Scenarios by Role" overview section

**Clean Header Standards:**
- Scenario headers contain NO status indicators (no ✅ IMPLEMENTED or ❌ NOT IMPLEMENTED)
- Agent names in role overview contain NO status indicators
- Status indicators ONLY appear at scenario level in overview section
- All headers use clean, professional formatting

## Content Guidelines

### Business Context Setup Requirements

**Persona Guidelines:**
- Use full name and specific title
- Always include "at Simulated Asset Management"
- Choose realistic financial services roles
- Examples: "Anna, Senior Portfolio Manager", "Dr. James Chen, Quantitative Analyst"

**Business Challenge Guidelines:**
- Describe specific pain points with current manual processes
- Include time inefficiencies and error risks
- Mention system silos and integration challenges
- Highlight decision-making delays
- Use realistic business language and scenarios

**Value Proposition Guidelines:**
- Lead with speed and efficiency gains
- Emphasize AI-powered capabilities
- Highlight integration benefits
- Focus on decision-making enhancement
- Use action-oriented language

### Demo Flow Requirements

**Scene Setting Guidelines:**
- Provide realistic business context for why tasks are needed now
- Include time pressure or meeting preparation scenarios
- Reference specific business events (quarterly reviews, client meetings, etc.)
- Make the scenario relatable and urgent

**User Input Guidelines:**
- Use natural business language, not technical queries
- Make queries realistic for the persona
- Include specific portfolio names, company names, or business terms
- Avoid overly technical or artificial phrasing
- Use UK English spelling and terminology

**Expected Response Guidelines (Simplified - No Specific Values):**
- Use hybrid format: bullet summaries with table structures
- Describe data TYPES returned, not specific values (no percentages, dates, or amounts)
- Include flagging requirements (concentration warnings, severity levels)
- Specify table column structure without example data
- This ensures documentation remains valid regardless of data generation

**Expected Response Format - CORRECT:**
```markdown
- **Performance Summary**: Period returns compared to benchmark
  | Metric Type | Description |
  |-------------|-------------|
  | Returns | Portfolio vs benchmark by period |
  | Attribution | Factor contributions to performance |
- **Flagging**: Positions exceeding concentration thresholds with warning/breach indicators
```

**Expected Response Format - AVOID (too detailed):**
```markdown
- Q4 2024 Return: +8.2%
- Benchmark (MSCI ACWI): +7.5%
- Top Holding: Apple at 8.2% (£41.2M)
```

**Presenter Transition Guidelines (REQUIRED for Steps 2+):**
- Include between ALL steps in multi-step scenarios
- Format as quoted presenter speech explaining why moving to next step
- Add *Reasoning* explanation for demo logic
- Helps presenters understand the flow and explain it naturally

**Presenter Transition Format:**
```markdown
**Presenter Transition**:
> "We've seen the portfolio holdings. But data alone doesn't tell the full story—what are analysts saying about these positions? Let me show you how we seamlessly transition from quantitative data to qualitative research..."

*Reasoning: Quantitative holdings data raises questions that qualitative research can answer. This demonstrates the multi-modal capability.*
```

**Talking Points Guidelines:**
- Focus on business value, not technical features
- Emphasize speed and efficiency gains
- Highlight AI capabilities that impress audiences
- Connect to real business pain points
- Use presenter-friendly language

**Key Features Highlighted Guidelines:**
- Name specific Snowflake capabilities
- Focus on technical differentiators
- Emphasize integration and AI features
- Use technical terms appropriately
- Connect features to business outcomes

### Scenario Wrap-up Requirements

**Business Impact Summary Guidelines:**
- Use quantified benefits where possible (time savings, efficiency gains)
- Focus on measurable business outcomes
- Include operational improvements
- Highlight competitive advantages
- Use action-oriented impact categories

**Technical Differentiators Guidelines:**
- Emphasize unique Snowflake capabilities
- Focus on AI and integration advantages
- Highlight technical sophistication
- Use technical terms that impress IT audiences
- Connect technical features to business value

## Flagging and Response Behavior Documentation

### When to Document Expected Flagging
Always document flagging behaviors in Expected Response sections using the simplified format (describe types, not specific values):

**Concentration Warnings:**
```markdown
**Expected Response**:
- **Holdings Analysis**: Table of positions by weight
  | Column | Description |
  |--------|-------------|
  | Ticker | Security identifier |
  | Weight % | Portfolio allocation |
  | Status | Compliant/Warning/Breach indicator |
- **Flagging**: Positions >6.5% flagged with warning, >7.0% flagged as breach
- **Summary**: Total flagged exposure and recommended actions
```

**Compliance Breaches:**
```markdown
**Expected Response**:
- **Breach Identification**: List of positions exceeding policy limits
  | Column | Description |
  |--------|-------------|
  | Position | Security or issuer name |
  | Current | Current weight percentage |
  | Limit | Policy threshold |
  | Status | Warning or Breach classification |
- **Severity Assessment**: Classification by urgency and impact
- **Remediation**: Required actions and timelines per policy
```

**ESG Severity Levels:**
```markdown
**Expected Response**:
- **Controversy Summary**: Flagged issues by severity level
  | Column | Description |
  |--------|-------------|
  | Company | Affected portfolio company |
  | Issue | Nature of controversy |
  | Severity | High/Medium/Low classification |
  | Source | NGO or news source |
- **Exposure Analysis**: Portfolio impact of flagged companies
- **Recommended Actions**: Engagement or divestment considerations
```

### Alignment with Agent Instructions
Ensure all expected flagging behaviors are reflected in corresponding agent instructions:
- Portfolio agents: Concentration warning flagging (6.5%)
- Compliance agents: Breach (7%) and warning (6.5%) flagging
- ESG agents: Severity level classification (High/Medium/Low)
- Sales agents: Professional report formatting requirements
- Quant agents: Statistical significance and confidence intervals

## Quality Standards

### Content Quality Requirements
- **Realistic Language**: Use authentic business terminology and scenarios
- **Professional Tone**: Maintain executive-level communication standards
- **Consistent Formatting**: Follow template structure exactly
- **UK English**: Use British spelling and financial terminology throughout
- **Business Focus**: Emphasize business value over technical features

### Technical Accuracy Requirements
- **Agent Alignment**: Ensure expected responses match agent capabilities
- **Data Consistency**: Use realistic portfolio names and company examples
- **Feature Accuracy**: Only reference implemented Snowflake capabilities
- **Integration Logic**: Ensure multi-step flows make business sense

### Presentation Requirements
- **Demo Flow Logic**: Each step should build naturally to the next
- **Time Management**: 4-step flows should take 10-15 minutes total
- **Audience Engagement**: Include impressive moments and "wow" factors
- **Business Relevance**: All scenarios should solve real business problems

## Examples of Good vs Bad Documentation

### ✅ Good Example - Business Challenge
```markdown
**Business Challenge**: Portfolio managers need instant access to portfolio analytics, holdings information, and supporting research to make informed investment decisions. Traditional systems require multiple tools, manual data gathering, and time-consuming analysis that delays critical investment decisions.
```

### ❌ Bad Example - Business Challenge
```markdown
**Business Challenge**: Portfolio managers need data.
```

### ✅ Good Example - User Input
```markdown
**User Input**: 
```
"What are my top 10 holdings by market value in the SAM Technology & Infrastructure portfolio?"
```
```

### ❌ Bad Example - User Input
```markdown
**User Input**: 
```
"SELECT * FROM holdings WHERE portfolio = 'tech'"
```
```

### ✅ Good Example - Expected Response (Simplified Format)
```markdown
**Expected Response**:
- **Holdings Table**: Top positions by market value
  | Column | Description |
  |--------|-------------|
  | Ticker | Security identifier |
  | Company Name | Full company name |
  | Weight % | Portfolio allocation percentage |
  | Market Value | Position value in base currency |
- **Concentration Flags**: Positions exceeding 6.5% flagged with warning indicator
- **Summary**: Total exposure percentage of top positions
```

### ❌ Bad Example - Expected Response (Too Specific)
```markdown
**Expected Response**:
- Apple: 8.2% (£41.2M) - 🚨 BREACH
- Microsoft: 7.4% (£37.1M) - 🚨 BREACH
- NVIDIA: 6.8% (£34.1M) - ⚠️ WARNING
- Q4 2024 Return: +8.2%
```

### ❌ Bad Example - Expected Response (Too Vague)
```markdown
**Expected Response**:
- Show some data
```

## Demo Coherence Requirements

### Critical Challenge: Multi-Step Flow Dependencies
Demo scenarios with multiple steps must ensure logical progression where each step builds on previous results. Random data generation can break coherence when Step 2 references entities not mentioned in Step 1.

### Solution Approach: Dual Strategy
1. **Enhanced Data Generation**: Ensure key demo companies get theme-specific content
2. **Refined Query Design**: Make queries more specific to increase hit probability

### Example: Research Copilot Demo Fix
**Problem**: 
- Step 1: "What is the latest research saying about technology sector opportunities?"
- Step 2: "Based on those technology opportunities, give me a detailed analysis of Microsoft's recent performance..."
- **Issue**: Step 1 didn't return Microsoft research, breaking Step 2 flow

**Solution Applied**:
- **Data Enhancement**: Modified broker research generation to ensure Microsoft gets "technology sector opportunities" themed content
- **Query Refinement**: Changed Step 1 to "What is the latest research saying about AI and cloud computing opportunities in technology companies?"
- **Result**: Guaranteed Microsoft appears in Step 1 for coherent Step 2 follow-up

### Demo Coherence Best Practices
1. **Map Dependencies**: Identify which entities must appear in which steps
2. **Specific Queries**: Use targeted queries rather than broad themes
3. **Expected Alignment**: Ensure expected responses match likely data generation outcomes
4. **Validation Testing**: Test complete flows after data regeneration
5. **Fallback Strategies**: Design queries that work even with partial data coverage

### Query Design Patterns
```markdown
# ✅ Good - Specific and targeted
"What is the latest research saying about AI and cloud computing opportunities in technology companies?"

# ❌ Risky - Too broad, unpredictable results  
"What is the latest research saying about technology sector opportunities?"

# ✅ Good - References specific context
"Based on those AI and cloud opportunities, give me a detailed analysis of Microsoft's recent performance..."

# ❌ Bad - Assumes specific company mentioned
"Based on those technology opportunities, give me a detailed analysis of Apple's recent performance..."
```

## Status Management Standards

### Implementation Status Guidelines

**Status Centralization:**
- All implementation status tracking occurs ONLY in "Available Scenarios by Role" section
- Status appears at scenario level: `✅ **IMPLEMENTED**` or `❌ **NOT IMPLEMENTED**`
- Agent names and scenario headers throughout document contain NO status indicators
- Clean, professional headers maintain focus on content rather than implementation state

**Status Placement Rules:**
```markdown
# ✅ CORRECT - Status in overview only (at document top)
## Available Scenarios by Role

### Portfolio Manager
**Agent: Portfolio Copilot**
- Portfolio Insights & Benchmarking ✅ **IMPLEMENTED**

---

## Portfolio Manager

### Portfolio Copilot - Portfolio Insights & Benchmarking
{Clean header with no status - Level 3 heading}

#### Business Context Setup
{Level 4 heading}

#### Demo Flow
{Level 4 heading}

##### Step 1: Top Holdings Overview
{Level 5 heading}

# ❌ WRONG - Status in scenario headers
### Portfolio Copilot - Portfolio Insights & Benchmarking ✅ **IMPLEMENTED**
```

**Document Organization Benefits:**
- **Professional Presentation**: Clean headers suitable for client-facing documentation
- **Centralized Tracking**: Implementation status visible in one overview location
- **Content Focus**: Scenario content emphasizes business value rather than technical status
- **Executive Appeal**: Professional structure appropriate for senior business audiences

### Content vs. Implementation Separation

**Implementation Overview** (with status):
- Located at document beginning for quick reference
- Shows current state of demo capabilities
- Used for project planning and priority setting
- Updated as scenarios are implemented

**Scenario Content** (clean, no status):
- Professional business narratives and demonstration flows
- Focus on business value and technical capabilities
- Suitable for client presentations and executive briefings
- Timeless content that doesn't require status updates

## Implementation Checklist

When creating or updating demo scenarios:

**Document Structure:**
- [ ] **Role-Based Organization** scenarios grouped by business role
- [ ] **Status Centralized** in "Available Scenarios by Role" section only
- [ ] **Clean Headers** throughout document with no status indicators
- [ ] **Professional Format** suitable for executive and client audiences

**Content Quality:**
- [ ] **Business Context Setup** includes all three required elements
- [ ] **Persona** has full name and title at Simulated Asset Management
- [ ] **Business Challenge** describes specific pain points and inefficiencies
- [ ] **Value Proposition** clearly articulates AI solution benefits
- [ ] **Scene Setting** provides realistic business context and urgency
- [ ] **User Inputs** use natural business language with specific examples
- [ ] **Expected Responses** use simplified format (data types, not specific values)
- [ ] **Presenter Transitions** included between ALL steps in multi-step scenarios
- [ ] **Talking Points** focus on business value and presenter guidance
- [ ] **Key Features** highlight specific Snowflake capabilities
- [ ] **Business Impact Summary** includes qualitative benefits (no specific percentages)
- [ ] **Technical Differentiators** emphasize unique Snowflake advantages

**Technical Validation:**
- [ ] **Agent Alignment** ensures expected behaviors match agent instructions
- [ ] **Demo Coherence** validated through complete flow testing
- [ ] **Query Specificity** ensures predictable and relevant results
- [ ] **UK English** used consistently throughout
- [ ] **Professional Tone** maintained for executive audiences

## Summary

This rule ensures all demo scenarios follow professional standards with role-based organization, centralized status tracking, and compelling business narratives. Follow these guidelines when creating new scenarios or updating existing ones to maintain quality and effectiveness.

**Key Principles:**
- **Role-Based Organization**: Group scenarios by business role for intuitive navigation
- **Status Centralization**: Implementation tracking only in overview section for clean presentation
- **Business First**: Always lead with business value and outcomes over technical features
- **Professional Structure**: Clean headers and content suitable for executive and client audiences
- **Realistic Content**: Use authentic scenarios and professional language throughout
- **Technical Accuracy**: Ensure alignment with actual agent capabilities and data model
- **Presenter Support**: Provide clear talking points and feature highlights for demonstrations
- **Executive Appeal**: Professional format appropriate for senior business stakeholders

**Expected Response Standards:**
- **Simplified Format**: Describe data types returned, not specific values
- **Hybrid Structure**: Bullet summaries with table column descriptions
- **Data Independence**: Documentation remains valid regardless of data generation
- **Flagging Focus**: Describe what gets flagged and why, not specific examples

**Multi-Step Flow Standards:**
- **Presenter Transitions**: REQUIRED between all steps in multi-step scenarios
- **Logical Progression**: Each step builds naturally on the previous
- **Demo Coherence**: Steps reference entities that will actually appear in responses
- **Reasoning Clarity**: Explain why each transition makes sense for the demo narrative

**Documentation Organization Standards:**
- **Clean Headers**: No status indicators in scenario headers throughout document
- **Centralized Tracking**: Status management only in "Available Scenarios by Role" section
- **Professional Presentation**: Document structure suitable for client-facing use
- **Content Focus**: Scenario content emphasizes business value rather than implementation state