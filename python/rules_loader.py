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

# =============================================================================
# RULES LOADER - Dynamic YAML Configuration Loading
# =============================================================================
"""
Loads configuration from content_library/_rules/ YAML files.
Provides centralized access to:
- Numeric bounds (by doc_type and sector)
- Fictional provider names (brokers, NGOs)
- Placeholder contracts (validation specs)
"""

import os
import yaml
from functools import lru_cache
from typing import Dict, List, Any, Optional

import config

# =============================================================================
# YAML FILE LOADERS (with caching)
# =============================================================================

def _get_rules_path() -> str:
    """Get the path to the _rules directory."""
    return os.path.join(config.CONTENT_LIBRARY_PATH, '_rules')


@lru_cache(maxsize=1)
def _load_numeric_bounds() -> Dict[str, Any]:
    """Load numeric_bounds.yaml (cached)."""
    file_path = os.path.join(_get_rules_path(), 'numeric_bounds.yaml')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load numeric_bounds.yaml: {e}")
        return {}


@lru_cache(maxsize=1)
def _load_fictional_providers() -> Dict[str, Any]:
    """Load fictional_providers.yaml (cached)."""
    file_path = os.path.join(_get_rules_path(), 'fictional_providers.yaml')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load fictional_providers.yaml: {e}")
        return {}


@lru_cache(maxsize=1)
def _load_placeholder_contract() -> Dict[str, Any]:
    """Load placeholder_contract.yaml (cached)."""
    file_path = os.path.join(_get_rules_path(), 'placeholder_contract.yaml')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load placeholder_contract.yaml: {e}")
        return {}


# =============================================================================
# NUMERIC BOUNDS ACCESSORS
# =============================================================================

def get_numeric_bounds(doc_type: str, sector: str) -> Dict[str, Dict[str, float]]:
    """
    Get numeric bounds for a document type and sector.
    
    Args:
        doc_type: Document type (e.g., 'broker_research')
        sector: GICS sector (e.g., 'Information Technology')
    
    Returns:
        Dict mapping placeholder names to {min, max} bounds
    """
    bounds_data = _load_numeric_bounds()
    
    # Map doc_type to YAML structure
    # YAML structure: security.broker_research.{sector} or issuer.ngo_reports.{sector}
    linkage_map = {
        'broker_research': 'security',
        'internal_research': 'security',
        'investment_memo': 'security',
        'press_releases': 'security',
        'ngo_reports': 'issuer',
        'engagement_notes': 'issuer',
        'policy_docs': 'global',
        'sales_templates': 'global',
        'philosophy_docs': 'global',
        'report_templates': 'global',
        'macro_events': 'global'
    }
    
    linkage = linkage_map.get(doc_type, 'security')
    
    # Get bounds for this doc_type and sector
    linkage_data = bounds_data.get(linkage, {})
    doc_bounds = linkage_data.get(doc_type, {})
    
    # Try sector-specific, then default
    sector_bounds = doc_bounds.get(sector, {})
    default_bounds = doc_bounds.get('_default', {})
    
    # Merge default with sector-specific (sector takes priority)
    merged = {**default_bounds, **sector_bounds}
    
    return merged


def get_all_numeric_bounds() -> Dict[str, Any]:
    """Get the entire numeric bounds structure."""
    return _load_numeric_bounds()


# =============================================================================
# FICTIONAL PROVIDER ACCESSORS
# =============================================================================

def get_fictional_brokers() -> List[str]:
    """Get list of fictional broker names."""
    providers = _load_fictional_providers()
    brokers = providers.get('fictional_brokers', [])
    
    # Fallback if YAML not loaded
    if not brokers:
        return [
            'Ashfield Partners', 'Northgate Analytics', 'Blackstone Ridge Research',
            'Fairmont Capital Insights', 'Kingswell Securities Research',
            'Brookline Advisory Group', 'Harrow Street Markets', 'Marlowe & Co. Research',
            'Crescent Point Analytics', 'Simulated Wharf Intelligence', 'Granite Peak Advisory',
            'Alder & Finch Investments', 'Bluehaven Capital Research', 'Regent Square Analytics',
            'Whitestone Equity Research'
        ]
    return brokers


def get_fictional_ngos() -> Dict[str, List[str]]:
    """Get dict of fictional NGO names by category."""
    providers = _load_fictional_providers()
    ngos = providers.get('fictional_ngos', {})
    
    # Fallback if YAML not loaded
    if not ngos:
        return {
            'environmental': [
                'Global Sustainability Watch', 'Environmental Justice Initiative',
                'Climate Action Network', 'Green Future Alliance'
            ],
            'social': [
                'Human Rights Monitor', 'Labour Rights Observatory',
                'Ethical Investment Coalition', 'Fair Workplace Institute'
            ],
            'governance': [
                'Corporate Accountability Forum', 'Transparency Advocacy Group',
                'Corporate Responsibility Institute', 'Ethical Governance Council'
            ]
        }
    return ngos


def get_forbidden_providers() -> Dict[str, List[str]]:
    """Get list of forbidden (real) provider names for validation."""
    providers = _load_fictional_providers()
    return providers.get('forbidden_providers', {'brokers': [], 'ngos': []})


# =============================================================================
# PLACEHOLDER CONTRACT ACCESSORS
# =============================================================================

def get_placeholder_contract() -> Dict[str, Any]:
    """Get the full placeholder contract specification."""
    return _load_placeholder_contract()


def get_required_placeholders(doc_type: str) -> List[str]:
    """Get required placeholders for a document type."""
    contract = _load_placeholder_contract()
    return contract.get('required', {}).get(doc_type, [])


def get_optional_placeholders(doc_type: str) -> List[str]:
    """Get optional placeholders for a document type."""
    contract = _load_placeholder_contract()
    return contract.get('optional', {}).get(doc_type, [])


# =============================================================================
# CACHE MANAGEMENT
# =============================================================================

def clear_cache():
    """Clear all cached YAML data (useful for testing or reloading)."""
    _load_numeric_bounds.cache_clear()
    _load_fictional_providers.cache_clear()
    _load_placeholder_contract.cache_clear()


def reload_rules():
    """Force reload all rules from YAML files."""
    clear_cache()
    # Trigger reload by accessing each
    _load_numeric_bounds()
    _load_fictional_providers()
    _load_placeholder_contract()

