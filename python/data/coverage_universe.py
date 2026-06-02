"""
Coverage Universe — defines which issuers get AI processing.

Configuration lives in data/reference_data/companies.yaml under `coverage_universe`:
  tiers: [core, major, additional, supply_chain]   # which tiers to include
  expanded_additions: [ABNB, ARM, ...]             # extra tickers from expanded tier

Used to filter expensive AI operations (speaker mapping, NLP signals, earnings insights)
to a realistic ~100-150 name universe instead of the full ~500 issuer market data set.
"""

from snowflake.snowpark import Session
import config
from utils.logging import log_info


def get_coverage_tickers() -> list:
    """Get coverage universe tickers from reference_data config."""
    coverage_config = config.REF_DATA['companies'].get('coverage_universe', {})
    tiers = coverage_config.get('tiers', ['core', 'major', 'additional', 'supply_chain'])
    expanded_additions = coverage_config.get('expanded_additions', [])

    coverage_tickers = [
        ticker for ticker, data in config.DEMO_COMPANIES.items()
        if data.get('tier') in tiers
    ]

    for t in expanded_additions:
        if t not in coverage_tickers and t in config.DEMO_COMPANIES:
            coverage_tickers.append(t)

    return coverage_tickers


def build_coverage_universe(session: Session):
    """Create or replace DIM_COVERAGE_UNIVERSE from companies.yaml config."""
    database = config.DATABASE['name']
    schema = config.DATABASE['schemas']['curated']

    coverage_tickers = get_coverage_tickers()

    if not coverage_tickers:
        log_info("  WARNING: No coverage tickers resolved — using all non-expanded")
        coverage_tickers = [
            ticker for ticker, data in config.DEMO_COMPANIES.items()
            if data.get('tier') != 'expanded'
        ]

    ticker_list = ",".join(f"'{t}'" for t in coverage_tickers)

    session.sql(f"""
        CREATE OR REPLACE TABLE {database}.{schema}.DIM_COVERAGE_UNIVERSE AS
        SELECT
            i.ISSUERID,
            i.PRIMARYTICKER AS TICKER,
            i.LEGALNAME AS COMPANY_NAME,
            i.GICS_SECTOR,
            i.COUNTRYOFINCORPORATION,
            CURRENT_TIMESTAMP() AS ADDED_AT
        FROM {database}.{schema}.DIM_ISSUER i
        WHERE i.PRIMARYTICKER IN ({ticker_list})
          AND i.PRIMARYTICKER IS NOT NULL
        ORDER BY i.GICS_SECTOR, i.LEGALNAME
    """).collect()

    count = session.sql(f"SELECT COUNT(*) AS CNT FROM {database}.{schema}.DIM_COVERAGE_UNIVERSE").collect()[0]['CNT']
    coverage_config = config.REF_DATA['companies'].get('coverage_universe', {})
    tiers = coverage_config.get('tiers', [])
    extras = len(coverage_config.get('expanded_additions', []))
    log_info(f"  Coverage universe: {count} issuers (tiers: {tiers}, +{extras} expanded additions)")
