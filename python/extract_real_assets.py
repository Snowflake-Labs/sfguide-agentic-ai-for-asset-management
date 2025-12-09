"""
Real Asset Data View Creation for SAM Demo

This module creates the V_REAL_ASSETS view from the SEC Filings dataset
using the OpenFIGI standard to get authentic tickers for equities, corporate bonds, and ETFs.
Dataset: "SEC Filings" - Financial statements, press releases, & fiscal calendars for US public companies
"""

from snowflake.snowpark import Session
import config


def verify_real_assets_view_exists(session: Session) -> bool:
    """
    Verify that the V_REAL_ASSETS view exists.
    
    Args:
        session: Active Snowpark session
        
    Returns:
        bool: True if view exists, raises exception if not
    """
    try:
        # Check if view exists by trying to query it
        session.sql(f"SELECT 1 FROM {config.DATABASE['name']}.{config.DATABASE['schemas']['RAW'.lower()]}.V_REAL_ASSETS LIMIT 1").collect()
        return True
    except Exception as e:
        raise Exception(f"V_REAL_ASSETS view not found. It should have been created during foundation build. Error: {e}")


def verify_sec_filings_access(session: Session) -> bool:
    """
    Verify that the SEC Filings database and schema exist and are accessible.
    
    Args:
        session: Active Snowpark session
        
    Returns:
        bool: True if accessible, raises exception if not
    """
    try:
        # Check if SEC Filings database exists
        databases = session.sql("SHOW DATABASES").collect()
        db_names = [row['name'] for row in databases]
        
        if config.SECURITIES['sec_filings_database'] not in db_names:
            raise Exception(f"SEC Filings database '{config.SECURITIES['sec_filings_database']}' not found. "
                          f"Please ensure you have access to the SEC Filings dataset.")
        
        # Check if schema exists
        schemas = session.sql(f"SHOW SCHEMAS IN {config.SECURITIES['sec_filings_database']}").collect()
        schema_names = [row['name'] for row in schemas]
        
        if config.SECURITIES['sec_filings_schema'] not in schema_names:
            raise Exception(f"Schema '{config.SECURITIES['sec_filings_schema']}' not found in {config.SECURITIES['sec_filings_database']}. "
                          f"Please verify your SEC Filings dataset access.")
        
        # Verify we can access a key table
        session.sql(f"SELECT 1 FROM {config.SECURITIES['sec_filings_database']}.{config.SECURITIES['sec_filings_schema']}.COMPANY_INDEX LIMIT 1").collect()
        
        # print(f"✅ Verified access to {config.SECURITIES['sec_filings_database']}.{config.SECURITIES['sec_filings_schema']}")
        return True
        
    except Exception as e:
        # print(f"❌ SEC Filings access verification failed: {e}")
        raise


