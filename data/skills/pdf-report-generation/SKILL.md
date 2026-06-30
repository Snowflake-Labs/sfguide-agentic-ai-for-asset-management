---
name: pdf-report-generation
description: Use this skill when the user explicitly requests a PDF document, file export, or downloadable report. Trigger on phrases like "generate PDF", "create PDF", "export as PDF", or "save as document". Do NOT trigger for general requests like "report", "summary", or "document" alone — those should produce markdown text output.
---

# PDF Report Generation

## When to Activate

Trigger ONLY when the user explicitly says one of:
- "generate PDF", "create PDF", "PDF document", "PDF report", "export as PDF", "save as document"

Do NOT trigger for: "document", "report", "summary", "briefing", or "memo" alone. These should produce markdown text output.

## Workflow

1. Prepare markdown content with proper structure:
   - Use `##` for main sections, `###` for subsections
   - Use markdown tables for data presentation
   - Include clear section headers
   - Add source citations throughout

2. Determine audience:
   - `external_client` — Client-facing reports (simplified language, no internal references)
   - `internal` — Investment committee memos, research reports (full detail, technical language)

3. Call `pdf_generator` with:
   - `markdown_content`: Complete formatted markdown
   - `report_title`: Descriptive title (e.g., "Q4 2024 Quarterly Client Report", "NVIDIA Investment Memo")
   - `document_audience`: One of `external_client` or `internal`

4. After calling pdf_generator, ALWAYS include the returned download link verbatim in your response so the user can click it to download the PDF.

## Error Handling

If PDF generation fails:
- Present the full content as formatted markdown inline
- Note: "PDF generation encountered an issue. Here is the full content in text format."
- Do not retry automatically

## Formatting Best Practices

- Tables: Use for performance summaries, financial data, scenario analysis, risk matrices
- Headers: Maximum 3 levels deep (##, ###, ####)
- Lists: Use bullet points for qualitative analysis, numbered lists for sequential steps
- Emphasis: Bold for key metrics and findings, italic for caveats and limitations

## Stopping Points

- This is a utility skill invoked at the end of a workflow. Stopping points are inherited from the calling workflow.
- If the user has not explicitly confirmed their request for PDF output, confirm before calling pdf_generator.

## Output

A downloadable PDF link returned by `pdf_generator`, included verbatim in the response.
