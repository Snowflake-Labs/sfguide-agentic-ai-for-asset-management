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
    # print(" Starting AI components build...")
    # print(f"   Scenarios: {', '.join(scenarios)}")
    
    if build_semantic:
        # print("🧠 Building semantic views...")
        try:
            create_semantic_views(session, scenarios)
        except Exception as e:
            print(f"ERROR: CRITICAL FAILURE: Semantic view creation failed: {e}")
            # print("🛑 STOPPING BUILD - Cannot continue without semantic views")
            raise
    
    if build_search:
        # print(" Building Cortex Search services...")
        try:
            create_search_services(session, scenarios)
        except Exception as e:
            print(f"ERROR: CRITICAL FAILURE: Search service creation failed: {e}")
            # print("🛑 STOPPING BUILD - Cannot continue without required search services")
            raise
    
    # Create custom tools (PDF generation, M&A simulation)
    # print("📄 Creating custom tools...")
    try:
        create_pdf_report_stage(session)
        create_simple_pdf_tool(session)
    except Exception as e:
        print(f"ERROR: Warning: PDF tool creation failed: {e}")
        # print("   Continuing build - custom tools are optional for basic functionality")
    
    # Create M&A simulation tool for executive scenario
    if 'executive_copilot' in scenarios:
        try:
            create_ma_simulation_tool(session)
        except Exception as e:
            print(f"ERROR: Warning: M&A simulation tool creation failed: {e}")
    
    # Create Snowflake Intelligence agents
    if build_agents:
        # print("🤖 Creating Snowflake Intelligence agents...")
        try:
            import create_agents
            created, failed = create_agents.create_all_agents(session, scenarios)
            if failed > 0:
                print(f"   ⚠️  WARNING: {failed} agents failed to create")
        except Exception as e:
            print(f"ERROR: Warning: Agent creation failed: {e}")
            # print("   Continuing build - agents can be created manually if needed")
    
    # Validate components
    # print(" Validating AI components...")
    try:
        validate_components(session, build_semantic, build_search)
    except Exception as e:
        print(f"ERROR: CRITICAL FAILURE: AI component validation failed: {e}")
        # print("🛑 STOPPING BUILD - AI components not working properly")
        raise
    
    # print(" AI components build complete")

def create_pdf_report_stage(session: Session):
    """Create internal stage for PDF report files."""
    session.sql(f"""
        CREATE STAGE IF NOT EXISTS {config.DATABASE['name']}.AI.PDF_REPORTS
        DIRECTORY = (ENABLE = TRUE)
        ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    """).collect()