def create_real_assets_view(session: Session) -> bool:
    """
    Create a view in the RAW schema that contains all real asset data.
    This replaces the CSV extraction approach with a dynamic view.
    
    Args:
        session: Active Snowpark session
        
    Returns:
        bool: True if successful
    """
    # print("📊 Creating real assets view in RAW schema...")
    
    # First verify SEC Filings dataset access
    verify_sec_filings_access(session)
    
    # The same SQL query as CSV extraction, but as a view
    view_sql = f"""
    CREATE OR REPLACE VIEW {config.DATABASE['name']}.{config.DATABASE['schemas']['RAW'.lower()]}.V_REAL_ASSETS AS
    WITH Enriched_Securities AS (
        -- This CTE joins the main security index with geography, company characteristics, and aggregated exchange codes.
        SELECT
            osi.TOP_LEVEL_OPENFIGI_ID,
            osi.SECURITY_NAME,
            osi.ASSET_CLASS,
            osi.SECURITY_TYPE,
            osi.SECURITY_SUBTYPE,
            osi.PRIMARY_TICKER,
            ci.PRIMARY_EXCHANGE_CODE,
            ci.PRIMARY_EXCHANGE_NAME,
            osi.EXCHANGE_CODES,
            ci.COMPANY_NAME AS ISSUER_NAME,
            ci.CIK,  -- Extract CIK for SEC filings integration
            -- Extract Country of Domicile from company characteristics
            MAX(CASE WHEN char.RELATIONSHIP_TYPE = 'business_address_country' THEN char.VALUE END) AS COUNTRY_OF_DOMICILE,
            -- Use SIC Description as a proxy for industry, as GICS is not in this base dataset
            MAX(CASE WHEN char.RELATIONSHIP_TYPE = 'sic_description' THEN char.VALUE END) AS INDUSTRY_SECTOR
        FROM
            {config.SECURITIES['sec_filings_database']}.{config.SECURITIES['sec_filings_schema']}.OPENFIGI_SECURITY_INDEX AS osi
        LEFT JOIN
            {config.SECURITIES['sec_filings_database']}.{config.SECURITIES['sec_filings_schema']}.COMPANY_SECURITY_RELATIONSHIPS AS rship 
                ON osi.TOP_LEVEL_OPENFIGI_ID = rship.SECURITY_ID AND osi.TOP_LEVEL_OPENFIGI_ID_TYPE = rship.security_id_type
        LEFT JOIN
            {config.SECURITIES['sec_filings_database']}.{config.SECURITIES['sec_filings_schema']}.COMPANY_INDEX AS ci ON rship.COMPANY_ID = ci.COMPANY_ID
        LEFT JOIN
            {config.SECURITIES['sec_filings_database']}.{config.SECURITIES['sec_filings_schema']}.COMPANY_CHARACTERISTICS AS char ON rship.COMPANY_ID = char.COMPANY_ID
        WHERE
            NOT (ARRAY_CONTAINS('CEDEAR'::variant, osi.SECURITY_TYPE) 
                OR ARRAY_CONTAINS('PRIV PLACEMENT'::variant, osi.SECURITY_TYPE)
                OR ARRAY_CONTAINS('Crypto'::variant, osi.SECURITY_TYPE))
        GROUP BY
            osi.TOP_LEVEL_OPENFIGI_ID,
            osi.SECURITY_NAME,
            osi.ASSET_CLASS,
            osi.SECURITY_TYPE,
            osi.SECURITY_SUBTYPE,
            osi.PRIMARY_TICKER,
            ci.PRIMARY_EXCHANGE_CODE,
            ci.PRIMARY_EXCHANGE_NAME,
            osi.EXCHANGE_CODES,
            ci.COMPANY_NAME,
            ci.CIK  -- Include CIK in GROUP BY
    ),
    Categorized_Securities AS (
        -- This CTE applies the asset class and market region logic to each security.
        SELECT
            es.TOP_LEVEL_OPENFIGI_ID,
            es.SECURITY_NAME,
            es.ISSUER_NAME,
            es.PRIMARY_TICKER,
            es.PRIMARY_EXCHANGE_CODE,
            IFNULL(es.PRIMARY_EXCHANGE_NAME, es.EXCHANGE_CODES[0]::varchar) AS PRIMARY_EXCHANGE_NAME,
            es.EXCHANGE_CODES,
            es.INDUSTRY_SECTOR,
            es.COUNTRY_OF_DOMICILE,
            es.CIK,  -- Pass through CIK
            -- Asset Category Classification Logic (Expanded to include more bond types)
            CASE
                WHEN es.ASSET_CLASS = 'Corp' THEN 'Corporate Bond'
                WHEN es.ASSET_CLASS = 'Govt' THEN 'Government Bond'
                WHEN es.ASSET_CLASS = 'Muni' THEN 'Municipal Bond'
                WHEN es.ASSET_CLASS = 'Mtge' THEN 'Mortgage-Backed Security'
                WHEN es.ASSET_CLASS = 'Equity' AND (
                    ARRAY_CONTAINS('ETF'::variant, es.SECURITY_TYPE) OR
                    ARRAY_CONTAINS('Exchange Traded Fund'::variant, es.SECURITY_TYPE) OR
                    ARRAY_CONTAINS('ETN'::variant, es.SECURITY_TYPE) OR
                    ARRAY_CONTAINS('ETP'::variant, es.SECURITY_TYPE) OR
                    ARRAY_CONTAINS('Unit Trust'::variant, es.SECURITY_TYPE) OR
                    ARRAY_CONTAINS('UIT'::variant, es.SECURITY_TYPE) OR
                    ARRAY_CONTAINS('Closed-End Fund'::variant, es.SECURITY_TYPE) OR
                    ARRAY_CONTAINS('Open-End Fund'::variant, es.SECURITY_TYPE) OR
                    ARRAY_CONTAINS('Fund of Funds'::variant, es.SECURITY_TYPE) OR
                    ARRAY_CONTAINS('Mutual Fund'::variant, es.SECURITY_SUBTYPE)
                ) THEN 'ETF'
                WHEN es.ASSET_CLASS = 'Equity' THEN 'Equity'
                ELSE NULL
            END AS ASSET_CATEGORY,
            -- Market Region Logic (USA included)
            CASE
                WHEN es.COUNTRY_OF_DOMICILE IN (
                    'AT', 'BE', 'BG', 'HR', 'CY', 'DK', 'EE', 'FI', 'FR', 'DE', 'GI', 'GG',
                    'GR', 'IS', 'IE', 'IM', 'IT', 'JE', 'LV', 'LI', 'LT', 'LU', 'MT', 'MC',
                    'NL', 'NO', 'PT', 'RO', 'SM', 'SK', 'SI', 'ES', 'SE', 'CH', 'GB', 'VA'
                ) THEN 'Europe'
                WHEN es.COUNTRY_OF_DOMICILE = 'US' THEN 'USA'
                WHEN es.COUNTRY_OF_DOMICILE IN (
                    'AF', 'AU', 'BD', 'BT', 'BR', 'BN', 'KH', 'CL', 'CN', 'CO', 'CK', 'CZ',
                    'KP', 'EG', 'FJ', 'GR', 'HK', 'HU', 'IN', 'ID', 'JP', 'KI', 'KW', 'LA',
                    'MY', 'MV', 'MH', 'MX', 'FM', 'MN', 'MM', 'NR', 'NP', 'NZ', 'PK', 'PW',
                    'PG', 'PE', 'PH', 'PL', 'QA', 'KR', 'WS', 'SA', 'SG', 'SB', 'ZA', 'LK',
                    'TW', 'TH', 'TL', 'TO', 'TR', 'TV', 'AE', 'VU', 'VN'
                ) THEN 'APAC/EM'
                ELSE 'Other'
            END AS MARKET_REGION
        FROM
            Enriched_Securities AS es
    )
    -- Final SELECT Statement with CIK included
    SELECT
        cs.MARKET_REGION,
        cs.ASSET_CATEGORY,
        cs.ISSUER_NAME,
        cs.INDUSTRY_SECTOR,
        cs.TOP_LEVEL_OPENFIGI_ID,
        cs.SECURITY_NAME,
        cs.PRIMARY_TICKER,
        cs.PRIMARY_EXCHANGE_CODE,
        cs.PRIMARY_EXCHANGE_NAME,
        cs.COUNTRY_OF_DOMICILE,
        cs.EXCHANGE_CODES,
        cs.CIK  -- Include CIK in final output
    FROM
        Categorized_Securities cs
    WHERE
        cs.ASSET_CATEGORY IS NOT NULL
    ORDER BY
        cs.MARKET_REGION,
        cs.ASSET_CATEGORY,
        cs.ISSUER_NAME,
        cs.SECURITY_NAME
    """
    
    try:
        session.sql(view_sql).collect()
        
        # Verify the view was created and get statistics
        stats = session.sql(f"""
        SELECT 
            COUNT(*) as total_assets,
            COUNT(DISTINCT ASSET_CATEGORY) as asset_categories,
            COUNT(DISTINCT MARKET_REGION) as market_regions,
            COUNT(CIK) as assets_with_cik
        FROM {config.DATABASE['name']}.{config.DATABASE['schemas']['RAW'.lower()]}.V_REAL_ASSETS
        """).collect()[0]
        
        # print(f"✅ Created view V_REAL_ASSETS with {stats['TOTAL_ASSETS']:,} assets")
        # print(f"   📊 Asset categories: {stats['ASSET_CATEGORIES']}")
        # print(f"   🌍 Market regions: {stats['MARKET_REGIONS']}")
        # print(f"   🔗 Assets with CIK: {stats['ASSETS_WITH_CIK']:,}")
        
        return True
        
    except Exception as e:
        # print(f"❌ Failed to create real assets view: {e}")
        raise

