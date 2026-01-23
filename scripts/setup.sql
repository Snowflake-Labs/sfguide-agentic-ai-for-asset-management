-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- ============================================================================
-- SAM Demo - Complete Setup Script
-- ============================================================================
-- This script sets up the entire SAM demo environment in Snowflake.
--
-- RESULT:
-- - 9 Cortex Agents (portfolio, research, thematic, ESG, sales, quant, compliance, ops, executive)
-- - 10 Semantic Views (Cortex Analyst) for portfolio analytics, fundamentals, SEC data
-- - 16 Cortex Search services (15 document types + SEC filings)
-- - 48 CURATED tables (33 dimension/fact + 15 corpus) with 14,000+ real securities
-- - 5 CURATED views (holdings, returns, ESG, benchmark comparison)
-- - 9 MARKET_DATA tables (real SEC financials, prices, segments, analyst coverage, brokers)
-- - 15 RAW tables (unprocessed documents by type)
--
-- REQUIRES: ACCOUNTADMIN role
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- Set query tag for tracking
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"agentic_ai_for_asset_management","version":{"major":1,"minor":0},"attributes":{"is_quickstart":1,"source":"sql"}}';

-- ============================================================================
-- SECTION 1: Database and Schemas
-- ============================================================================

CREATE DATABASE IF NOT EXISTS SAM_DEMO
    COMMENT = 'Simulated Asset Management (SAM) - Agentic AI Demo Database';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.RAW
    COMMENT = 'Raw data layer - external data and unprocessed documents';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.CURATED
    COMMENT = 'Curated data layer - clean, validated, business-ready data';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.AI
    COMMENT = 'AI components - semantic views, search services, agents';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.PUBLIC
    COMMENT = 'Public schema for Git integration';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.MARKET_DATA
    COMMENT = 'Market data layer - synthetic and real market data from external sources';

-- ============================================================================
-- SECTION 2: Role Creation and Grants
-- ============================================================================

CREATE ROLE IF NOT EXISTS SAM_DEMO_ROLE
    COMMENT = 'Dedicated role for SAM demo operations';

-- Database-level privileges
GRANT USAGE ON DATABASE SAM_DEMO TO ROLE SAM_DEMO_ROLE;
GRANT CREATE SCHEMA ON DATABASE SAM_DEMO TO ROLE SAM_DEMO_ROLE;

-- Schema-level grants (includes all object types: tables, views, procedures, functions, stages, etc.)
-- ALL PRIVILEGES on schema automatically covers future objects created in that schema
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.RAW TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.CURATED TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.PUBLIC TO ROLE SAM_DEMO_ROLE;
GRANT ALL PRIVILEGES ON SCHEMA SAM_DEMO.MARKET_DATA TO ROLE SAM_DEMO_ROLE;

-- Role hierarchy
GRANT ROLE SAM_DEMO_ROLE TO ROLE ACCOUNTADMIN;
GRANT ROLE SAM_DEMO_ROLE TO ROLE SYSADMIN;

-- ============================================================================
-- SECTION 3: Warehouse
-- ============================================================================

CREATE WAREHOUSE IF NOT EXISTS SAM_DEMO_WH
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for SAM demo operations';

-- Grant warehouse permissions
GRANT USAGE ON WAREHOUSE SAM_DEMO_WH TO ROLE SAM_DEMO_ROLE;
GRANT OPERATE ON WAREHOUSE SAM_DEMO_WH TO ROLE SAM_DEMO_ROLE;
GRANT MODIFY ON WAREHOUSE SAM_DEMO_WH TO ROLE SAM_DEMO_ROLE;

-- ============================================================================
-- SECTION 4: Marketplace Data Access
-- ============================================================================

-- PREREQUISITE: Accept Marketplace listing terms first
-- https://app.snowflake.com/marketplace/listing/GZTSZ290BV255

GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_PUBLIC_DATA_FREE TO ROLE SAM_DEMO_ROLE;

