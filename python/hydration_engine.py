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
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, date
from snowflake.snowpark import Session
import config
import rules_loader
from logging_utils import log_warning
from demo_helpers import get_demo_company_priority_sql
from db_helpers import get_max_price_date

# Module-level anchor date for consistent date generation across all documents
# Set by hydrate_documents() to max_price_date from stock prices
_anchor_date: Optional[date] = None

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
            log_warning(f"  Template {file_path} missing required fields: {missing_fields}")
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
    entity_id = context.get('SECURITY_ID') or context.get('ISSUER_ID') or context.get('PORTFOLIO_ID')
    doc_type = context.get('_doc_type', 'unknown')
    doc_num = context.get('_doc_num', 0)
    
    # For global documents (no entity ID), cycle through templates using doc_num directly
    # This ensures all template variants are used when docs_total matches template count
    if entity_id is None:
        template_index = doc_num % len(templates)
        return templates[template_index]
    
    # Meeting type-based routing for engagement notes
    # If context has MEETING_TYPE, find templates that match that meeting_type
    meeting_type = context.get('MEETING_TYPE', '')
    if meeting_type and doc_type == 'engagement_notes':
        # Convert meeting type to template metadata format (lowercase, underscore)
        meeting_type_key = meeting_type.lower().replace(' ', '_')
        meeting_matched = [
            t for t in templates
            if t.get('metadata', {}).get('meeting_type', '').lower() == meeting_type_key
        ]
        if meeting_matched:
            # Use the meeting-type specific template
            return meeting_matched[0]
    
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
    
    # Deterministic selection using MD5 hash (Python's hash() is randomized per-process)
    hash_input = f"{entity_id}:{doc_type}:{config.RNG_SEED}".encode('utf-8')
    hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
    template_index = hash_value % len(candidate_templates)
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
    if doc_type == 'portfolio_review':
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


def get_breach_context_for_issuer(session: Session, issuer_id: int) -> Optional[Dict[str, Any]]:
    """
    Query FACT_COMPLIANCE_ALERTS for breach data to enrich engagement note context.
    
    Used for compliance_discussion meeting type engagement notes to include
    actual breach details (portfolio, weight, thresholds) in the generated document.
    
    Args:
        session: Snowpark session
        issuer_id: IssuerID to look up breaches for
    
    Returns:
        Dict with breach context fields, or None if no breach found for this issuer
    """
    database_name = config.DATABASE['name']
    
    breach_data = session.sql(f"""
        SELECT 
            ca.CurrentValue,
            ca.OriginalValue,
            ca.AlertDate,
            ca.ActionDeadline,
            ca.ResolvedBy,
            ca.ResolutionNotes,
            ca.AlertSeverity,
            ca.AlertType,
            p.PortfolioName,
            s.Ticker
        FROM {database_name}.CURATED.FACT_COMPLIANCE_ALERTS ca
        JOIN {database_name}.CURATED.DIM_PORTFOLIO p ON ca.PortfolioID = p.PortfolioID
        JOIN {database_name}.CURATED.DIM_SECURITY s ON ca.SecurityID = s.SecurityID
        WHERE s.IssuerID = {issuer_id}
          AND ca.AlertType IN ('CONCENTRATION_BREACH', 'CONCENTRATION_WARNING')
        ORDER BY 
            CASE ca.AlertType WHEN 'CONCENTRATION_BREACH' THEN 1 ELSE 2 END,
            ca.AlertDate DESC
        LIMIT 1
    """).collect()
    
    if not breach_data:
        return None
    
    b = breach_data[0]
    
    # Parse weight values (stored as strings like "7.2%")
    current_weight = b['CURRENTVALUE'] if b['CURRENTVALUE'] else '7.0%'
    breach_threshold = b['ORIGINALVALUE'] if b['ORIGINALVALUE'] else '7.0%'
    
    # Calculate derived values
    try:
        weight_num = float(current_weight.replace('%', ''))
        target_weight = f"{weight_num - 1.5:.1f}"  # Target 1.5% below current
    except:
        target_weight = '6.0'
    
    # Calculate days outstanding
    from datetime import datetime
    alert_date = b['ALERTDATE']
    if alert_date:
        days_outstanding = (datetime.now().date() - alert_date).days
    else:
        days_outstanding = 10
    
    return {
        'PORTFOLIO_NAME': b['PORTFOLIONAME'],
        'CURRENT_WEIGHT': current_weight,
        'BREACH_THRESHOLD': breach_threshold,
        'ALERT_DATE': str(alert_date) if alert_date else 'Recent',
        'PM_NAME': b['RESOLVEDBY'] if b['RESOLVEDBY'] else 'Anna Chen',
        'TARGET_DATE': str(b['ACTIONDEADLINE']) if b['ACTIONDEADLINE'] else 'Within 30 days',
        'REMEDIATION_DAYS': '15',
        'TARGET_WEIGHT': target_weight,
        'DAYS_OUTSTANDING': str(days_outstanding),
        'EXCESS_AMOUNT': f"{float(current_weight.replace('%', '')) - float(breach_threshold.replace('%', '')):.1f}%" if '%' in current_weight else '0.5%'
    }


