-- ============================================================================
-- SAM Demo - Complete Setup Script
-- ============================================================================
-- This script sets up the entire SAM demo environment in Snowflake.
--
-- RESULT:
-- - 50+ CURATED dimension/fact tables with 14,000+ real securities
-- - 26 RAW document tables from 76+ templates  
-- - 26 corpus tables (document collections)
-- - 16 Cortex Search services
-- - 10 Semantic Views (Cortex Analyst)
-- - 9 Cortex Agents
--
-- RUN TIME: ~10-12 minutes
-- REQUIRES: ACCOUNTADMIN role
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- ============================================================================
-- SECTION 1: Database and Schemas
-- ============================================================================

CREATE DATABASE IF NOT EXISTS SAM_DEMO
    COMMENT = 'Snowcrest Asset Management (SAM) - Agentic AI Demo Database';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.RAW
    COMMENT = 'Raw data layer - external data and unprocessed documents';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.CURATED
    COMMENT = 'Curated data layer - clean, validated, business-ready data';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.AI
    COMMENT = 'AI components - semantic views, search services, agents';

CREATE SCHEMA IF NOT EXISTS SAM_DEMO.PUBLIC
    COMMENT = 'Public schema for Git integration and notebooks';

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
-- SECTION 6: Git Integration
-- ============================================================================

CREATE OR REPLACE SECRET SAM_DEMO.PUBLIC.GITHUB_SECRET
  TYPE = PASSWORD
  USERNAME = 'user_name'
  PASSWORD = 'pat_token'
  COMMENT = 'GitHub PAT for accessing private SAM demo repository';

-- Grant secret usage to role
GRANT USAGE ON SECRET SAM_DEMO.PUBLIC.GITHUB_SECRET TO ROLE SAM_DEMO_ROLE;
GRANT READ ON SECRET SAM_DEMO.PUBLIC.GITHUB_SECRET TO ROLE SAM_DEMO_ROLE;

-- Create API integration for Git (must reference the secret in ALLOWED_AUTHENTICATION_SECRETS)
CREATE OR REPLACE API INTEGRATION GITHUB_INTEGRATION_SAM_DEMO
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/')
  ALLOWED_AUTHENTICATION_SECRETS = (SAM_DEMO.PUBLIC.GITHUB_SECRET)
  ENABLED = TRUE
  COMMENT = 'Git integration with GitHub for SAM Demo repository';

-- Create Git repository object pointing to the SAM demo repo (with authentication)
CREATE OR REPLACE GIT REPOSITORY SAM_DEMO.PUBLIC.sam_demo_repo
  API_INTEGRATION = GITHUB_INTEGRATION_SAM_DEMO
  GIT_CREDENTIALS = SAM_DEMO.PUBLIC.GITHUB_SECRET
  ORIGIN = 'https://github.com/sfc-gh-dshemsi/sfguide-agentic-ai-for-asset-management.git'
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

-- Create stage for PDF reports
CREATE STAGE IF NOT EXISTS SAM_DEMO.CURATED.SAM_REPORTS_STAGE
    DIRECTORY = (ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Stage for generated PDF reports';

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
    
    all_scenarios = [
        'portfolio_copilot', 'research_copilot', 'thematic_macro_advisor',
        'esg_guardian', 'sales_advisor', 'quant_analyst', 'compliance_advisor',
        'middle_office_copilot', 'executive_copilot'
    ]
    
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
        created, failed = create_agents.create_all_agents(session, ['all'])
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

-- PDF Report Generator (used by all agents)
CREATE OR REPLACE PROCEDURE SAM_DEMO.AI.GENERATE_PDF_REPORT(
    MARKDOWN_CONTENT VARCHAR,
    REPORT_TITLE VARCHAR,
    DOCUMENT_AUDIENCE VARCHAR DEFAULT 'internal'
)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'fpdf2')
HANDLER = 'generate_pdf_report'
EXECUTE AS CALLER
AS
$$
from snowflake.snowpark import Session
from datetime import datetime
import re
import tempfile
import os