-- ============================================================================
-- SECTION 5: Snowflake Intelligence and Cortex Setup
-- ============================================================================

-- Enable cross-region Cortex (required for accounts not in Cortex-enabled regions)
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

-- Create Snowflake Intelligence object
CREATE SNOWFLAKE INTELLIGENCE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;

-- Snowflake Intelligence grants
GRANT CREATE SNOWFLAKE INTELLIGENCE ON ACCOUNT TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SAM_DEMO_ROLE;
GRANT MODIFY ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE SAM_DEMO_ROLE;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT TO ROLE PUBLIC;

-- AI/Cortex component creation grants
GRANT CREATE AGENT ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT CREATE CORTEX SEARCH SERVICE ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;
GRANT CREATE SEMANTIC VIEW ON SCHEMA SAM_DEMO.AI TO ROLE SAM_DEMO_ROLE;

-- Account-level Cortex privileges (required for LLM functions)
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE SAM_DEMO_ROLE;

-- ============================================================================
-- SECTION 6: Git Integration (Public Repository - No Authentication Required)
-- ============================================================================

-- Create API integration for Git (no authentication needed for public repos)
CREATE OR REPLACE API INTEGRATION GITHUB_INTEGRATION_SAM_DEMO
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/')
  ENABLED = TRUE
  COMMENT = 'Git integration with GitHub for SAM Demo repository';

-- Create Git repository object pointing to the public SAM demo repo
CREATE OR REPLACE GIT REPOSITORY SAM_DEMO.PUBLIC.sam_demo_repo
  API_INTEGRATION = GITHUB_INTEGRATION_SAM_DEMO
  ORIGIN = 'https://github.com/Snowflake-Labs/sfguide-agentic-ai-for-asset-management.git'
  COMMENT = 'Git repository for SAM demo setup files';

-- Grant Git repository usage to role
GRANT READ ON GIT REPOSITORY SAM_DEMO.PUBLIC.sam_demo_repo TO ROLE SAM_DEMO_ROLE;

-- Fetch latest code from Git
ALTER GIT REPOSITORY SAM_DEMO.PUBLIC.sam_demo_repo FETCH;

-- ============================================================================
-- SECTION 7: Python Stored Procedures (Data Generation)
-- ============================================================================

USE ROLE SAM_DEMO_ROLE;
USE WAREHOUSE SAM_DEMO_WH;
USE DATABASE SAM_DEMO;

-- Master Setup Procedure (Data Generation)
CREATE OR REPLACE PROCEDURE SAM_DEMO.PUBLIC.SETUP_SAM_DEMO(TEST_MODE BOOLEAN DEFAULT FALSE)
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'pyyaml', 'jinja2')
HANDLER = 'run_setup'
EXECUTE AS CALLER
AS
$$
import os
import sys

