# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Created by Mats Stellwall, Snowflake, and Snowflake CoCo

"""
PDF Exporter Module for SAM Demo Unstructured Documents

Generates professional-looking PDF files from hydrated markdown documents
using ReportLab. Supports internal (SAM) and external (broker/company/NGO)
branding with logos and headers/footers.

Usage:
    from pdf_exporter import export_document_to_pdf
    
    export_document_to_pdf(
        markdown_content='# Report Title\n\nBody text...',
        doc_type='broker_research',
        context={'BROKER_NAME': 'Ashfield Partners', 'TICKER': 'AAPL'},
        output_dir='/path/to/output'
    )
"""

import os
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas

import config
from utils.logging import log_detail, log_warning

# =============================================================================
# BRAND COLORS
# =============================================================================

# SAM (Simulated Asset Management) brand colors
SAM_PRIMARY = HexColor('#1F4E79')      # Deep blue
SAM_SECONDARY = HexColor('#2E75B6')    # Medium blue
SAM_ACCENT = HexColor('#3F7CAC')       # Light blue
SAM_TEXT = HexColor('#2C3E50')         # Dark grey

# External document colors (neutral professional)
EXT_PRIMARY = HexColor('#333333')      # Dark grey
EXT_SECONDARY = HexColor('#666666')    # Medium grey
EXT_ACCENT = HexColor('#4A90D9')       # Professional blue


# =============================================================================
# CUSTOM FLOWABLE FOR LOGO
# =============================================================================

class LogoFlowable(Flowable):
    """
    Custom flowable that draws a simple text-based logo.
    Used when image logos are not available.
    """
    
    def __init__(self, text: str, width: float = 50*mm, height: float = 15*mm,
                 primary_color=SAM_PRIMARY, is_internal: bool = True):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        self.height = height
        self.primary_color = primary_color
        self.is_internal = is_internal
    
    def draw(self):
        """Draw the logo."""
        c = self.canv
        
        if self.is_internal:
            # SAM logo: mountain peak icon + text
            # Draw stylized mountain peaks
            c.setFillColor(SAM_PRIMARY)
            c.setStrokeColor(SAM_PRIMARY)
            
            # Main peak
            peak_path = c.beginPath()
            peak_path.moveTo(5*mm, 0)
            peak_path.lineTo(12*mm, 12*mm)
            peak_path.lineTo(19*mm, 0)
            peak_path.close()
            c.drawPath(peak_path, fill=1, stroke=0)
            
            # Secondary peak
            c.setFillColor(SAM_SECONDARY)
            peak_path2 = c.beginPath()
            peak_path2.moveTo(12*mm, 0)
            peak_path2.lineTo(17*mm, 8*mm)
            peak_path2.lineTo(22*mm, 0)
            peak_path2.close()
            c.drawPath(peak_path2, fill=1, stroke=0)
            
            # Snow cap
            c.setFillColor(white)
            cap_path = c.beginPath()
            cap_path.moveTo(12*mm, 12*mm)
            cap_path.lineTo(10*mm, 9*mm)
            cap_path.lineTo(14*mm, 9*mm)
            cap_path.close()
            c.drawPath(cap_path, fill=1, stroke=0)
            
            # Text: SAM
            c.setFillColor(SAM_PRIMARY)
            c.setFont('Helvetica-Bold', 10)
            c.drawString(25*mm, 6*mm, 'SIMULATED')
            c.setFont('Helvetica', 7)
            c.drawString(25*mm, 2*mm, 'Asset Management')
        else:
            # External logo: simple lettermark box
            c.setFillColor(self.primary_color)
            c.roundRect(0, 0, 12*mm, 12*mm, 2*mm, fill=1, stroke=0)
            
            # Lettermark (first letter or initials)
            initials = self._get_initials(self.text)
            c.setFillColor(white)
            c.setFont('Helvetica-Bold', 10)
            c.drawCentredString(6*mm, 4*mm, initials)
            
            # Organization name
            c.setFillColor(EXT_PRIMARY)
            c.setFont('Helvetica-Bold', 9)
            # Truncate long names
            display_name = self.text[:25] + '...' if len(self.text) > 25 else self.text
            c.drawString(15*mm, 6*mm, display_name)
    
    def _get_initials(self, text: str) -> str:
        """Extract initials from organization name."""
        words = text.split()
        if len(words) >= 2:
            return (words[0][0] + words[1][0]).upper()
        elif words:
            return words[0][:2].upper()
        return 'XX'


# =============================================================================
# PAGE TEMPLATES
# =============================================================================

