# =============================================================================
# SQL UTILITIES - SQL generation helpers
# =============================================================================
"""
Helper functions for generating SQL fragments and queries.
"""


def safe_sql_tuple(items: list, default_value: str = "'__NONE__'") -> str:
    """
    Convert a list to a SQL-safe tuple string with proper quoting.
    Returns a tuple with a dummy value if the list is empty to avoid SQL syntax errors.
    
    Args:
        items: List of items to convert to tuple
        default_value: Default value to use if list is empty (should be a SQL literal)
    
    Returns:
        String representation of tuple for SQL IN clause
    """
    if not items or len(items) == 0:
        return f"({default_value})"
    
    # Format items with SQL quotes
    quoted_items = [f"'{item}'" for item in items]
    # SQL doesn't use trailing comma for single items (unlike Python)
    return f"({', '.join(quoted_items)})"
