"""
Rules Loader - Load configuration from content_library/_rules/ YAML files

This module provides a single source of truth for:
- Fictional provider names (brokers, NGOs)
- Numeric bounds by sector and document type
- Placeholder contract definitions
- Distribution rules (ratings, severity levels, etc.)

All rules are loaded from YAML files to avoid hardcoding and enable
easy updates without code changes.
"""

import os
import yaml
from typing import Dict, List, Any, Optional
from functools import lru_cache

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

def _get_rules_path() -> str:
    """Get the path to the _rules directory."""
    # This file is in python/, content_library is at the same level
    config_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(config_dir)
    return os.path.join(project_root, 'content_library', '_rules')


# ============================================================================
# YAML LOADERS (cached for performance)
# ============================================================================

@lru_cache(maxsize=1)
def _load_fictional_providers() -> Dict[str, Any]:
    """Load fictional_providers.yaml (cached)."""
    file_path = os.path.join(_get_rules_path(), 'fictional_providers.yaml')
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def _load_numeric_bounds() -> Dict[str, Any]:
    """Load numeric_bounds.yaml (cached)."""
    file_path = os.path.join(_get_rules_path(), 'numeric_bounds.yaml')
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def _load_placeholder_contract() -> Dict[str, Any]:
    """Load placeholder_contract.yaml (cached)."""
    file_path = os.path.join(_get_rules_path(), 'placeholder_contract.yaml')
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


# ============================================================================
# FICTIONAL PROVIDERS API
# ============================================================================

def get_fictional_brokers() -> List[str]:
    """
    Get list of fictional broker names.
    
    Returns:
        List of 15 fictional broker names for use in broker research documents.
        
    Example:
        >>> brokers = get_fictional_brokers()
        >>> brokers[0]
        'Ashfield Partners'
    """
    data = _load_fictional_providers()
    return data.get('fictional_brokers', [])


def get_fictional_ngos(category: Optional[str] = None) -> Dict[str, List[str]] | List[str]:
    """
    Get fictional NGO names, optionally filtered by category.
    
    Args:
        category: Optional category filter ('environmental', 'social', 'governance')
                  If None, returns all categories as a dict.
    
    Returns:
        If category provided: List of NGO names for that category
        If category is None: Dict mapping categories to lists of NGO names
        
    Example:
        >>> get_fictional_ngos('environmental')
        ['Global Sustainability Watch', 'Environmental Justice Initiative', ...]
        >>> get_fictional_ngos()
        {'environmental': [...], 'social': [...], 'governance': [...]}
    """
    data = _load_fictional_providers()
    ngos = data.get('fictional_ngos', {})
    
    if category:
        return ngos.get(category, ngos.get('environmental', []))
    return ngos


def get_forbidden_providers() -> Dict[str, List[str]]:
    """
    Get lists of forbidden (real) provider names for validation.
    
    Returns:
        Dict with 'brokers' and 'ngos' lists of names that should NOT be used.
        
    Example:
        >>> forbidden = get_forbidden_providers()
        >>> 'Goldman Sachs' in forbidden['brokers']
        True
    """
    data = _load_fictional_providers()
    return data.get('forbidden_providers', {'brokers': [], 'ngos': []})


# ============================================================================
# NUMERIC BOUNDS API
# ============================================================================

def get_numeric_bounds(doc_type: str, sector: str) -> Dict[str, Dict[str, float]]:
    """
    Get numeric bounds for a specific document type and sector.
    
    All placeholders are explicitly defined per document type with:
    1. A 'default' section containing all placeholders for that doc type
    2. Sector-specific overrides that take precedence over defaults
    
    Args:
        doc_type: Document type (e.g., 'broker_research', 'internal_research', 
                  'earnings_transcripts', 'portfolio_review')
        sector: GICS sector (e.g., 'Information Technology', 'Health Care')
    
    Returns:
        Dict mapping placeholder names to {min, max} bounds.
        
    Example:
        >>> bounds = get_numeric_bounds('broker_research', 'Information Technology')
        >>> bounds['YOY_REVENUE_GROWTH_PCT']
        {'min': 8, 'max': 25}
    """
    data = _load_numeric_bounds()
    result_bounds = {}
    
    # Determine the category (security, portfolio, issuer, global)
    category_mapping = {
        'broker_research': ('security', 'broker_research'),
        'internal_research': ('security', 'internal_research'),
        'investment_memo': ('security', 'investment_memo'),
        'earnings_transcripts': ('security', 'earnings_transcripts'),
        'press_releases': ('security', 'press_releases'),
        'portfolio_review': ('portfolio', 'portfolio_review'),
        'custodian_reports': ('portfolio', 'custodian_reports'),
        'ips': ('portfolio', 'portfolio_review'),
        'ngo_reports': ('issuer', 'ngo_reports'),
        'engagement_notes': ('issuer', 'engagement_notes'),
        'market_data': ('global', 'market_data'),
        'risk_framework': ('global', 'risk_framework'),
        'ssi_documents': ('global', 'ssi_documents'),
    }
    
    category, sub_type = category_mapping.get(doc_type, ('security', 'broker_research'))
    
    # Navigate to the correct section
    category_data = data.get(category, {})
    doc_type_data = category_data.get(sub_type, {})
    
    # Step 1: Start with the 'default' bounds for this document type
    default_bounds = doc_type_data.get('default', {})
    result_bounds.update(default_bounds)
    
    # Step 2: Override with sector-specific bounds (for security-level docs)
    if category == 'security' and sector:
        sector_bounds = doc_type_data.get(sector, {})
        result_bounds.update(sector_bounds)
    
    return result_bounds


def get_all_numeric_bounds() -> Dict[str, Any]:
    """
    Get the complete numeric bounds configuration.
    
    Returns:
        Full numeric_bounds.yaml content as nested dict.
    """
    return _load_numeric_bounds()


