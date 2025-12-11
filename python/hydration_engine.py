"""
Hydration Engine for Pre-Generated Content Templates

This module implements the template hydration system that replaces LLM generation
with deterministic template-based document creation.

Modules:
- content_loader: Load and parse templates with YAML front matter
- variant_picker: Deterministic template selection
- context_builder: Build placeholder context from DIM tables
- numeric_rules: Sample numeric values within bounds
- conditional_renderer: Handle conditional placeholder logic
- renderer: Fill all placeholders and validate
- writer: Write to RAW tables with Context-First approach
"""

import os
import re
import yaml
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from snowflake.snowpark import Session
import config

# ============================================================================
# MODULE: Content Loader
# ============================================================================

def load_templates(doc_type: str) -> List[Dict[str, Any]]:
    """
    Scan content library and load all templates for specified document type.
    
    Args:
        doc_type: Document type identifier (e.g., 'broker_research')
    
    Returns:
        List of template dicts with 'metadata' (YAML) and 'body' (markdown)
    """
    if doc_type not in config.DOCUMENT_TYPES:
        raise ValueError(f"Unknown document type: {doc_type}")
    
    template_dir = config.DOCUMENT_TYPES[doc_type].get('template_dir')
    if not template_dir:
        raise ValueError(f"No template_dir configured for {doc_type}")
    
    template_path = os.path.join(config.CONTENT_LIBRARY_PATH, template_dir)
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template directory not found: {template_path}")
    
    templates = []
    
    # Recursively find all .md files in template directory
    for root, dirs, files in os.walk(template_path):
        for file in files:
            if file.endswith('.md') and not file.startswith('_'):
                file_path = os.path.join(root, file)
                template = load_single_template(file_path)
                if template:
                    templates.append(template)
    
    if not templates:
        raise ValueError(f"No templates found for {doc_type} in {template_path}")
    
    # print(f"    Loaded {len(templates)} template(s) for {doc_type}")
    return templates