def make_internal_header_footer(canvas: canvas.Canvas, doc, title: str):
    """Draw SAM-branded header and footer for internal documents."""
    canvas.saveState()
    
    width, height = A4
    
    # Header
    # Blue bar at top
    canvas.setFillColor(SAM_PRIMARY)
    canvas.rect(0, height - 20*mm, width, 20*mm, fill=1, stroke=0)
    
    # SAM text in header
    canvas.setFillColor(white)
    canvas.setFont('Helvetica-Bold', 11)
    canvas.drawString(15*mm, height - 12*mm, 'SIMULATED ASSET MANAGEMENT')
    
    # Document title on right
    canvas.setFont('Helvetica', 9)
    canvas.drawRightString(width - 15*mm, height - 12*mm, title[:50])
    
    # INTERNAL badge
    canvas.setFillColor(HexColor('#E7F3FF'))
    canvas.roundRect(15*mm, height - 18*mm, 20*mm, 5*mm, 1*mm, fill=1, stroke=0)
    canvas.setFillColor(SAM_PRIMARY)
    canvas.setFont('Helvetica-Bold', 6)
    canvas.drawString(17*mm, height - 17*mm, 'INTERNAL')
    
    # Footer
    canvas.setStrokeColor(SAM_PRIMARY)
    canvas.setLineWidth(1)
    canvas.line(15*mm, 15*mm, width - 15*mm, 15*mm)
    
    canvas.setFillColor(SAM_TEXT)
    canvas.setFont('Helvetica', 7)
    canvas.drawString(15*mm, 10*mm, 'Confidential - Internal Use Only')
    canvas.drawCentredString(width/2, 10*mm, f'Generated {datetime.now().strftime("%d %B %Y")}')
    canvas.drawRightString(width - 15*mm, 10*mm, f'Page {doc.page}')
    
    canvas.restoreState()


def make_external_header_footer(canvas: canvas.Canvas, doc, title: str, org_name: str):
    """Draw external-branded header and footer."""
    canvas.saveState()
    
    width, height = A4
    
    # Header - light grey bar
    canvas.setFillColor(HexColor('#F5F5F5'))
    canvas.rect(0, height - 18*mm, width, 18*mm, fill=1, stroke=0)
    
    # Organization name
    canvas.setFillColor(EXT_PRIMARY)
    canvas.setFont('Helvetica-Bold', 11)
    display_org = org_name[:40] if len(org_name) > 40 else org_name
    canvas.drawString(15*mm, height - 12*mm, display_org)
    
    # Document type on right
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(EXT_SECONDARY)
    canvas.drawRightString(width - 15*mm, height - 12*mm, title[:40])
    
    # Footer
    canvas.setStrokeColor(EXT_SECONDARY)
    canvas.setLineWidth(0.5)
    canvas.line(15*mm, 15*mm, width - 15*mm, 15*mm)
    
    canvas.setFillColor(EXT_SECONDARY)
    canvas.setFont('Helvetica', 7)
    canvas.drawString(15*mm, 10*mm, org_name[:30])
    canvas.drawCentredString(width/2, 10*mm, f'{datetime.now().strftime("%d %B %Y")}')
    canvas.drawRightString(width - 15*mm, 10*mm, f'Page {doc.page}')
    
    canvas.restoreState()


# =============================================================================
# MARKDOWN TO FLOWABLES CONVERSION
# =============================================================================

def get_pdf_styles() -> Dict[str, ParagraphStyle]:
    """Get custom paragraph styles for PDF generation."""
    base_styles = getSampleStyleSheet()
    
    styles = {
        'Title': ParagraphStyle(
            'Title',
            parent=base_styles['Title'],
            fontSize=16,
            textColor=SAM_PRIMARY,
            spaceAfter=12,
            leading=20
        ),
        'Heading1': ParagraphStyle(
            'Heading1',
            parent=base_styles['Heading1'],
            fontSize=14,
            textColor=SAM_PRIMARY,
            spaceBefore=14,
            spaceAfter=8,
            leading=18,
            borderPadding=(0, 0, 0, 4),
            borderWidth=0,
            borderColor=SAM_PRIMARY
        ),
        'Heading2': ParagraphStyle(
            'Heading2',
            parent=base_styles['Heading2'],
            fontSize=12,
            textColor=SAM_SECONDARY,
            spaceBefore=10,
            spaceAfter=6,
            leading=15
        ),
        'Heading3': ParagraphStyle(
            'Heading3',
            parent=base_styles['Heading3'],
            fontSize=10,
            textColor=SAM_ACCENT,
            spaceBefore=8,
            spaceAfter=4,
            leading=13
        ),
        'BodyText': ParagraphStyle(
            'BodyText',
            parent=base_styles['BodyText'],
            fontSize=9,
            textColor=SAM_TEXT,
            spaceBefore=2,
            spaceAfter=6,
            leading=12
        ),
        'BulletItem': ParagraphStyle(
            'BulletItem',
            parent=base_styles['BodyText'],
            fontSize=9,
            textColor=SAM_TEXT,
            leftIndent=10*mm,
            bulletIndent=5*mm,
            spaceBefore=1,
            spaceAfter=2,
            leading=11
        ),
        'TableHeader': ParagraphStyle(
            'TableHeader',
            parent=base_styles['BodyText'],
            fontSize=8,
            textColor=white,
            alignment=TA_LEFT
        ),
        'TableCell': ParagraphStyle(
            'TableCell',
            parent=base_styles['BodyText'],
            fontSize=8,
            textColor=SAM_TEXT,
            alignment=TA_LEFT
        ),
    }
    
    return styles


