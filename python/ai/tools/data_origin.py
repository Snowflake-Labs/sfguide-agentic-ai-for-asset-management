from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_error


def create_data_origin_tool(session: Session):
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']

    data_origin_sql = f"""
CREATE OR REPLACE PROCEDURE {database_name}.{ai_schema}.EXPLAIN_DATA_ORIGIN(
    semantic_view_name VARCHAR,
    business_term VARCHAR
)
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS OWNER
AS $$
DECLARE
    physical_expr VARCHAR DEFAULT '';
    term_kind VARCHAR DEFAULT '';
    term_table VARCHAR DEFAULT '';
    term_comment VARCHAR DEFAULT '';
    term_synonyms VARCHAR DEFAULT '';
    term_data_type VARCHAR DEFAULT '';
    base_db VARCHAR DEFAULT '';
    base_schema VARCHAR DEFAULT '';
    base_table_name VARCHAR DEFAULT '';
    physical_table VARCHAR DEFAULT '';
    semantic_context VARCHAR DEFAULT '';
    structural_lineage ARRAY DEFAULT ARRAY_CONSTRUCT();
    target_column VARCHAR DEFAULT '';
    view_definitions ARRAY DEFAULT ARRAY_CONSTRUCT();
    root_ddl VARCHAR DEFAULT '';
    describe_qid VARCHAR DEFAULT '';
    cur_ddl VARCHAR;
    cur_body VARCHAR;
    lineage_rs RESULTSET;
    seen_views ARRAY DEFAULT ARRAY_CONSTRUCT();
BEGIN
    EXECUTE IMMEDIATE 'DESCRIBE SEMANTIC VIEW ' || :semantic_view_name;
    describe_qid := LAST_QUERY_ID();
    SELECT MAX(CASE WHEN "object_kind" IS NOT NULL THEN "object_kind" END), MAX(CASE WHEN "property" = 'EXPRESSION' THEN "property_value" END), MAX(CASE WHEN "property" = 'COMMENT' THEN "property_value" END), MAX(CASE WHEN "property" = 'SYNONYMS' THEN "property_value" END), MAX(CASE WHEN "property" = 'DATA_TYPE' THEN "property_value" END), MAX(CASE WHEN "object_kind" IS NOT NULL THEN "parent_entity" END), LISTAGG(CASE WHEN "property" IS NOT NULL THEN "property" || ': ' || "property_value" END, '; ') WITHIN GROUP (ORDER BY "property") INTO :term_kind, :physical_expr, :term_comment, :term_synonyms, :term_data_type, :term_table, :semantic_context FROM TABLE(RESULT_SCAN(:describe_qid)) WHERE UPPER("object_name") = UPPER(:business_term);
    SELECT MAX(CASE WHEN "property" = 'BASE_TABLE_DATABASE_NAME' THEN "property_value" END), MAX(CASE WHEN "property" = 'BASE_TABLE_SCHEMA_NAME' THEN "property_value" END), MAX(CASE WHEN "property" = 'BASE_TABLE_NAME' THEN "property_value" END) INTO :base_db, :base_schema, :base_table_name FROM TABLE(RESULT_SCAN(:describe_qid)) WHERE UPPER("object_name") = UPPER(:term_table);
    physical_table := :base_db || '.' || :base_schema || '.' || :base_table_name;
    target_column := UPPER(REGEXP_REPLACE(:physical_expr, '.*\\\\(([A-Za-z_][A-Za-z0-9_]*)\\\\).*', '\\\\1'));
    IF (target_column = '' OR target_column = UPPER(:physical_expr)) THEN
        target_column := UPPER(:physical_expr);
    END IF;
    BEGIN
        LET raw_ddl VARCHAR := GET_DDL('VIEW', :physical_table);
        IF (UPPER(raw_ddl) LIKE 'CREATE%VIEW%') THEN
            root_ddl := SUBSTR(raw_ddl, POSITION(' AS ' IN UPPER(raw_ddl)) + 4);
        ELSE
            root_ddl := '';
        END IF;
    EXCEPTION
        WHEN OTHER THEN
            root_ddl := '';
    END;
    BEGIN
        lineage_rs := (SELECT SOURCE_OBJECT_DATABASE || '.' || SOURCE_OBJECT_SCHEMA || '.' || SOURCE_OBJECT_NAME AS source_fqn, SOURCE_OBJECT_DOMAIN AS source_type, TARGET_OBJECT_DATABASE || '.' || TARGET_OBJECT_SCHEMA || '.' || TARGET_OBJECT_NAME AS target_fqn, TARGET_OBJECT_DOMAIN AS target_type, DISTANCE AS depth FROM TABLE(SNOWFLAKE.CORE.GET_LINEAGE(:physical_table, 'TABLE', 'UPSTREAM', 5)));
    EXCEPTION
        WHEN OTHER THEN
            lineage_rs := (SELECT NULL::VARCHAR AS source_fqn, NULL::VARCHAR AS source_type, NULL::VARCHAR AS target_fqn, NULL::VARCHAR AS target_type, NULL::NUMBER AS depth WHERE 1=0);
    END;
    LET lineage_cur CURSOR FOR lineage_rs;
    FOR edge IN lineage_cur DO
        structural_lineage := ARRAY_APPEND(:structural_lineage, OBJECT_CONSTRUCT('depth', edge.depth, 'source', edge.source_fqn, 'source_type', edge.source_type, 'target', edge.target_fqn, 'target_type', edge.target_type));
        IF (edge.source_type = 'VIEW' AND NOT ARRAY_CONTAINS(edge.source_fqn::VARIANT, :seen_views)) THEN
            seen_views := ARRAY_APPEND(:seen_views, edge.source_fqn);
            cur_body := '';
            BEGIN
                cur_ddl := GET_DDL('VIEW', edge.source_fqn);
                cur_body := SUBSTR(cur_ddl, POSITION(' as ' IN LOWER(cur_ddl)) + 4);
            EXCEPTION
                WHEN OTHER THEN
                    cur_body := '';
            END;
            IF (cur_body != '' AND (target_column = UPPER(:physical_expr) OR UPPER(cur_body) LIKE '%' || :target_column || '%')) THEN
                view_definitions := ARRAY_APPEND(:view_definitions, OBJECT_CONSTRUCT('object_name', edge.source_fqn, 'object_type', 'VIEW', 'sql_body', cur_body));
            END IF;
        END IF;
    END FOR;
    RETURN OBJECT_CONSTRUCT('business_term', :business_term, 'term_type', COALESCE(:term_kind, 'UNKNOWN'), 'semantic_expression', :physical_expr, 'semantic_comment', :term_comment, 'semantic_synonyms', :term_synonyms, 'data_type', :term_data_type, 'semantic_properties', :semantic_context, 'logical_table', :term_table, 'physical_table', :physical_table, 'target_column', :target_column, 'root_view_sql', :root_ddl, 'lineage_tree', :structural_lineage, 'view_definitions', :view_definitions);
END
$$
    """

    try:
        session.sql(data_origin_sql).collect()
        log_detail("  Created EXPLAIN_DATA_ORIGIN")
    except Exception as e:
        log_error(f" EXPLAIN_DATA_ORIGIN creation failed: {e}")
