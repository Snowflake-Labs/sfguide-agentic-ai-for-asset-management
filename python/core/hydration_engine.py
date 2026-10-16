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
from utils.logging import log_warning, log_detail
from utils.demo_helpers import get_demo_company_priority_sql
from utils.sql import safe_sql_tuple
from utils.snowflake import get_max_price_date

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
        dirs.sort()
        for file in sorted(files):
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

    # Stance routing. A template may declare `rating_stance: [bull]` in front
    # matter to restrict itself to ratings implying that stance. Templates that
    # declare no stance are stance-neutral and stay eligible for any rating -
    # they get their stance from the STANCE_PHRASES placeholders instead. This
    # keeps a bear-rated stock off a permanently bullish variant without
    # requiring every sector to carry a full set of three variant files.
    stance = config.RATING_TO_STANCE.get(context.get('RATING'))
    if stance:
        stance_eligible = [
            t for t in candidate_templates
            if stance in (t['metadata'].get('rating_stance') or [stance])
        ]
        if stance_eligible:
            candidate_templates = stance_eligible
        else:
            # Every candidate is stance-restricted and none matches. Fall through
            # rather than failing to produce a document.
            log_detail(
                f"  No {stance} template for {doc_type} sector '{gics_sector}' - "
                "using stance-neutral prose"
            )
    
    # For portfolio documents with multiple docs per entity, use doc_num to cycle templates
    if doc_type in ['custodian_reports']:
        template_index = doc_num % len(candidate_templates)
        return candidate_templates[template_index]
    
    hash_input = f"{entity_id}:{doc_type}:{doc_num}:{config.RNG_SEED}".encode('utf-8')
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


# ============================================================================
# MODULE: Context Builder
# ============================================================================



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
    
    result = session.sql(f"""
        SELECT DISTINCT s.IssuerID
        FROM {database_name}.CURATED.FACT_COMPLIANCE_ALERTS ca
        JOIN {database_name}.CURATED.DIM_SECURITY s ON ca.SecurityID = s.SecurityID
        WHERE ca.AlertType IN ('CONCENTRATION_BREACH', 'CONCENTRATION_WARNING')
    """).collect()
    return {row['ISSUERID'] for row in result}


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

def _stable_hash(key: str) -> int:
    """Deterministic non-negative hash, as a drop-in for the builtin hash().

    Python salts str hashing per process (PYTHONHASHSEED), so _stable_hash(f"...{RNG_SEED}")
    is NOT reproducible across runs even though the seed is in the key. That made
    the broker, analyst, CEO/CFO, competitor and NGO names attributed to a
    document change on every build - and an unstable broker name also breaks the
    join from a document back to its FACT_RECOMMENDATION row.
    """
    return int(hashlib.md5(key.encode('utf-8')).hexdigest()[:12], 16)


def _stable_offset(seed_parts: List[Any], low: int, high: int) -> int:
    """Deterministic integer in [low, high] derived from seed_parts.

    Replaces random.randint for date offsets. Unseeded randint made PUBLISH_DATE
    move on every build, which in turn changed the document id and filename, so
    the pipeline MERGE could never recognise a regenerated document as the same
    one. A stable hash keeps the same spread while making a rebuild reproducible.
    """
    key = '|'.join('' if p is None else str(p) for p in seed_parts)
    digest = hashlib.md5(key.encode('utf-8')).hexdigest()
    span = max(1, high - low + 1)
    return low + (int(digest[:8], 16) % span)


def make_document_id(doc_type: str, entity_id: Any, doc_num: int, vintage: Any) -> str:
    """Deterministic document id: MD5(doc_type|entity_id|doc_num|vintage).

    Previously this was f"{doc_type}_{entity_id}_{doc_num}_{hash(rendered)}", but
    Python salts str hashing per process, so the same document got a new id and a
    new filename on every run and documents accumulated as duplicates rather than
    merging. Keying on the logical identity plus the vintage means re-running a
    vintage is idempotent while a new vintage is naturally a new document.
    """
    if isinstance(vintage, (datetime, date)):
        vintage_key = vintage.strftime('%Y-%m-%d')
    else:
        vintage_key = str(vintage or '')
    key = f"{doc_type}|{entity_id}|{doc_num}|{vintage_key}"
    return hashlib.md5(key.encode('utf-8')).hexdigest()


_PERIOD_PINNED_CADENCES = ('annual', 'quarterly', 'monthly')