def prefetch_issuers_with_breaches(session: Session) -> set:
    """
    Get set of IssuerIDs that have concentration breaches or warnings.
    
    Used to determine which issuers should get "Compliance Discussion" 
    meeting type for engagement notes.
    
    Args:
        session: Snowpark session
    
    Returns:
        Set of IssuerIDs that have breach/warning alerts
    """
    database_name = config.DATABASE['name']
    
    try:
        result = session.sql(f"""
            SELECT DISTINCT s.IssuerID
            FROM {database_name}.CURATED.FACT_COMPLIANCE_ALERTS ca
            JOIN {database_name}.CURATED.DIM_SECURITY s ON ca.SecurityID = s.SecurityID
            WHERE ca.AlertType IN ('CONCENTRATION_BREACH', 'CONCENTRATION_WARNING')
        """).collect()
        return {row['ISSUERID'] for row in result}
    except Exception as e:
        log_warning(f"  Could not prefetch breach data: {e}")
        return set()


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
            FROM {config.REAL_DATA_SOURCES['database']}.{config.REAL_DATA_SOURCES['schema']}.SEC_FISCAL_CALENDARS
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
    Uses fiscal calendar data when available for broker_research.
    
    Args:
        doc_type: Document type
        context: Optional context dict containing CIK for fiscal calendar lookup
        session: Optional Snowpark session for fiscal calendar queries
    
    Returns:
        Dict with date placeholders
    """
    current_date = datetime.now()
    
    dates = {}
    
    # Try to use fiscal calendar for broker research (aligns with earnings dates)
    fiscal_periods = []
    if doc_type == 'broker_research' and context and session:
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
    
    elif doc_type in ['ngo_reports', 'engagement_notes']:
        # Use anchor_date (max_price_date) for consistent date alignment with other data
        # NGO reports within last 60 days for recency, engagement notes over 180 days for history
        anchor = _anchor_date if _anchor_date else current_date.date()
        if doc_type == 'ngo_reports':
            offset_days = random.randint(1, 60)  # More recent for controversy scanning
        else:
            offset_days = random.randint(1, 180)  # Broader range for engagement history
        publish_date = datetime.combine(anchor, datetime.min.time()) - timedelta(days=offset_days)
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

def generate_provider_context(context: Dict[str, Any], doc_type: str, 
                              issuers_with_breaches: Optional[set] = None) -> Dict[str, Any]:
    """
    Generate provider names, ratings, severity levels, etc.
    
    Args:
        context: Existing context
        doc_type: Document type
        issuers_with_breaches: Optional set of IssuerIDs that have concentration breaches
                               (used for engagement notes to determine Compliance Discussion meeting type)
    
    Returns:
        Dict with provider/attribution placeholders
    """
    provider_context = {}
    entity_id = context.get('SECURITY_ID') or context.get('ISSUER_ID') or context.get('PORTFOLIO_ID') or 0
    
    if doc_type in ['broker_research', 'internal_research', 'investment_memo']:
        # Select fictional broker from YAML rules
        fictional_brokers = rules_loader.get_fictional_brokers()
        broker_index = hash(f"{entity_id}:broker:{config.RNG_SEED}") % len(fictional_brokers)
        provider_context['BROKER_NAME'] = fictional_brokers[broker_index]
        
        # Generate analyst name
        analyst_id = (hash(f"{entity_id}:analyst:{config.RNG_SEED}") % 100) + 1
        provider_context['ANALYST_NAME'] = f'Analyst_{analyst_id:02d}'
        
        # Select rating from distribution
        provider_context['RATING'] = select_from_distribution('rating')
        
        # Add portfolio name for investment memos
        if doc_type == 'investment_memo':
            provider_context['PORTFOLIO_NAME'] = config.DEFAULT_DEMO_PORTFOLIO
        
        # Add investment memo specific placeholders (competitors, etc.)
        tech_competitors = ['Salesforce', 'Oracle', 'SAP', 'Adobe', 'ServiceNow', 'Workday', 'Splunk', 'Datadog']
        healthcare_competitors = ['Pfizer', 'Johnson & Johnson', 'AbbVie', 'Merck', 'Bristol-Myers Squibb', 'Eli Lilly']
        financial_competitors = ['JPMorgan', 'Bank of America', 'Goldman Sachs', 'Morgan Stanley', 'Wells Fargo']
        
        sector = context.get('SIC_DESCRIPTION', 'Information Technology')
        if 'Health' in sector or 'Pharma' in sector or 'Medical' in sector:
            competitors = healthcare_competitors
        elif 'Financ' in sector or 'Bank' in sector or 'Insurance' in sector:
            competitors = financial_competitors
        else:
            competitors = tech_competitors
        
        # Select 3 different competitors deterministically
        comp1_idx = hash(f"{entity_id}:comp1:{config.RNG_SEED}") % len(competitors)
        comp2_idx = (comp1_idx + 1) % len(competitors)
        comp3_idx = (comp1_idx + 2) % len(competitors)
        provider_context['COMPETITOR_1'] = competitors[comp1_idx]
        provider_context['COMPETITOR_2'] = competitors[comp2_idx]
        provider_context['COMPETITOR_3'] = competitors[comp3_idx]
    
    elif doc_type == 'ngo_reports':
        # Determine ESG category (from template or random)
        category = context.get('_category', random.choice(['environmental', 'social', 'governance']))
        
        # Select NGO from appropriate category (from YAML rules)
        fictional_ngos = rules_loader.get_fictional_ngos()
        category_ngos = fictional_ngos.get(category, fictional_ngos.get('environmental', []))
        ngo_index = hash(f"{entity_id}:ngo:{category}:{config.RNG_SEED}") % len(category_ngos) if category_ngos else 0
        provider_context['NGO_NAME'] = category_ngos[ngo_index] if category_ngos else 'Global Sustainability Watch'
        
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
        # Select meeting type - only use Compliance Discussion if issuer has breach data
        issuer_id = context.get('ISSUER_ID')
        if issuers_with_breaches and issuer_id and issuer_id in issuers_with_breaches:
            # This issuer has breach data, assign Compliance Discussion
            provider_context['MEETING_TYPE'] = 'Compliance Discussion'
        else:
            # No breach data - use other meeting types (exclude Compliance Discussion)
            # Only include meeting types that have matching templates
            non_compliance_types = {
                'Management Meeting': 0.60,
                'Shareholder Call': 0.40
            }
            # Select from distribution excluding Compliance Discussion
            rand_val = random.random()
            cumulative = 0.0
            selected = 'Management Meeting'
            for meeting_type, weight in non_compliance_types.items():
                cumulative += weight
                if rand_val <= cumulative:
                    selected = meeting_type
                    break
            provider_context['MEETING_TYPE'] = selected
        
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
            'Management Meeting': 0.40,
            'Shareholder Call': 0.25,
            'Site Visit': 0.15,
            'Compliance Discussion': 0.20
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
    
    ONLY fills missing placeholders - does not overwrite values already set in context.
    This allows SEC financial metrics (injected earlier) to take precedence over sampling.
    
    Args:
        context: Existing context with sector info (may contain pre-set financial metrics)
        doc_type: Document type
    
    Returns:
        Dict with Tier 1 numeric placeholders (only for keys not already in context)
    """
    numerics = {}
    entity_id = context.get('SECURITY_ID') or context.get('PORTFOLIO_ID') or 0
    sector = context.get('SIC_DESCRIPTION', 'Information Technology')
    
    # Load numeric bounds from YAML rules
    bounds = rules_loader.get_numeric_bounds(doc_type, sector)
    
    # Sample each numeric placeholder deterministically (ONLY if not already set)
    for placeholder, bound_spec in bounds.items():
        # Skip placeholders that already have values (e.g., from SEC financial data)
        if placeholder in context and context[placeholder] is not None:
            continue
        
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
        log_warning(f"  Tier 2 query failed for portfolio {portfolio_id}: {e}")
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
            log_warning(f"  Conditional placeholder {name} evaluation failed: {e}")
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
            log_warning(f"  Could not load partial {partial_name}: {e}")
    
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
        log_warning(f"  Unresolved placeholders: {unresolved[:5]}")  # Show first 5
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
        log_warning(f"  No documents to write for {doc_type}")
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
        
        elif doc_type == 'portfolio_review':
            row['FISCAL_QUARTER'] = ctx.get('FISCAL_QUARTER')
            row['QTD_RETURN_PCT'] = ctx.get('QTD_RETURN_PCT')
            row['YTD_RETURN_PCT'] = ctx.get('YTD_RETURN_PCT')
        
        data.append(row)
    
    # Create DataFrame and write to table
    if data:
        df = session.create_dataframe(data)
        df.write.mode("overwrite").save_as_table(table_name)

