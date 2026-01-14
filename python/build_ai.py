# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
AI Components Builder for SAM Demo

This module orchestrates the creation of AI components including:
- Semantic views for Cortex Analyst (via create_semantic_views.py)
- Cortex Search services for document types (via create_cortex_search.py)
- Custom tools (PDF generation)
- Validation and testing of AI components
"""

from snowflake.snowpark import Session
from typing import List
import config
from create_semantic_views import create_semantic_views
from create_cortex_search import create_search_services
from logging_utils import log_error, log_warning

def build_all(session: Session, scenarios: List[str], build_semantic: bool = True, build_search: bool = True, build_agents: bool = True):
    """
    Build AI components for the specified scenarios.
    
    Args:
        session: Active Snowpark session
        scenarios: List of scenario names
        build_semantic: Whether to build semantic views
        build_search: Whether to build search services
        build_agents: Whether to create Snowflake Intelligence agents
    """
    
    if build_semantic:
        try:
            create_semantic_views(session, scenarios)
        except Exception as e:
            log_error(f"CRITICAL: Semantic view creation failed: {e}")
            raise
    
    if build_search:
        try:
            create_search_services(session, scenarios)
        except Exception as e:
            log_error(f"CRITICAL: Search service creation failed: {e}")
            raise
    
    # Create custom tools (PDF generation, M&A simulation)
    try:
        create_pdf_report_stage(session)
        create_pdf_report_tool(session)
    except Exception as e:
        log_warning(f" PDF tool creation failed: {e}")
    
    # Create M&A simulation tool for executive scenario
    if 'executive_copilot' in scenarios:
        try:
            create_ma_simulation_tool(session)
        except Exception as e:
            log_warning(f" M&A simulation tool creation failed: {e}")
    
    # Create Snowflake Intelligence agents
    if build_agents:
        try:
            import create_agents
            created, failed = create_agents.create_all_agents(session, scenarios)
            if failed > 0:
                log_warning(f" {failed} agents failed to create")
        except Exception as e:
            log_warning(f" Agent creation failed: {e}")
    
    # Validate components
    try:
        validate_components(session, build_semantic, build_search)
    except Exception as e:
        log_error(f"CRITICAL: AI component validation failed: {e}")
        raise
    

def create_pdf_report_stage(session: Session):
    """Create internal stage for PDF report files with directory enabled for presigned URLs."""
    session.sql(f"""
        CREATE STAGE IF NOT EXISTS {config.DATABASE['name']}.AI.PDF_REPORTS
        DIRECTORY = (ENABLE = TRUE)
        ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
        COMMENT = 'Stage for generated PDF reports'
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
            <p><strong>Compliance Contact:</strong> compliance@sam-demo.example</p>
            <p><strong>Generated:</strong> {{report_timestamp}}</p>
            \"\"\"
        else:  # external_client
            footer_content = f\"\"\"
            <p><strong>Important:</strong> Past performance does not guarantee future results. Investment involves risk including possible loss of principal.</p>
            <p><strong>Contact:</strong> clientservices@sam-demo.example</p>
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
        
        return f"[{{audience_label}}: {{report_title}}]({{presigned_url}}) - Professional PDF generated successfully with Simulated branding."
$$;
    """
    try:
        session.sql(pdf_generator_sql).collect()
    except Exception as e:
        log_error(f" PDF generator creation failed: {e}")

def create_ma_simulation_tool(session: Session):
    """
    Create M&A simulation tool for executive scenario.
    
    This tool models the financial impact of potential acquisitions using
    firm-specific assumptions for cost synergies and integration costs.
    
    Used by: Executive Copilot for strategic M&A analysis
    Inputs: Target AUM, target revenue, cost synergy percentage
    Outputs: EPS accretion, synergy value, timeline, risk factors
    """
    ma_simulation_sql = f"""