def markdown_to_flowables(markdown_text: str, styles: Dict[str, ParagraphStyle]) -> List:
    """
    Convert markdown text to ReportLab flowables.
    
    Handles:
    - Headings (# ## ###)
    - Paragraphs
    - Bullet lists (- or *)
    - Bold (**text**) and italic (*text*)
    - Basic tables (| col | col |)
    
    Args:
        markdown_text: Hydrated markdown content
        styles: Paragraph styles dict
    
    Returns:
        List of ReportLab flowables
    """
    flowables = []
    lines = markdown_text.split('\n')
    
    current_paragraph = []
    in_table = False
    table_rows = []
    in_list = False
    list_items = []
    
    def flush_paragraph():
        nonlocal current_paragraph
        if current_paragraph:
            text = ' '.join(current_paragraph).strip()
            if text:
                # Convert markdown bold/italic to ReportLab markup
                text = convert_inline_formatting(text)
                flowables.append(Paragraph(text, styles['BodyText']))
            current_paragraph = []
    
    def flush_list():
        nonlocal in_list, list_items
        if list_items:
            for item in list_items:
                text = convert_inline_formatting(item)
                flowables.append(Paragraph(f'• {text}', styles['BulletItem']))
            list_items = []
        in_list = False
    
    def flush_table():
        nonlocal in_table, table_rows
        if table_rows and len(table_rows) > 0:
            # Build table
            table = build_table(table_rows, styles)
            if table:
                flowables.append(Spacer(1, 4*mm))
                flowables.append(table)
                flowables.append(Spacer(1, 4*mm))
            table_rows = []
        in_table = False
    
    for line in lines:
        stripped = line.strip()
        
        # Empty line - flush current context
        if not stripped:
            flush_paragraph()
            flush_list()
            if in_table and table_rows:
                flush_table()
            continue
        
        # Heading
        if stripped.startswith('#'):
            flush_paragraph()
            flush_list()
            flush_table()
            
            level = len(stripped) - len(stripped.lstrip('#'))
            heading_text = stripped.lstrip('#').strip()
            heading_text = convert_inline_formatting(heading_text)
            
            if level == 1:
                flowables.append(Paragraph(heading_text, styles['Title']))
            elif level == 2:
                flowables.append(Paragraph(heading_text, styles['Heading1']))
            elif level == 3:
                flowables.append(Paragraph(heading_text, styles['Heading2']))
            else:
                flowables.append(Paragraph(heading_text, styles['Heading3']))
            continue
        
        # Table row
        if stripped.startswith('|') and stripped.endswith('|'):
            flush_paragraph()
            flush_list()
            
            # Skip separator rows (|---|---|)
            if re.match(r'^\|[\s\-:|]+\|$', stripped):
                continue
            
            in_table = True
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            table_rows.append(cells)
            continue
        
        # If we were in a table and now we're not, flush it
        if in_table:
            flush_table()
        
        # Bullet list item
        if stripped.startswith('- ') or stripped.startswith('* '):
            flush_paragraph()
            in_list = True
            list_items.append(stripped[2:])
            continue
        
        # If we were in a list and now we're not, flush it
        if in_list and not (stripped.startswith('- ') or stripped.startswith('* ')):
            flush_list()
        
        # Regular paragraph text
        current_paragraph.append(stripped)
    
    # Flush remaining content
    flush_paragraph()
    flush_list()
    flush_table()
    
    return flowables


def convert_inline_formatting(text: str) -> str:
    """Convert markdown inline formatting to ReportLab XML tags."""
    # Bold: **text** -> <b>text</b>
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    # Italic: *text* -> <i>text</i> (but not **text**)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', text)
    # Escape any remaining problematic characters
    text = text.replace('&', '&amp;').replace('<b>', '\x00B\x00').replace('</b>', '\x00/B\x00')
    text = text.replace('<i>', '\x00I\x00').replace('</i>', '\x00/I\x00')
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('\x00B\x00', '<b>').replace('\x00/B\x00', '</b>')
    text = text.replace('\x00I\x00', '<i>').replace('\x00/I\x00', '</i>')
    return text