# ============================================================================
# PUBLIC API
# ============================================================================

def hydrate_documents(session: Session, doc_type: str, test_mode: bool = False) -> int:
    """
    Main hydration function: load templates, build contexts, render, and write.
    
    Uses batched prefetch for efficiency (no per-entity SELECT queries per performance-io.mdc).
    
    Args:
        session: Snowpark session
        doc_type: Document type to hydrate
        test_mode: If True, use reduced document counts for faster development
    
    Returns:
        Number of documents generated
    """
    import snowflake_io_utils
    
    # Set module-level anchor date for consistent date generation
    # All document dates will be relative to max_price_date from stock prices
    global _anchor_date
    if _anchor_date is None:
        _anchor_date = get_max_price_date(session)
    
    # Load templates
    templates = load_templates(doc_type)
    
    # Get entities to hydrate
    entities = get_entities_for_doc_type(session, doc_type, test_mode)
    
    if not entities:
        log_warning(f"  No entities found for {doc_type}")
        return 0
    
    linkage_level = config.DOCUMENT_TYPES[doc_type]['linkage_level']
    database_name = config.DATABASE['name']
    
    # PREFETCH: Get all needed data in ONE query per linkage level (no collect-in-loop)
    prefetched_contexts: Dict[int, Dict[str, Any]] = {}
    fiscal_calendar_cache: Dict[str, List[Dict[str, Any]]] = {}
    
    # SEC financials cache for period-aligned metrics (security-level docs)
    sec_financials_cache: Dict[str, Dict[tuple, Dict[str, Any]]] = {}
    
    if linkage_level == 'security':
        security_ids = [e['id'] for e in entities]
        prefetched_contexts = snowflake_io_utils.prefetch_security_contexts(
            session, database_name, security_ids
        )
        # Prefetch fiscal calendars for all CIKs if needed for this doc type
        if doc_type == 'broker_research':
            ciks = [ctx.get('CIK') for ctx in prefetched_contexts.values() if ctx.get('CIK')]
            if ciks:
                fiscal_calendar_cache = snowflake_io_utils.prefetch_fiscal_calendars(
                    session,
                    config.REAL_DATA_SOURCES['database'],
                    config.REAL_DATA_SOURCES['schema'],
                    ciks
                )
        
        # Prefetch SEC financials for period-aligned metrics in security-level docs
        # This enables broker research and other docs to quote actual financial figures
        ciks_for_financials = [ctx.get('CIK') for ctx in prefetched_contexts.values() if ctx.get('CIK')]
        if ciks_for_financials:
            sec_financials_cache = snowflake_io_utils.prefetch_sec_financials(
                session, database_name, ciks_for_financials
            )
    
    elif linkage_level == 'issuer':
        issuer_ids = [e['id'] for e in entities]
        prefetched_contexts = snowflake_io_utils.prefetch_issuer_contexts(
            session, database_name, issuer_ids
        )
        # Prefetch fiscal calendars for issuer CIKs if needed
        if doc_type in ['ngo_reports', 'engagement_notes']:
            ciks = [ctx.get('CIK') for ctx in prefetched_contexts.values() if ctx.get('CIK')]
            if ciks:
                fiscal_calendar_cache = snowflake_io_utils.prefetch_fiscal_calendars(
                    session,
                    config.REAL_DATA_SOURCES['database'],
                    config.REAL_DATA_SOURCES['schema'],
                    ciks
                )
    
    # Prefetch issuers with breaches for engagement_notes (for Compliance Discussion meeting type)
    issuers_with_breaches: set = set()
    if doc_type == 'engagement_notes':
        issuers_with_breaches = prefetch_issuers_with_breaches(session)
        if issuers_with_breaches:
            from logging_utils import log_detail
            log_detail(f"  Found {len(issuers_with_breaches)} issuers with breach data for Compliance Discussion")
    
    elif linkage_level == 'portfolio':
        portfolio_ids = [e['id'] for e in entities]
        prefetched_contexts = snowflake_io_utils.prefetch_portfolio_contexts(
            session, database_name, portfolio_ids
        )
    
    # Render documents using prefetched data
    documents = []
    
    for entity in entities:
        try:
            # Build context from prefetched data (no per-entity queries)
            if linkage_level == 'security':
                context = build_security_context_from_prefetch(
                    prefetched_contexts.get(entity['id']), 
                    doc_type,
                    fiscal_calendar_cache,
                    sec_financials_cache
                )
            elif linkage_level == 'issuer':
                context = build_issuer_context_from_prefetch(
                    prefetched_contexts.get(entity['id']),
                    doc_type,
                    fiscal_calendar_cache,
                    session,  # Pass session for breach context queries (engagement notes)
                    issuers_with_breaches  # Pass breach set for Compliance Discussion meeting type
                )
            elif linkage_level == 'portfolio':
                context = build_portfolio_context_from_prefetch(
                    session,  # Still need session for Tier 2 portfolio metrics
                    prefetched_contexts.get(entity['id']),
                    doc_type
                )
            else:  # global
                context = build_global_context(doc_type, entity.get('num', 0))
            
            if context is None:
                log_warning(f"  No prefetched data for {doc_type} entity {entity.get('id')}")
                continue
            
            # Select appropriate template
            if doc_type == 'portfolio_review':
                template = select_portfolio_review_variant(templates, context)
            else:
                template = select_template(templates, context)
            
            # Override SEVERITY_LEVEL from template metadata for NGO reports
            # This ensures metadata field matches hardcoded severity in template body
            if doc_type == 'ngo_reports':
                template_severity = template.get('metadata', {}).get('severity', '')
                if template_severity:
                    context['SEVERITY_LEVEL'] = template_severity.title()  # 'high' -> 'High'
            
            # Render template
            rendered, enriched_context = render_template(template, context)
            
            # Add document ID
            enriched_context['_document_id'] = f"{doc_type}_{entity['id']}_{hash(rendered) % 100000}"
            
            documents.append({
                'rendered': rendered,
                'context': enriched_context
            })
            
        except Exception as e:
            log_warning(f"  Failed to hydrate {doc_type} for entity {entity.get('id')}: {e}")
            continue
    
    # Write to RAW table
    write_to_raw_table(session, doc_type, documents)
    
    return len(documents)