def _cadence_period_start(doc_type: str, reference_date: datetime) -> datetime:
    """Pin a global reference document's date to the start of its cadence period.

    Policies, philosophies, methodologies, templates and the like are reissued per
    cadence period, not per build. Dating them from the build anchor gave each
    build or refresh on a different day a new vintage, so a new document id and a
    new filename, and the append-only corpus indexed the same policy repeatedly.
    Entity-linked and weekly global types keep their reference date.
    """
    spec = config.DOCUMENT_TYPES.get(doc_type, {})
    period = (spec.get('cadence') or {}).get('period')
    if spec.get('linkage_level') != 'global' or period not in _PERIOD_PINNED_CADENCES:
        return reference_date
    if period == 'annual':
        return reference_date.replace(month=1, day=1)
    if period == 'quarterly':
        return reference_date.replace(month=3 * ((reference_date.month - 1) // 3) + 1, day=1)
    return reference_date.replace(day=1)


def generate_dates_for_doc_type(doc_type: str, context: Optional[Dict[str, Any]] = None, session: Optional[Session] = None, vintage: Optional[date] = None, fiscal_periods: Optional[List[Dict[str, Any]]] = None) -> Dict[str, str]:
    """
    Generate appropriate dates based on document type.
    Uses fiscal calendar data when available for broker_research.

    Args:
        doc_type: Document type
        context: Optional context dict containing CIK for fiscal calendar lookup
        session: Optional Snowpark session for fiscal calendar queries
        vintage: Optional as-of date for this document. When supplied it drives
            every derived date, which is what lets the same code produce a
            historical backfill and a forward weekly increment. Falls back to the
            module anchor (max_price_date) rather than datetime.now() so dates
            stay aligned with the market data and reproducible across builds.
        fiscal_periods: Optional prefetched fiscal periods, to avoid a query.

    Returns:
        Dict with date placeholders
    """
    if vintage is not None:
        reference_date = datetime.combine(vintage, datetime.min.time())
    elif _anchor_date:
        reference_date = datetime.combine(_anchor_date, datetime.min.time())
    else:
        reference_date = datetime.now()
    current_date = _cadence_period_start(doc_type, reference_date)

    # Stable seed for date offsets: identity of the document, plus its vintage so
    # a new vintage lands on a different day within the window.
    context = context or {}
    seed_base = [
        doc_type,
        context.get('SecurityID') or context.get('IssuerID') or context.get('CIK')
        or context.get('PortfolioID') or context.get('ClientID'),
        context.get('doc_num', 0),
        reference_date.strftime('%Y-%m-%d'),
    ]

    dates = {}
    
    # Try to use fiscal calendar for broker research (aligns with earnings dates)
    fiscal_periods = list(fiscal_periods) if fiscal_periods else []
    if doc_type == 'broker_research' and not fiscal_periods and context and session:
        cik = context.get('CIK')
        if cik:
            fiscal_periods = get_fiscal_calendar_dates(session, cik, num_periods=4)
    
    if doc_type in ['broker_research', 'internal_research', 'press_releases', 'investment_memo']:
        # If we have fiscal calendar data and this is broker research, align with most recent earnings
        if doc_type == 'broker_research' and fiscal_periods:
            # Pick a recent fiscal period (0-2 quarters back for more recent research)
            period_idx = _stable_offset(seed_base + ['period'], 0, min(2, len(fiscal_periods) - 1))
            fiscal_period = fiscal_periods[period_idx]
            
            # Broker research typically published 7-45 days after earnings release
            # Earnings call is typically 14-30 days after period end
            period_end = fiscal_period['PERIOD_END_DATE']
            days_after_period_end = _stable_offset(seed_base + ['after_earnings'], 21, 75)
            publish_date = period_end + timedelta(days=days_after_period_end)

            # A note cannot be published after "today". For the most recent
            # fiscal period the offset runs past the anchor, which produced
            # research dated up to three weeks into the future.
            _anchor_dt = reference_date
            if not isinstance(publish_date, datetime):
                _anchor_dt = reference_date.date()
            if publish_date > _anchor_dt:
                publish_date = _anchor_dt

            dates['PUBLISH_DATE'] = publish_date.strftime('%d %B %Y')
            dates['FISCAL_QUARTER'] = fiscal_period['FISCAL_PERIOD']
            dates['FISCAL_YEAR'] = str(fiscal_period['FISCAL_YEAR'])
        else:
            # Fallback: Recent dates within last 90 days
            offset_days = _stable_offset(seed_base + ['recent'], 1, 90)
            publish_date = current_date - timedelta(days=offset_days)
            dates['PUBLISH_DATE'] = publish_date.strftime('%d %B %Y')
    
    elif doc_type in ['ngo_reports', 'engagement_notes']:
        # Use anchor_date (max_price_date) for consistent date alignment with other data
        # NGO reports within last 60 days for recency, engagement notes over 180 days for history
        anchor = _anchor_date if _anchor_date else current_date.date()
        if doc_type == 'ngo_reports':
            offset_days = _stable_offset(seed_base + ['ngo'], 1, 60)
        else:
            offset_days = _stable_offset(seed_base + ['engagement'], 1, 180)
        publish_date = datetime.combine(anchor, datetime.min.time()) - timedelta(days=offset_days)
        dates['PUBLISH_DATE'] = publish_date.strftime('%d %B %Y')
    
    
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

def apply_memo_analytics(context: Dict[str, Any], doc_type: str) -> None:
    """Derive the coupled valuation analytics used by research memos.

    These placeholders are not independent. A memo that samples them separately
    prints analysis that contradicts itself in ways any analyst reading the demo
    would spot immediately:

      - WACC must equal RFR + BETA * ERP, or the cost of capital does not follow
        from its own stated inputs.
      - Terminal growth must sit below WACC, or the terminal value is negative
        and the DCF is nonsense.
      - The Y1-Y3 projection must compound off one starting EPS and taper toward
        terminal growth, rather than three unrelated draws.
      - The implied multiple must reconcile to the price target that the rest of
        the document quotes.

    So they are derived here from values already in the context - the graded
    recommendation's price target and spot, plus the sector-bounded PE and growth
    - rather than sampled. Deterministic, and only fills what is not already set.
    """
    def _num(key: str, default: float) -> float:
        try:
            value = float(context.get(key))
            return value if value else default
        except (TypeError, ValueError):
            return default

    entity_id = context.get('SECURITY_ID') or context.get('ISSUER_ID') or 0
    seed_base = f"{entity_id}:{doc_type}:{config.RNG_SEED}"

    def _draw(name: str, low: float, high: float) -> float:
        span = _stable_hash(f"{seed_base}:{name}") % 10000 / 10000.0
        return low + span * (high - low)

    # Cost of capital, built up so the components reconcile.
    rfr = round(_draw('RFR', 3.5, 4.75), 2)
    erp = round(_draw('ERP', 4.0, 5.5), 2)
    beta = round(_draw('BETA', 0.75, 1.55), 2)
    wacc = round(rfr + beta * erp, 1)
    context.setdefault('RFR', rfr)
    context.setdefault('ERP', erp)
    context.setdefault('BETA', beta)
    context.setdefault('WACC', wacc)
    context.setdefault('WACC_PCT', wacc)

    # Terminal growth must stay below WACC for the model to converge.
    terminal = round(min(_draw('TERMINAL_GROWTH', 1.5, 3.25), wacc - 1.5), 2)
    context.setdefault('TERMINAL_GROWTH', terminal)
    context.setdefault('LT_GROWTH', terminal)

    # Three-year projection tapering from current growth toward terminal.
    g0 = max(min(_num('YOY_REVENUE_GROWTH_PCT', 10.0), 40.0), -10.0)
    growth = [round(g0 + (terminal - g0) * step, 1) for step in (0.25, 0.5, 0.75)]
    for idx, value in enumerate(growth, start=1):
        context.setdefault(f'Y{idx}_GROWTH', value)
        context.setdefault(f'YEAR{idx}_GROWTH', value)

    # EPS compounded off the multiple the document already quotes, so the
    # projection reconciles to spot rather than floating free.
    pe = max(_num('PE_RATIO', 20.0), 4.0)
    close = _num('CURRENT_PRICE', 100.0)
    eps = close / pe
    margin = round(_num('EBIT_MARGIN_PCT', 20.0), 1)
    fcf_margin = round(max(margin * 0.75, 4.0), 1)
    context.setdefault('FCF_MARGIN', fcf_margin)

    running_eps = eps
    for idx, value in enumerate(growth, start=1):
        running_eps = running_eps * (1 + value / 100.0)
        context.setdefault(f'Y{idx}_EPS', round(running_eps, 2))
        # Free cash flow per share tracks EPS at the FCF margin's share of EBIT.
        context.setdefault(f'Y{idx}_FCF', round(running_eps * fcf_margin / max(margin, 1.0), 2))
        context.setdefault(f'Y{idx}_MARGIN', round(margin + idx * 0.4, 1))

    context.setdefault('TERMINAL_MARGIN', round(margin + 1.6, 1))
    context.setdefault('FCF_CAGR', round(sum(growth) / len(growth), 1))

    # Multiples reconciled to the target the recommendation produced.
    target = _num('PRICE_TARGET_USD', close)
    y1_eps = float(context.get('Y1_EPS') or eps)
    context.setdefault('PE_VALUE', round(target / max(y1_eps, 0.01), 1))
    context.setdefault('SALES_VALUE', round(target / max(y1_eps * 4.0, 0.01), 2))
    # Premium/discount of the target against spot, so the sign always agrees
    # with the upside the document quotes.
    context.setdefault('PREMIUM_DISCOUNT', round((target / max(close, 0.01) - 1) * 100, 1))

    # Committee and review dates, anchored on the document's own publish date.
    publish = context.get('PUBLISH_DATE')
    base = None
    if publish:
        for fmt in ('%d %B %Y', '%Y-%m-%d'):
            try:
                base = datetime.strptime(str(publish), fmt).date()
                break
            except (ValueError, TypeError):
                continue
    base = base or _anchor_date or date.today()
    for key, low, high in (('IC_DATE', 7, 30), ('IC_MEETING_DATE', 7, 30),
                           ('NEXT_REVIEW_DATE', 80, 100)):
        if key not in context:
            offset = _stable_offset([entity_id, doc_type, key], low, high)
            context[key] = (base + timedelta(days=offset)).strftime('%d %B %Y')

    if 'CARBON_NEUTRAL_STATUS' not in context:
        options = ['committed to 2040', 'committed to 2050', 'targeting 2035',
                   'no published target']
        context['CARBON_NEUTRAL_STATUS'] = options[
            _stable_hash(f"{seed_base}:carbon") % len(options)
        ]


def apply_derived_placeholders(context: Dict[str, Any], doc_type: str) -> None:
    """Fill non-numeric placeholders that have a real source in the context.

    These have no entry in numeric_bounds.yaml because they are not numerics, so
    before this they rendered literally as "{{SUB_INDUSTRY}}" in the published
    text. Each is derived from something real rather than invented.
    """
    # The issuer's actual industry description, not a generic label.
    if 'SUB_INDUSTRY' not in context:
        context['SUB_INDUSTRY'] = context.get('SIC_DESCRIPTION') or 'diversified'

    # Templates write "Q{{QUARTER}}", so this is the bare quarter number. Taken
    # from the fiscal quarter already resolved from the real filing calendar.
    if 'QUARTER' not in context:
        fq = str(context.get('FISCAL_QUARTER', ''))
        digits = ''.join(ch for ch in fq.split(' ')[0] if ch.isdigit())
        context['QUARTER'] = digits or '4'

    # Forward-looking catalyst dates, anchored on the document's own publish date
    # so a note never points at a readout that already happened when it was
    # written. Deterministic offsets keep the document reproducible.
    publish = context.get('PUBLISH_DATE')
    base = None
    if publish:
        for fmt in ('%d %B %Y', '%Y-%m-%d'):
            try:
                base = datetime.strptime(str(publish), fmt).date()
                break
            except (ValueError, TypeError):
                continue
    if base is None:
        base = _anchor_date or date.today()

    entity_id = context.get('SECURITY_ID') or context.get('ISSUER_ID') or 0
    for placeholder, low, high in (
        ('NEXT_DATA_READOUT', 45, 150),
        ('NEXT_APPROVAL_DATE', 90, 270),
    ):
        if placeholder in context:
            continue
        offset = _stable_offset([entity_id, doc_type, placeholder], low, high)
        context[placeholder] = (base + timedelta(days=offset)).strftime('%B %Y')


def apply_stance_to_context(context: Dict[str, Any], doc_type: str) -> None:
    """Resolve the stance-dependent prose placeholders from the rating.

    Templates previously hard-coded bullish language, so a Sell-rated note still
    claimed a "positive view" and "strong unit economics". The stance-dependent
    sentences are now placeholders filled from config.STANCE_PHRASES, keyed on the
    stance the rating implies, so prose and rating can no longer contradict.

    Deterministic per document, and only fills placeholders that are not already
    set, so a template or caller can override any individual one.
    """
    rating = context.get('RATING')
    stance = config.RATING_TO_STANCE.get(rating)
    if not stance:
        return

    context['RATING_STANCE'] = stance
    entity_id = (
        context.get('SECURITY_ID') or context.get('ISSUER_ID')
        or context.get('PORTFOLIO_ID') or 0
    )
    doc_num = context.get('_doc_num', 0)

    for placeholder, options in config.STANCE_PHRASES[stance].items():
        if context.get(placeholder):
            continue
        seed = f"{entity_id}:{doc_type}:{doc_num}:{placeholder}:{config.RNG_SEED}"
        context[placeholder] = options[_stable_hash(seed) % len(options)]


def resolve_recommendation_as_of(
    candidates: Optional[List[Dict[str, Any]]],
    publish_date: Optional[str],
    entity_id: Any,
) -> Optional[Dict[str, Any]]:
    """Pick the recommendation row a document should quote.

    Two steps, both deterministic:

    1. As-of resolution. Take the newest vintage on or before the document's
       publish date, so a note dated 18 months ago quotes the house view that was
       current then rather than today's. If the document predates every vintage,
       fall back to the oldest available rather than returning nothing.
    2. Broker selection. Pick one of the brokers covering that security at that
       vintage, keyed on the security so a stock is consistently covered by the
       same house. The broker name comes from the chosen row, which guarantees the
       document and its numbers always agree - picking a broker first and then
       looking it up could select a house that does not cover the stock.
    """
    if not candidates:
        return None

    as_of = None
    if publish_date:
        for fmt in ('%d %B %Y', '%Y-%m-%d'):
            try:
                as_of = datetime.strptime(str(publish_date), fmt).date()
                break
            except (ValueError, TypeError):
                continue

    def _vintage(row: Dict[str, Any]) -> Optional[date]:
        v = row.get('VINTAGEDATE')
        return v if isinstance(v, date) else None

    eligible = candidates
    if as_of is not None:
        on_or_before = [r for r in candidates if _vintage(r) and _vintage(r) <= as_of]
        if on_or_before:
            newest = max(_vintage(r) for r in on_or_before)
            eligible = [r for r in on_or_before if _vintage(r) == newest]
        else:
            oldest = min((_vintage(r) for r in candidates if _vintage(r)), default=None)
            eligible = [r for r in candidates if _vintage(r) == oldest] or candidates

    eligible = sorted(eligible, key=lambda r: str(r.get('BROKERNAME', '')))
    idx = _stable_hash(f"{entity_id}:broker:{config.RNG_SEED}") % len(eligible)
    return eligible[idx]


def apply_recommendation_to_context(context: Dict[str, Any], rec: Dict[str, Any]) -> None:
    """Populate the rating/target placeholder family from a recommendation row.

    These were previously invented independently - RATING drawn at random,
    PRICE_TARGET_USD sampled uniformly over sector bounds, and UPSIDE_POTENTIAL
    sampled separately rather than computed - so a Strong Sell note could quote
    positive upside and a target unrelated to the share price. Taking all of them
    from one row makes the document internally consistent and consistent with
    FACT_ESTIMATE_DATA, which is projected from the same table.
    """
    target = float(rec['PRICETARGET'])
    close = float(rec['CLOSEPRICE'])
    upside_pct = round(float(rec['UPSIDEPCT']) * 100, 1)

    context['BROKER_NAME'] = rec['BROKERNAME']
    context['RATING'] = rec['RATING']
    context['PRIOR_RATING'] = rec.get('PRIORRATING') or rec['RATING']
    context['RATING_ACTION'] = rec.get('RATINGACTION') or 'initiate'
    context['VALUATION_DRIVERS'] = rec.get('DRIVERSUMMARY') or ''
    context['VALUATION_BASIS'] = rec.get('VALUATIONBASIS') or ''

    context['CURRENT_PRICE'] = round(close, 2)
    context['PRICE_TARGET_USD'] = round(target, 2)
    context['TARGET_PRICE_USD'] = round(target, 2)
    context['FAIR_VALUE_USD'] = round(float(rec['FAIRVALUE']), 2)
    # Upside is computed, never sampled, so it always agrees with the target.
    context['UPSIDE_POTENTIAL'] = upside_pct
    context['UPSIDE_POTENTIAL_PCT'] = upside_pct
    context['UPSIDE_PCT'] = upside_pct

    prior_target = rec.get('PRIORPRICETARGET')
    context['PRIOR_PRICE_TARGET_USD'] = (
        round(float(prior_target), 2) if prior_target is not None else round(target, 2)
    )

    # Scenario and action levels. internal_research and investment_memo quote a
    # bull/bear case, a valuation range and add/trim levels; left to the generic
    # numeric sampler these contradicted the target - a bear case above the bull
    # case, or a "downside" that was positive. Deriving them all from the same
    # fair value keeps the memo internally consistent.
    fair_value = float(rec['FAIRVALUE'])
    spread = config.MEMO_VALUATION['scenario_spread']
    bull = fair_value * (1 + spread)
    bear = fair_value * (1 - spread)

    context['BULL_CASE_PRICE'] = round(bull, 2)
    context['BEAR_CASE_PRICE'] = round(bear, 2)
    context['BEAR_FAIR_VALUE'] = round(bear, 2)
    context['FAIR_VALUE_LOW'] = round(fair_value * 0.90, 2)
    context['FAIR_VALUE_HIGH'] = round(fair_value * 1.10, 2)
    context['VALUATION_LOW'] = round(fair_value * 0.90, 2)
    context['VALUATION_HIGH'] = round(fair_value * 1.10, 2)
    # Downside is measured to the bear case, so it is negative whenever the bear
    # case sits below spot - which is the only way the word makes sense.
    context['DOWNSIDE_PCT'] = round((bear / close - 1) * 100, 1)

    # Action levels bracket spot, so "add below" is genuinely below and "trim
    # above" genuinely above.
    add_price = close * 0.95
    context['ADD_PRICE'] = round(add_price, 2)
    context['ENTRY_PRICE_HIGH'] = round(close * 1.03, 2)
    context['TRIM_PRICE'] = round(max(target, close) * 1.02, 2)
    context['ADD_UPSIDE'] = round((target / add_price - 1) * 100, 1)

    # Position sizing tracks conviction: a Strong Sell memo should not recommend
    # the same weight as a Strong Buy.
    size_pct = config.MEMO_VALUATION['position_size_by_rating'].get(rec['RATING'], 1.5)
    context['POSITION_SIZE_PCT'] = size_pct
    context['POSITION_SIZE_USD'] = round(
        size_pct / 100 * config.MEMO_VALUATION['reference_aum_usd']
    )


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
        # Broker, analyst and rating come from the grounded recommendation row
        # when one is available (see apply_recommendation_to_context, called by
        # the hydration loop). These are only fallbacks for the case where no
        # recommendation exists for the security - e.g. an issuer with no usable
        # fundamentals - so a document can still render.
        if 'BROKER_NAME' not in provider_context and 'BROKER_NAME' not in context:
            broker_index = _stable_hash(f"{entity_id}:broker:{config.RNG_SEED}") % len(config.BROKER_NAMES)
            provider_context['BROKER_NAME'] = config.BROKER_NAMES[broker_index]

        # Generate analyst name
        analyst_id = (_stable_hash(f"{entity_id}:analyst:{config.RNG_SEED}") % 100) + 1
        provider_context['ANALYST_NAME'] = f'Analyst_{analyst_id:02d}'

        # RATING is no longer drawn at random - it is derived from implied upside
        # in FACT_RECOMMENDATION. Only fall back to a draw if no row was found.
        if 'RATING' not in context:
            provider_context['RATING'] = select_from_distribution('rating')
        
        # Add portfolio name for investment memos
        if doc_type == 'investment_memo':
            provider_context['PORTFOLIO_NAME'] = config.DEFAULT_DEMO_PORTFOLIO
        
        # Add investment memo specific placeholders (competitors, etc.)
        tech_competitors = ['Salesforce', 'Oracle', 'SAP', 'Adobe', 'ServiceNow', 'Workday', 'Splunk', 'Datadog']
        semiconductor_competitors = ['NVIDIA', 'AMD', 'Intel', 'Broadcom', 'Qualcomm', 'TSMC', 'Marvell Technology', 'Micron Technology']
        healthcare_competitors = ['Pfizer', 'Johnson & Johnson', 'AbbVie', 'Merck', 'Bristol-Myers Squibb', 'Eli Lilly']
        financial_competitors = ['JPMorgan', 'Bank of America', 'Goldman Sachs', 'Morgan Stanley', 'Wells Fargo']
        consumer_discretionary_competitors = ['Amazon', 'Tesla', 'Home Depot', 'Nike', "McDonald's", 'Starbucks', 'Booking Holdings', "Lowe's"]
        communication_services_competitors = ['Alphabet', 'Meta Platforms', 'Netflix', 'Walt Disney', 'Comcast', 'T-Mobile', 'Verizon', 'AT&T']
        
        sector = context.get('SIC_DESCRIPTION', 'Information Technology')
        ticker = context.get('TICKER', '')
        company_name = context.get('COMPANY_NAME', '')
        semi_tickers = {'NVDA', 'AMD', 'INTC', 'AVGO', 'QCOM', 'TSM'}
        if ticker in semi_tickers or 'Semiconductor' in sector or 'Electronic' in sector:
            competitors = [c for c in semiconductor_competitors if c.upper() not in company_name.upper()]
        elif 'Health' in sector or 'Pharma' in sector or 'Medical' in sector:
            competitors = healthcare_competitors
        elif 'Financ' in sector or 'Bank' in sector or 'Insurance' in sector:
            competitors = financial_competitors
        elif 'Consumer Disc' in sector or 'Retail' in sector:
            competitors = [c for c in consumer_discretionary_competitors if c.upper() not in company_name.upper()]
        elif 'Communication' in sector or 'Media' in sector or 'Telecom' in sector:
            competitors = [c for c in communication_services_competitors if c.upper() not in company_name.upper()]
        else:
            competitors = tech_competitors
        
        # Select 3 different competitors deterministically
        comp1_idx = _stable_hash(f"{entity_id}:comp1:{config.RNG_SEED}") % len(competitors)
        comp2_idx = (comp1_idx + 1) % len(competitors)
        comp3_idx = (comp1_idx + 2) % len(competitors)
        provider_context['COMPETITOR_1'] = competitors[comp1_idx]
        provider_context['COMPETITOR_2'] = competitors[comp2_idx]
        provider_context['COMPETITOR_3'] = competitors[comp3_idx]
    
    elif doc_type == 'ngo_reports':
        # Determine ESG category (from template or random)
        category = context.get('_category', random.choice(['environmental', 'social', 'governance']))
        
        # Select NGO from appropriate category
        category_ngos = config.FICTIONAL_NGO_NAMES.get(category, config.FICTIONAL_NGO_NAMES['environmental'])
        ngo_index = _stable_hash(f"{entity_id}:ngo:{category}:{config.RNG_SEED}") % len(category_ngos)
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
        city_index = _stable_hash(f"{entity_id}:city:{config.RNG_SEED}") % len(cities)
        provider_context['CITY'] = cities[city_index]
        
        # Generate executive name deterministically
        ceo_id = _stable_hash(f"{entity_id}:ceo:{config.RNG_SEED}") % 100
        provider_context['CEO_NAME'] = f'CEO_{ceo_id:02d}'
        
        cfo_id = _stable_hash(f"{entity_id}:cfo:{config.RNG_SEED}") % 100
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
        drug_index = _stable_hash(f"{entity_id}:drug:{config.RNG_SEED}") % len(drug_names)
        provider_context['DRUG_NAME'] = drug_names[drug_index]
        
        indications = ['Type 2 Diabetes', 'Cardiovascular Disease', 'Oncology', 'Immunology']
        indication_index = _stable_hash(f"{entity_id}:indication:{config.RNG_SEED}") % len(indications)
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
        product_index = _stable_hash(f"{entity_id}:product:{config.RNG_SEED}") % len(products)
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
    # numeric_bounds.yaml is keyed by GICS sector, but the context carries the
    # raw SIC description ("Services-Prepackaged Software"), which never matched.
    # Every security-level document was therefore sampling from the generic
    # _default bounds rather than its sector's, and any sector-specific
    # placeholder resolved to nothing and rendered literally.
    sic_description = context.get('SIC_DESCRIPTION', '')
    sector = map_sic_to_gics(sic_description) or sic_description or 'Information Technology'
    # map_sic_to_gics returns the YAML spelling 'Health Care' while the resolver
    # normalises its keys to the DIM_ISSUER spelling 'Healthcare', so without
    # this every healthcare name also fell through to the defaults.
    sector = config.SECTOR_NAME_ALIASES.get(sector, sector)

    bounds = get_numeric_bounds_for_doc_type(doc_type, sector)
    
    # Sample each numeric placeholder deterministically (ONLY if not already set)
    for placeholder, bound_spec in bounds.items():
        # Skip placeholders that already have values (e.g., from SEC financial data)
        if placeholder in context and context[placeholder] is not None:
            continue
        
        # Builtin hash() is salted per process, so this seed - and therefore
        # every Tier 1 numeric including the price target shown in document
        # titles - changed on every build. _stable_hash keeps it reproducible.
        seed = config.RNG_SEED + _stable_hash(f"{entity_id}|{doc_type}|{placeholder}")
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

# Safety-net bounds for placeholders that numeric_bounds.yaml does not define.
# Many are template-specific (ONCOLOGY_REVENUE, CARDIO_GROWTH, DIGITAL_GROWTH),
# so this must stay in code: dropping it would leave those placeholders unbound.
_DEFAULT_NUMERIC_BOUNDS = {
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
            'BRAND_AWARENESS': {'min': 2, 'max': 8},
            # Templates are cross-applied: a technology variant can be selected
            # for a name whose SIC maps to another sector, so these
            # template-specific placeholders need a bound for every sector or
            # they render literally as "{{CLOUD_REVENUE_PCT}}". The YAML holds
            # the sector-tuned values; these are the safety net.
            'CLOUD_REVENUE_PCT': {'min': 25, 'max': 65},
            'SOFTWARE_REVENUE_PCT': {'min': 20, 'max': 55},
            'SERVICES_REVENUE_PCT': {'min': 8, 'max': 30},
            'NA_REVENUE_PCT': {'min': 40, 'max': 70},
            'EUROPE_REVENUE_PCT': {'min': 15, 'max': 35},
            'R_AND_D_INTENSITY_PCT': {'min': 6, 'max': 25},
            'CLOUD_GROWTH': {'min': 15, 'max': 45},
            'CLOUD_GROWTH_PCT': {'min': 15, 'max': 45},
            'GROWTH_RATE': {'min': 4, 'max': 22},
            'REVENUE_CAGR': {'min': 3, 'max': 18},
            'CURRENT_MARGIN': {'min': 12, 'max': 32},
            'TARGET_MARGIN': {'min': 18, 'max': 40},
            'PORTFOLIO_RISK_CONTRIBUTION': {'min': 0.5, 'max': 6.0},
            'NIM_EXPANSION_BPS': {'min': -25, 'max': 60},
            'RATE_SENSITIVITY_PCT': {'min': 2, 'max': 15},
            'DEPOSIT_BETA_PCT': {'min': 25, 'max': 70},
            'LOAN_GROWTH_PCT': {'min': 1, 'max': 12},
            'EFFICIENCY_RATIO_PCT': {'min': 45, 'max': 70},
            # Remaining memo placeholders that are genuinely independent. The
            # coupled ones (WACC, RFR, ERP, BETA, terminal growth, the Y1-Y3
            # projection, and the implied multiples) are NOT here - they are
            # derived in apply_memo_analytics so they reconcile with each other
            # and with the price target.
            'APAC_REVENUE_PCT': {'min': 10, 'max': 30},
            'OTHER_REVENUE_PCT': {'min': 3, 'max': 15},
            'MARGIN_EXPANSION': {'min': 0.5, 'max': 4.0},
            'INTL_TARGET': {'min': 30, 'max': 60},
            'PRICE_TO_BOOK': {'min': 1.0, 'max': 8.0},
            'PAYOUT_RATIO_PCT': {'min': 15, 'max': 60},
            'SECTOR_CAGR': {'min': 4, 'max': 18},
            'ROIC': {'min': 8, 'max': 30},
            'EV_SALES': {'min': 2.0, 'max': 12.0},
            'NET_CASH': {'min': 2, 'max': 60},
            'OCF': {'min': 3, 'max': 70},
            'OPERATING_CASH_FLOW': {'min': 0.5, 'max': 15},
            'CET1_RATIO_PCT': {'min': 11, 'max': 16},
            'NET_RETENTION': {'min': 100, 'max': 135},
            'CUSTOMER_COUNT': {'min': 2000, 'max': 90000},
            'CUSTOMER_GROWTH': {'min': 5, 'max': 30},
            'ACV': {'min': 25000, 'max': 250000},
            'ACV_GROWTH': {'min': 3, 'max': 20},
            'CLOUD_ARR': {'min': 2, 'max': 45},
            'ERP_SPEND': {'min': 1, 'max': 20},
            'GROWTH_PREMIUM': {'min': 5, 'max': 30},
            'MARGIN_PREMIUM': {'min': 2, 'max': 18},
            'SOFTWARE_PREMIUM': {'min': 5, 'max': 35},
            'SECTOR_TOTAL': {'min': 8, 'max': 30},
            'PORTFOLIO_WEIGHT': {'min': 0.5, 'max': 5.0},
            'PORTFOLIO_CONTRIBUTION': {'min': 0.2, 'max': 4.0},
            'RISK_BUDGET_PCT': {'min': 2, 'max': 12},
            'TRANSACTION_VALUE': {'min': 5, 'max': 120},
            'AI_ALLOCATION': {'min': 5, 'max': 25},
            'TECH_ALLOCATION': {'min': 15, 'max': 40},
            'THEMATIC_ALLOCATION': {'min': 5, 'max': 20},
}

# numeric_bounds.yaml nests bounds under a scope (security / portfolio / global).
# Flatten those so a doc_type resolves regardless of which scope it lives in.
_BOUNDS_SCOPES = ('security', 'portfolio', 'global')

# Doc types that legitimately share broker_research bounds. The YAML defines all
# 11 sectors for broker_research but only 'Information Technology' for
# internal_research, and nothing at all for investment_memo - so without this
# chain those doc types would fall back to IT bounds whatever the real sector.
_BOUNDS_DOC_TYPE_PARENT = {
    'internal_research': 'broker_research',
    'investment_memo': 'broker_research',
    'earnings_transcripts': 'broker_research',
}

# Keys used inside a doc_type when there is no per-sector breakdown.
_BOUNDS_NON_SECTOR_KEYS = ('returns', 'general')


def _flattened_bounds() -> Dict[str, Dict[str, Any]]:
    """doc_type -> sector -> bounds, flattened across numeric_bounds.yaml scopes."""
    raw = config.get_numeric_bounds()
    flat: Dict[str, Dict[str, Any]] = {}
    for scope in _BOUNDS_SCOPES:
        for doc_type, sectors in (raw.get(scope) or {}).items():
            if isinstance(sectors, dict):
                flat.setdefault(doc_type, {}).update(sectors)
    return flat


def get_numeric_bounds_for_doc_type(doc_type: str, sector: str) -> Dict[str, Dict[str, float]]:
    """
    Get numeric bounds for a document type and sector.

    Loads content_library/_rules/numeric_bounds.yaml, which is the canonical
    source and covers all 11 GICS sectors. This previously used a hard-coded map
    holding only 5 sectors, so Consumer Staples, Industrials, Energy, Materials,
    Utilities, Real Estate and Healthcare all silently fell back to generic
    defaults.

    Sector names are normalised via config.SECTOR_NAME_ALIASES because the YAML
    says 'Health Care' where DIM_ISSUER says 'Healthcare'.

    Args:
        doc_type: Document type
        sector: GICS sector as it appears in DIM_ISSUER

    Returns:
        Dict mapping placeholder names to {min, max} bounds
    """
    flat = _flattened_bounds()

    # Normalise YAML sector spellings to the DIM_ISSUER spelling.
    def _normalise(sectors: Dict[str, Any]) -> Dict[str, Any]:
        return {config.SECTOR_NAME_ALIASES.get(k, k): v for k, v in sectors.items()}

    candidates = [doc_type]
    parent = _BOUNDS_DOC_TYPE_PARENT.get(doc_type)
    if parent:
        candidates.append(parent)

    resolved: Dict[str, Dict[str, float]] = {}
    for candidate in candidates:
        sectors = _normalise(flat.get(candidate) or {})
        if not sectors:
            continue
        if sector in sectors:
            resolved = dict(sectors[sector])
            break
        for key in _BOUNDS_NON_SECTOR_KEYS:
            if key in sectors:
                resolved = dict(sectors[key])
                break
        if resolved:
            break

    # Templates are cross-applied across sectors, so a placeholder the YAML only
    # defines for one sector (TAM_BILLIONS, NRR_PCT, CLOUD_GROWTH_PCT under
    # Information Technology) would otherwise render literally for every other
    # sector. Borrow the bound from another sector of the same doc type.
    for candidate in candidates:
        for sector_bounds in _normalise(flat.get(candidate) or {}).values():
            if not isinstance(sector_bounds, dict):
                continue
            for key, value in sector_bounds.items():
                if isinstance(value, dict) and 'min' in value:
                    resolved.setdefault(key, value)

    if not resolved and doc_type not in flat and not parent:
        # Unknown doc type: defaults only, matching the previous behaviour of
        # returning nothing rather than guessing another doc type's bounds.
        return {}

    # Merge the safety net for any placeholder the YAML does not define.
    for key, value in _DEFAULT_NUMERIC_BOUNDS.items():
        resolved.setdefault(key, value)

    return resolved

# ============================================================================
# MODULE: Tier 2 Derivations (Portfolio Metrics from CURATED Tables)
# ============================================================================


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
    current_date = (datetime.combine(_anchor_date, datetime.min.time())
                    if _anchor_date else datetime.now())
    week_start = current_date - timedelta(days=current_date.weekday())
    week_hash = _stable_hash(week_start.strftime('%Y-%W'))
    
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

def write_to_raw_table(
    session: Session,
    doc_type: str,
    documents: List[Dict[str, Any]],
    full_rebuild: bool = False,
):
    """
    Write rendered documents to RAW table using Context-First approach.

    Args:
        session: Snowpark session
        doc_type: Document type
        documents: List of dicts with 'rendered' content and 'context'
        full_rebuild: Replace the table instead of merging into it. Only for an
            intentional rebuild - the weekly refresh must never set this, or it
            would discard every previously published vintage.
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
            # Fall back to a content hash rather than Python's salted hash(),
            # which produced a different id for identical content on every run.
            'DOCUMENT_ID': ctx.get(
                '_document_id',
                hashlib.md5(rendered.encode('utf-8')).hexdigest()
            ),
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
        
        
        data.append(row)
    
    # Create DataFrame and write to table
    if data:
        df = session.create_dataframe(data)

        if full_rebuild:
            df.write.mode("overwrite").save_as_table(table_name)
            return

        # Append-only and idempotent. Overwriting here discarded every earlier
        # vintage, which is what made the weekly refresh destructive: documents
        # are immutable once published, and a rerun of the same vintage must be a
        # no-op rather than a duplicate. DOCUMENT_ID is deterministic (logical
        # identity plus vintage), so it is a safe merge key - a blind append
        # would duplicate a regenerated document instead.
        staging_table = f"{table_name}__STAGING"
        df.write.mode("overwrite").save_as_table(staging_table, table_type="transient")
        try:
            session.sql(
                f"CREATE TABLE IF NOT EXISTS {table_name} LIKE {staging_table}"
            ).collect()

            columns = [f'"{c}"' if not c.startswith('"') else c for c in df.columns]
            assignments = ", ".join(f"tgt.{c} = src.{c}" for c in columns)
            column_list = ", ".join(columns)
            source_list = ", ".join(f"src.{c}" for c in columns)

            session.sql(f"""
                MERGE INTO {table_name} AS tgt
                USING {staging_table} AS src
                ON tgt."DOCUMENT_ID" = src."DOCUMENT_ID"
                WHEN MATCHED THEN UPDATE SET {assignments}
                WHEN NOT MATCHED THEN INSERT ({column_list}) VALUES ({source_list})
            """).collect()
        finally:
            session.sql(f"DROP TABLE IF EXISTS {staging_table}").collect()

# ============================================================================
# PDF EXPORT
# ============================================================================

def export_documents_to_pdf(doc_type: str, documents: List[Dict[str, Any]]):
    """
    Export rendered documents to PDF files.
    
    Creates per-doc-type subfolders and generates branded PDFs with
    internal or external headers/footers based on document type.
    
    Args:
        doc_type: Document type (e.g., 'broker_research')
        documents: List of dicts with 'rendered' content and 'context'
    """
    # Check if PDF export is enabled
    if not config.PDF_EXPORT_ENABLED:
        return
    
    # Check if this doc_type should be exported
    audience = config.PDF_DOC_AUDIENCE.get(doc_type, 'internal')
    if audience == 'skip':
        log_warning(f"  Skipping PDF export for {doc_type} (configured as 'skip')")
        return
    
    if not documents:
        return
    
    try:
        from core import pdf_exporter
        import shutil
        output_dir = pdf_exporter.get_output_directory()
        
        doc_type_dir = os.path.join(output_dir, doc_type)
        if os.path.exists(doc_type_dir):
            shutil.rmtree(doc_type_dir)
    except ImportError as e:
        log_warning(f"  PDF export unavailable (reportlab not installed): {e}")
        return
    
    exported_count = 0
    failed_count = 0
    
    for doc in documents:
        try:
            document_id = doc['context'].get(
                '_document_id',
                hashlib.md5(doc['rendered'].encode('utf-8')).hexdigest()
            )
            result = pdf_exporter.export_document_to_pdf(
                markdown_content=doc['rendered'],
                doc_type=doc_type,
                context=doc['context'],
                output_dir=output_dir,
                document_id=document_id
            )
            if result:
                exported_count += 1
            else:
                failed_count += 1
        except Exception as e:
            log_warning(f"  PDF export failed for document: {e}")
            failed_count += 1
    
    if exported_count > 0:
        log_detail(f"  Exported {exported_count} PDFs to {output_dir}/{doc_type}/")
    if failed_count > 0:
        log_warning(f"  {failed_count} PDF exports failed for {doc_type}")


# ============================================================================
# PUBLIC API
# ============================================================================

def hydrate_documents(
    session: Session,
    doc_type: str,
    test_mode: bool = False,
    entities: Optional[List[Dict[str, Any]]] = None,
) -> int:
    """
    Main hydration function: load templates, build contexts, render documents.
    
    Pipeline-only architecture:
    - PDF doc types: export PDFs only (no DB write) - pipeline parses and loads
    - Non-PDF doc types: write to RAW table - pipeline stream triggers corpus build
    
    Uses batched prefetch for efficiency (no per-entity SELECT queries per performance-io.mdc).
    
    Args:
        session: Snowpark session
        doc_type: Document type to hydrate
        test_mode: If True, use reduced document counts for faster development
        entities: Restrict generation to these entities instead of the full
            coverage set. The weekly refresh needs this: cadence decides per
            *entity* whether a new vintage is due, and without the filter every
            stock would get a fresh note whenever any one of them triggered -
            which is the weekly-churn behaviour the cadence registry exists to
            prevent. Defaults to the full set, so the initial build is unchanged.
    
    Returns:
        Number of documents generated
    """
    from utils import snowflake as snowflake_io_utils
    
    # Set module-level anchor date for consistent date generation
    # All document dates will be relative to max_price_date from stock prices
    global _anchor_date
    if _anchor_date is None:
        _anchor_date = get_max_price_date(session)
    
    # Load templates
    templates = load_templates(doc_type)
    
    # Get entities to hydrate (or use the caller's restricted set)
    if entities is None:
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

    # Grounded recommendations keyed by SecurityID (research-style docs only)
    recommendation_cache: Dict[int, List[Dict[str, Any]]] = {}
    
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

        # Grounded ratings and price targets for research-style documents. One
        # query for every security; the as-of vintage and broker are resolved
        # per document in Python.
        if doc_type in ['broker_research', 'internal_research', 'investment_memo']:
            recommendation_cache = snowflake_io_utils.prefetch_recommendations(
                session, database_name, security_ids
            )
            if not recommendation_cache:
                log_warning(
                    f"  No FACT_RECOMMENDATION rows for {doc_type} securities - "
                    "ratings and price targets will fall back to sampled values. "
                    "Build recommendations first (data.recommendations)."
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
            # Seed the RNG deterministically per document, before any context is
            # built. A number of placeholders (NGO emissions figures, board
            # composition, product names) still use random.*; seeding here once
            # makes all of them reproducible across builds without having to
            # rewrite every call site. Keyed on the document's logical identity
            # plus the build anchor, so the same document regenerates identically
            # while different documents stay varied.
            random.seed(_stable_hash(
                f"{doc_type}|{entity.get('id')}|{entity.get('doc_num', 0)}"
                f"|{config.RNG_SEED}|{_anchor_date or ''}"
            ))

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
                if context is not None and entity.get('meeting_type'):
                    context['MEETING_TYPE'] = entity['meeting_type']
            elif linkage_level == 'portfolio':
                context = build_portfolio_context_from_prefetch(
                    session,
                    prefetched_contexts.get(entity['id']),
                    doc_type,
                    entity.get('doc_num', 0)
                )
            else:  # global
                context = build_global_context(doc_type, entity.get('num', 0))
            
            if context is None:
                log_warning(f"  No prefetched data for {doc_type} entity {entity.get('id')}")
                continue

            # Apply the grounded rating and price target family. Done after the
            # context (and therefore PUBLISH_DATE) exists, so the as-of lookup
            # uses the document's own vintage, and before template selection and
            # rendering so both see the real rating.
            if recommendation_cache:
                rec = resolve_recommendation_as_of(
                    recommendation_cache.get(entity['id']),
                    context.get('PUBLISH_DATE'),
                    entity['id'],
                )
                if rec:
                    apply_recommendation_to_context(context, rec)
                else:
                    log_detail(
                        f"  No recommendation for {doc_type} security "
                        f"{entity.get('id')} - falling back to sampled rating"
                    )
            
            # Resolve stance-dependent prose from the rating, whatever its
            # source, so template selection and the rendered text agree with it.
            apply_stance_to_context(context, doc_type)
            apply_derived_placeholders(context, doc_type)
            apply_memo_analytics(context, doc_type)

            # Select appropriate template
            template = select_template(templates, context)
            
            # Override SEVERITY_LEVEL from template metadata for NGO reports
            # This ensures metadata field matches hardcoded severity in template body
            if doc_type == 'ngo_reports':
                template_severity = template.get('metadata', {}).get('severity', '')
                if template_severity:
                    context['SEVERITY_LEVEL'] = template_severity.title()  # 'high' -> 'High'
            
            # Render template
            rendered, enriched_context = render_template(template, context)

            doc_num = entity.get('doc_num', 0)
            # Keyed on logical identity plus the document's own vintage, so
            # re-running a vintage is idempotent and a new vintage is naturally a
            # new document. PUBLISH_DATE is the vintage for every dated doc type;
            # undated types fall back to the build anchor.
            doc_vintage = (
                enriched_context.get('PUBLISH_DATE')
                or enriched_context.get('REPORT_DATE')
                or enriched_context.get('TEMPLATE_DATE')
                or (_anchor_date.strftime('%d %B %Y') if _anchor_date else '')
            )
            enriched_context['_document_id'] = make_document_id(
                doc_type, entity['id'], doc_num, doc_vintage
            )
            
            documents.append({
                'rendered': rendered,
                'context': enriched_context
            })
            
        except Exception as e:
            log_warning(f"  Failed to hydrate {doc_type} for entity {entity.get('id')}: {e}")
            continue
    
    # Pipeline-only architecture: determine output path based on document audience
    audience = config.PDF_DOC_AUDIENCE.get(doc_type, 'skip')
    
    if audience in ('internal', 'external'):
        # PDF doc type: export PDFs only (no DB write)
        # Pipeline will parse PDFs from stage and write to RAW/CORPUS tables
        export_documents_to_pdf(doc_type, documents)
    else:
        # Non-PDF doc type: write to RAW table
        # Pipeline stream will trigger corpus build task
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


def _latest_sec_period(
    cik_financials: Dict[tuple, Dict[str, Any]],
    period: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Most recently filed period for one CIK, by PERIOD_END_DATE.

    Pass period='FY' to restrict to annual rows. Returns None when the cache holds
    nothing usable. Ordering uses PERIOD_END_DATE rather than the (year, period) key
    because fiscal years do not align with calendar years - sorting on the key would
    put a January-ending FY2026 after a June-ending FY2026.
    """
    candidates = [
        data for (_, per), data in cik_financials.items()
        if (period is None or per == period) and data.get('PERIOD_END_DATE')
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda d: d['PERIOD_END_DATE'])


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
    
    # Some doc types carry no fiscal context at all - internal_research and
    # investment_memo are dated but not period-aligned. They still quote revenue
    # growth, so returning {} here handed those figures to the randomiser too.
    # Leave fiscal_year/fiscal_period unset and let the lookups below fall through
    # to the most recent filed period.
    cik_financials = sec_financials_cache.get(cik, {})
    if not cik_financials:
        return {}
    
    # Look up matching financial data
    period_key = (fiscal_year, fiscal_period)
    period_data = cik_financials.get(period_key)

    # The requested period is frequently not filed yet. Document dates are anchored
    # on the latest price date, and a company whose fiscal year ends mid-calendar is
    # already into a fiscal year SEC has no data for - at a 2026-09-18 anchor, NVDA
    # is in FY2027 Q1 while FACT_SEC_FINANCIALS stops at FY2026. Returning {} here
    # left every figure to the seeded randomiser, whose REVENUE_BILLIONS bound is
    # 5-150, which is how a broker note came to claim Snowflake earns $110bn. Fall
    # back to the most recent filed period instead: a real figure from a slightly
    # earlier period beats an invented one, and the templates say "annual revenue
    # of approximately $X" without naming a period, so it stays consistent.
    if not period_data:
        period_data = _latest_sec_period(cik_financials)
    if not period_data:
        return {}
    
    # Build metric placeholders from SEC data
    metrics = {}

    # Quarterly figures (convert to billions for template compatibility)
    revenue = period_data.get('REVENUE')
    if revenue is not None:
        metrics['QUARTERLY_REVENUE_BILLIONS'] = round(revenue / 1e9, 2)

    # Annual figures come from the reported FY row, not the quarter multiplied by
    # four. Templates say "annual revenue of approximately $XB", and a broker note
    # asserting a figure the agent can contradict from FACT_SEC_FINANCIALS in the
    # same breath makes the research corpus look broken. Only fall back to 4x the
    # quarter when the issuer has no FY row at all.
    annual_data = (cik_financials.get((fiscal_year, 'FY'))
                   or _latest_sec_period(cik_financials, period='FY')
                   or {})
    annual_revenue = annual_data.get('REVENUE')
    if annual_revenue is not None:
        metrics['REVENUE_BILLIONS'] = round(annual_revenue / 1e9, 1)
    elif revenue is not None:
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
    
    # Margin percentages (already calculated in FACT_SEC_FINANCIALS).
    # Prefer the annual figure so it is consistent with the annual revenue above -
    # templates pair the two in one sentence.
    gross_margin = annual_data.get('GROSS_MARGIN_PCT') or period_data.get('GROSS_MARGIN_PCT')
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
    
    # YoY revenue growth (precomputed in prefetch). Annual first, for the same
    # reason as the margin above.
    yoy_growth = annual_data.get('YOY_REVENUE_GROWTH_PCT')
    if yoy_growth is None:
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

    operating_cash_flow = period_data.get('OPERATING_CASH_FLOW')
    if operating_cash_flow is not None:
        metrics['OPERATING_CASH_FLOW'] = round(operating_cash_flow / 1e9, 2)
    
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
    doc_type: str,
    doc_num: int = 0
) -> Optional[Dict[str, Any]]:
    """
    Build context for portfolio-level documents from prefetched data.
    Still needs session for Tier 2 derived metrics queries.
    
    Args:
        session: Snowpark session (for Tier 2 metrics only)
        prefetched_row: Row from prefetch_portfolio_contexts()
        doc_type: Document type
        doc_num: Document number for this portfolio (for cycling through report types)
    
    Returns:
        Context dict or None if prefetched_row is missing
    """
    if not prefetched_row:
        return None
    
    context = {
        '_doc_type': doc_type,
        '_doc_num': doc_num,
        'PORTFOLIO_ID': prefetched_row.get('PORTFOLIOID'),
        'PORTFOLIO_NAME': prefetched_row.get('PORTFOLIONAME'),
        'STRATEGY': prefetched_row.get('STRATEGY'),
        'BASE_CURRENCY': prefetched_row.get('BASECURRENCY'),
        'INCEPTION_DATE': str(prefetched_row.get('INCEPTIONDATE')) if prefetched_row.get('INCEPTIONDATE') else None,
    }
    
    report_types = config.DOCUMENT_TYPES.get(doc_type, {}).get('report_types', [])
    if report_types:
        context['REPORT_TYPE'] = report_types[doc_num % len(report_types)]
    
    context.update(generate_dates_for_doc_type(doc_type))
    
    
    # Add Tier 1 numerics for performance data
    context.update(generate_tier1_numerics(context, doc_type))
    
    return context


def generate_dates_for_doc_type_from_cache(
    doc_type: str,
    context: Dict[str, Any],
    fiscal_periods: List[Dict[str, Any]],
    vintage: Optional[date] = None
) -> Dict[str, str]:
    """
    Generate dates using cached fiscal calendar data (no queries).

    Delegates to generate_dates_for_doc_type so there is a single implementation.
    This used to be a near-copy, which meant every determinism fix had to be made
    twice and the two copies could silently drift apart.

    Args:
        doc_type: Document type
        context: Context dict (for fallback values)
        fiscal_periods: Prefetched fiscal periods for this entity's CIK
        vintage: Optional as-of date driving every derived date

    Returns:
        Dict with date placeholders
    """
    return generate_dates_for_doc_type(
        doc_type,
        context=context,
        session=None,
        vintage=vintage,
        fiscal_periods=fiscal_periods,
    )

def get_coverage_settings() -> Dict[str, Any]:
    """Coverage-universe settings from documents.yaml, with defaults applied."""
    from utils.demo_helpers import get_pinned_portfolio_names

    raw = (config.REF_DATA['documents'].get('coverage') or {})
    starter_pack = raw.get('starter_pack') or [
        'broker_research', 'press_releases', 'ngo_reports', 'engagement_notes'
    ]
    return {
        'top_n_per_portfolio': int(raw.get('top_n_per_portfolio', 10)),
        'scenario_portfolios': raw.get('scenario_portfolios') or get_pinned_portfolio_names(),
        'universe_doc_types': raw.get('universe_doc_types') or starter_pack,
        'starter_pack': starter_pack,
        'required_doc_types': raw.get('required_doc_types') or ['broker_research', 'press_releases'],
        'require_recommendation': bool(raw.get('require_recommendation', True)),
        'backfill_max_names': int(raw.get('backfill_max_names', 20)),
    }


def get_scenario_top_holdings_sql(top_n: Optional[int] = None) -> str:
    """SQL of (PortfolioName, SecurityID, IssuerID, Ticker, WeightRank) for the
    top-N equity holdings of every scenario portfolio at the latest HoldingDate."""
    settings = get_coverage_settings()
    n = settings['top_n_per_portfolio'] if top_n is None else int(top_n)
    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    portfolios_sql = safe_sql_tuple(settings['scenario_portfolios'])
    return f"""
        SELECT PortfolioName, SecurityID, IssuerID, Ticker, WeightRank
        FROM (
            SELECT p.PortfolioName, s.SecurityID, s.IssuerID, s.Ticker,
                   ROW_NUMBER() OVER (
                       PARTITION BY p.PortfolioID
                       ORDER BY SUM(f.PortfolioWeight) DESC, s.Ticker
                   ) AS WeightRank
            FROM {database}.{curated}.FACT_POSITION_DAILY_ABOR f
            JOIN {database}.{curated}.DIM_PORTFOLIO p ON p.PortfolioID = f.PortfolioID
            JOIN {database}.{curated}.DIM_SECURITY s ON s.SecurityID = f.SecurityID
            WHERE f.HoldingDate = (
                SELECT MAX(HoldingDate) FROM {database}.{curated}.FACT_POSITION_DAILY_ABOR
            )
              AND s.AssetClass = 'Equity'
              AND p.PortfolioName IN {portfolios_sql}
            GROUP BY p.PortfolioID, p.PortfolioName, s.SecurityID, s.IssuerID, s.Ticker
        )
        WHERE WeightRank <= {n}
    """


def get_coverage_universe_sql(top_n: Optional[int] = None) -> str:
    """SQL of (SecurityID, IssuerID, Ticker): DEMO_COMPANIES core, every pinned
    scenario anchor, plus the top-N holdings of every scenario portfolio at the
    latest month-end."""
    from utils.demo_helpers import (
        get_demo_company_tickers,
        get_pinned_portfolio_names,
        get_portfolio_target_weights,
    )

    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    anchor_tickers = set(get_demo_company_tickers(tier='core'))
    for portfolio_name in get_pinned_portfolio_names():
        anchor_tickers.update(get_portfolio_target_weights(portfolio_name).keys())
    core_sql = safe_sql_tuple(sorted(anchor_tickers))
    return f"""
        SELECT DISTINCT SecurityID, IssuerID, Ticker FROM (
            SELECT s.SecurityID, s.IssuerID, s.Ticker
            FROM {database}.{curated}.DIM_SECURITY s
            WHERE s.AssetClass = 'Equity' AND s.Ticker IN {core_sql}
            UNION ALL
            SELECT SecurityID, IssuerID, Ticker FROM ({get_scenario_top_holdings_sql(top_n)})
        )
    """


def _positions_available(session: Session) -> bool:
    database = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    return bool(session.sql(f"""
        SELECT COUNT(*) AS n
        FROM {database}.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{curated}' AND TABLE_NAME = 'FACT_POSITION_DAILY_ABOR'
    """).collect()[0]['N'])


def get_coverage_universe(session: Session) -> List[Dict[str, Any]]:
    """Coverage universe as rows of {SecurityID, IssuerID, Ticker}, ordered by
    demo priority. Falls back to DEMO_COMPANIES core before positions exist."""
    from utils.demo_helpers import get_demo_company_tickers

    if not _positions_available(session):
        database = config.DATABASE['name']
        curated = config.DATABASE['schemas']['curated']
        rows = session.sql(f"""
            SELECT s.SecurityID, s.IssuerID, s.Ticker
            FROM {database}.{curated}.DIM_SECURITY s
            WHERE s.AssetClass = 'Equity'
              AND s.Ticker IN {safe_sql_tuple(get_demo_company_tickers(tier='core'))}
            ORDER BY CASE {get_demo_company_priority_sql()} ELSE 10 END, s.Ticker
        """).collect()
    else:
        rows = session.sql(f"""
            SELECT s.SecurityID, s.IssuerID, s.Ticker
            FROM ({get_coverage_universe_sql()}) s
            ORDER BY CASE {get_demo_company_priority_sql()} ELSE 10 END, s.Ticker
        """).collect()
    return [
        {'SecurityID': r['SECURITYID'], 'IssuerID': r['ISSUERID'], 'Ticker': r['TICKER']}
        for r in rows
    ]


def _uses_coverage_universe(session: Session, doc_type: str, test_mode: bool) -> bool:
    if test_mode or config.DOCUMENT_TYPES[doc_type].get('source') == 'real':
        return False
    if doc_type not in get_coverage_settings()['universe_doc_types']:
        return False
    return _positions_available(session)


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
        
        # Research documents quote a grounded rating and price target, so they
        # are only written about securities that can actually be valued. Around
        # 70 of 503 covered names cannot be - foreign issuers reporting in a
        # different currency to their listing, filers with no annual period, or
        # rows with no share count - and emitting a note with an invented rating
        # for those would contradict FACT_RECOMMENDATION. Skipping them lets the
        # next-priority company take the slot instead.
        requires_recommendation = doc_type in [
            'broker_research', 'internal_research', 'investment_memo'
        ]
        if requires_recommendation:
            # Guard the bootstrap case: on a fresh build the recommendation table
            # may not exist yet, and a missing table must not fail the document
            # pipeline outright.
            exists = session.sql(f"""
                SELECT COUNT(*) AS n
                FROM {config.DATABASE['name']}.INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'CURATED'
                  AND TABLE_NAME = 'FACT_RECOMMENDATION'
            """).collect()[0]['N']
            if not exists:
                log_warning(
                    "  FACT_RECOMMENDATION does not exist - selecting research "
                    "entities without valuation filtering. Build recommendations "
                    "first for grounded ratings."
                )
                requires_recommendation = False
        recommendation_filter = f"""
              AND EXISTS (
                  SELECT 1 FROM {config.DATABASE['name']}.CURATED.FACT_RECOMMENDATION r
                  WHERE r.SecurityID = s.SecurityID
              )
        """ if requires_recommendation else ''

        if _uses_coverage_universe(session, doc_type, test_mode):
            universe_filter = f"AND s.SecurityID IN (SELECT SecurityID FROM ({get_coverage_universe_sql()}))"
            limit_clause = ''
        else:
            universe_filter = ''
            limit_clause = f"LIMIT {coverage_count}"

        # Use same prioritization as portfolio holdings to ensure alignment with demo scenarios
        securities = session.sql(f"""
            SELECT 
                s.SecurityID as id,
                s.Ticker
            FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s
            JOIN {config.DATABASE['name']}.CURATED.DIM_ISSUER i ON s.IssuerID = i.IssuerID
            WHERE s.AssetClass = 'Equity'
            {recommendation_filter}
            {universe_filter}
            ORDER BY 
                -- Prioritize demo scenario companies by tier from config.DEMO_COMPANIES
                CASE 
                    {get_demo_company_priority_sql()}
                    -- Companies not in DEMO_COMPANIES
                    ELSE 10
                END,
                s.Ticker
            {limit_clause}
        """).collect()
        
        return [{'id': s['ID']} for s in securities]
    
    elif linkage_level == 'issuer':
        # Get issuers for demo coverage - prioritize companies that appear in portfolios
        base_coverage = config.DOCUMENT_TYPES[doc_type].get('coverage_count', 8)
        coverage_count = max(3, int(base_coverage * config.TEST_MODE_MULTIPLIER)) if test_mode else base_coverage
        
        if _uses_coverage_universe(session, doc_type, test_mode):
            universe_filter = f"AND s.SecurityID IN (SELECT SecurityID FROM ({get_coverage_universe_sql()}))"
            limit_clause = ''
        else:
            universe_filter = ''
            limit_clause = f"LIMIT {coverage_count}"

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
                {universe_filter}
                GROUP BY i.IssuerID, i.LegalName
            )
            SELECT 
                IssuerID as id,
                LegalName
            FROM prioritized_securities
            ORDER BY priority, LegalName
            {limit_clause}
        """).collect()
        
        entities = [{'id': i['ID']} for i in issuers]

        # Pinned thematic engagements, e.g. a supply-chain and labour review for a
        # name whose routine note is a compliance discussion. Each is a second note
        # for that issuer, so it takes doc_num 1 and a distinct document id.
        focus = config.DOCUMENT_TYPES[doc_type].get('focus_engagements') or []
        if focus:
            focus_by_ticker = {f['ticker']: f['meeting_type'] for f in focus}
            focus_issuers = session.sql(f"""
                SELECT DISTINCT s.Ticker, s.IssuerID AS id
                FROM {config.DATABASE['name']}.CURATED.DIM_SECURITY s
                WHERE s.AssetClass = 'Equity'
                  AND s.Ticker IN {safe_sql_tuple(list(focus_by_ticker))}
            """).collect()
            for row in focus_issuers:
                entities.append({
                    'id': row['ID'],
                    'doc_num': 1,
                    'meeting_type': focus_by_ticker[row['TICKER']],
                })

        return entities
    
    elif linkage_level == 'portfolio':
        portfolios_list = config.DOCUMENT_TYPES[doc_type].get('portfolios', [])
        
        if not portfolios_list:
            return []
        
        if test_mode:
            portfolios_list = portfolios_list[:1]
        
        portfolio_names_str = "','".join(portfolios_list)
        portfolios = session.sql(f"""
            SELECT PortfolioID as id
            FROM {config.DATABASE['name']}.CURATED.DIM_PORTFOLIO
            WHERE PortfolioName IN ('{portfolio_names_str}')
        """).collect()
        
        base_docs_per_portfolio = config.DOCUMENT_TYPES[doc_type].get('docs_per_portfolio', 1)
        docs_per_portfolio = max(1, int(base_docs_per_portfolio * config.TEST_MODE_MULTIPLIER)) if test_mode else base_docs_per_portfolio
        
        entities = []
        for p in portfolios:
            for doc_num in range(docs_per_portfolio):
                entities.append({'id': p['ID'], 'doc_num': doc_num})
        
        return entities
    
    else:  # global
        # Global documents: generate specified count
        base_count = config.DOCUMENT_TYPES[doc_type].get('docs_total', 1)
        docs_total = max(1, int(base_count * config.TEST_MODE_MULTIPLIER)) if test_mode else base_count
        return [{'id': i, 'num': i} for i in range(docs_total)]