# ============================================================================
# DISTRIBUTIONS API
# ============================================================================

def get_distribution(name: str) -> Dict[str, float]:
    """
    Get a probability distribution by name.
    
    Args:
        name: Distribution name ('rating', 'severity_level', 'meeting_type')
    
    Returns:
        Dict mapping values to probabilities (sum to 1.0)
        
    Example:
        >>> get_distribution('rating')
        {'Strong Buy': 0.10, 'Buy': 0.25, 'Hold': 0.45, 'Sell': 0.15, 'Strong Sell': 0.05}
    """
    data = _load_numeric_bounds()
    distributions = data.get('distributions', {})
    return distributions.get(name, {})


def get_rating_distribution() -> Dict[str, float]:
    """Get the rating distribution for broker research."""
    return get_distribution('rating')


def get_severity_distribution() -> Dict[str, float]:
    """Get the severity level distribution for NGO reports."""
    return get_distribution('severity_level')


def get_meeting_type_distribution() -> Dict[str, float]:
    """Get the meeting type distribution for engagement notes."""
    return get_distribution('meeting_type')


# ============================================================================
# PLACEHOLDER CONTRACT API
# ============================================================================

def get_placeholder_contract() -> Dict[str, Any]:
    """
    Get the complete placeholder contract.
    
    Returns:
        Full placeholder_contract.yaml content defining all valid placeholders,
        their types, sources, and validation rules.
    """
    return _load_placeholder_contract()


def get_placeholders_for_context(context_type: str) -> Dict[str, Dict[str, Any]]:
    """
    Get placeholder definitions for a specific context.
    
    Args:
        context_type: One of 'security_context', 'portfolio_context', 
                      'date_context', 'provider_context', 'tier1_numerics', 
                      'tier2_numerics', 'conditional_placeholders'
    
    Returns:
        Dict mapping placeholder names to their definitions.
        
    Example:
        >>> placeholders = get_placeholders_for_context('security_context')
        >>> placeholders['COMPANY_NAME']['source']
        'DIM_SECURITY.Description'
    """
    contract = _load_placeholder_contract()
    return contract.get(context_type, {})


def get_required_placeholders(doc_type: str) -> List[str]:
    """
    Get list of required placeholders for a document type.
    
    Args:
        doc_type: Document type (e.g., 'broker_research')
    
    Returns:
        List of placeholder names required for this document type.
    """
    contract = _load_placeholder_contract()
    required = []
    
    # Check all context types for placeholders required for this doc type
    for context_type in ['security_context', 'portfolio_context', 'date_context', 
                         'provider_context', 'tier1_numerics']:
        context = contract.get(context_type, {})
        for placeholder, definition in context.items():
            required_for = definition.get('required_for', [])
            if doc_type in required_for:
                required.append(placeholder)
    
    return required


def get_validation_rules() -> Dict[str, Any]:
    """
    Get validation rules from the placeholder contract.
    
    Returns:
        Dict of validation rules for placeholder processing.
    """
    contract = _load_placeholder_contract()
    return contract.get('validation', {})


# ============================================================================
# TIER 2 DERIVATIONS (SQL Queries)
# ============================================================================

def get_tier2_derivations() -> Dict[str, Dict[str, Any]]:
    """
    Get Tier 2 derivation SQL queries for portfolio metrics.
    
    Returns:
        Dict mapping metric names to query definitions.
    """
    data = _load_numeric_bounds()
    return data.get('tier2_derivations', {})


# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

def clear_cache():
    """
    Clear all cached YAML data.
    
    Call this if you've modified the YAML files and want to reload them
    without restarting the Python process.
    """
    _load_fictional_providers.cache_clear()
    _load_numeric_bounds.cache_clear()
    _load_placeholder_contract.cache_clear()


def preload_rules():
    """
    Preload all rules into cache.
    
    Call this at startup to ensure all YAML files are valid and loaded.
    Returns True if all files loaded successfully.
    """
    try:
        _load_fictional_providers()
        _load_numeric_bounds()
        _load_placeholder_contract()
        return True
    except Exception as e:
        print(f"Error preloading rules: {e}")
        return False


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_provider_name(name: str, provider_type: str = 'broker') -> bool:
    """
    Validate that a provider name is fictional (not a real company).
    
    Args:
        name: The provider name to validate
        provider_type: 'broker' or 'ngo'
    
    Returns:
        True if the name is safe (fictional), False if it's a forbidden real name.
    """
    forbidden = get_forbidden_providers()
    forbidden_list = forbidden.get(f'{provider_type}s', [])
    
    # Case-insensitive comparison
    name_lower = name.lower()
    for forbidden_name in forbidden_list:
        if forbidden_name.lower() in name_lower or name_lower in forbidden_name.lower():
            return False
    return True


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

if __name__ == '__main__':
    # Quick test when run directly
    print("Testing rules_loader...")
    
    print("\nFictional Brokers ({0}):".format(len(get_fictional_brokers())))
    for broker in get_fictional_brokers()[:3]:
        print("  - {0}".format(broker))
    print("  ...")
    
    print("\nFictional NGOs:")
    for category, ngos in get_fictional_ngos().items():
        print("  {0}: {1}, ...".format(category, ngos[0]))
    
    print("\nRating Distribution:")
    for rating, prob in get_rating_distribution().items():
        print("  {0}: {1:.0%}".format(rating, prob))
    
    print("\nNumeric Bounds (broker_research, Information Technology):")
    bounds = get_numeric_bounds('broker_research', 'Information Technology')
    for placeholder, bound in list(bounds.items())[:3]:
        print("  {0}: {1}".format(placeholder, bound))
    
    print("\n✅ All rules loaded successfully!")