def build_security_context_from_prefetch(
    prefetched_row: Optional[Dict[str, Any]],
    doc_type: str,
    fiscal_calendar_cache: Dict[str, List[Dict[str, Any]]],
    sec_financials_cache: Optional[Dict[str, Dict[tuple, Dict[str, Any]]]] = None
) -> Optional[Dict[str, Any]]:
    """
    Build context for security-level documents from prefetched data.
    No database queries - uses data already fetched in batch.
    
    Args:
        prefetched_row: Row from prefetch_security_contexts()
        doc_type: Document type for context enrichment
        fiscal_calendar_cache: Prefetched fiscal calendar data keyed by CIK
        sec_financials_cache: Prefetched SEC financial metrics keyed by CIK then (year, period)
    
    Returns:
        Context dict or None if prefetched_row is missing
    """
    if not prefetched_row:
        return None
    
    # Build base context from prefetched data
    context = {
        '_doc_type': doc_type,
        'SECURITY_ID': prefetched_row.get('SECURITYID'),
        'ISSUER_ID': prefetched_row.get('ISSUERID'),
        'COMPANY_NAME': prefetched_row.get('COMPANY_NAME'),
        'TICKER': prefetched_row.get('TICKER'),
        'SIC_DESCRIPTION': prefetched_row.get('SIC_DESCRIPTION'),
        'ISSUER_NAME': prefetched_row.get('ISSUER_NAME'),
        'ASSET_CLASS': prefetched_row.get('ASSETCLASS'),
        'CIK': prefetched_row.get('CIK'),
    }
    
    # Get fiscal periods from cache (no query)
    fiscal_periods = []
    cik = context.get('CIK')
    if cik and cik in fiscal_calendar_cache:
        fiscal_periods = fiscal_calendar_cache[cik]
    
    # Add dates using cached fiscal data
    context.update(generate_dates_for_doc_type_from_cache(doc_type, context, fiscal_periods))
    
    # Add provider/attribution fields
    context.update(generate_provider_context(context, doc_type))
    
    # Inject period-aligned SEC financial metrics (if available)
    # This must happen BEFORE generate_tier1_numerics() so real data takes precedence
    if sec_financials_cache:
        context.update(inject_sec_financial_metrics(context, sec_financials_cache))
    
    # Add Tier 1 numerics (fills in missing placeholders with sampled values)
    context.update(generate_tier1_numerics(context, doc_type))
    
    return context


