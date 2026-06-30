---
name: client-review-preparation
description: Use this skill when the user asks to "prepare for a client meeting", needs "meeting prep", or wants a "client review" briefing. Also use when the user mentions a client by name and wants talking points, relationship context, or portfolio performance summary for that client.
---

# Client Review Preparation

## When to Activate

Trigger when user asks for: "prepare for client meeting", "client review preparation", "meeting prep for [client]", "client briefing for [name]"

## 4-Step Workflow

1. **Client relationship**: Query `client_analyzer` for "Flow history and AUM for [client]"
   - Extract: total AUM, flow history (12 months), relationship tenure, client type
2. **Portfolio performance**: Query `quantitative_analyzer` for "Latest performance for client portfolios"
   - Extract: returns, benchmark comparison, key holdings
3. **Philosophy content**: Search `search_internal_docs` for "Investment philosophy materials" (filter DOCUMENT_TYPE = 'philosophy_docs')
   - Extract: key positioning statements, strategic alignment context
4. **Synthesise**: Combine into meeting prep document:
   - Client context (AUM, tenure, flow trends)
   - Portfolio performance highlights
   - Key talking points (what to emphasise, what to address proactively)
   - Supporting philosophy/strategy materials

## Error Handling

- **Client not found**: "No flow data found for this client. Please verify the exact client name. I can list all institutional clients if helpful."
- **Missing philosophy docs**: Fall back to general strategy description from portfolio performance data

## Output Format

Structure as a concise meeting prep brief:
- **Client Overview**: One paragraph with key relationship metrics
- **Performance Dashboard**: Summary table
- **Key Talking Points**: 3-5 bullet points
- **Potential Questions & Answers**: Anticipate likely client questions based on recent performance

## Stopping Points

- After Step 2 (performance data gathered): confirm the correct client and portfolios with user
- After Step 4 (brief drafted): present for review before the meeting