def build_table(rows: List[List[str]], styles: Dict[str, ParagraphStyle]):
    """Build a ReportLab Table from row data."""
    if not rows:
        return None
    
    # Convert cells to Paragraphs
    data = []
    for i, row in enumerate(rows):
        if i == 0:
            # Header row
            data.append([Paragraph(convert_inline_formatting(cell), styles['TableHeader']) for cell in row])
        else:
            data.append([Paragraph(convert_inline_formatting(cell), styles['TableCell']) for cell in row])
    
    # Calculate column widths
    num_cols = max(len(row) for row in rows)
    available_width = 170*mm  # A4 minus margins
    col_width = available_width / num_cols
    col_widths = [col_width] * num_cols
    
    table = Table(data, colWidths=col_widths)
    
    # Style the table
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), SAM_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('TEXTCOLOR', (0, 1), (-1, -1), SAM_TEXT),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#DDDDDD')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F8F9FA')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]
    
    table.setStyle(TableStyle(style_commands))
    return table


# =============================================================================
# MAIN EXPORT FUNCTION
# =============================================================================

def export_document_to_pdf(
    markdown_content: str,
    doc_type: str,
    context: Dict[str, Any],
    output_dir: str,
    document_id: str
) -> Optional[str]:
    """
    Export a hydrated document to PDF.
    
    Args:
        markdown_content: Rendered markdown content
        doc_type: Document type (e.g., 'broker_research', 'internal_research')
        context: Hydration context with entity data
        output_dir: Root output directory
        document_id: Unique document identifier
    
    Returns:
        Path to generated PDF file, or None if export failed
    """
    # Check if this doc_type should be exported
    audience = config.PDF_DOC_AUDIENCE.get(doc_type, 'internal')
    if audience == 'skip':
        return None
    
    is_internal = (audience == 'internal')
    
    # Extract document title from first heading or use fallback
    title_match = re.search(r'^#\s+(.+)$', markdown_content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
        # Clean up any remaining placeholders
        title = re.sub(r'\{\{[^}]+\}\}', '', title).strip()
    else:
        title = context.get('DOCUMENT_TITLE', f'{doc_type} Document')
    
    # Get organization name for external docs
    if is_internal:
        org_name = 'Simulated Asset Management'
    else:
        # Try to get source organization from context
        org_name = (
            context.get('BROKER_NAME') or
            context.get('NGO_NAME') or
            context.get('COMPANY_NAME') or
            context.get('ISSUER_NAME') or
            'External Source'
        )
    
    # Create output directory structure
    doc_type_dir = os.path.join(output_dir, doc_type)
    os.makedirs(doc_type_dir, exist_ok=True)
    
    # Generate safe filename with publish date suffix for pipeline extraction
    safe_title = re.sub(r'[^\w\s-]', '', title)[:40].strip().replace(' ', '_')
    safe_id = re.sub(r'[^\w-]', '', str(document_id))[:30]
    date_suffix = ''
    raw_date = context.get('PUBLISH_DATE', '')
    if raw_date:
        try:
            parsed_date = datetime.strptime(raw_date, '%d %B %Y')
            date_suffix = f'_{parsed_date.strftime("%Y%m%d")}'
        except (ValueError, TypeError):
            pass
    filename = f'{safe_title}_{safe_id}{date_suffix}.pdf'
    filepath = os.path.join(doc_type_dir, filename)
    
    try:
        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=15*mm,
            rightMargin=15*mm,
            topMargin=25*mm,
            bottomMargin=20*mm
        )
        
        # Get styles and convert markdown
        styles = get_pdf_styles()
        flowables = markdown_to_flowables(markdown_content, styles)
        
        # Add logo at the start
        logo = LogoFlowable(
            text=org_name,
            is_internal=is_internal,
            primary_color=SAM_PRIMARY if is_internal else EXT_ACCENT
        )
        flowables.insert(0, logo)
        flowables.insert(1, Spacer(1, 8*mm))
        
        # Build document with custom header/footer
        def on_page(canvas_obj, doc_obj):
            if is_internal:
                make_internal_header_footer(canvas_obj, doc_obj, title)
            else:
                make_external_header_footer(canvas_obj, doc_obj, title, org_name)
        
        doc.build(flowables, onFirstPage=on_page, onLaterPages=on_page)
        
        return filepath
    
    except Exception as e:
        log_warning(f'  PDF export failed for {doc_type}/{document_id}: {e}')
        return None


def get_output_directory() -> str:
    """
    Get the configured PDF output directory.
    Creates it if it doesn't exist.
    
    Returns:
        Absolute path to output directory
    """
    output_dir = config.UNSTRUCTURED_PDF_OUTPUT_DIR
    
    # If relative path, make it relative to project root
    if not os.path.isabs(output_dir):
        # Project root is parent of python/ directory (core/ is inside python/)
        python_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(python_dir)
        output_dir = os.path.join(project_root, output_dir)
    
    os.makedirs(output_dir, exist_ok=True)
    return output_dir
