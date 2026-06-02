"""
Export tables to CSV files.

Extracts data from existing SAM_DEMO tables and writes to CSV format
for inclusion in deployable packages.
"""

import csv
from pathlib import Path
from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_info


def export_tables(session, requirements, output_dir):
    """
    Export all required tables to CSV files.
    
    Args:
        session: Active Snowpark session
        requirements: Dict from manifest.get_requirements()
        output_dir: Path to output directory
        
    Returns:
        dict: Mapping of table_name -> row_count
    """
    database_name = config.DATABASE['name']
    data_dir = Path(output_dir) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    exported = {}
    
    for schema, tables in requirements['tables'].items():
        for table_name in tables:
            row_count = _export_single_table(session, database_name, schema, table_name, data_dir)
            exported[table_name] = row_count
    
    for table_name in requirements.get('corpus_tables', []):
        row_count = _export_single_table(session, database_name, 'CURATED', table_name, data_dir)
        exported[table_name] = row_count
    
    return exported


def _export_single_table(session, database_name, schema, table_name, data_dir):
    """
    Export a single table to CSV.
    
    Args:
        session: Active Snowpark session
        database_name: Database name
        schema: Schema name
        table_name: Table/view name
        data_dir: Path to data directory
        
    Returns:
        int: Number of rows exported
    """
    full_name = f"{database_name}.{schema}.{table_name}"
    log_detail(f"Exporting {table_name}...")
    
    df = session.sql(f"SELECT * FROM {full_name}").to_pandas()
    
    for col in df.columns:
        if df[col].dtype == 'datetime64[ns]':
            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        elif df[col].dtype == 'object':
            df[col] = df[col].apply(lambda x: str(x) if x is not None else '')
    
    csv_path = data_dir / f"{table_name.lower()}.csv"
    df.to_csv(csv_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
    
    log_detail(f"  {len(df):,} rows -> {csv_path.name}")
    return len(df)


def get_table_schema(session, database_name, schema, table_name):
    """
    Get column definitions for a table from INFORMATION_SCHEMA.
    
    Args:
        session: Active Snowpark session
        database_name: Database name
        schema: Schema name
        table_name: Table name
        
    Returns:
        list: List of (column_name, data_type) tuples
    """
    query = f"""
    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE
    FROM {database_name}.INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = '{schema}'
      AND TABLE_NAME = '{table_name}'
    ORDER BY ORDINAL_POSITION
    """
    
    try:
        result = session.sql(query).collect()
        columns = []
        for row in result:
            col_name = row['COLUMN_NAME']
            data_type = row['DATA_TYPE']
            
            if data_type == 'TEXT':
                max_len = row['CHARACTER_MAXIMUM_LENGTH']
                if max_len and max_len < 16777216:
                    data_type = f"VARCHAR({max_len})"
                else:
                    data_type = "VARCHAR"
            elif data_type == 'NUMBER':
                precision = row['NUMERIC_PRECISION']
                scale = row['NUMERIC_SCALE']
                if precision and scale is not None:
                    data_type = f"NUMBER({precision},{scale})"
            
            columns.append((col_name, data_type))
        return columns
    except Exception:
        return []


def get_all_table_schemas(session, requirements):
    """
    Get column definitions for all tables in requirements.
    
    Args:
        session: Active Snowpark session
        requirements: Dict from manifest.get_requirements()
        
    Returns:
        dict: Mapping of (schema, table_name) -> list of (column_name, data_type)
    """
    database_name = config.DATABASE['name']
    schemas = {}
    
    for schema, tables in requirements['tables'].items():
        for table_name in tables:
            columns = get_table_schema(session, database_name, schema, table_name)
            if columns:
                schemas[(schema, table_name)] = columns
    
    for table_name in requirements.get('corpus_tables', []):
        columns = get_table_schema(session, database_name, 'CURATED', table_name)
        if columns:
            schemas[('CURATED', table_name)] = columns
    
    return schemas
