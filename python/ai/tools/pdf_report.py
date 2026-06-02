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
PDF Report Tool for SAM Demo

Creates professional branded PDF reports with:
- Embedded SVG logo for Simulated Asset Management
- Audience-based headers/footers (internal, external_client, external_regulatory)
- Demo disclaimer in all footers
- Professional styling with SAM brand colors
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_error


def create_pdf_report_stage(session: Session):
    """Create internal stage for PDF report files."""
    session.sql(f"""
        CREATE STAGE IF NOT EXISTS {config.DATABASE['name']}.AI.PDF_REPORTS
        ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    """).collect()


def create_pdf_report_tool(session: Session):
    """
    Create generic PDF report generation tool as a Python stored procedure.
    
    This tool generates professional branded PDF reports with:
    - Embedded SVG logo for Simulated Asset Management
    - Audience-based headers/footers (internal, external_client, external_regulatory)
    - Demo disclaimer in all footers
    - Professional styling with SAM brand colors
    
    Used by: Multiple agents (Portfolio Copilot, Sales Advisor, Executive Copilot, 
             Research Copilot, Compliance Advisor, ESG Guardian, Middle Office Copilot)
    """
    pdf_generator_sql = f"""
CREATE OR REPLACE PROCEDURE {config.DATABASE['name']}.AI.GENERATE_PDF_REPORT(
    markdown_content VARCHAR,
    report_title VARCHAR,
    document_audience VARCHAR
)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python','markdown','weasyprint')
HANDLER = 'generate_pdf'
AS
$$
from snowflake.snowpark import Session
from datetime import datetime
import re
import markdown
import tempfile
import os
import base64

def generate_pdf(session: Session, markdown_content: str, report_title: str, document_audience: str):
    \"\"\"
    Generate professional branded PDF report from markdown content.
    
    Args:
        session: Snowpark session
        markdown_content: Complete markdown document from agent (using retrieved templates)
        report_title: Title for the document header (e.g., "Q4 2024 Client Review")
        document_audience: One of "internal", "external_client", or "external_regulatory"
        
    Returns:
        String with download link to generated PDF
    \"\"\"
    # Validate audience
    valid_audiences = ['internal', 'external_client', 'external_regulatory']
    if document_audience not in valid_audiences:
        document_audience = 'internal'  # Default to internal if invalid
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_title = re.sub(r'[^a-zA-Z0-9_]', '_', report_title)[:30]
    pdf_filename = f'{{document_audience}}_{{safe_title}}_{{timestamp}}.pdf'
    
    # Embedded SVG logo (mountain peak design with SAM brand colors)
    svg_logo = '''
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 50" width="120" height="50">
        <!-- Mountain peaks -->
        <polygon points="30,45 45,15 60,45" fill="#1F4E79"/>
        <polygon points="50,45 70,8 90,45" fill="#2E75B6"/>
        <polygon points="15,45 25,30 35,45" fill="#3F7CAC" opacity="0.8"/>
        <!-- Snow cap on main peak -->
        <polygon points="70,8 65,18 75,18" fill="white"/>
        <!-- Base line -->
        <line x1="10" y1="45" x2="95" y2="45" stroke="#1F4E79" stroke-width="2"/>
    </svg>
    '''
    
    # Encode SVG for embedding
    svg_base64 = base64.b64encode(svg_logo.encode('utf-8')).decode('utf-8')
    logo_src = f'data:image/svg+xml;base64,{{svg_base64}}'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Convert markdown to HTML
        html_body = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])
        
        # Professional CSS styling for investment reports
        css_style = \"\"\"
            @page {{ size: A4; margin: 2cm; }}
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #2C3E50; }}
            h1 {{ color: #1F4E79; border-bottom: 3px solid #1F4E79; padding-bottom: 10px; }}
            h2 {{ color: #2E75B6; border-left: 4px solid #2E75B6; padding-left: 15px; margin-top: 25px; }}
            h3 {{ color: #3F7CAC; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th {{ background-color: #1F4E79; color: white; padding: 12px; font-weight: bold; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            tr:nth-child(even) {{ background-color: #F8F9FA; }}
            .header {{ display: flex; align-items: center; border-bottom: 3px solid #1F4E79; padding-bottom: 15px; margin-bottom: 25px; }}
            .header-logo {{ margin-right: 20px; }}
            .header-text {{ flex: 1; }}
            .header-title {{ margin: 0; color: #1F4E79; font-size: 24px; }}
            .header-subtitle {{ margin: 5px 0 0 0; color: #666; font-size: 14px; }}
            .footer {{ margin-top: 30px; padding-top: 15px; border-top: 2px solid #1F4E79; font-size: 11px; color: #666; }}
            .demo-disclaimer {{ background: #FFF3CD; border: 1px solid #FFE69C; padding: 12px; margin-top: 15px; font-size: 10px; color: #664D03; border-radius: 4px; }}
            .internal-badge {{ background: #E7F3FF; color: #1F4E79; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; }}
            .regulatory-badge {{ background: #F8D7DA; color: #721C24; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; }}
        \"\"\"
        
        # Audience-specific header subtitle
        if document_audience == 'internal':
            header_subtitle = f'<span class="internal-badge">INTERNAL DOCUMENT</span> | {{report_title}}'
        elif document_audience == 'external_regulatory':
            header_subtitle = f'<span class="regulatory-badge">FCA REGULATED</span> | {{report_title}}'
        else:  # external_client
            header_subtitle = report_title
        
        # Build header with logo
        sam_header = f\"\"\"
        <div class="header">
            <div class="header-logo">
                <img src="{{logo_src}}" alt="Simulated Asset Management" style="height: 50px;"/>
            </div>
            <div class="header-text">
                <h1 class="header-title" style="border: none; padding: 0;">SIMULATED ASSET MANAGEMENT</h1>
                <p class="header-subtitle">{{header_subtitle}}</p>
            </div>
        </div>
        \"\"\"
        
        # Audience-specific footer content
        report_timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')
        
        if document_audience == 'internal':
            footer_content = f\"\"\"
            <p><strong>Classification:</strong> Internal Use Only - Not for Distribution</p>
            <p><strong>Generated:</strong> {{report_timestamp}}</p>
            <p><strong>Generated By:</strong> Snowflake Intelligence</p>
            \"\"\"
        elif document_audience == 'external_regulatory':
            footer_content = f\"\"\"
            <p><strong>Regulatory Status:</strong> Prepared in accordance with FCA reporting requirements</p>
            <p><strong>Compliance Contact:</strong> compliance@simulated-am.demo</p>
            <p><strong>Generated:</strong> {{report_timestamp}}</p>
            \"\"\"
        else:  # external_client
            footer_content = f\"\"\"
            <p><strong>Important:</strong> Past performance does not guarantee future results. Investment involves risk including possible loss of principal.</p>
            <p><strong>Contact:</strong> clientservices@simulated-am.demo</p>
            <p><strong>Generated:</strong> {{report_timestamp}}</p>
            \"\"\"
        
        # Demo disclaimer (all audiences)
        demo_disclaimer = \"\"\"
        <div class="demo-disclaimer">
            <strong>DEMONSTRATION ONLY:</strong> This document was generated by Snowflake Intelligence 
            for demonstration purposes. It does not represent real investment advice, actual portfolio data, 
            or genuine recommendations. Simulated Asset Management is a fictional entity created for this demo.
        </div>
        \"\"\"
        
        # Complete footer
        footer = f\"\"\"
        <div class="footer">
            {{footer_content}}
            {{demo_disclaimer}}
        </div>
        \"\"\"
        
        # Complete HTML document
        html_content = f\"\"\"
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Simulated Asset Management - {{report_title}}</title>
            <style>{{css_style}}</style>
        </head>
        <body>
            {{sam_header}}
            {{html_body}}
            {{footer}}
        </body>
        </html>
        \"\"\"
        
        # Create HTML file
        html_path = os.path.join(tmpdir, 'report.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Convert HTML to PDF
        import weasyprint
        pdf_path = os.path.join(tmpdir, pdf_filename)
        weasyprint.HTML(filename=html_path).write_pdf(pdf_path)
        
        # Upload to stage
        stage_path = '@{config.DATABASE["name"]}.{config.DATABASE["schemas"]["ai"]}.PDF_REPORTS'
        session.file.put(pdf_path, stage_path, overwrite=True, auto_compress=False)
        
        # Generate presigned URL for download
        presigned_url = session.sql(
            f"SELECT GET_PRESIGNED_URL('{{stage_path}}', '{{pdf_filename}}') AS url"
        ).collect()[0]['URL']
        
        # Format response based on audience
        audience_labels = {{
            'internal': 'Internal Report',
            'external_client': 'Client Report', 
            'external_regulatory': 'Regulatory Report'
        }}
        audience_label = audience_labels.get(document_audience, 'Report')
        
        return f"[{{audience_label}}: {{report_title}}]({{presigned_url}}) - Professional PDF generated successfully with SAM branding."
$$;
    """
    try:
        session.sql(pdf_generator_sql).collect()
    except Exception as e:
        log_error(f" PDF generator creation failed: {e}")