def load_single_template(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load and parse a single template file with YAML front matter.
    
    Args:
        file_path: Path to template markdown file
    
    Returns:
        Dict with 'metadata', 'body', and 'file_path' or None if parsing fails
    """
    try:
        # Skip partials directory - these are loaded separately
        if '_partials' in file_path:
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse YAML front matter and markdown body
        # Expected format: ---\nYAML\n---\nMarkdown
        parts = content.split('---', 2)
        
        if len(parts) < 3:
            # Not an error - partials don't have front matter
            return None
        
        # Parse YAML metadata
        metadata = yaml.safe_load(parts[1])
        
        if metadata is None:
            return None
        
        # Get markdown body (strip leading/trailing whitespace)
        body = parts[2].strip()
        
        # Validate required metadata fields
        required_fields = ['doc_type', 'linkage_level', 'word_count_target']
        missing_fields = [f for f in required_fields if f not in metadata]
        
        if missing_fields:
            print(f"   WARNING:  Template {file_path} missing required fields: {missing_fields}")
            return None
        
        return {
            'metadata': metadata,
            'body': body,
            'file_path': file_path
        }
        
    except Exception as e:
        # Silently skip files that don't parse (partials, etc.)
        return None

def load_sub_template(partial_name: str, base_template_path: str) -> str:
    """
    Load a sub-template partial (for market data partials).
    
    Args:
        partial_name: Name of partial (e.g., 'equity_markets')
        base_template_path: Path to main template for resolving relative paths
    
    Returns:
        Partial markdown content
    """
    # Construct path to partial
    template_dir = os.path.dirname(base_template_path)
    partial_path = os.path.join(template_dir, '_partials', f'{partial_name}.md')
    
    if not os.path.exists(partial_path):
        raise FileNotFoundError(f"Partial not found: {partial_path}")
    
    with open(partial_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

# ============================================================================
# MODULE: Variant Picker
# ============================================================================

def select_template(templates: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministically select template variant based on entity and context.
    
    Args:
        templates: List of available templates
        context: Entity context with SecurityID, sector, etc.
    
    Returns:
        Selected template dict
    """
    if not templates:
        raise ValueError("No templates provided for selection")
    
    # If only one template, return it
    if len(templates) == 1:
        return templates[0]
    
    # Get entity ID for deterministic selection
    entity_id = context.get('SECURITY_ID') or context.get('ISSUER_ID') or context.get('PORTFOLIO_ID') or 0
    doc_type = context.get('_doc_type', 'unknown')
    
    # Sector-aware routing: map SIC description to GICS sector for template matching
    entity_sector = context.get('SIC_DESCRIPTION', '')
    
    # Map SIC descriptions to GICS sectors for template matching
    gics_sector = map_sic_to_gics(entity_sector)
    
    # Filter templates matching entity sector (check both SIC description and mapped GICS sector)
    sector_matched = [
        t for t in templates 
        if any([
            entity_sector in t['metadata'].get('sector_tags', []),
            gics_sector in t['metadata'].get('sector_tags', [])
        ])
    ]
    
    # Use sector-matched templates if available, otherwise use all templates
    candidate_templates = sector_matched if sector_matched else templates
    
    # Deterministic selection using hash
    template_index = hash(f"{entity_id}:{doc_type}:{config.RNG_SEED}") % len(candidate_templates)
    selected = candidate_templates[template_index]
    
    return selected

def map_sic_to_gics(sic_description: str) -> str:
    """
    Map SIC industry description to GICS sector for template matching.
    Uses centralized mapping from config.SIC_TO_GICS_MAPPING.
    
    Args:
        sic_description: SIC industry description from DIM_ISSUER
    
    Returns:
        GICS sector name
    """
    sic_lower = sic_description.lower()
    
    # Check each GICS sector's keywords from config
    for gics_sector, keywords in config.SIC_TO_GICS_MAPPING.items():
        if any(keyword in sic_lower for keyword in keywords):
            return gics_sector
    
    # Default to empty if no match
    return ''

def select_portfolio_review_variant(templates: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Select portfolio review variant based on performance metrics.
    
    Args:
        templates: List of portfolio review templates
        context: Portfolio context with QTD_RETURN_PCT
    
    Returns:
        Selected template based on performance
    """
    qtd_return = context.get('QTD_RETURN_PCT', 0)
    benchmark_return = context.get('BENCHMARK_QTD_PCT', 0)
    
    # Determine performance category
    if abs(qtd_return - benchmark_return) < 1.0:
        # Mixed/neutral performance
        variant_id = 'mixed'
    elif qtd_return > benchmark_return:
        # Positive performance
        variant_id = 'positive'
    else:
        # Negative performance
        variant_id = 'negative'
    
    # Find template matching variant
    for template in templates:
        template_variant = template['metadata'].get('variant_id', '')
        if variant_id in template_variant:
            return template
    
    # Fallback to first template if no match
    return templates[0]

# ============================================================================
# MODULE: Context Builder
# ============================================================================

def build_security_context(session: Session, security_id: int, doc_type: str) -> Dict[str, Any]:
    """
    Build context for security-level documents.
    
    Args:
        session: Snowpark session
        security_id: SecurityID from DIM_SECURITY
        doc_type: Document type for context enrichment
    
    Returns:
        Context dict with all required placeholders
    """
    # Query security and issuer data (including CIK for fiscal calendar lookup)
    security_data = session.sql(f"""
        SELECT 
            ds.SecurityID,
            ds.Ticker,
            ds.Description as COMPANY_NAME,
            ds.AssetClass,
            di.IssuerID,
            di.LegalName as ISSUER_NAME,
            di.SIC_DESCRIPTION,
            di.CountryOfIncorporation,
            di.CIK
        FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY ds
        JOIN {config.DATABASE['name']}.CURATED.DIM_ISSUER di ON ds.IssuerID = di.IssuerID
        WHERE ds.SecurityID = {security_id}
    """).collect()
    
    if not security_data:
        raise ValueError(f"Security {security_id} not found in DIM_SECURITY")
    
    sec = security_data[0]
    
    # Build base context
    context = {
        '_doc_type': doc_type,
        'SECURITY_ID': sec['SECURITYID'],
        'ISSUER_ID': sec['ISSUERID'],
        'COMPANY_NAME': sec['COMPANY_NAME'],
        'TICKER': sec['TICKER'],
        'SIC_DESCRIPTION': sec['SIC_DESCRIPTION'],
        'ISSUER_NAME': sec['ISSUER_NAME'],
        'ASSET_CLASS': sec['ASSETCLASS'],
        'CIK': sec['CIK']  # Include CIK for fiscal calendar lookup
    }
    
    # Add dates (pass context and session for fiscal calendar lookup)
    context.update(generate_dates_for_doc_type(doc_type, context=context, session=session))
    
    # Add provider/attribution fields
    context.update(generate_provider_context(context, doc_type))
    
    # Add Tier 1 numerics
    context.update(generate_tier1_numerics(context, doc_type))
    
    return context

def build_portfolio_context(session: Session, portfolio_id: int, doc_type: str) -> Dict[str, Any]:
    """
    Build context for portfolio-level documents with Tier 2 derived metrics.
    
    Args:
        session: Snowpark session
        portfolio_id: PortfolioID from DIM_PORTFOLIO
        doc_type: Document type
    
    Returns:
        Context dict with portfolio data and derived metrics
    """
    # Query portfolio metadata
    portfolio_data = session.sql(f"""
        SELECT 
            PortfolioID,
            PortfolioName,
            Strategy,
            BaseCurrency,
            InceptionDate
        FROM {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO
        WHERE PortfolioID = {portfolio_id}
    """).collect()
    
    if not portfolio_data:
        raise ValueError(f"Portfolio {portfolio_id} not found")
    
    port = portfolio_data[0]
    
    # Build base context
    context = {
        '_doc_type': doc_type,
        'PORTFOLIO_ID': port['PORTFOLIOID'],
        'PORTFOLIO_NAME': port['PORTFOLIONAME'],
        'STRATEGY': port['STRATEGY'],
        'BASE_CURRENCY': port['BASECURRENCY'],
        'INCEPTION_DATE': str(port['INCEPTIONDATE'])
    }
    
    # Add dates
    context.update(generate_dates_for_doc_type(doc_type))
    
    # Add Tier 2 derived metrics for portfolio reviews
    if doc_type == 'portfolio_review' and config.NUMERIC_TIER_BY_DOC_TYPE.get(doc_type) == 'tier2':
        context.update(query_tier2_portfolio_metrics(session, portfolio_id))
    
    # Add Tier 1 numerics for performance data
    context.update(generate_tier1_numerics(context, doc_type))
    
    return context

def build_issuer_context(session: Session, issuer_id: int, doc_type: str) -> Dict[str, Any]:
    """
    Build context for issuer-level documents (NGO reports, engagement notes).
    
    Args:
        session: Snowpark session
        issuer_id: IssuerID from DIM_ISSUER
        doc_type: Document type
    
    Returns:
        Context dict with issuer data
    """
    # Query issuer data and get a representative ticker (including CIK)
    issuer_data = session.sql(f"""
        SELECT 
            di.IssuerID,
            di.LegalName as ISSUER_NAME,
            di.SIC_DESCRIPTION,
            di.CountryOfIncorporation,
            di.CIK,
            ds.Ticker
        FROM {config.DATABASE['name']}.CURATED.DIM_ISSUER di
        LEFT JOIN {config.DATABASE['name']}.CURATED.DIM_SECURITY ds ON di.IssuerID = ds.IssuerID
        WHERE di.IssuerID = {issuer_id}
        LIMIT 1
    """).collect()
    
    if not issuer_data:
        raise ValueError(f"Issuer {issuer_id} not found")
    
    iss = issuer_data[0]
    
    context = {
        '_doc_type': doc_type,
        'ISSUER_ID': iss['ISSUERID'],
        'ISSUER_NAME': iss['ISSUER_NAME'],
        'TICKER': iss['TICKER'] or 'N/A',
        'SIC_DESCRIPTION': iss['SIC_DESCRIPTION'],
        'CIK': iss['CIK']  # Include CIK for fiscal calendar lookup
    }
    
    # Add dates (pass context and session for fiscal calendar lookup)
    context.update(generate_dates_for_doc_type(doc_type, context=context, session=session))
    
    # Add NGO/meeting type context
    context.update(generate_provider_context(context, doc_type))
    
    return context

def build_global_context(doc_type: str, doc_num: int = 0) -> Dict[str, Any]:
    """
    Build context for global documents (no entity linkage).
    
    Args:
        doc_type: Document type
        doc_num: Document number for multiple global documents
    
    Returns:
        Context dict for global document
    """
    context = {
        '_doc_type': doc_type,
        '_doc_num': doc_num
    }
    
    # Add dates
    context.update(generate_dates_for_doc_type(doc_type))
    
    # Add market data regime for market_data documents
    if doc_type == 'market_data':
        context['_regime'] = select_market_regime()
    
    # Add Tier 1 numerics for market data
    if doc_type == 'market_data':
        context.update(generate_tier1_numerics(context, doc_type))
    
    return context

# ============================================================================
# MODULE: Fiscal Calendar Lookup
# ============================================================================

def get_fiscal_calendar_dates(session: Session, cik: str, num_periods: int = 4) -> List[Dict[str, Any]]:
    """
    Query SEC fiscal calendar for recent fiscal periods.
    
    Args:
        session: Snowpark session
        cik: Central Index Key for the company
        num_periods: Number of recent periods to return (default 4 for last 4 quarters)
    
    Returns:
        List of dicts with FISCAL_PERIOD, FISCAL_YEAR, PERIOD_END_DATE, PERIOD_START_DATE
        Ordered by most recent first
    """
    if not cik:
        return []
    
    try:
        fiscal_data = session.sql(f"""
            SELECT 
                CIK,
                COMPANY_NAME,
                FISCAL_PERIOD,
                FISCAL_YEAR,
                PERIOD_END_DATE,
                PERIOD_START_DATE,
                DAYS_IN_PERIOD
            FROM {config.SECURITIES['sec_filings_database']}.{config.SECURITIES['sec_filings_schema']}.SEC_FISCAL_CALENDARS
            WHERE CIK = '{cik}'
                AND FISCAL_PERIOD IN ('Q1', 'Q2', 'Q3', 'Q4')  -- Only quarterly data
                AND PERIOD_END_DATE IS NOT NULL
            ORDER BY PERIOD_END_DATE DESC
            LIMIT {num_periods}
        """).collect()
        
        if not fiscal_data:
            return []
        
        return [
            {
                'FISCAL_PERIOD': row['FISCAL_PERIOD'],
                'FISCAL_YEAR': row['FISCAL_YEAR'],
                'PERIOD_END_DATE': row['PERIOD_END_DATE'],
                'PERIOD_START_DATE': row['PERIOD_START_DATE'],
                'COMPANY_NAME': row['COMPANY_NAME']
            }
            for row in fiscal_data
        ]
    except Exception as e:
        # If SEC_FISCAL_CALENDARS is not accessible, return empty list
        # This allows fallback to synthetic date generation
        return []

# ============================================================================
# MODULE: Date Generation
# ============================================================================

def generate_dates_for_doc_type(doc_type: str, context: Optional[Dict[str, Any]] = None, session: Optional[Session] = None) -> Dict[str, str]:
    """
    Generate appropriate dates based on document type.
    Uses fiscal calendar data when available for earnings_transcripts and broker_research.
    
    Args:
        doc_type: Document type
        context: Optional context dict containing CIK for fiscal calendar lookup
        session: Optional Snowpark session for fiscal calendar queries
    
    Returns:
        Dict with date placeholders
    """
    current_date = datetime.now()
    
    dates = {}
    
    # Try to use fiscal calendar for earnings-related documents
    fiscal_periods = []
    if doc_type in ['earnings_transcripts', 'broker_research'] and context and session:
        cik = context.get('CIK')
        if cik:
            fiscal_periods = get_fiscal_calendar_dates(session, cik, num_periods=4)
    
    if doc_type in ['broker_research', 'internal_research', 'press_releases', 'investment_memo']:
        # If we have fiscal calendar data and this is broker research, align with most recent earnings
        if doc_type == 'broker_research' and fiscal_periods:
            # Pick a recent fiscal period (0-2 quarters back for more recent research)
            period_idx = random.randint(0, min(2, len(fiscal_periods) - 1))
            fiscal_period = fiscal_periods[period_idx]
            
            # Broker research typically published 7-45 days after earnings release
            # Earnings call is typically 14-30 days after period end
            period_end = fiscal_period['PERIOD_END_DATE']
            days_after_period_end = random.randint(21, 75)  # 3 weeks to 2.5 months after quarter end
            publish_date = period_end + timedelta(days=days_after_period_end)
            
            dates['PUBLISH_DATE'] = publish_date.strftime('%d %B %Y')
            dates['FISCAL_QUARTER'] = fiscal_period['FISCAL_PERIOD']
            dates['FISCAL_YEAR'] = str(fiscal_period['FISCAL_YEAR'])
        else:
            # Fallback: Recent dates within last 90 days
            offset_days = random.randint(1, 90)
            publish_date = current_date - timedelta(days=offset_days)
            dates['PUBLISH_DATE'] = publish_date.strftime('%d %B %Y')
    
    elif doc_type == 'earnings_transcripts':
        # Use fiscal calendar if available, otherwise fall back to synthetic dates
        if fiscal_periods:
            # Pick one of the recent fiscal periods (0-3 quarters back)
            period_idx = random.randint(0, len(fiscal_periods) - 1)
            fiscal_period = fiscal_periods[period_idx]
            
            # Earnings calls typically happen 14-30 days after period end
            period_end = fiscal_period['PERIOD_END_DATE']
            days_after_period_end = random.randint(14, 30)
            publish_date = period_end + timedelta(days=days_after_period_end)
            
            dates['FISCAL_QUARTER'] = fiscal_period['FISCAL_PERIOD']
            dates['FISCAL_YEAR'] = str(fiscal_period['FISCAL_YEAR'])
            dates['PUBLISH_DATE'] = publish_date.strftime('%d %B %Y')
            
            # Extract quarter number from fiscal period (e.g., 'Q3' -> 3)
            quarter_num = int(fiscal_period['FISCAL_PERIOD'][1])
            fiscal_year = fiscal_period['FISCAL_YEAR']
        else:
            # Fallback: Quarterly earnings dates using synthetic generation
            quarters_back = random.randint(0, 3)
            quarter_date = current_date - timedelta(days=90 * quarters_back)
            quarter_num = ((quarter_date.month - 1) // 3) + 1
            fiscal_year = quarter_date.year
            
            dates['FISCAL_QUARTER'] = f'Q{quarter_num} {fiscal_year}'
            dates['FISCAL_YEAR'] = str(fiscal_year)
            dates['PUBLISH_DATE'] = (quarter_date + timedelta(days=random.randint(14, 28))).strftime('%d %B %Y')
        
        # Add common earnings placeholders
        dates['QUARTER_NUM'] = str(quarter_num)
        dates['NEXT_QUARTER'] = str((quarter_num % 4) + 1)
        dates['FILING_QUARTER'] = f'Q{(quarter_num % 4) + 1}'
        dates['NEXT_YEAR'] = str(fiscal_year + 1)
        dates['CLOSE_QUARTER'] = f'Q{(quarter_num % 4) + 1}'
        dates['CLOSE_YEAR'] = str(fiscal_year + 1)
        dates['LAUNCH_QUARTER'] = f'Q{(quarter_num + 1) % 4 + 1}'
        dates['LAUNCH_YEAR'] = str(fiscal_year + 1)
    
    elif doc_type in ['ngo_reports', 'engagement_notes']:
        # ESG documents within last 180 days
        offset_days = random.randint(1, 180)
        publish_date = current_date - timedelta(days=offset_days)
        dates['PUBLISH_DATE'] = publish_date.strftime('%d %B %Y')
    
    elif doc_type == 'portfolio_review':
        # Quarterly review dates
        # Most recent quarter end
        if current_date.month <= 3:
            quarter = 'Q4'
            year = current_date.year - 1
        elif current_date.month <= 6:
            quarter = 'Q1'
            year = current_date.year
        elif current_date.month <= 9:
            quarter = 'Q2'
            year = current_date.year
        else:
            quarter = 'Q3'
            year = current_date.year
        
        dates['FISCAL_QUARTER'] = f'{quarter} {year}'
        dates['REPORT_DATE'] = current_date.strftime('%d %B %Y')
    
    elif doc_type == 'market_data':
        # Daily report
        dates['REPORT_DATE'] = current_date.strftime('%A, %d %B %Y')
    
    elif doc_type in ['sales_templates', 'philosophy_docs', 'policy_docs']:
        # Template documents - use current date as template creation/update date
        dates['TEMPLATE_DATE'] = current_date.strftime('%d %B %Y')
        dates['PUBLISH_DATE'] = current_date.strftime('%d %B %Y')
    
    else:
        # Default publish date
        dates['PUBLISH_DATE'] = current_date.strftime('%d %B %Y')
    
    return dates

# ============================================================================
# MODULE: Provider and Attribution Context
# ============================================================================

def generate_provider_context(context: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
    """
    Generate provider names, ratings, severity levels, etc.
    
    Args:
        context: Existing context
        doc_type: Document type
    
    Returns:
        Dict with provider/attribution placeholders
    """
    provider_context = {}
    entity_id = context.get('SECURITY_ID') or context.get('ISSUER_ID') or context.get('PORTFOLIO_ID') or 0
    
    if doc_type in ['broker_research', 'internal_research', 'investment_memo']:
        # Select fictional broker
        broker_index = hash(f"{entity_id}:broker:{config.RNG_SEED}") % len(config.FICTIONAL_BROKER_NAMES)
        provider_context['BROKER_NAME'] = config.FICTIONAL_BROKER_NAMES[broker_index]
        
        # Generate analyst name
        analyst_id = (hash(f"{entity_id}:analyst:{config.RNG_SEED}") % 100) + 1
        provider_context['ANALYST_NAME'] = f'Analyst_{analyst_id:02d}'
        
        # Select rating from distribution
        provider_context['RATING'] = select_from_distribution('rating')
        
        # Add portfolio name for investment memos
        if doc_type == 'investment_memo':
            provider_context['PORTFOLIO_NAME'] = config.DEFAULT_DEMO_PORTFOLIO
    
    elif doc_type == 'ngo_reports':
        # Determine ESG category (from template or random)
        category = context.get('_category', random.choice(['environmental', 'social', 'governance']))
        
        # Select NGO from appropriate category
        category_ngos = config.FICTIONAL_NGO_NAMES.get(category, config.FICTIONAL_NGO_NAMES['environmental'])
        ngo_index = hash(f"{entity_id}:ngo:{category}:{config.RNG_SEED}") % len(category_ngos)
        provider_context['NGO_NAME'] = category_ngos[ngo_index]
        
        # Select severity level
        provider_context['SEVERITY_LEVEL'] = select_from_distribution('severity_level')
        
        # Add environmental metrics
        provider_context['EMISSIONS_INCREASE'] = str(random.randint(5, 25))
        provider_context['EMISSIONS_REDUCTION'] = str(random.randint(5, 20))
        provider_context['CARBON_NEUTRAL_STATUS'] = random.choice(['carbon neutrality in Scope 1 and 2 emissions', 'working toward carbon neutrality', 'committed to net-zero by 2030'])
        
        # Add governance metrics
        provider_context['BOARD_SIZE'] = str(random.randint(8, 15))
        provider_context['INDEPENDENT_COUNT'] = str(random.randint(5, 12))
        provider_context['INDEPENDENCE_PCT'] = str(random.randint(60, 85))
        provider_context['GENDER_DIVERSITY_PCT'] = str(random.randint(20, 45))
        provider_context['FEMALE_DIRECTORS'] = str(random.randint(2, 6))
        provider_context['SECTOR_MEDIAN'] = str(random.randint(25, 40))
        provider_context['AVERAGE_TENURE'] = str(round(random.uniform(4.5, 8.5), 1))
        provider_context['NEW_DIRECTORS'] = str(random.randint(1, 3))
    
    elif doc_type == 'engagement_notes':
        # Select meeting type
        provider_context['MEETING_TYPE'] = select_from_distribution('meeting_type')
        
        # Add ESG engagement metrics
        provider_context['EMISSIONS_REDUCTION'] = str(random.randint(5, 20))
        provider_context['RENEWABLE_PCT'] = str(random.randint(30, 75))
        provider_context['RENEWABLE_TARGET'] = str(random.randint(80, 100))
        provider_context['DIVERSITY_METRIC'] = str(random.randint(3, 12))
        provider_context['ENGAGEMENT_INCREASE'] = str(random.randint(2, 8))
        provider_context['SUPPLIER_COVERAGE'] = str(random.randint(65, 85))
        provider_context['SUPPLIER_ISSUES'] = str(random.randint(3, 15))
        provider_context['CERT_QUARTER'] = f'Q{random.randint(1, 4)}'
        provider_context['NEXT_QUARTER'] = f'Q{random.randint(1, 4)}'
        provider_context['NEXT_YEAR'] = str(datetime.now().year + 1)
    
    elif doc_type == 'earnings_transcripts':
        # Generate realistic executive names deterministically from config
        ceo_first_names = config.EXECUTIVE_NAMES['ceo']['first_names']
        ceo_last_names = config.EXECUTIVE_NAMES['ceo']['last_names']
        cfo_first_names = config.EXECUTIVE_NAMES['cfo']['first_names']
        cfo_last_names = config.EXECUTIVE_NAMES['cfo']['last_names']
        
        ceo_first_index = hash(f"{entity_id}:ceo_first:{config.RNG_SEED}") % len(ceo_first_names)
        ceo_last_index = hash(f"{entity_id}:ceo_last:{config.RNG_SEED}") % len(ceo_last_names)
        provider_context['CEO_NAME'] = f'{ceo_first_names[ceo_first_index]} {ceo_last_names[ceo_last_index]}'
        
        cfo_first_index = hash(f"{entity_id}:cfo_first:{config.RNG_SEED}") % len(cfo_first_names)
        cfo_last_index = hash(f"{entity_id}:cfo_last:{config.RNG_SEED}") % len(cfo_last_names)
        provider_context['CFO_NAME'] = f'{cfo_first_names[cfo_first_index]} {cfo_last_names[cfo_last_index]}'
        
        # Add quarter-specific context
        quarter_num = int(context.get('FISCAL_QUARTER', 'Q1 2024')[1])
        provider_context['QUARTER_NUM'] = str(quarter_num)
        provider_context['NEXT_Q'] = str((quarter_num % 4) + 1)
    
    elif doc_type == 'press_releases':
        # Add common press release fields
        cities = ['New York', 'San Francisco', 'Boston', 'Seattle', 'London', 'Frankfurt']
        city_index = hash(f"{entity_id}:city:{config.RNG_SEED}") % len(cities)
        provider_context['CITY'] = cities[city_index]
        
        # Generate executive name deterministically
        ceo_id = hash(f"{entity_id}:ceo:{config.RNG_SEED}") % 100
        provider_context['CEO_NAME'] = f'CEO_{ceo_id:02d}'
        
        cfo_id = hash(f"{entity_id}:cfo:{config.RNG_SEED}") % 100
        provider_context['CFO_NAME'] = f'CFO_{cfo_id:02d}'
        
        # Acquisition-specific
        provider_context['TARGET_COMPANY'] = 'Digital Solutions Inc.'
        provider_context['NEXT_YEAR'] = str(datetime.now().year + 1)
        
        # Earnings press release placeholders
        quarter_date = datetime.now() - timedelta(days=random.randint(0, 90))
        quarter_end = quarter_date.replace(day=1) + timedelta(days=32)
        quarter_end = quarter_end.replace(day=1) - timedelta(days=1)
        provider_context['QUARTER_END_DATE'] = quarter_end.strftime('%d %B %Y')
        provider_context['GUIDANCE_LOW'] = str(round(random.uniform(10, 50), 1))
        provider_context['GUIDANCE_HIGH'] = str(round(random.uniform(12, 55), 1))
        provider_context['GUIDANCE_GROWTH'] = str(round(random.uniform(10, 25), 0))
        
        # Healthcare press release specific
        drug_names = ['InnovaRx', 'BioAdvance', 'TherapX', 'MediCure', 'HealthPlus']
        drug_index = hash(f"{entity_id}:drug:{config.RNG_SEED}") % len(drug_names)
        provider_context['DRUG_NAME'] = drug_names[drug_index]
        
        indications = ['Type 2 Diabetes', 'Cardiovascular Disease', 'Oncology', 'Immunology']
        indication_index = hash(f"{entity_id}:indication:{config.RNG_SEED}") % len(indications)
        provider_context['INDICATION'] = indications[indication_index]
        
        provider_context['TRIAL_PATIENTS'] = f'{random.randint(500, 3000):,}'
        provider_context['MARKET_SIZE'] = str(random.randint(5, 50))
        provider_context['PEAK_SHARE'] = str(random.randint(15, 35))
        provider_context['TARGET_PATIENTS'] = str(random.randint(1, 10))
        
        # FDA approval specific
        provider_context['EFFICACY_METRIC'] = str(random.randint(20, 60))
        provider_context['TRIAL_NAME'] = 'ADVANCE'
        provider_context['PRIMARY_ENDPOINT'] = 'HbA1c reduction'
        provider_context['SECONDARY_ENDPOINTS'] = 'weight loss and cardiovascular safety'
        provider_context['LAUNCH_QUARTER'] = f'Q{random.randint(1, 4)}'
        provider_context['LAUNCH_YEAR'] = str(datetime.now().year + 1)
        
        # Acquisition specific
        provider_context['CLOSE_QUARTER'] = f'Q{random.randint(1, 4)}'
        provider_context['CLOSE_YEAR'] = str(datetime.now().year)
        
        # Product launch placeholders  
        products = ['Cloud Platform', 'AI Suite', 'Analytics Dashboard', 'Security Solution', 'Mobile App', 'Data Platform']
        product_index = hash(f"{entity_id}:product:{config.RNG_SEED}") % len(products)
        provider_context['PRODUCT_CATEGORY'] = products[product_index]
    
    elif doc_type == 'earnings_transcripts':
        # Market condition narrative
        market_conditions = ['strong growth', 'mixed results', 'resilient performance']
        market_index = hash(f"{entity_id}:market:{config.RNG_SEED}") % len(market_conditions)
        provider_context['MARKET_CONDITION'] = market_conditions[market_index]
        
        # Get sector to generate appropriate context
        entity_sector = context.get('SIC_DESCRIPTION', '')
        
        # Healthcare-specific placeholders (only for Health Care sector)
        if 'Health Care' in entity_sector or 'Pharmaceuticals' in entity_sector or 'Medical' in entity_sector:
            # Mechanism of action (for healthcare)
            mechanisms = ['dual GLP-1/GIP receptor agonism', 'selective insulin receptor modulation', 'novel glucose regulation pathway']
            mech_index = hash(f"{entity_id}:mechanism:{config.RNG_SEED}") % len(mechanisms)
            provider_context['MECHANISM'] = mechanisms[mech_index]
            
            # Pipeline asset names
            pipeline_assets = ['Compound-247', 'BIO-553', 'TherapX-901']
            pipeline_index = hash(f"{entity_id}:pipeline:{config.RNG_SEED}") % len(pipeline_assets)
            provider_context['PIPELINE_ASSET'] = pipeline_assets[pipeline_index]
            
            # Healthcare metrics that appear in earnings calls
            provider_context['TARGET_PATIENTS'] = f'{random.randint(1, 10)}M'  # Format with M for millions
            provider_context['PEAK_SHARE'] = str(random.randint(15, 35))
            provider_context['RESPONSE_THRESHOLD'] = str(random.randint(40, 70))
            provider_context['DIABETES_MARKET'] = str(random.randint(25, 65))
            provider_context['PATENT_EXPIRY'] = str(random.randint(2028, 2035))
        
        # Generic sustainability materials (for all sectors)
        sustainability_materials = ['100% recycled', '80% renewable', '75% sustainable']
        sustain_index = hash(f"{entity_id}:sustain:{config.RNG_SEED}") % len(sustainability_materials)
        provider_context['SUSTAINABLE_MATERIAL'] = sustainability_materials[sustain_index]
    
    return provider_context

def select_from_distribution(distribution_name: str) -> str:
    """
    Select value from configured distribution.
    
    Args:
        distribution_name: Name of distribution (rating, severity_level, meeting_type)
    
    Returns:
        Selected value
    """
    # Load distributions from numeric_bounds.yaml (simplified for now)
    distributions = {
        'rating': {
            'Strong Buy': 0.10,
            'Buy': 0.25,
            'Hold': 0.45,
            'Sell': 0.15,
            'Strong Sell': 0.05
        },
        'severity_level': {
            'High': 0.20,
            'Medium': 0.40,
            'Low': 0.40
        },
        'meeting_type': {
            'Management Meeting': 0.50,
            'Shareholder Call': 0.30,
            'Site Visit': 0.20
        }
    }
    
    if distribution_name not in distributions:
        raise ValueError(f"Unknown distribution: {distribution_name}")
    
    dist = distributions[distribution_name]
    values = list(dist.keys())
    weights = list(dist.values())
    
    return random.choices(values, weights=weights)[0]

# ============================================================================
# MODULE: Numeric Rules (Tier 1)
# ============================================================================

def generate_tier1_numerics(context: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
    """
    Generate Tier 1 numeric placeholders by sampling within sector-specific bounds.
    
    Args:
        context: Existing context with sector info
        doc_type: Document type
    
    Returns:
        Dict with Tier 1 numeric placeholders
    """
    numerics = {}
    entity_id = context.get('SECURITY_ID') or context.get('PORTFOLIO_ID') or 0
    sector = context.get('SIC_DESCRIPTION', 'Information Technology')
    
    # Load numeric bounds from config (simplified - would load from YAML file in production)
    bounds = get_numeric_bounds_for_doc_type(doc_type, sector)
    
    # Sample each numeric placeholder deterministically
    for placeholder, bound_spec in bounds.items():
        seed = config.RNG_SEED + hash(str(entity_id)) + hash(doc_type) + hash(placeholder)
        random.seed(seed)
        
        min_val = bound_spec.get('min', 0)
        max_val = bound_spec.get('max', 100)
        
        # Generate value within bounds
        value = random.uniform(min_val, max_val)
        
        # Format based on placeholder type
        if 'PCT' in placeholder or 'MARGIN' in placeholder or 'GROWTH' in placeholder:
            numerics[placeholder] = round(value, 1)
        elif 'BILLIONS' in placeholder:
            numerics[placeholder] = round(value, 2)
        elif '_USD' in placeholder or 'PRICE' in placeholder or 'TARGET' in placeholder:
            numerics[placeholder] = round(value, 2)
        elif 'RATIO' in placeholder:
            numerics[placeholder] = round(value, 1)
        elif 'REVENUE' in placeholder or 'PROFIT' in placeholder or 'INCOME' in placeholder:
            numerics[placeholder] = round(value, 2)
        elif 'SPEND' in placeholder or 'OPEX' in placeholder or 'CASH' in placeholder:
            numerics[placeholder] = round(value, 2)
        elif 'AMOUNT' in placeholder or 'FLOW' in placeholder or 'BALANCE' in placeholder:
            numerics[placeholder] = round(value, 2)
        elif 'RATE' in placeholder:
            numerics[placeholder] = round(value, 1)
        else:
            numerics[placeholder] = round(value, 2)
    
    return numerics

def get_numeric_bounds_for_doc_type(doc_type: str, sector: str) -> Dict[str, Dict[str, float]]:
    """
    Get numeric bounds for document type and sector.
    
    This is a simplified version - production would load from numeric_bounds.yaml
    
    Args:
        doc_type: Document type
        sector: GICS sector
    
    Returns:
        Dict mapping placeholder names to {min, max} bounds
    """
    # Simplified bounds (production would load from YAML)
    bounds_map = {
        'broker_research': {
            'Information Technology': {
                'YOY_REVENUE_GROWTH_PCT': {'min': 8, 'max': 25},
                'EBIT_MARGIN_PCT': {'min': 12, 'max': 28},
                'PRICE_TARGET_USD': {'min': 80, 'max': 450},
                'PE_RATIO': {'min': 15, 'max': 35},
                'GROSS_MARGIN_PCT': {'min': 50, 'max': 70}
            },
            'Health Care': {
                'YOY_REVENUE_GROWTH_PCT': {'min': 5, 'max': 18},
                'EBIT_MARGIN_PCT': {'min': 15, 'max': 35},
                'PRICE_TARGET_USD': {'min': 60, 'max': 350},
                'PE_RATIO': {'min': 18, 'max': 40},
                'GROSS_MARGIN_PCT': {'min': 60, 'max': 80}
            },
            'Financials': {
                'YOY_REVENUE_GROWTH_PCT': {'min': 3, 'max': 15},
                'EBIT_MARGIN_PCT': {'min': 20, 'max': 40},
                'PRICE_TARGET_USD': {'min': 50, 'max': 300},
                'PE_RATIO': {'min': 8, 'max': 18},
                'ROE_PCT': {'min': 10, 'max': 25}
            },
            'Consumer Discretionary': {
                'YOY_REVENUE_GROWTH_PCT': {'min': 4, 'max': 20},
                'EBIT_MARGIN_PCT': {'min': 8, 'max': 18},
                'PRICE_TARGET_USD': {'min': 40, 'max': 400},
                'PE_RATIO': {'min': 12, 'max': 30}
            },
            'Communication Services': {
                'YOY_REVENUE_GROWTH_PCT': {'min': 5, 'max': 22},
                'EBIT_MARGIN_PCT': {'min': 10, 'max': 30},
                'PRICE_TARGET_USD': {'min': 45, 'max': 350},
                'PE_RATIO': {'min': 12, 'max': 28},
                'REVENUE_BILLIONS': {'min': 10, 'max': 200}
            },
            # Default bounds for sectors not explicitly listed
            '_default': {
                'YOY_REVENUE_GROWTH_PCT': {'min': 3, 'max': 20},
                'EBIT_MARGIN_PCT': {'min': 10, 'max': 30},
                'PRICE_TARGET_USD': {'min': 50, 'max': 350},
                'PE_RATIO': {'min': 12, 'max': 28},
                'REVENUE_BILLIONS': {'min': 5, 'max': 150},
                'GROSS_MARGIN_PCT': {'min': 30, 'max': 60},
                'EBIT_MARGIN_PCT_UPPER': {'min': 15, 'max': 35},
                'UPSIDE_POTENTIAL': {'min': 15, 'max': 45},
                'ROE_PCT': {'min': 10, 'max': 25},
                # Add all sector-specific placeholders to default so they work regardless of sector
                'MARKET_SHARE': {'min': 15, 'max': 45},
                'CARDIO_GROWTH': {'min': 8, 'max': 25},
                'SEQUENTIAL_GROWTH': {'min': 2, 'max': 12},
                'ONCOLOGY_REVENUE': {'min': 2, 'max': 15},
                'ONCOLOGY_GROWTH': {'min': 10, 'max': 30},
                'DIGITAL_GROWTH': {'min': 15, 'max': 40},
                'DIGITAL_PCT': {'min': 20, 'max': 45},
                'NEW_PRODUCTS': {'min': 5, 'max': 25},
                'PRODUCT_CATEGORY': {'min': 1, 'max': 5},
                'BRAND_AWARENESS': {'min': 2, 'max': 8}
            }
        },
        'internal_research': {
            'Information Technology': {
                'YOY_REVENUE_GROWTH_PCT': {'min': 8, 'max': 25},
                'EBIT_MARGIN_PCT': {'min': 12, 'max': 28},
                'TARGET_PRICE_USD': {'min': 80, 'max': 450},
                'FAIR_VALUE_USD': {'min': 75, 'max': 500},
                'UPSIDE_POTENTIAL_PCT': {'min': 10, 'max': 60},
                'PE_RATIO': {'min': 15, 'max': 35}
            }
        },
        'investment_memo': {
            'Information Technology': {
                'YOY_REVENUE_GROWTH_PCT': {'min': 8, 'max': 25},
                'EBIT_MARGIN_PCT': {'min': 12, 'max': 28},
                'TARGET_PRICE_USD': {'min': 80, 'max': 450},
                'PE_RATIO': {'min': 15, 'max': 35},
                'POSITION_SIZE_PCT': {'min': 2, 'max': 7}
            }
        },
        'portfolio_review': {
            'returns': {
                'QTD_RETURN_PCT': {'min': -8, 'max': 12},
                'YTD_RETURN_PCT': {'min': -15, 'max': 20},
                'BENCHMARK_QTD_PCT': {'min': -7, 'max': 10},
                'BENCHMARK_YTD_PCT': {'min': -12, 'max': 18},
                'TRACKING_ERROR_PCT': {'min': 2, 'max': 8}
            }
        },
        'earnings_transcripts': {
            'Information Technology': {
                'QUARTERLY_REVENUE_BILLIONS': {'min': 10, 'max': 60},
                'QUARTERLY_EPS': {'min': 1.0, 'max': 5.0},
                'YOY_GROWTH_PCT': {'min': 8, 'max': 25},
                'OPERATING_MARGIN_PCT': {'min': 20, 'max': 40},
                'CLOUD_GROWTH': {'min': 20, 'max': 45},
                'INTERNATIONAL_GROWTH': {'min': 15, 'max': 35},
                'SOFTWARE_GROWTH': {'min': 12, 'max': 28},
                'SERVICES_GROWTH': {'min': 8, 'max': 20},
                'NET_RETENTION': {'min': 110, 'max': 130},
                'INTL_GROWTH': {'min': 15, 'max': 35},
                'SUBSCRIPTION_REVENUE': {'min': 5, 'max': 50},
                'CLOUD_REVENUE': {'min': 8, 'max': 45},
                'CLOUD_PERCENTAGE': {'min': 35, 'max': 60},
                'CLOUD_MARGIN': {'min': 55, 'max': 75},
                'SOFTWARE_REVENUE': {'min': 3, 'max': 25},
                'SERVICES_REVENUE': {'min': 2, 'max': 15},
                'SUBSCRIPTION_GROWTH': {'min': 15, 'max': 35},
                'SUBSCRIPTION_PCT': {'min': 65, 'max': 85},
                'US_REVENUE': {'min': 6, 'max': 35},
                'US_GROWTH': {'min': 10, 'max': 25},
                'INTL_REVENUE': {'min': 4, 'max': 25},
                'INTL_PCT': {'min': 25, 'max': 45},
                'GROSS_PROFIT': {'min': 5, 'max': 35},
                'GROSS_MARGIN_PCT': {'min': 55, 'max': 75},
                'OPEX': {'min': 3, 'max': 20},
                'OPEX_GROWTH': {'min': 8, 'max': 20},
                'NET_INCOME': {'min': 2, 'max': 15},
                'EPS_GROWTH': {'min': 10, 'max': 30},
                'TAX_RATE': {'min': 18, 'max': 25},
                'INTL_CONSTANT_GROWTH': {'min': 12, 'max': 30},
                'INTL_PRIOR_PCT': {'min': 20, 'max': 40},
                'RD_SPEND': {'min': 2, 'max': 12},
                'RD_PCT': {'min': 12, 'max': 22},
                'SALES_SPEND': {'min': 2, 'max': 15},
                'SALES_PCT': {'min': 15, 'max': 30},
                'OPERATING_INCOME': {'min': 3, 'max': 18},
                'CASH_BALANCE': {'min': 10, 'max': 80},
                'OPERATING_CASH_FLOW': {'min': 4, 'max': 20},
                'FREE_CASH_FLOW': {'min': 3, 'max': 18},
                'BUYBACK_AMOUNT': {'min': 1, 'max': 8},
                'DIVIDEND_AMOUNT': {'min': 50, 'max': 500},
                'GUIDANCE_REVENUE_LOW': {'min': 10, 'max': 55},
                'GUIDANCE_REVENUE_HIGH': {'min': 12, 'max': 60},
                'GUIDANCE_GROWTH_LOW': {'min': 8, 'max': 20},
                'GUIDANCE_GROWTH_HIGH': {'min': 10, 'max': 25},
                'GUIDANCE_OPMARGIN': {'min': 25, 'max': 38},
                'FULL_YEAR_GROWTH_LOW': {'min': 12, 'max': 22},
                'FULL_YEAR_GROWTH_HIGH': {'min': 15, 'max': 28},
                'FULL_YEAR_MARGIN': {'min': 28, 'max': 38},
                'Q_NEXT_LOW': {'min': 12, 'max': 58},
                'Q_NEXT_HIGH': {'min': 14, 'max': 62},
                'Q_NEXT_GROWTH_LOW': {'min': 10, 'max': 22},
                'Q_NEXT_GROWTH_HIGH': {'min': 12, 'max': 28},
                'Q_NEXT_MARGIN': {'min': 25, 'max': 38},
                'FY_GROWTH_LOW': {'min': 12, 'max': 22},
                'FY_GROWTH_HIGH': {'min': 15, 'max': 28},
                'FY_MARGIN': {'min': 28, 'max': 38},
                'MARGIN_EXPANSION': {'min': 50, 'max': 150},
                'MARGIN_EXPANSION_BPS': {'min': 50, 'max': 150},
                'OCF': {'min': 4, 'max': 22},
                'FCF': {'min': 3, 'max': 20},
                'FCF_MARGIN': {'min': 20, 'max': 35},
                'CASH': {'min': 15, 'max': 90},
                'CAPITAL_RETURN': {'min': 2, 'max': 12},
                'BUYBACK': {'min': 1, 'max': 10},
                'DIVIDEND': {'min': 100, 'max': 800},
                'ACV_GROWTH': {'min': 12, 'max': 30},
                'DIV_INCREASE': {'min': 8, 'max': 15},
                'NET_RETENTION_PCT': {'min': 110, 'max': 135},
                'AI_ADOPTION_PCT': {'min': 45, 'max': 75},
                'RD_GROWTH': {'min': 10, 'max': 25},
                'ENTERPRISE_PCT': {'min': 55, 'max': 75},
                'ENTERPRISE_GROWTH': {'min': 12, 'max': 28},
                'SMB_GROWTH': {'min': 18, 'max': 35},
                'AI_REVENUE_CONTRIBUTION': {'min': 5, 'max': 20},
                'APAC_GROWTH': {'min': 18, 'max': 40},
                'FCF_CONVERSION': {'min': 75, 'max': 92},
                'DIVIDEND_INCREASE': {'min': 8, 'max': 18},
                'RD_BILLIONS': {'min': 2, 'max': 15}
            },
            'Health Care': {
                'QUARTERLY_REVENUE_BILLIONS': {'min': 5, 'max': 40},
                'QUARTERLY_EPS': {'min': 0.8, 'max': 4.0},
                'YOY_GROWTH_PCT': {'min': 5, 'max': 18},
                'OPERATING_MARGIN_PCT': {'min': 18, 'max': 38},
                'MARKET_SHARE': {'min': 15, 'max': 45},
                'CARDIO_GROWTH': {'min': 8, 'max': 25},
                'SEQUENTIAL_GROWTH': {'min': 2, 'max': 12},
                'ONCOLOGY_REVENUE': {'min': 2, 'max': 15},
                'ONCOLOGY_GROWTH': {'min': 10, 'max': 30},
                'CARDIO_REVENUE': {'min': 1, 'max': 10},
                'IMMUNO_REVENUE': {'min': 0.5, 'max': 8},
                'IMMUNO_GROWTH': {'min': 15, 'max': 40},
                'US_PCT': {'min': 40, 'max': 60},
                'EUROPE_PCT': {'min': 20, 'max': 35},
                'ROW_PCT': {'min': 10, 'max': 25},
                'GROSS_PROFIT': {'min': 3, 'max': 28},
                'GROSS_MARGIN': {'min': 60, 'max': 80},
                'SGA_SPEND': {'min': 2, 'max': 15},
                'SGA_PCT': {'min': 20, 'max': 40},
                'DEBT': {'min': 5, 'max': 35},
                'GUIDANCE_LOW': {'min': 5, 'max': 38},
                'GUIDANCE_HIGH': {'min': 6, 'max': 42},
                'EPS_LOW': {'min': 0.8, 'max': 3.8},
                'EPS_HIGH': {'min': 1.0, 'max': 4.2},
                'FY_LOW': {'min': 8, 'max': 16},
                'FY_HIGH': {'min': 10, 'max': 20}
            },
            'Consumer Discretionary': {
                'QUARTERLY_REVENUE_BILLIONS': {'min': 3, 'max': 100},
                'QUARTERLY_EPS': {'min': 0.5, 'max': 3.0},
                'YOY_GROWTH_PCT': {'min': 4, 'max': 20},
                'OPERATING_MARGIN_PCT': {'min': 8, 'max': 18},
                'DIGITAL_GROWTH': {'min': 15, 'max': 40},
                'DIGITAL_PCT': {'min': 20, 'max': 45},
                'NEW_PRODUCTS': {'min': 5, 'max': 25},
                'INTL_GROWTH': {'min': 10, 'max': 30},
                'INTL_PCT': {'min': 20, 'max': 40},
                'INTL_PRIOR_PCT': {'min': 18, 'max': 38},
                'BRAND_AWARENESS': {'min': 2, 'max': 8},
                'SENTIMENT_IMPROVEMENT': {'min': 3, 'max': 12},
                'INSTOCK_PCT': {'min': 92, 'max': 98},
                'PRODUCT_CATEGORY': {'min': 1, 'max': 5},
                'RETAIL_REVENUE': {'min': 5, 'max': 60},
                'RETAIL_GROWTH': {'min': 3, 'max': 18},
                'DTC_REVENUE': {'min': 2, 'max': 30},
                'DTC_GROWTH': {'min': 20, 'max': 50},
                'WHOLESALE_REVENUE': {'min': 3, 'max': 40},
                'WHOLESALE_GROWTH': {'min': 2, 'max': 15},
                'GROSS_PROFIT': {'min': 3, 'max': 50},
                'GROSS_MARGIN': {'min': 35, 'max': 55},
                'MARKETING': {'min': 1, 'max': 15},
                'MARKETING_PCT': {'min': 8, 'max': 20},
                'GA': {'min': 1, 'max': 10},
                'GROSS_MARGIN': {'min': 35, 'max': 55},
                'DIVIDENDS': {'min': 100, 'max': 600},
                'BUYBACKS': {'min': 500, 'max': 3000},
                'INVENTORY': {'min': 2, 'max': 15},
                'INVENTORY_DAYS': {'min': 45, 'max': 90}
            },
            # Fallback bounds that include ALL placeholders used in any template
            '_fallback': {
                # Include all possible placeholders with reasonable defaults
                'MARKET_SHARE': {'min': 15, 'max': 45},
                'CARDIO_GROWTH': {'min': 8, 'max': 25},
                'CARDIO_REVENUE': {'min': 1, 'max': 10},
                'SEQUENTIAL_GROWTH': {'min': 2, 'max': 12},
                'ONCOLOGY_REVENUE': {'min': 2, 'max': 15},
                'ONCOLOGY_GROWTH': {'min': 10, 'max': 30},
                'IMMUNO_REVENUE': {'min': 0.5, 'max': 8},
                'IMMUNO_GROWTH': {'min': 15, 'max': 40},
                'DIGITAL_GROWTH': {'min': 15, 'max': 40},
                'DIGITAL_PCT': {'min': 20, 'max': 45},
                'NEW_PRODUCTS': {'min': 5, 'max': 25},
                'PRODUCT_CATEGORY': {'min': 1, 'max': 5},
                'BRAND_AWARENESS': {'min': 2, 'max': 8},
                'SENTIMENT_IMPROVEMENT': {'min': 3, 'max': 12},
                'INSTOCK_PCT': {'min': 92, 'max': 98},
                'RETAIL_REVENUE': {'min': 5, 'max': 60},
                'RETAIL_GROWTH': {'min': 3, 'max': 18},
                'DTC_REVENUE': {'min': 2, 'max': 30},
                'DTC_GROWTH': {'min': 20, 'max': 50},
                'WHOLESALE_REVENUE': {'min': 3, 'max': 40},
                'WHOLESALE_GROWTH': {'min': 2, 'max': 15},
                'US_PCT': {'min': 40, 'max': 60},
                'EUROPE_PCT': {'min': 20, 'max': 35},
                'ROW_PCT': {'min': 10, 'max': 25},
                'GROSS_MARGIN': {'min': 35, 'max': 70},
                'SGA_SPEND': {'min': 2, 'max': 15},
                'SGA_PCT': {'min': 20, 'max': 40},
                'DEBT': {'min': 5, 'max': 35},
                'GUIDANCE_LOW': {'min': 5, 'max': 40},
                'GUIDANCE_HIGH': {'min': 6, 'max': 45},
                'MARKETING': {'min': 1, 'max': 15},
                'MARKETING_PCT': {'min': 8, 'max': 20},
                'GA': {'min': 1, 'max': 10},
                'DIVIDENDS': {'min': 100, 'max': 600},
                'BUYBACKS': {'min': 500, 'max': 3000},
                'EPS_LOW': {'min': 0.8, 'max': 3.8},
                'EPS_HIGH': {'min': 1.0, 'max': 4.2},
                'FY_LOW': {'min': 8, 'max': 16},
                'FY_HIGH': {'min': 10, 'max': 20},
                'WEIGHT_BENEFIT': {'min': 3, 'max': 8},
                'A1C_REDUCTION': {'min': 0.8, 'max': 1.8},
                'PLACEBO_A1C': {'min': 0.1, 'max': 0.4},
                'MECHANISM': {'min': 1, 'max': 3},  # Will be text
                'DIGITAL_MARGIN_PREMIUM': {'min': 5, 'max': 15},
                'DIGITAL_VS_RETAIL': {'min': 3, 'max': 12},
                'INVENTORY': {'min': 2, 'max': 15},
                'INVENTORY_DAYS': {'min': 45, 'max': 90},
                'SUSTAINABILITY_METRIC': {'min': 15, 'max': 40},
                'SUSTAINABLE_PREMIUM': {'min': 8, 'max': 18},
                'DIABETES_MARKET': {'min': 25, 'max': 65},
                'PATENT_EXPIRY': {'min': 2028, 'max': 2035},
                'PIPELINE_ASSET': {'min': 1, 'max': 3},  # Will be text
                'EROSION_PCT': {'min': 40, 'max': 70},
                'RD_ANNUAL': {'min': 3, 'max': 12},
                'TOTAL_RETURN': {'min': 1, 'max': 8},
                'RESPONSE_THRESHOLD': {'min': 40, 'max': 70},
                'SUSTAINABLE_MATERIAL': {'min': 60, 'max': 100},  # Will be text
                'TARGET_PATIENTS': {'min': 1, 'max': 10},  # Will be formatted with M
                'PEAK_SHARE': {'min': 15, 'max': 35}
            }
        },
        'press_releases': {
            'general': {
                'DEAL_VALUE_MILLIONS': {'min': 50, 'max': 5000},
                'PARTNERSHIP_VALUE_MILLIONS': {'min': 100, 'max': 3000},
                'QUARTERLY_REVENUE_BILLIONS': {'min': 5, 'max': 60},
                'YOY_GROWTH_PCT': {'min': 5, 'max': 25},
                'QUARTERLY_EPS': {'min': 0.8, 'max': 4.0},
                'CLOUD_GROWTH_PCT': {'min': 15, 'max': 40},
                'OPERATING_CASH_FLOW': {'min': 2, 'max': 20}
            }
        }
    }
    
    # Get bounds for this doc_type and sector
    if doc_type in bounds_map:
        sector_bounds = {}
        
        # Start with sector-specific bounds if available
        if sector in bounds_map[doc_type]:
            sector_bounds = bounds_map[doc_type][sector].copy()
        elif 'returns' in bounds_map[doc_type]:  # Portfolio review
            sector_bounds = bounds_map[doc_type]['returns'].copy()
        elif 'general' in bounds_map[doc_type]:  # Press releases
            sector_bounds = bounds_map[doc_type]['general'].copy()
        elif not sector_bounds:
            # Use first available sector as base
            first_sector = [k for k in bounds_map[doc_type].keys() if not k.startswith('_')][0]
            sector_bounds = bounds_map[doc_type][first_sector].copy()
        
        # Merge in default bounds for any missing placeholders
        if '_default' in bounds_map[doc_type]:
            for key, value in bounds_map[doc_type]['_default'].items():
                if key not in sector_bounds:
                    sector_bounds[key] = value
        
        # Merge in fallback bounds for any still missing
        if '_fallback' in bounds_map[doc_type]:
            for key, value in bounds_map[doc_type]['_fallback'].items():
                if key not in sector_bounds:
                    sector_bounds[key] = value
        
        return sector_bounds
    
    return {}

# ============================================================================
# MODULE: Tier 2 Derivations (Portfolio Metrics from CURATED Tables)
# ============================================================================

def query_tier2_portfolio_metrics(session: Session, portfolio_id: int) -> Dict[str, Any]:
    """
    Query actual portfolio metrics from CURATED tables (Tier 2).
    
    Args:
        session: Snowpark session
        portfolio_id: PortfolioID
    
    Returns:
        Dict with derived metrics
    """
    metrics = {}
    
    try:
        # Query top 10 holdings
        top10 = session.sql(f"""
            SELECT 
                s.Ticker,
                s.Description as COMPANY_NAME,
                p.PortfolioWeight * 100 as WEIGHT_PCT,
                p.MarketValue_Base as MARKET_VALUE_USD
            FROM {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR p
            JOIN {config.DATABASE['name']}.CURATED.DIM_SECURITY s ON p.SecurityID = s.SecurityID
            WHERE p.PortfolioID = {portfolio_id}
            AND p.HoldingDate = (SELECT MAX(HoldingDate) FROM {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR)
            ORDER BY p.MarketValue_Base DESC
            LIMIT 10
        """).collect()
        
        if top10:
            metrics['TOP10_HOLDINGS'] = top10
            metrics['TOP10_WEIGHT_PCT'] = round(sum([h['WEIGHT_PCT'] for h in top10]), 1)
            metrics['LARGEST_POSITION_NAME'] = top10[0]['COMPANY_NAME']
            metrics['LARGEST_POSITION_WEIGHT'] = round(top10[0]['WEIGHT_PCT'], 2)
            metrics['CONCENTRATION_WARNING'] = 'YES' if top10[0]['WEIGHT_PCT'] > config.COMPLIANCE_RULES['concentration']['warning_threshold'] * 100 else 'NO'
        
        # Query sector allocation
        sectors = session.sql(f"""
            SELECT 
                i.SIC_DESCRIPTION as SECTOR,
                SUM(p.PortfolioWeight) * 100 as WEIGHT_PCT
            FROM {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR p
            JOIN {config.DATABASE['name']}.CURATED.DIM_SECURITY s ON p.SecurityID = s.SecurityID
            JOIN {config.DATABASE['name']}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE p.PortfolioID = {portfolio_id}
            AND p.HoldingDate = (SELECT MAX(HoldingDate) FROM {config.DATABASE['name']}.CURATED.FACT_POSITION_DAILY_ABOR)
            GROUP BY i.SIC_DESCRIPTION
            ORDER BY WEIGHT_PCT DESC
        """).collect()
        
        if sectors:
            metrics['SECTOR_ALLOCATION_TABLE'] = sectors
    
    except Exception as e:
        print(f"   WARNING:  Tier 2 query failed for portfolio {portfolio_id}: {e}")
        # print(f"   ℹ️  Falling back to Tier 1 numerics")
        # Fallback to Tier 1 if queries fail
        pass
    
    return metrics

# ============================================================================
# MODULE: Market Regime Selection
# ============================================================================

def select_market_regime() -> str:
    """
    Select market regime based on build date (weekly rotation).
    
    Returns:
        Regime name: 'risk_on', 'risk_off', or 'mixed'
    """
    # Hash current week to select regime
    current_date = datetime.now()
    week_start = current_date - timedelta(days=current_date.weekday())
    week_hash = hash(week_start.strftime('%Y-%W'))
    
    regimes = ['risk_on', 'risk_off', 'mixed']
    regime_index = week_hash % len(regimes)
    
    return regimes[regime_index]

# ============================================================================
# MODULE: Conditional Renderer
# ============================================================================

def process_conditional_placeholders(template: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process conditional placeholders and add resolved values to context.
    
    Args:
        template: Template dict with metadata
        context: Current context dict
    
    Returns:
        Updated context with conditional placeholders resolved
    """
    conditionals = template['metadata'].get('placeholders', {}).get('conditional', [])
    
    if not conditionals:
        return context
    
    for conditional in conditionals:
        name = conditional['name']
        cond_type = conditional['type']
        condition = conditional['condition']
        options = conditional['options']
        
        # Evaluate condition
        try:
            # Simple condition evaluation (e.g., "QTD_RETURN_PCT > 0")
            condition_result = eval_condition(condition, context)
            
            # Select appropriate option
            if condition_result:
                selected_value = options.get('positive', options.get('high', ''))
            else:
                selected_value = options.get('negative', options.get('low', ''))
            
            # Add to context
            context[name] = selected_value
            
        except Exception as e:
            print(f"   WARNING:  Conditional placeholder {name} evaluation failed: {e}")
            # Use first available option as fallback
            context[name] = list(options.values())[0] if options else ''
    
    return context

def eval_condition(condition: str, context: Dict[str, Any]) -> bool:
    """
    Safely evaluate a condition expression.
    
    Args:
        condition: Condition string (e.g., "QTD_RETURN_PCT > 0")
        context: Context with values
    
    Returns:
        Boolean result of condition evaluation
    """
    # Replace placeholders in condition with actual values
    for key, value in context.items():
        if isinstance(value, (int, float)):
            condition = condition.replace(key, str(value))
    
    try:
        # Evaluate as Python expression (safe for simple numeric comparisons)
        result = eval(condition)
        return bool(result)
    except:
        # Default to False if evaluation fails
        return False

# ============================================================================
# MODULE: Renderer
# ============================================================================

def render_template(template: Dict[str, Any], context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Render template by filling all placeholders.
    
    Args:
        template: Template dict with metadata and body
        context: Context dict with all placeholder values
    
    Returns:
        Tuple of (rendered_markdown, enriched_context)
    """
    body = template['body']
    metadata = template['metadata']
    
    # Process conditional placeholders first
    context = process_conditional_placeholders(template, context)
    
    # Process sub-template includes (for market data partials)
    includes = metadata.get('placeholders', {}).get('includes', metadata.get('includes', []))
    for partial_name in includes:
        try:
            partial_content = load_sub_template(partial_name, template['file_path'])
            # Replace {{> partial_name}} with partial content
            body = body.replace(f'{{{{> {partial_name}}}}}', partial_content)
        except Exception as e:
            print(f"   WARNING:  Could not load partial {partial_name}: {e}")
    
    # Fill all {{PLACEHOLDER}} patterns
    rendered = body
    
    for key, value in context.items():
        if key.startswith('_'):
            # Skip internal context keys
            continue
        
        placeholder_pattern = f'{{{{{key}}}}}'
        
        # Convert value to string for replacement
        if isinstance(value, (list, dict)):
            # Skip complex types (tables, arrays) - these need special handling
            continue
        else:
            str_value = str(value) if value is not None else ''
            rendered = rendered.replace(placeholder_pattern, str_value)
    
    # Check for unresolved placeholders
    unresolved = re.findall(r'\{\{([A-Z_]+)\}\}', rendered)
    if unresolved:
        print(f"   WARNING:  Unresolved placeholders: {unresolved[:5]}")  # Show first 5
        # Don't fail - some placeholders might be optional
    
    # Extract document title from first H1 if not in context
    if 'DOCUMENT_TITLE' not in context:
        title_match = re.search(r'^#\s+(.+)$', rendered, re.MULTILINE)
        if title_match:
            context['DOCUMENT_TITLE'] = title_match.group(1).strip()
        else:
            context['DOCUMENT_TITLE'] = f"{context.get('COMPANY_NAME', 'Document')} - {metadata.get('doc_type', '')}"
    
    # Word count validation (excluding placeholders from count)
    # Disabled - word count variance is normal and expected with template substitution
    # word_count = len(rendered.split())
    # target = metadata.get('word_count_target', 0)
    
    return rendered, context

# ============================================================================
# MODULE: Writer (RAW Tables with Context-First Approach)
# ============================================================================

def write_to_raw_table(session: Session, doc_type: str, documents: List[Dict[str, Any]]):
    """
    Write rendered documents to RAW table using Context-First approach.
    
    Args:
        session: Snowpark session
        doc_type: Document type
        documents: List of dicts with 'rendered' content and 'context'
    """
    if not documents:
        print(f"   WARNING:  No documents to write for {doc_type}")
        return
    
    table_name = f"{config.DATABASE['name']}.RAW.{config.DOCUMENT_TYPES[doc_type]['table_name']}"
    
    # Build data for DataFrame based on linkage level
    linkage_level = config.DOCUMENT_TYPES[doc_type]['linkage_level']
    
    data = []
    for doc in documents:
        ctx = doc['context']
        rendered = doc['rendered']
        
        # Base columns (common to all document types)
        row = {
            'DOCUMENT_ID': ctx.get('_document_id', str(hash(rendered))[:16]),
            'DOCUMENT_TITLE': ctx.get('DOCUMENT_TITLE', '')[:500],
            'DOCUMENT_TYPE': doc_type.replace('_', ' ').title(),
            'PUBLISH_DATE': ctx.get('PUBLISH_DATE', ctx.get('REPORT_DATE', '')),
            'LANGUAGE': 'en',
            'RAW_MARKDOWN': rendered
        }
        
        # Add linkage columns based on type
        if linkage_level == 'security':
            row['SecurityID'] = ctx.get('SECURITY_ID')
            row['IssuerID'] = ctx.get('ISSUER_ID')
            row['TICKER'] = ctx.get('TICKER')
            row['COMPANY_NAME'] = ctx.get('COMPANY_NAME')
            row['SIC_DESCRIPTION'] = ctx.get('SIC_DESCRIPTION')
        
        elif linkage_level == 'issuer':
            row['SecurityID'] = None
            row['IssuerID'] = ctx.get('ISSUER_ID')
            row['TICKER'] = ctx.get('TICKER')
        
        elif linkage_level == 'portfolio':
            row['PortfolioID'] = ctx.get('PORTFOLIO_ID')
            row['PORTFOLIO_NAME'] = ctx.get('PORTFOLIO_NAME')
            row['SecurityID'] = None
            row['IssuerID'] = None
        
        else:  # global
            row['SecurityID'] = None
            row['IssuerID'] = None
            row['PortfolioID'] = None
        
        # Add golden record columns (Context-First Option B)
        if doc_type in ['broker_research', 'internal_research']:
            row['BROKER_NAME'] = ctx.get('BROKER_NAME')
            row['ANALYST_NAME'] = ctx.get('ANALYST_NAME')
            row['RATING'] = ctx.get('RATING')
            row['PRICE_TARGET'] = ctx.get('PRICE_TARGET_USD')
        
        elif doc_type == 'ngo_reports':
            row['NGO_NAME'] = ctx.get('NGO_NAME')
            row['REPORT_CATEGORY'] = ctx.get('_category', 'Environmental')
            row['SEVERITY_LEVEL'] = ctx.get('SEVERITY_LEVEL')
        
        elif doc_type == 'engagement_notes':
            row['MEETING_TYPE'] = ctx.get('MEETING_TYPE')
        
        elif doc_type == 'earnings_transcripts':
            row['FISCAL_QUARTER'] = ctx.get('FISCAL_QUARTER')
            row['TRANSCRIPT_TYPE'] = 'Summary'  # Simplified
        
        elif doc_type == 'portfolio_review':
            row['FISCAL_QUARTER'] = ctx.get('FISCAL_QUARTER')
            row['QTD_RETURN_PCT'] = ctx.get('QTD_RETURN_PCT')
            row['YTD_RETURN_PCT'] = ctx.get('YTD_RETURN_PCT')
        
        data.append(row)
    
    # Create DataFrame and write to table
    if data:
        df = session.create_dataframe(data)
        df.write.mode("overwrite").save_as_table(table_name)
        # print(f"   ✅ Wrote {len(data)} documents to {table_name}")

# ============================================================================
# PUBLIC API
# ============================================================================

def hydrate_documents(session: Session, doc_type: str, test_mode: bool = False) -> int:
    """
    Main hydration function: load templates, build contexts, render, and write.
    
    Args:
        session: Snowpark session
        doc_type: Document type to hydrate
        test_mode: If True, use reduced document counts for faster development
    
    Returns:
        Number of documents generated
    """
    # print(f"    Hydrating {doc_type}...")
    
    # Load templates
    templates = load_templates(doc_type)
    
    # Get entities to hydrate
    entities = get_entities_for_doc_type(session, doc_type, test_mode)
    
    if not entities:
        print(f"   WARNING:  No entities found for {doc_type}")
        return 0
    
    # Render documents
    documents = []
    
    for entity in entities:
        try:
            # Build context based on linkage level
            linkage_level = config.DOCUMENT_TYPES[doc_type]['linkage_level']
            
            if linkage_level == 'security':
                context = build_security_context(session, entity['id'], doc_type)
            elif linkage_level == 'issuer':
                context = build_issuer_context(session, entity['id'], doc_type)
            elif linkage_level == 'portfolio':
                context = build_portfolio_context(session, entity['id'], doc_type)
            else:  # global
                context = build_global_context(doc_type, entity.get('num', 0))
            
            # Select appropriate template
            if doc_type == 'portfolio_review':
                template = select_portfolio_review_variant(templates, context)
            else:
                template = select_template(templates, context)
            
            # Render template
            rendered, enriched_context = render_template(template, context)
            
            # Add document ID
            enriched_context['_document_id'] = f"{doc_type}_{entity['id']}_{hash(rendered) % 100000}"
            
            documents.append({
                'rendered': rendered,
                'context': enriched_context
            })
            
        except Exception as e:
            print(f"   WARNING:  Failed to hydrate {doc_type} for entity {entity.get('id')}: {e}")
            continue
    
    # Write to RAW table
    write_to_raw_table(session, doc_type, documents)
    
    return len(documents)

def get_entities_for_doc_type(session: Session, doc_type: str, test_mode: bool = False) -> List[Dict[str, Any]]:
    """
    Get list of entities to hydrate for this document type.
    
    Args:
        session: Snowpark session
        doc_type: Document type
        test_mode: If True, use reduced entity counts
    
    Returns:
        List of entity dicts with 'id' and other metadata
    """
    linkage_level = config.DOCUMENT_TYPES[doc_type]['linkage_level']
    
    if linkage_level == 'security':
        # Get securities for demo coverage - prioritize demo scenario companies
        base_coverage = config.DOCUMENT_TYPES[doc_type].get('coverage_count', 8)
        coverage_count = max(3, int(base_coverage * config.TEST_MODE_MULTIPLIER)) if test_mode else base_coverage
        
        # Use same prioritization as portfolio holdings to ensure alignment with demo scenarios
        securities = session.sql(f"""
            SELECT 
                s.SecurityID as id,
                s.FIGI,
                s.Ticker
            FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s
            JOIN {config.DATABASE['name']}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE s.AssetClass = 'Equity'
            ORDER BY 
                -- Prioritize demo scenario companies (from config.DEMO_COMPANIES - same logic as portfolio holdings)
                CASE 
                    -- Demo companies with their configured priorities from config.DEMO_COMPANIES
                    {config.get_demo_company_priority_sql()}
                    -- Other major US stocks (from config.MAJOR_US_STOCKS)
                    WHEN s.Ticker IN {config.safe_sql_tuple(config.get_major_us_stocks('tier1'))} AND i.CountryOfIncorporation = 'US' THEN 5
                    -- Other US equities
                    WHEN i.CountryOfIncorporation = 'US' THEN 6
                    -- Non-US equities
                    ELSE 7
                END,
                s.Ticker
            LIMIT {coverage_count}
        """).collect()
        
        return [{'id': s['ID']} for s in securities]
    
    elif linkage_level == 'issuer':
        # Get issuers for demo coverage - prioritize companies that appear in portfolios
        base_coverage = config.DOCUMENT_TYPES[doc_type].get('coverage_count', 8)
        coverage_count = max(3, int(base_coverage * config.TEST_MODE_MULTIPLIER)) if test_mode else base_coverage
        
        # Prioritize issuers of securities that are in portfolios (especially demo companies)
        # Use subquery to prioritize, then select distinct issuers
        issuers = session.sql(f"""
            WITH prioritized_securities AS (
                SELECT 
                    i.IssuerID,
                    i.LegalName,
                    MIN(
                        CASE 
                            -- Demo companies with their configured priorities from config.DEMO_COMPANIES
                            {config.get_demo_company_priority_sql()}
                            -- Other major US stocks from config.MAJOR_US_STOCKS
                            WHEN s.Ticker IN {config.safe_sql_tuple(config.get_major_us_stocks('tier1'))} AND i.CountryOfIncorporation = 'US' THEN 5
                            WHEN i.CountryOfIncorporation = 'US' THEN 6
                            ELSE 7
                        END
                    ) as priority
                FROM {config.DATABASE['name']}.CURATED.DIM_ISSUER i
                JOIN {config.DATABASE['name']}.CURATED.DIM_SECURITY s ON i.IssuerID = s.IssuerID
                WHERE s.AssetClass = 'Equity'
                GROUP BY i.IssuerID, i.LegalName
            )
            SELECT 
                IssuerID as id,
                LegalName
            FROM prioritized_securities
            ORDER BY priority, LegalName
            LIMIT {coverage_count}
        """).collect()
        
        return [{'id': i['ID']} for i in issuers]
    
    elif linkage_level == 'portfolio':
        # Get portfolios specified in config
        portfolios_list = config.DOCUMENT_TYPES[doc_type].get('portfolios', [])
        
        if not portfolios_list:
            return []
        
        # In test mode, limit to first portfolio
        if test_mode:
            portfolios_list = portfolios_list[:1]
        
        # Query portfolio IDs for named portfolios
        portfolio_names_str = "','".join(portfolios_list)
        portfolios = session.sql(f"""
            SELECT PortfolioID as id
            FROM {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO
            WHERE PortfolioName IN ('{portfolio_names_str}')
        """).collect()
        
        return [{'id': p['ID']} for p in portfolios]
    
    else:  # global
        # Global documents: generate specified count
        base_count = config.DOCUMENT_TYPES[doc_type].get('docs_total', 1)
        docs_total = max(1, int(base_count * config.TEST_MODE_MULTIPLIER)) if test_mode else base_count
        return [{'id': i, 'num': i} for i in range(docs_total)]

