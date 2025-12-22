# =============================================================================
# SCENARIO UTILITIES - Scenario-related helper functions
# =============================================================================
"""
Helper functions for working with demo scenarios.
Centralizes logic that was previously duplicated across modules.
"""

from typing import List
import config


def get_required_document_types(scenarios: List[str]) -> List[str]:
    """
    Get unique list of document types required for the specified scenarios.
    
    Args:
        scenarios: List of scenario names (e.g., ['portfolio_copilot', 'research_copilot'])
    
    Returns:
        List of unique document type names required by those scenarios
    """
    required_types = set()
    for scenario in scenarios:
        if scenario in config.SCENARIO_DATA_REQUIREMENTS:
            required_types.update(config.SCENARIO_DATA_REQUIREMENTS[scenario])
    return list(required_types)