def generate_pdf_report(session: Session, markdown_content: str, report_title: str, document_audience: str = 'internal'):
    from fpdf import FPDF
    
    def clean_text(text: str) -> str:
        """Clean text for PDF - remove emojis and non-latin1 characters."""
        if not text:
            return text
        replacements = {
            '🚨': '[!]', '⚠️': '[!]', '✅': '[Y]', '❌': '[N]',
            '📊': '', '📈': '', '📉': '', '💰': '$', '🏔️': '',
            '📄': '', '📥': '', '🔴': '[H]', '🟡': '[M]', '🟢': '[L]',
            '✓': 'Y', '✗': 'N', '→': '>', '←': '<', '•': '-',
            '📋': '', '🎯': '', '💡': '', '🔍': '', '📝': '',
            '★': '*', '☆': '*', '●': '-', '○': '-', '✔': 'Y', '✘': 'N',
        }
        for e, r in replacements.items():
            text = text.replace(e, r)
        text = re.compile("[\U0001F000-\U0001FFFF]", re.UNICODE).sub('', text)
        try:
            text.encode('latin-1')
        except UnicodeEncodeError:
            text = text.encode('latin-1', errors='ignore').decode('latin-1')
        return text
    
    def parse_content(content: str) -> dict:
        """Parse content into structured sections - strips ALL markdown formatting."""
        sections = []
        current_section = {'title': 'Overview', 'content': [], 'subsections': []}
        current_subsection = None
        
        lines = content.split('\\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Strip markdown syntax - ultra-safe approach with fallbacks
            clean = line
            
            # Remove links [text](url) → text (safe approach with fallback)
            try:
                clean = re.sub(r'\\[([^\\]]+)\\]\\([^\\)]+\\)', r'\\1', clean)
            except:
                # Fallback: just remove brackets
                clean = clean.replace('[', '').replace(']', '')
                
            # Remove images ![alt](url) (safe approach)
            try:
                clean = re.sub(r'!\\[([^\\]]+)\\]\\([^\\)]+\\)', r'\\1', clean)
            except:
                pass
                
            # Remove code blocks `text` → text
            try:
                clean = re.sub(r'`([^`]+)`', r'\\1', clean)
            except:
                clean = clean.replace('`', '')
                
            # Remove bold **text** → text (simple greedy removal)
            while '**' in clean:
                clean = clean.replace('**', '', 2)
                
            # Remove remaining markdown symbols
            clean = clean.replace('*', '').replace('_', ' ').replace('#', '')
            
            # Remove any remaining parentheses from failed link parsing
            if '(' in clean and ')' in clean:
                # Simple cleanup of (url) patterns
                clean = re.sub(r'\\([^\\)]+\\)', '', clean)
                
            # Clean emojis and special chars
            clean = clean_text(clean)
            
            if line.startswith('# '):
                if current_section['content'] or current_section['subsections']:
                    sections.append(current_section)
                current_section = {'title': clean_text(line[2:]), 'content': [], 'subsections': []}
                current_subsection = None
            elif line.startswith('## '):
                current_subsection = {'title': clean_text(line[3:]), 'content': []}
                current_section['subsections'].append(current_subsection)
            elif line.startswith('### '):
                target = current_subsection['content'] if current_subsection else current_section['content']
                target.append(('subheading', clean_text(line[4:])))
            elif line.startswith('**') and '**:' in line:
                parts = line.split('**:', 1)
                key = clean_text(parts[0].replace('**', '').strip())
                value = clean_text(parts[1].strip()) if len(parts) > 1 else ''
                target = current_subsection['content'] if current_subsection else current_section['content']
                target.append(('keyvalue', key, value))
            elif line.startswith('- ') or line.startswith('* '):
                target = current_subsection['content'] if current_subsection else current_section['content']
                target.append(('bullet', clean))
            elif line.startswith('|') and not line.startswith('|--'):
                cells = [clean_text(c.strip()) for c in line.split('|') if c.strip() and not c.strip().startswith('-')]
                if cells:
                    target = current_subsection['content'] if current_subsection else current_section['content']
                    target.append(('tablerow', cells))
            elif re.match(r'^\\d+\\.\\s', line):
                target = current_subsection['content'] if current_subsection else current_section['content']
                target.append(('numbered', clean))
            elif clean:
                target = current_subsection['content'] if current_subsection else current_section['content']
                target.append(('paragraph', clean))
        
        if current_section['content'] or current_section['subsections']:
            sections.append(current_section)
        
        return sections if sections else [{'title': 'Report Content', 'content': [('paragraph', clean_text(content))], 'subsections': []}]
    
    schemes = {
        'internal': {'primary': (25, 55, 95), 'accent': (0, 120, 180), 'highlight': (255, 200, 50), 'label': 'INTERNAL MEMO'},
        'external_client': {'primary': (0, 60, 110), 'accent': (0, 140, 100), 'highlight': (0, 180, 80), 'label': 'CLIENT REPORT'},
        'external_regulatory': {'primary': (50, 50, 50), 'accent': (80, 80, 80), 'highlight': (180, 0, 0), 'label': 'REGULATORY FILING'}
    }
    scheme = schemes.get(document_audience, schemes['internal'])
    
    timestamp = datetime.now()
    safe_title = re.sub(r'[^a-zA-Z0-9_]', '_', clean_text(report_title))[:40]
    pdf_filename = f'{safe_title}_{timestamp.strftime("%Y%m%d_%H%M%S")}.pdf'
    report_title = clean_text(report_title)
    
    class BusinessReport(FPDF):
        def __init__(self):
            super().__init__()
            self.section_num = 0
            
        def header(self):
            if self.page_no() == 1:
                return
            self.set_fill_color(*scheme['primary'])
            self.rect(0, 0, 210, 12, 'F')
            self.set_text_color(255, 255, 255)
            self.set_font('Helvetica', '', 8)
            self.set_xy(15, 4)
            self.cell(100, 5, 'Snowcrest Asset Management')
            self.cell(80, 5, report_title[:40], align='R')
            self.set_y(18)
            self.set_text_color(0, 0, 0)
            
        def footer(self):
            self.set_y(-15)
            self.set_draw_color(*scheme['primary'])
            self.line(15, self.get_y(), 195, self.get_y())
            self.set_font('Helvetica', '', 8)
            self.set_text_color(120, 120, 120)
            self.set_y(-12)
            self.cell(60, 5, f'Ref: SAM-{timestamp.strftime("%Y%m%d")}-{self.page_no():03d}')
            self.cell(60, 5, 'CONFIDENTIAL', align='C')
            self.cell(60, 5, f'Page {self.page_no()}', align='R')
            
        def cover_page(self):
            self.set_fill_color(*scheme['primary'])
            self.rect(0, 0, 210, 100, 'F')
            
            self.set_text_color(255, 255, 255)
            self.set_font('Helvetica', 'B', 24)
            self.set_xy(0, 25)
            self.cell(210, 12, 'SNOWCREST', align='C')
            self.set_font('Helvetica', '', 14)
            self.set_xy(0, 40)
            self.cell(210, 8, 'ASSET MANAGEMENT', align='C')
            
            self.set_fill_color(*scheme['highlight'])
            self.set_xy(65, 60)
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(0, 0, 0) if scheme['highlight'][0] > 100 else self.set_text_color(255, 255, 255)
            self.cell(80, 8, scheme['label'], align='C', fill=True)
            
            self.set_text_color(0, 0, 0)
            self.set_font('Helvetica', 'B', 18)
            self.set_xy(20, 115)
            
            title_lines = []
            words = report_title.split()
            current_line = ''
            for word in words:
                test_line = current_line + ' ' + word if current_line else word
                if len(test_line) > 45:
                    title_lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            if current_line:
                title_lines.append(current_line)
            
            for i, line in enumerate(title_lines[:3]):
                self.set_xy(20, 115 + i * 12)
                self.cell(170, 10, line)
            
            self.set_fill_color(245, 245, 250)
            self.rect(20, 165, 170, 50, 'F')
            self.set_draw_color(*scheme['primary'])
            self.rect(20, 165, 170, 50, 'D')
            
            self.set_font('Helvetica', '', 10)
            self.set_text_color(80, 80, 80)
            self.set_xy(25, 172)
            self.cell(40, 6, 'Prepared By:')
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(0, 0, 0)
            self.cell(120, 6, 'Investment Management Division')
            
            self.set_font('Helvetica', '', 10)
            self.set_text_color(80, 80, 80)
            self.set_xy(25, 182)
            self.cell(40, 6, 'Date:')
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(0, 0, 0)
            self.cell(120, 6, timestamp.strftime('%B %d, %Y'))
            
            self.set_font('Helvetica', '', 10)
            self.set_text_color(80, 80, 80)
            self.set_xy(25, 192)
            self.cell(40, 6, 'Classification:')
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(*scheme['primary'])
            self.cell(120, 6, document_audience.replace('_', ' ').upper())
            
            self.set_xy(25, 202)
            self.set_font('Helvetica', '', 10)
            self.set_text_color(80, 80, 80)
            self.cell(40, 6, 'Reference:')
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(0, 0, 0)
            self.cell(120, 6, f'SAM-RPT-{timestamp.strftime("%Y%m%d-%H%M")}')
            
            self.set_fill_color(255, 250, 230)
            self.set_draw_color(200, 150, 0)
            self.rect(20, 235, 170, 20, 'FD')
            self.set_font('Helvetica', 'B', 9)
            self.set_text_color(150, 100, 0)
            self.set_xy(25, 240)
            self.cell(160, 10, 'DEMONSTRATION DOCUMENT - Contains synthetic data for illustration purposes only', align='C')
            
        def section_title(self, title):
            self.section_num += 1
            self.ln(8)
            self.set_fill_color(*scheme['primary'])
            self.set_text_color(255, 255, 255)
            self.set_font('Helvetica', 'B', 12)
            self.cell(0, 10, f'  {self.section_num}. {title.upper()}', fill=True)
            self.ln(12)
            self.set_text_color(0, 0, 0)
            
        def subsection_title(self, title):
            self.ln(4)
            self.set_draw_color(*scheme['accent'])
            self.set_text_color(*scheme['accent'])
            self.set_font('Helvetica', 'B', 11)
            self.cell(0, 7, title)
            self.ln(2)
            self.line(self.get_x(), self.get_y(), self.get_x() + 50, self.get_y())
            self.ln(6)
            self.set_text_color(0, 0, 0)
            
        def body_text(self, text):
            self.set_font('Helvetica', '', 10)
            self.set_text_color(40, 40, 40)
            self.multi_cell(0, 5.5, text)
            self.ln(3)
            
        def key_value_pair(self, key, value):
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(80, 80, 80)
            self.cell(55, 6, key + ':')
            self.set_font('Helvetica', '', 10)
            self.set_text_color(0, 0, 0)
            self.multi_cell(0, 6, str(value))
            self.ln(1)
            
        def bullet_point(self, text):
            self.set_font('Helvetica', '', 10)
            self.set_text_color(40, 40, 40)
            x = self.get_x()
            self.cell(8, 5.5, chr(149))
            self.multi_cell(0, 5.5, text[2:] if text.startswith('- ') or text.startswith('* ') else text)
            
        def numbered_item(self, text):
            self.set_font('Helvetica', '', 10)
            self.set_text_color(40, 40, 40)
            self.multi_cell(0, 5.5, text)
            
        def data_table(self, rows):
            if not rows:
                return
            headers = rows[0] if rows else []
            data_rows = rows[1:] if len(rows) > 1 else []
            
            col_count = len(headers)
            if col_count == 0:
                return
            col_width = 180 / col_count
            
            self.set_fill_color(*scheme['primary'])
            self.set_text_color(255, 255, 255)
            self.set_font('Helvetica', 'B', 9)
            for h in headers:
                self.cell(col_width, 7, str(h)[:20], border=1, align='C', fill=True)
            self.ln()
            
            self.set_text_color(0, 0, 0)
            self.set_font('Helvetica', '', 9)
            for i, row in enumerate(data_rows):
                if i % 2 == 0:
                    self.set_fill_color(250, 250, 252)
                else:
                    self.set_fill_color(255, 255, 255)
                for cell in row:
                    self.cell(col_width, 6, str(cell)[:20], border=1, fill=True)
                self.ln()
            self.ln(4)
    
    sections = parse_content(markdown_content)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf = BusinessReport()
        pdf.set_auto_page_break(auto=True, margin=20)
        
        pdf.add_page()
        pdf.cover_page()
        
        pdf.add_page()
        
        table_buffer = []
        
        for section in sections:
            pdf.section_title(section['title'])
            
            for item in section['content']:
                if item[0] == 'paragraph':
                    pdf.body_text(item[1])
                elif item[0] == 'keyvalue':
                    pdf.key_value_pair(item[1], item[2])
                elif item[0] == 'bullet':
                    pdf.bullet_point(item[1])
                elif item[0] == 'numbered':
                    pdf.numbered_item(item[1])
                elif item[0] == 'subheading':
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.cell(0, 7, item[1])
                    pdf.ln(8)
                elif item[0] == 'tablerow':
                    table_buffer.append(item[1])
                    
            if table_buffer:
                pdf.data_table(table_buffer)
                table_buffer = []
            
            for subsection in section['subsections']:
                pdf.subsection_title(subsection['title'])
                for item in subsection['content']:
                    if item[0] == 'paragraph':
                        pdf.body_text(item[1])
                    elif item[0] == 'keyvalue':
                        pdf.key_value_pair(item[1], item[2])
                    elif item[0] == 'bullet':
                        pdf.bullet_point(item[1])
                    elif item[0] == 'numbered':
                        pdf.numbered_item(item[1])
                    elif item[0] == 'subheading':
                        pdf.set_font('Helvetica', 'B', 10)
                        pdf.cell(0, 7, item[1])
                        pdf.ln(8)
                    elif item[0] == 'tablerow':
                        table_buffer.append(item[1])
                        
                if table_buffer:
                    pdf.data_table(table_buffer)
                    table_buffer = []
        
        pdf.ln(15)
        pdf.set_draw_color(*scheme['primary'])
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(8)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 6, 'Document Approval')
        pdf.ln(10)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(90, 5, 'Prepared by: _______________________')
        pdf.cell(90, 5, 'Approved by: _______________________')
        pdf.ln(8)
        pdf.cell(90, 5, 'Date: _______________________')
        pdf.cell(90, 5, 'Date: _______________________')
        
        pdf_path = os.path.join(tmpdir, pdf_filename)
        pdf.output(pdf_path)
        
        stage_path = '@SAM_DEMO.CURATED.SAM_REPORTS_STAGE'
        session.file.put(pdf_path, stage_path, overwrite=True, auto_compress=False)
        
        presigned_url = session.sql(
            f"SELECT GET_PRESIGNED_URL('{stage_path}', '{pdf_filename}') AS url"
        ).collect()[0]['URL']
        
        return f"**Report Generated Successfully**\\n\\n[Download: {report_title}]({presigned_url})\\n\\n*Classification: {document_audience.replace('_', ' ').title()}*\\n*Reference: SAM-RPT-{timestamp.strftime('%Y%m%d-%H%M')}*"