def create_simple_pdf_tool(session: Session):
    """Create simple PDF generation tool as a Python stored procedure."""
    pdf_generator_sql = f"""
CREATE OR REPLACE PROCEDURE {config.DATABASE['name']}.AI.GENERATE_INVESTMENT_COMMITTEE_PDF(
    markdown_content VARCHAR,
    portfolio_name VARCHAR,
    security_ticker VARCHAR
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

def generate_pdf(session: Session, markdown_content: str, portfolio_name: str, security_ticker: str):
    \"\"\"
    Generate PDF report from markdown content provided by the agent.
    
    Args:
        session: Snowpark session
        markdown_content: Complete markdown document from agent analysis
        portfolio_name: Portfolio name for filename
        security_ticker: Security ticker for filename
        
    Returns:
        String with download link to generated PDF
    \"\"\"
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_portfolio = re.sub(r'[^a-zA-Z0-9_]', '_', portfolio_name)[:20]
    safe_ticker = re.sub(r'[^a-zA-Z0-9_]', '_', security_ticker)[:10]
    pdf_filename = f'mandate_compliance_{{safe_portfolio}}_{{safe_ticker}}_{{timestamp}}.pdf'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Convert markdown to HTML
        html_body = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])
        
        # Professional CSS styling for investment reports
        css_style = \"\"\"
            @page {{ size: A4; margin: 2cm; }}
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #2C3E50; }}
            h1 {{ color: #1F4E79; border-bottom: 3px solid #1F4E79; padding-bottom: 10px; }}
            h2 {{ color: #2E75B6; border-left: 4px solid #2E75B6; padding-left: 15px; }}
            h3 {{ color: #3F7CAC; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th {{ background-color: #1F4E79; color: white; padding: 12px; font-weight: bold; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            tr:nth-child(even) {{ background-color: #F8F9FA; }}
            .alert-box {{ background-color: #F8D7DA; border: 1px solid #F5C6CB; padding: 15px; margin: 20px 0; }}
            .recommendation {{ background-color: #D4EDDA; border: 1px solid #C3E6CB; padding: 15px; margin: 20px 0; }}
        \"\"\"
        
        # Snowcrest Asset Management header
        sam_header = \"\"\"
        <div style="text-align: center; background: linear-gradient(135deg, #1F4E79, #2E75B6); color: white; padding: 20px; margin-bottom: 30px; border-radius: 10px;">
            <h1 style="margin: 0; font-size: 28px; color: white; border: none;">🏔️ SNOWCREST ASSET MANAGEMENT</h1>
            <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">Investment Committee Decision Documentation</p>
        </div>
        \"\"\"
        
        # Professional footer
        footer = f\"\"\"
        <div class="footer" style="margin-top: 30px; padding-top: 15px; border-top: 2px solid #1F4E79; font-size: 12px; color: #666;">
            <p><strong>Report Generated:</strong> {{datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}}</p>
            <p><strong>Generated By:</strong> Snowflake Intelligence - Portfolio Co-Pilot</p>
            <p><em>This report demonstrates AI-powered investment decision making with Snowflake Intelligence</em></p>
        </div>
        \"\"\"
        
        # Complete HTML document
        html_content = f\"\"\"
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Snowcrest Asset Management - Investment Committee Report</title>
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
        stage_path = '@SAM_DEMO.CURATED.SAM_REPORTS_STAGE'
        session.file.put(pdf_path, stage_path, overwrite=True, auto_compress=False)
        
        # Generate presigned URL for download
        presigned_url = session.sql(
            f"SELECT GET_PRESIGNED_URL('{{stage_path}}', '{{pdf_filename}}') AS url"
        ).collect()[0]['URL']
        
        # Format response with clickable link
        report_display_name = f"Investment Committee Decision - {{portfolio_name}} - {{security_ticker}}"
        return f"[{{report_display_name}}]({{presigned_url}}) - Professional mandate compliance report generated successfully. The document includes full analysis, data sources, and conversational audit trail for investment committee review."
$$;
    """
    try:
        session.sql(pdf_generator_sql).collect()
    except Exception as e:
        print(f"ERROR: PDF generator creation failed: {e}")

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
    Simulate the financial impact of an acquisition on Snowcrest Asset Management.
    
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
        # print("   ✅ Created M&A simulation tool: MA_SIMULATION_TOOL")
    except Exception as e:
        print(f"ERROR: M&A simulation tool creation failed: {e}")

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
                print("ERROR: SAM_ANALYST_VIEW validation failed - no results returned")
                validation_passed = False
            # else:
                # print("   ✅ SAM_ANALYST_VIEW validated")
                
        except Exception as e:
            print(f"ERROR: SAM_ANALYST_VIEW validation failed: {e}")
            validation_passed = False
    
    if search_built:
        # Validate at least one search service exists
        try:
            services = session.sql(f"""
                SHOW CORTEX SEARCH SERVICES IN {config.DATABASE['name']}.AI
            """).collect()
            
            if len(services) == 0:
                print("ERROR: No Cortex Search services found")
                validation_passed = False
            else:
                # print(f"   ✅ Found {len(services)} Cortex Search service(s)")
                
                # Test first service
                service_name = services[0]['name']
                try:
                    test_result = session.sql(f"""
                        SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                            '{config.DATABASE['name']}.AI.{service_name}',
                            '{{"query": "test", "limit": 1}}'
                        )
                    """).collect()
                    # print(f"   ✅ Search service {service_name} validated")
                except Exception as e:
                    print(f"ERROR: Search service {service_name} validation failed: {e}")
                    validation_passed = False
                    
        except Exception as e:
            print(f"ERROR: Search service validation failed: {e}")
            validation_passed = False
    
    if not validation_passed:
        raise Exception("AI component validation failed")
    
    # print("   ✅ AI components validated successfully")
