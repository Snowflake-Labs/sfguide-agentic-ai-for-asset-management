# Python Tool Creation

Patterns for creating Snowflake Python stored procedures and UDFs as custom tools for agents.

## Critical: Config Resolution at Build Time

The Python `config` module is NOT available in Snowflake. All config references must be resolved when the SQL string is built.

```python
# ✅ CORRECT - Single braces for outer f-string interpolation
tool_sql = f"""
CREATE OR REPLACE FUNCTION {config.DATABASE['name']}.AI.MY_TOOL(...)
AS
$$
def handler(session, param):
    stage_path = '@{config.DATABASE["name"]}.AI.MY_STAGE'
$$;
"""
```

## SQL Definition Pattern

Use `$$` delimiters for Python code blocks:

```python
def create_custom_tool(session: Session):
    tool_sql = f"""
CREATE OR REPLACE FUNCTION {config.DATABASE['name']}.AI.MY_TOOL(
    param1 VARCHAR,
    param2 FLOAT
)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'my_handler'
AS
$$
def my_handler(param1: str, param2: float) -> dict:
    \"\"\"Handler docstring.\"\"\"
    return {{"result": param1, "value": param2}}
$$;
    """
    session.sql(tool_sql).collect()
```

## String Escaping Rules

| Context | Write | Result | Purpose |
|---------|-------|--------|---------|
| Config injection | `{config.DATABASE['name']}` | `SAM_DEMO` | Build-time value |
| Inner f-string var | `{{my_variable}}` | `{my_variable}` | Snowflake Python |
| Dict literal | `{{key: value}}` | `{key: value}` | Dict in Snowflake |
| Triple quotes | `\"\"\"` | `"""` | Docstrings |

## Function vs Procedure

| Feature | Function (UDF) | Stored Procedure |
|---------|---------------|------------------|
| Keyword | `CREATE FUNCTION` | `CREATE PROCEDURE` |
| Session access | No | Yes (first parameter) |
| Side effects | Not allowed | Allowed |
| Tool resource type | `type: "function"` | `type: "procedure"` |

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `NameError: config` | Config at runtime | Use `{config...}` single braces |
| `Unexpected '{'` | Missing escape | Use `{{variable}}` |
| Literal `{{` in output | Over-escaping | Use single `{` |

## Checklist

- [ ] Using `$$` delimiters
- [ ] Config uses single braces `{config...}`
- [ ] Inner f-strings use `{{variable}}`
- [ ] Dict literals use `{{key: value}}`
- [ ] Docstrings use `\"\"\"`