$$;

-- M&A Simulation Tool
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
    """Simulate the financial impact of an acquisition."""
    sam_baseline_eps = 2.50
    sam_shares_outstanding = 50_000_000
    sam_current_aum = 12_500_000_000
    sam_operating_margin = 0.35
    
    integration_cost_one_time = 30_000_000
    year1_synergy_realization = 0.70
    revenue_synergy_pct = 0.02
    
    target_operating_income = target_revenue * sam_operating_margin
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
            "net_contribution_millions": round(year1_contribution / 1_000_000, 1)
        },
        "year2_projection": {
            "eps_accretion_pct": round(eps_accretion_year2_pct, 1),
            "eps_impact_usd": round(eps_impact_year2, 2),
            "net_contribution_millions": round(year2_contribution / 1_000_000, 1)
        },
        "strategic_impact": {
            "combined_aum_billions": round(combined_aum / 1_000_000_000, 1),
            "aum_growth_pct": round(aum_growth_pct, 1)
        },
        "risk_assessment": {
            "integration_risk_level": risk_level,
            "timeline_months": 12 if risk_level == "Low" else 18 if risk_level == "Medium" else 24
        },
        "recommendation": f"Based on {round(eps_accretion_year1_pct, 1)}% Year 1 EPS accretion, this acquisition appears financially attractive."
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
-- SECTION 11: Post-Setup Optimization
-- ============================================================================

ALTER WAREHOUSE SAM_DEMO_WH SET WAREHOUSE_SIZE = 'MEDIUM';
ALTER WAREHOUSE SAM_DEMO_WH SUSPEND;

-- Completion message
SELECT 'Setup complete - SAM demo ready to use in Snowflake Intelligence' AS status;