def inject_sec_financial_metrics(
    context: Dict[str, Any],
    sec_financials_cache: Dict[str, Dict[tuple, Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Inject period-aligned SEC financial metrics into the hydration context.
    
    Uses the CIK and fiscal period/year from the context to look up matching
    financial data from the prefetched SEC financials cache.
    
    Args:
        context: Current hydration context with FISCAL_QUARTER, FISCAL_YEAR, CIK
        sec_financials_cache: Prefetched SEC financials keyed by CIK then (year, period)
    
    Returns:
        Dict of financial metric placeholders (may be empty if no matching data)
    """
    cik = context.get('CIK')
    if not cik or cik not in sec_financials_cache:
        return {}
    
    # Parse fiscal period and year from context
    # FISCAL_QUARTER may be 'Q3' or 'Q3 2024' depending on branch
    fiscal_quarter_raw = context.get('FISCAL_QUARTER', '')
    fiscal_year_raw = context.get('FISCAL_YEAR', '')
    
    # Extract period (Q1, Q2, Q3, Q4)
    fiscal_period = None
    fiscal_year = None
    
    if fiscal_quarter_raw:
        # Handle 'Q3' format
        if fiscal_quarter_raw.startswith('Q') and len(fiscal_quarter_raw) == 2:
            fiscal_period = fiscal_quarter_raw
        # Handle 'Q3 2024' format
        elif fiscal_quarter_raw.startswith('Q') and ' ' in fiscal_quarter_raw:
            parts = fiscal_quarter_raw.split(' ')
            fiscal_period = parts[0]
            if len(parts) > 1 and parts[1].isdigit():
                fiscal_year = int(parts[1])
    
    # Use explicit FISCAL_YEAR if provided
    if fiscal_year_raw and fiscal_year is None:
        try:
            # Handle both "2025" and "2025.0" formats
            fiscal_year = int(float(fiscal_year_raw))
        except (ValueError, TypeError):
            pass
    
    if not fiscal_period or not fiscal_year:
        return {}
    
    # Look up matching financial data
    cik_financials = sec_financials_cache.get(cik, {})
    period_key = (fiscal_year, fiscal_period)
    period_data = cik_financials.get(period_key)
    
    if not period_data:
        return {}
    
    # Build metric placeholders from SEC data
    metrics = {}
    
    # Quarterly figures (convert to billions for template compatibility)
    revenue = period_data.get('REVENUE')
    if revenue is not None:
        metrics['QUARTERLY_REVENUE_BILLIONS'] = round(revenue / 1e9, 2)
        # Also set annual scale approximation (trailing 4Q)
        metrics['REVENUE_BILLIONS'] = round(revenue * 4 / 1e9, 1)
    
    net_income = period_data.get('NET_INCOME')
    if net_income is not None:
        metrics['NET_INCOME'] = round(net_income / 1e9, 2)
    
    gross_profit = period_data.get('GROSS_PROFIT')
    if gross_profit is not None:
        metrics['GROSS_PROFIT'] = round(gross_profit / 1e9, 2)
    
    operating_income = period_data.get('OPERATING_INCOME')
    if operating_income is not None:
        metrics['OPERATING_INCOME'] = round(operating_income / 1e9, 2)
    
    # EPS (diluted preferred, fallback to basic)
    eps_diluted = period_data.get('EPS_DILUTED')
    eps_basic = period_data.get('EPS_BASIC')
    if eps_diluted is not None:
        metrics['QUARTERLY_EPS'] = round(eps_diluted, 2)
    elif eps_basic is not None:
        metrics['QUARTERLY_EPS'] = round(eps_basic, 2)
    
    # Margin percentages (already calculated in FACT_SEC_FINANCIALS)
    gross_margin = period_data.get('GROSS_MARGIN_PCT')
    if gross_margin is not None:
        metrics['GROSS_MARGIN_PCT'] = round(gross_margin, 1)
    
    operating_margin = period_data.get('OPERATING_MARGIN_PCT')
    if operating_margin is not None:
        metrics['OPERATING_MARGIN_PCT'] = round(operating_margin, 1)
        # Use operating margin as EBIT margin proxy
        metrics['EBIT_MARGIN_PCT'] = round(operating_margin, 1)
    
    net_margin = period_data.get('NET_MARGIN_PCT')
    if net_margin is not None:
        metrics['NET_MARGIN_PCT'] = round(net_margin, 1)
    
    # YoY revenue growth (precomputed in prefetch)
    yoy_growth = period_data.get('YOY_REVENUE_GROWTH_PCT')
    if yoy_growth is not None:
        metrics['YOY_REVENUE_GROWTH_PCT'] = round(yoy_growth, 1)
        metrics['YOY_GROWTH_PCT'] = round(yoy_growth, 1)
    
    # Other useful metrics
    roe = period_data.get('ROE_PCT')
    if roe is not None:
        metrics['ROE_PCT'] = round(roe, 1)
    
    roa = period_data.get('ROA_PCT')
    if roa is not None:
        metrics['ROA_PCT'] = round(roa, 1)
    
    debt_to_equity = period_data.get('DEBT_TO_EQUITY')
    if debt_to_equity is not None:
        metrics['DEBT_TO_EQUITY'] = round(debt_to_equity, 2)
    
    current_ratio = period_data.get('CURRENT_RATIO')
    if current_ratio is not None:
        metrics['CURRENT_RATIO'] = round(current_ratio, 2)
    
    free_cash_flow = period_data.get('FREE_CASH_FLOW')
    if free_cash_flow is not None:
        metrics['FREE_CASH_FLOW'] = round(free_cash_flow / 1e9, 2)
    
    return metrics


def build_issuer_context_from_prefetch(
    prefetched_row: Optional[Dict[str, Any]],
    doc_type: str,
    fiscal_calendar_cache: Dict[str, List[Dict[str, Any]]],
    session: Optional[Session] = None,
    issuers_with_breaches: Optional[set] = None
) -> Optional[Dict[str, Any]]:
    """
    Build context for issuer-level documents from prefetched data.
    Mostly uses prefetched data, but may query for breach context when needed.
    
    Args:
        prefetched_row: Row from prefetch_issuer_contexts()
        doc_type: Document type
        fiscal_calendar_cache: Prefetched fiscal calendar data keyed by CIK
        session: Optional Snowpark session for breach context queries
        issuers_with_breaches: Optional set of IssuerIDs that have concentration breaches
    
    Returns:
        Context dict or None if prefetched_row is missing
    """
    if not prefetched_row:
        return None
    
    context = {
        '_doc_type': doc_type,
        'ISSUER_ID': prefetched_row.get('ISSUERID'),
        'ISSUER_NAME': prefetched_row.get('ISSUER_NAME'),
        'TICKER': prefetched_row.get('TICKER') or 'N/A',
        'SIC_DESCRIPTION': prefetched_row.get('SIC_DESCRIPTION'),
        'CIK': prefetched_row.get('CIK'),
    }
    
    # Get fiscal periods from cache (no query)
    fiscal_periods = []
    cik = context.get('CIK')
    if cik and cik in fiscal_calendar_cache:
        fiscal_periods = fiscal_calendar_cache[cik]
    
    # Add dates using cached fiscal data
    context.update(generate_dates_for_doc_type_from_cache(doc_type, context, fiscal_periods))
    
    # Add NGO/meeting type context (pass issuers_with_breaches for engagement notes)
    context.update(generate_provider_context(context, doc_type, issuers_with_breaches))
    
    # For engagement notes with Compliance Discussion meeting type, enrich with breach data
    # (Now only happens for issuers that actually have breaches, since meeting type is 
    # only set to "Compliance Discussion" for those issuers by generate_provider_context)
    if doc_type == 'engagement_notes' and session is not None:
        meeting_type = context.get('MEETING_TYPE')
        if meeting_type == 'Compliance Discussion':
            issuer_id = context.get('ISSUER_ID')
            if issuer_id:
                breach_ctx = get_breach_context_for_issuer(session, issuer_id)
                if breach_ctx:
                    # Breach found - enrich context with breach-specific data
                    context.update(breach_ctx)
                # Note: No fallback needed since meeting type is only set to 
                # "Compliance Discussion" for issuers confirmed to have breaches
    
    return context


def build_portfolio_context_from_prefetch(
    session: Session,
    prefetched_row: Optional[Dict[str, Any]],
    doc_type: str
) -> Optional[Dict[str, Any]]:
    """
    Build context for portfolio-level documents from prefetched data.
    Still needs session for Tier 2 derived metrics queries.
    
    Args:
        session: Snowpark session (for Tier 2 metrics only)
        prefetched_row: Row from prefetch_portfolio_contexts()
        doc_type: Document type
    
    Returns:
        Context dict or None if prefetched_row is missing
    """
    if not prefetched_row:
        return None
    
    context = {
        '_doc_type': doc_type,
        'PORTFOLIO_ID': prefetched_row.get('PORTFOLIOID'),
        'PORTFOLIO_NAME': prefetched_row.get('PORTFOLIONAME'),
        'STRATEGY': prefetched_row.get('STRATEGY'),
        'BASE_CURRENCY': prefetched_row.get('BASECURRENCY'),
        'INCEPTION_DATE': str(prefetched_row.get('INCEPTIONDATE')) if prefetched_row.get('INCEPTIONDATE') else None,
    }
    
    # Add dates
    context.update(generate_dates_for_doc_type(doc_type))
    
    # Add Tier 2 derived metrics for portfolio reviews (still needs session)
    portfolio_id = context.get('PORTFOLIO_ID')
    if doc_type == 'portfolio_review' and portfolio_id:
        context.update(query_tier2_portfolio_metrics(session, portfolio_id))
    
    # Add Tier 1 numerics for performance data
    context.update(generate_tier1_numerics(context, doc_type))
    
    return context


def generate_dates_for_doc_type_from_cache(
    doc_type: str,
    context: Dict[str, Any],
    fiscal_periods: List[Dict[str, Any]]
) -> Dict[str, str]:
    """
    Generate dates using cached fiscal calendar data (no queries).
    
    This is the cache-aware version of generate_dates_for_doc_type.
    
    Args:
        doc_type: Document type
        context: Context dict (for fallback values)
        fiscal_periods: Prefetched fiscal periods for this entity's CIK
    
    Returns:
        Dict with date placeholders
    """
    current_date = datetime.now()
    dates = {}
    
    if doc_type in ['broker_research', 'internal_research', 'press_releases', 'investment_memo']:
        if doc_type == 'broker_research' and fiscal_periods:
            # Pick a recent fiscal period (0-2 quarters back for more recent research)
            period_idx = random.randint(0, min(2, len(fiscal_periods) - 1))
            fiscal_period = fiscal_periods[period_idx]
            
            period_end = fiscal_period.get('PERIOD_END_DATE')
            if period_end:
                days_after_period_end = random.randint(21, 75)
                publish_date = period_end + timedelta(days=days_after_period_end)
                dates['PUBLISH_DATE'] = publish_date.strftime('%d %B %Y')
                dates['FISCAL_QUARTER'] = fiscal_period.get('FISCAL_PERIOD', '')
                dates['FISCAL_YEAR'] = str(fiscal_period.get('FISCAL_YEAR', ''))
            else:
                offset_days = random.randint(1, 90)
                publish_date = current_date - timedelta(days=offset_days)
                dates['PUBLISH_DATE'] = publish_date.strftime('%d %B %Y')
        else:
            offset_days = random.randint(1, 90)
            publish_date = current_date - timedelta(days=offset_days)
            dates['PUBLISH_DATE'] = publish_date.strftime('%d %B %Y')
    
    elif doc_type in ['ngo_reports', 'engagement_notes']:
        # Use anchor_date (max_price_date) for consistent date alignment with other data
        # NGO reports within last 60 days of anchor date for recency in demos
        # Engagement notes spread over last 180 days for historical depth
        anchor = _anchor_date if _anchor_date else current_date.date()
        if doc_type == 'ngo_reports':
            offset_days = random.randint(1, 60)  # More recent for controversy scanning
        else:
            offset_days = random.randint(1, 180)  # Broader range for engagement history
        publish_date = datetime.combine(anchor, datetime.min.time()) - timedelta(days=offset_days)
        dates['PUBLISH_DATE'] = publish_date.strftime('%d %B %Y')
    
    elif doc_type == 'portfolio_review':
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
        dates['REPORT_DATE'] = current_date.strftime('%A, %d %B %Y')
    
    elif doc_type in ['sales_templates', 'philosophy_docs', 'policy_docs']:
        dates['TEMPLATE_DATE'] = current_date.strftime('%d %B %Y')
    
    return dates

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
                s.Ticker
            FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s
            JOIN {config.DATABASE['name']}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE s.AssetClass = 'Equity'
            ORDER BY 
                -- Prioritize demo scenario companies by tier from config.DEMO_COMPANIES
                CASE 
                    {get_demo_company_priority_sql()}
                    -- Companies not in DEMO_COMPANIES
                    ELSE 10
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
                            -- Demo companies by tier from config.DEMO_COMPANIES
                            {get_demo_company_priority_sql()}
                            -- Companies not in DEMO_COMPANIES
                            ELSE 10
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