def run_setup(session, test_mode: bool = False) -> str:
    """
    Master setup procedure that orchestrates the entire SAM demo setup.
    Downloads Python modules from Git and runs all data generation steps.
    """
    import tempfile
    import shutil
    
    # Create temp directory for downloads
    tmp_dir = tempfile.mkdtemp(prefix='sam_demo_')
    python_dir = os.path.join(tmp_dir, 'python')
    content_dir = os.path.join(tmp_dir, 'content_library')
    os.makedirs(python_dir, exist_ok=True)
    os.makedirs(content_dir, exist_ok=True)
    
    results = []
    results.append(f"Temp directory: {tmp_dir}")
    
    # Step 1: Download Python files from Git
    results.append("\n=== Step 1: Downloading Python modules ===")
    git_stage = '@SAM_DEMO.PUBLIC.sam_demo_repo/branches/main'
    
    # All Python modules needed for SAM demo
    python_files = [
        'config.py', 'config_accessors.py', 'db_helpers.py', 'demo_helpers.py',
        'logging_utils.py', 'scenario_utils.py', 'snowflake_io_utils.py',
        'sql_case_builders.py', 'sql_utils.py', 'rules_loader.py',
        'generate_structured.py', 'generate_unstructured.py', 'generate_market_data.py',
        'generate_real_transcripts.py', 'hydration_engine.py',
        'build_ai.py', 'create_agents.py', 'create_semantic_views.py', 'create_cortex_search.py'
    ]
    
    downloaded = 0
    for f in python_files:
        try:
            session.file.get(f"{git_stage}/python/{f}", python_dir + '/')
            downloaded += 1
        except Exception as e:
            results.append(f"  Warning: {f} - {e}")
    
    results.append(f"  Downloaded {downloaded}/{len(python_files)} Python files")
    
    # Step 2: Download content library templates
    results.append("\n=== Step 2: Downloading content library ===")
    try:
        content_files = session.sql(f"LIST {git_stage}/content_library/").collect()
        template_count = 0
        for row in content_files:
            file_path = row['name']
            if file_path.endswith('.md') or file_path.endswith('.yaml'):
                rel_path = file_path.split('/content_library/')[-1]
                local_dir = os.path.dirname(os.path.join(content_dir, rel_path))
                os.makedirs(local_dir, exist_ok=True)
                try:
                    full_stage_path = f"{git_stage}/content_library/{rel_path}"
                    session.file.get(full_stage_path, local_dir + '/')
                    template_count += 1
                except Exception as get_err:
                    results.append(f"    Warning: Could not download {rel_path}: {get_err}")
        results.append(f"  Downloaded {template_count} template files")
    except Exception as e:
        results.append(f"  Warning: Could not list content library: {e}")
    
    # Step 3: Configure Python path
    sys.path.insert(0, python_dir)
    
    import config
    config.PROJECT_ROOT = tmp_dir
    config.CONTENT_LIBRARY_PATH = content_dir
    
    results.append(f"\n=== Configuration ===")
    results.append(f"  Database: {config.DATABASE['name']}")
    results.append(f"  Content library: {config.CONTENT_LIBRARY_PATH}")
    
    import generate_structured
    import generate_market_data
    
    # Step 3: Build dimension tables
    results.append("\n=== Step 3: Building dimension tables ===")
    try:
        generate_structured.create_database_structure(session, recreate_database=False)
        generate_structured.build_dimension_tables(session, test_mode=test_mode)
        results.append("  Dimension tables complete!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    # Step 4: Build FACT_STOCK_PRICES as date anchor
    results.append("\n=== Step 4: Building price anchor (FACT_STOCK_PRICES) ===")
    try:
        generate_market_data.build_price_anchor(session, test_mode=test_mode)
        results.append("  Price anchor established!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    # Step 5: Build fact tables
    results.append("\n=== Step 5: Building fact tables ===")
    try:
        generate_structured.build_fact_tables(session, test_mode=test_mode)
        results.append("  Fact tables complete!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    # Step 6: Build scenario-specific data
    results.append("\n=== Step 6: Building scenario data ===")
    try:
        for scenario in config.AVAILABLE_SCENARIOS:
            generate_structured.build_scenario_data(session, scenario)
        generate_structured.validate_data_quality(session)
        results.append("  Scenario data complete!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    # Step 7: Build remaining market data
    results.append("\n=== Step 7: Building remaining market data ===")
    try:
        generate_market_data.build_all(session, test_mode=test_mode)
        results.append("  Market data complete!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    # Step 7.5: Build performance views (required by SAM_ANALYST_VIEW)
    results.append("\n=== Step 7.5: Building performance views ===")
    try:
        generate_structured.build_security_returns_view(session)
        generate_structured.build_esg_latest_view(session)
        results.append("  Security returns and ESG views complete!")
        
        generate_structured.build_fact_strategy_performance(session)
        results.append("  Strategy performance complete!")
        
        generate_structured.build_fact_benchmark_performance(session)
        results.append("  Benchmark performance complete!")
        
        generate_structured.build_portfolio_benchmark_comparison_view(session)
        results.append("  Portfolio vs benchmark view complete!")
    except Exception as e:
        results.append(f"  ERROR building performance views: {e}")
        raise
    
    # Step 8: Generate real transcripts
    results.append("\n=== Step 8: Generating transcripts ===")
    real_transcripts_available = False
    try:
        import generate_real_transcripts
        if generate_real_transcripts.verify_transcripts_available(session):
            generate_real_transcripts.build_all(session, test_mode=test_mode)
            results.append("  Real transcripts complete!")
            real_transcripts_available = True
        else:
            results.append("  Real transcript source not available")
    except Exception as e:
        results.append(f"  Real transcripts failed: {e}")
    
    if not real_transcripts_available:
        results.append("  INFO: Real transcripts not available. Search will use fallback.")
    
    # Step 9: Generate unstructured documents
    results.append("\n=== Step 9: Generating documents from templates ===")
    try:
        import generate_unstructured
        generate_unstructured.build_all(session, ['all'], test_mode=test_mode)
        results.append("  Document generation complete!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    try:
        shutil.rmtree(tmp_dir)
    except:
        pass
    
    results.append("\n=== Data Generation Complete ===")
    return "\n".join(results)
$$;

-- ============================================================================
-- SECTION 8: AI Components Procedures
-- ============================================================================

-- AI Components Setup (Semantic Views & Search Services)
CREATE OR REPLACE PROCEDURE SAM_DEMO.PUBLIC.SETUP_AI_COMPONENTS()
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'pyyaml')
HANDLER = 'run_ai_setup'
EXECUTE AS CALLER
AS
$$
import os
import sys

def run_ai_setup(session) -> str:
    """Creates AI components: semantic views and Cortex Search services."""
    import tempfile
    
    tmp_dir = tempfile.mkdtemp(prefix='sam_ai_')
    python_dir = os.path.join(tmp_dir, 'python')
    os.makedirs(python_dir, exist_ok=True)
    
    results = []
    git_stage = '@SAM_DEMO.PUBLIC.sam_demo_repo/branches/main'
    
    python_files = [
        'config.py', 'config_accessors.py', 'db_helpers.py', 'demo_helpers.py',
        'logging_utils.py', 'scenario_utils.py',
        'build_ai.py', 'create_semantic_views.py', 'create_cortex_search.py'
    ]
    
    for f in python_files:
        try:
            session.file.get(f"{git_stage}/python/{f}", python_dir + '/')
        except Exception as e:
            results.append(f"Warning: {f} - {e}")
    
    sys.path.insert(0, python_dir)
    
    import config
    config.PROJECT_ROOT = tmp_dir
    
    # Use config as source of truth for available scenarios
    all_scenarios = config.AVAILABLE_SCENARIOS
    
    # Create semantic views
    results.append("=== Creating Semantic Views ===")
    try:
        import create_semantic_views
        create_semantic_views.create_semantic_views(session, all_scenarios)
        results.append("  Semantic views created!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    # Create search services
    results.append(f"\n=== Creating Cortex Search Services ===")
    try:
        import create_cortex_search
        create_cortex_search.create_search_services(session, all_scenarios)
        results.append("  Search services created!")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    import shutil
    try:
        shutil.rmtree(tmp_dir)
    except:
        pass
    
    results.append("\n=== AI Components Complete ===")
    return "\n".join(results)
$$;

-- Agent Creation Procedure
CREATE OR REPLACE PROCEDURE SAM_DEMO.PUBLIC.SETUP_AGENTS()
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'pyyaml')
HANDLER = 'run_agent_setup'
EXECUTE AS CALLER
AS
$$
import os
import sys

def run_agent_setup(session) -> str:
    """Creates all Cortex agents for the SAM demo."""
    import tempfile
    
    tmp_dir = tempfile.mkdtemp(prefix='sam_agents_')
    python_dir = os.path.join(tmp_dir, 'python')
    os.makedirs(python_dir, exist_ok=True)
    
    results = []
    git_stage = '@SAM_DEMO.PUBLIC.sam_demo_repo/branches/main'
    
    python_files = [
        'config.py', 'config_accessors.py', 'db_helpers.py', 'demo_helpers.py',
        'logging_utils.py', 'create_agents.py'
    ]
    
    for f in python_files:
        try:
            session.file.get(f"{git_stage}/python/{f}", python_dir + '/')
        except Exception as e:
            results.append(f"Warning: {f} - {e}")
    
    sys.path.insert(0, python_dir)
    
    import config
    config.PROJECT_ROOT = tmp_dir
    
    results.append("=== Creating Cortex Agents ===")
    try:
        import create_agents
        # Use config.AVAILABLE_SCENARIOS for consistency (creates all 9 agents)
        created, failed = create_agents.create_all_agents(session, config.AVAILABLE_SCENARIOS)
        results.append(f"  Created: {created} agents")
        if failed > 0:
            results.append(f"  Failed: {failed} agents")
    except Exception as e:
        results.append(f"  ERROR: {e}")
        raise
    
    import shutil
    try:
        shutil.rmtree(tmp_dir)
    except:
        pass
    
    results.append("\n=== Agent Creation Complete ===")
    return "\n".join(results)
$$;

-- ============================================================================
-- SECTION 9: Custom Tools
-- ============================================================================

-- Create stage for PDF reports 
CREATE STAGE IF NOT EXISTS SAM_DEMO.AI.PDF_REPORTS
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- PDF Report Generator (used by all agents) 
CREATE OR REPLACE PROCEDURE SAM_DEMO.AI.GENERATE_PDF_REPORT(
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
    """
    Generate professional branded PDF report from markdown content.
    
    Args:
        session: Snowpark session
        markdown_content: Complete markdown document from agent (using retrieved templates)
        report_title: Title for the document header (e.g., "Q4 2024 Client Review")
        document_audience: One of "internal", "external_client", or "external_regulatory"
        
    Returns:
        String with download link to generated PDF
    """
    # Validate audience
    valid_audiences = ['internal', 'external_client', 'external_regulatory']
    if document_audience not in valid_audiences:
        document_audience = 'internal'  # Default to internal if invalid
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_title = re.sub(r'[^a-zA-Z0-9_]', '_', report_title)[:30]
    pdf_filename = f'{document_audience}_{safe_title}_{timestamp}.pdf'
    
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
    logo_src = f'data:image/svg+xml;base64,{svg_base64}'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Convert markdown to HTML
        html_body = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])
        
        # Professional CSS styling for investment reports
        css_style = """
            @page { size: A4 landscape; margin: 1.5cm; }
            body { font-family: Arial, sans-serif; line-height: 1.5; color: #2C3E50; font-size: 11px; }
            h1 { color: #1F4E79; border-bottom: 3px solid #1F4E79; padding-bottom: 8px; font-size: 20px; }
            h2 { color: #2E75B6; border-left: 4px solid #2E75B6; padding-left: 12px; margin-top: 20px; font-size: 16px; }
            h3 { color: #3F7CAC; font-size: 14px; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; table-layout: auto; font-size: 10px; }
            th { background-color: #1F4E79; color: white; padding: 8px 6px; font-weight: bold; text-align: left; white-space: nowrap; }
            td { padding: 6px; border-bottom: 1px solid #ddd; word-wrap: break-word; }
            tr:nth-child(even) { background-color: #F8F9FA; }
            .header { display: flex; align-items: center; border-bottom: 3px solid #1F4E79; padding-bottom: 12px; margin-bottom: 20px; }
            .header-logo { margin-right: 15px; }
            .header-text { flex: 1; }
            .header-title { margin: 0; color: #1F4E79; font-size: 20px; }
            .header-subtitle { margin: 5px 0 0 0; color: #666; font-size: 12px; }
            .footer { margin-top: 25px; padding-top: 12px; border-top: 2px solid #1F4E79; font-size: 9px; color: #666; }
            .demo-disclaimer { background: #FFF3CD; border: 1px solid #FFE69C; padding: 10px; margin-top: 12px; font-size: 9px; color: #664D03; border-radius: 4px; }
            .internal-badge { background: #E7F3FF; color: #1F4E79; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold; }
            .regulatory-badge { background: #F8D7DA; color: #721C24; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold; }
        """
        
        # Audience-specific header subtitle
        if document_audience == 'internal':
            header_subtitle = f'<span class="internal-badge">INTERNAL DOCUMENT</span> | {report_title}'
        elif document_audience == 'external_regulatory':
            header_subtitle = f'<span class="regulatory-badge">FCA REGULATED</span> | {report_title}'
        else:  # external_client
            header_subtitle = report_title
        
        # Build header with logo
        sam_header = f"""
        <div class="header">
            <div class="header-logo">
                <img src="{logo_src}" alt="Simulated Asset Management" style="height: 50px;"/>
            </div>
            <div class="header-text">
                <h1 class="header-title" style="border: none; padding: 0;">SIMULATED ASSET MANAGEMENT</h1>
                <p class="header-subtitle">{header_subtitle}</p>
            </div>
        </div>
        """
        
        # Audience-specific footer content
        report_timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')
        
        if document_audience == 'internal':
            footer_content = f"""
            <p><strong>Classification:</strong> Internal Use Only - Not for Distribution</p>
            <p><strong>Generated:</strong> {report_timestamp}</p>
            <p><strong>Generated By:</strong> Snowflake Intelligence</p>
            """
        elif document_audience == 'external_regulatory':
            footer_content = f"""
            <p><strong>Regulatory Status:</strong> Prepared in accordance with FCA reporting requirements</p>
            <p><strong>Compliance Contact:</strong> compliance@sam-demo.example</p>
            <p><strong>Generated:</strong> {report_timestamp}</p>
            """
        else:  # external_client
            footer_content = f"""
            <p><strong>Important:</strong> Past performance does not guarantee future results. Investment involves risk including possible loss of principal.</p>
            <p><strong>Contact:</strong> clientservices@sam-demo.example</p>
            <p><strong>Generated:</strong> {report_timestamp}</p>
            """
        
        # Demo disclaimer (all audiences)
        demo_disclaimer = """
        <div class="demo-disclaimer">
            <strong>DEMONSTRATION ONLY:</strong> This document was generated by Snowflake Intelligence 
            for demonstration purposes. It does not represent real investment advice, actual portfolio data, 
            or genuine recommendations. Simulated Asset Management is a fictional entity created for this demo.
        </div>
        """
        
        # Complete footer
        footer = f"""
        <div class="footer">
            {footer_content}
            {demo_disclaimer}
        </div>
        """
        
        # Complete HTML document
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Simulated Asset Management - {report_title}</title>
            <style>{css_style}</style>
        </head>
        <body>
            {sam_header}
            {html_body}
            {footer}
        </body>
        </html>
        """
        
        # Create HTML file
        html_path = os.path.join(tmpdir, 'report.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Convert HTML to PDF
        import weasyprint
        pdf_path = os.path.join(tmpdir, pdf_filename)
        weasyprint.HTML(filename=html_path).write_pdf(pdf_path)
        
        # Upload to stage (AI schema to match am_ai_demo)
        stage_path = '@SAM_DEMO.AI.PDF_REPORTS'
        session.file.put(pdf_path, stage_path, overwrite=True, auto_compress=False)
        
        # Generate presigned URL for download
        presigned_url = session.sql(
            f"SELECT GET_PRESIGNED_URL('{stage_path}', '{pdf_filename}') AS url"
        ).collect()[0]['URL']
        
        # Format response based on audience
        audience_labels = {
            'internal': 'Internal Report',
            'external_client': 'Client Report', 
            'external_regulatory': 'Regulatory Report'
        }
        audience_label = audience_labels.get(document_audience, 'Report')
        
        return f"[{audience_label}: {report_title}]({presigned_url}) - Professional PDF generated successfully with SAM branding."
$$;

-- M&A Simulation Tool - matches am_ai_demo/build_ai.py exactly
CREATE OR REPLACE FUNCTION SAM_DEMO.AI.MA_SIMULATION_TOOL(
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
    """
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
    """
    
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
    
    year1_contribution = (target_operating_income + cost_synergies_year1 + 
        (revenue_synergies * sam_operating_margin) - integration_cost_one_time)
    year2_contribution = (target_operating_income + cost_synergies_full + 
        (revenue_synergies * sam_operating_margin))
    
    eps_impact_year1 = year1_contribution / sam_shares_outstanding
    eps_impact_year2 = year2_contribution / sam_shares_outstanding
    eps_accretion_year1_pct = (eps_impact_year1 / sam_baseline_eps) * 100
    eps_accretion_year2_pct = (eps_impact_year2 / sam_baseline_eps) * 100
    
    combined_aum = sam_current_aum + target_aum
    aum_growth_pct = (target_aum / sam_current_aum) * 100
    
    risk_level = "Low" if target_aum < 5_000_000_000 else "Medium" if target_aum < 20_000_000_000 else "High"
    
    return {
        "simulation_summary": {
            "target_aum_billions": round(target_aum / 1_000_000_000, 1),
            "target_revenue_millions": round(target_revenue / 1_000_000, 1),
            "cost_synergy_assumption_pct": cost_synergy_pct * 100
        },
        "year1_projection": {
            "eps_accretion_pct": round(eps_accretion_year1_pct, 1),
            "eps_impact_usd": round(eps_impact_year1, 2),
            "synergies_realized_millions": round(cost_synergies_year1 / 1_000_000, 1),
            "integration_costs_millions": round(integration_cost_one_time / 1_000_000, 1),
            "net_contribution_millions": round(year1_contribution / 1_000_000, 1)
        },
        "year2_projection": {
            "eps_accretion_pct": round(eps_accretion_year2_pct, 1),
            "eps_impact_usd": round(eps_impact_year2, 2),
            "full_synergies_millions": round(cost_synergies_full / 1_000_000, 1),
            "net_contribution_millions": round(year2_contribution / 1_000_000, 1)
        },
        "strategic_impact": {
            "combined_aum_billions": round(combined_aum / 1_000_000_000, 1),
            "aum_growth_pct": round(aum_growth_pct, 1),
            "revenue_synergies_millions": round(revenue_synergies / 1_000_000, 1)
        },
        "risk_assessment": {
            "integration_risk_level": risk_level,
            "key_risks": [
                "Client retention during transition",
                "Key personnel retention",
                "System integration complexity",
                "Regulatory approval timeline"
            ],
            "timeline_months": 12 if risk_level == "Low" else 18 if risk_level == "Medium" else 24
        },
        "recommendation": f"Based on {round(eps_accretion_year1_pct, 1)}% Year 1 EPS accretion, this acquisition appears financially attractive. Recommend detailed due diligence focusing on client retention and integration planning."
    }
$$;

-- ============================================================================
-- SECTION 10: Execute Setup
-- ============================================================================

-- Generate all data
CALL SAM_DEMO.PUBLIC.SETUP_SAM_DEMO(FALSE);

-- Create AI components
CALL SAM_DEMO.PUBLIC.SETUP_AI_COMPONENTS();

-- Create agents
CALL SAM_DEMO.PUBLIC.SETUP_AGENTS();

-- ============================================================================
-- Complete
-- ============================================================================

-- Optimize warehouse size
ALTER WAREHOUSE SAM_DEMO_WH SET WAREHOUSE_SIZE = 'MEDIUM';

-- Completion message
SELECT 'Setup complete - SAM demo ready to use in Snowflake Intelligence' AS status;