CREATE OR REPLACE FUNCTION {config.DATABASE['name']}.AI.MA_SIMULATION_TOOL(
    target_aum FLOAT,
    target_revenue FLOAT,
    cost_synergy_pct FLOAT DEFAULT 0.20
)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
HANDLER = 'simulate_acquisition'
AS
$$
def simulate_acquisition(target_aum: float, target_revenue: float, cost_synergy_pct: float = 0.20) -> dict:
    \"\"\"
    Simulate the financial impact of an acquisition on Simulated Asset Management.
    
    This model uses SAM's standard acquisition assumptions:
    - Integration costs: $30M one-time (standard for mid-sized deals)
    - Operating margin: 35% (SAM's current margin)
    - Cost synergy realization: 70% in Year 1, 100% by Year 2
    - Revenue synergy: Conservative 2% cross-sell uplift
    - SAM baseline EPS: $2.50 (illustrative)
    - SAM shares outstanding: 50M (illustrative)
    
    Args:
        target_aum: Target company AUM in USD (e.g., 50000000000 for $50B)
        target_revenue: Target company annual revenue in USD
        cost_synergy_pct: Expected cost synergy as decimal (default 0.20 = 20%)
    
    Returns:
        Dict with simulation results including EPS accretion, synergy value, timeline
    \"\"\"
    
    # SAM baseline assumptions (illustrative for demo)
    sam_baseline_eps = 2.50  # Current EPS
    sam_shares_outstanding = 50_000_000  # 50M shares
    sam_current_aum = 12_500_000_000  # $12.5B AUM
    sam_operating_margin = 0.35  # 35% operating margin
    
    # Integration assumptions
    integration_cost_one_time = 30_000_000  # $30M one-time
    year1_synergy_realization = 0.70  # 70% of synergies realized in Year 1
    revenue_synergy_pct = 0.02  # 2% cross-sell uplift
    
    # Calculate target operating income
    target_operating_income = target_revenue * sam_operating_margin
    
    # Calculate synergies
    cost_synergies_full = target_revenue * cost_synergy_pct
    cost_synergies_year1 = cost_synergies_full * year1_synergy_realization
    revenue_synergies = target_revenue * revenue_synergy_pct
    
    # Year 1 contribution (after integration costs)
    year1_contribution = (
        target_operating_income +
        cost_synergies_year1 +
        (revenue_synergies * sam_operating_margin) -
        integration_cost_one_time
    )
    
    # Year 2 contribution (full synergies, no integration costs)
    year2_contribution = (
        target_operating_income +
        cost_synergies_full +
        (revenue_synergies * sam_operating_margin)
    )
    
    # EPS impact (assuming cash deal, no share dilution)
    eps_impact_year1 = year1_contribution / sam_shares_outstanding
    eps_impact_year2 = year2_contribution / sam_shares_outstanding
    
    # EPS accretion percentage
    eps_accretion_year1_pct = (eps_impact_year1 / sam_baseline_eps) * 100
    eps_accretion_year2_pct = (eps_impact_year2 / sam_baseline_eps) * 100
    
    # Combined AUM
    combined_aum = sam_current_aum + target_aum
    aum_growth_pct = (target_aum / sam_current_aum) * 100
    
    # Risk factors based on deal size
    risk_level = "Low" if target_aum < 5_000_000_000 else "Medium" if target_aum < 20_000_000_000 else "High"
    
    return {{
        "simulation_summary": {{
            "target_aum_billions": round(target_aum / 1_000_000_000, 1),
            "target_revenue_millions": round(target_revenue / 1_000_000, 1),
            "cost_synergy_assumption_pct": cost_synergy_pct * 100
        }},
        "year1_projection": {{
            "eps_accretion_pct": round(eps_accretion_year1_pct, 1),
            "eps_impact_usd": round(eps_impact_year1, 2),
            "synergies_realized_millions": round(cost_synergies_year1 / 1_000_000, 1),
            "integration_costs_millions": round(integration_cost_one_time / 1_000_000, 1),
            "net_contribution_millions": round(year1_contribution / 1_000_000, 1)
        }},
        "year2_projection": {{
            "eps_accretion_pct": round(eps_accretion_year2_pct, 1),
            "eps_impact_usd": round(eps_impact_year2, 2),
            "full_synergies_millions": round(cost_synergies_full / 1_000_000, 1),
            "net_contribution_millions": round(year2_contribution / 1_000_000, 1)
        }},
        "strategic_impact": {{
            "combined_aum_billions": round(combined_aum / 1_000_000_000, 1),
            "aum_growth_pct": round(aum_growth_pct, 1),
            "revenue_synergies_millions": round(revenue_synergies / 1_000_000, 1)
        }},
        "risk_assessment": {{
            "integration_risk_level": risk_level,
            "key_risks": [
                "Client retention during transition",
                "Key personnel retention",
                "System integration complexity",
                "Regulatory approval timeline"
            ],
            "timeline_months": 12 if risk_level == "Low" else 18 if risk_level == "Medium" else 24
        }},
        "recommendation": f"Based on {{round(eps_accretion_year1_pct, 1)}}% Year 1 EPS accretion, this acquisition appears financially attractive. Recommend detailed due diligence focusing on client retention and integration planning."
    }}
$$;
    """
    try:
        session.sql(ma_simulation_sql).collect()
    except Exception as e:
        log_error(f" M&A simulation tool creation failed: {e}")

def validate_components(session: Session, semantic_built: bool, search_built: bool):
    """Validate that AI components are working correctly."""
    
    validation_passed = True
    
    if semantic_built:
        try:
            # Test SAM_ANALYST_VIEW
            result = session.sql(f"""
                SELECT * FROM SEMANTIC_VIEW(
                    {config.DATABASE['name']}.AI.SAM_ANALYST_VIEW
                    METRICS TOTAL_MARKET_VALUE
                    DIMENSIONS PORTFOLIONAME
                ) LIMIT 1
            """).collect()
            
            if len(result) == 0:
                log_error(" SAM_ANALYST_VIEW validation failed - no results returned")
                validation_passed = False
            # else:
                
        except Exception as e:
            log_error(f" SAM_ANALYST_VIEW validation failed: {e}")
            validation_passed = False
    
    if search_built:
        # Validate at least one search service exists
        try:
            services = session.sql(f"""
                SHOW CORTEX SEARCH SERVICES IN {config.DATABASE['name']}.AI
            """).collect()
            
            if len(services) == 0:
                log_error(" No Cortex Search services found")
                validation_passed = False
            else:
                
                # Test first service
                service_name = services[0]['name']
                try:
                    test_result = session.sql(f"""
                        SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                            '{config.DATABASE['name']}.AI.{service_name}',
                            '{{"query": "test", "limit": 1}}'
                        )
                    """).collect()
                except Exception as e:
                    log_error(f" Search service {service_name} validation failed: {e}")
                    validation_passed = False
                    
        except Exception as e:
            log_error(f" Search service validation failed: {e}")
            validation_passed = False
    
    if not validation_passed:
        raise Exception("AI component validation failed")
    
