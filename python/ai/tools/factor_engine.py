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
Factor Engine Tools for SAM Demo

Creates the output tables for the ML-based quant factor workflow and
populates SQL stand-ins for FACT_FACTOR_RETURNS and FACT_OPTIMAL_PORTFOLIO.
The Feature Store setup, Fama-MacBeth UDTF, XGBoost factor discovery and
portfolio optimisation are demonstrated interactively in
notebooks/factor_discovery.ipynb; the stand-ins keep the tables sane when
the notebook has not been run.
"""

from typing import Any, Dict

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_info, log_warning
from .ml_common import get_ml_schema_ref

STANDIN_FACTORS = ['MOMENTUM', 'VALUE', 'QUALITY', 'GROWTH', 'SIZE', 'VOLATILITY']


def create_factor_tables(session: Session):
    ml_ref = get_ml_schema_ref()

    session.sql(f"""
    CREATE TABLE IF NOT EXISTS {ml_ref}.FACT_FACTOR_SCORES (
        TICKER              VARCHAR(20) NOT NULL,
        MONTH_DATE          DATE NOT NULL,
        MOMENTUM_SCORE      FLOAT,
        VALUE_SCORE         FLOAT,
        QUALITY_SCORE       FLOAT,
        GROWTH_SCORE        FLOAT,
        SIZE_SCORE          FLOAT,
        VOLATILITY_SCORE    FLOAT,
        PROFITABILITY_SCORE FLOAT,
        LEVERAGE_SCORE       FLOAT,
        EARNINGS_REVISION   FLOAT,
        DIVIDEND_YIELD_SCORE FLOAT,
        BETA_SCORE          FLOAT,
        LIQUIDITY_SCORE     FLOAT
    )
    """).collect()
    log_detail("  Created: FACT_FACTOR_SCORES")

    session.sql(f"""
    CREATE TABLE IF NOT EXISTS {ml_ref}.FACT_FACTOR_RETURNS (
        MONTH_DATE          DATE NOT NULL,
        MOMENTUM_RETURN     FLOAT,
        VALUE_RETURN        FLOAT,
        QUALITY_RETURN      FLOAT,
        GROWTH_RETURN       FLOAT,
        SIZE_RETURN         FLOAT,
        VOLATILITY_RETURN   FLOAT,
        MOMENTUM_TSTAT      FLOAT,
        VALUE_TSTAT         FLOAT,
        QUALITY_TSTAT       FLOAT,
        GROWTH_TSTAT        FLOAT,
        SIZE_TSTAT          FLOAT,
        VOLATILITY_TSTAT    FLOAT,
        R_SQUARED           FLOAT
    )
    """).collect()
    log_detail("  Created: FACT_FACTOR_RETURNS")

    session.sql(f"""
    CREATE TABLE IF NOT EXISTS {ml_ref}.FACT_ML_FACTOR_PREDICTIONS (
        TICKER              VARCHAR(20) NOT NULL,
        MONTH_DATE          DATE NOT NULL,
        PREDICTED_RETURN    FLOAT,
        SHAP_TOP_FEATURE    VARCHAR(50),
        SHAP_TOP_VALUE      FLOAT,
        MODEL_VERSION       VARCHAR(50),
        SCORED_AT           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    )
    """).collect()
    log_detail("  Created: FACT_ML_FACTOR_PREDICTIONS")

    session.sql(f"""
    CREATE TABLE IF NOT EXISTS {ml_ref}.FACT_OPTIMAL_PORTFOLIO (
        TICKER              VARCHAR(20) NOT NULL,
        MONTH_DATE          DATE NOT NULL,
        WEIGHT              FLOAT,
        EXPECTED_RETURN     FLOAT,
        RISK_CONTRIBUTION   FLOAT
    )
    """).collect()
    log_detail("  Created: FACT_OPTIMAL_PORTFOLIO")


def _monthly_returns_ctes(database_name: str, market_data: str) -> str:
    return f"""
    last_px AS (
        SELECT MAX(PRICE_DATE) AS D FROM {database_name}.{market_data}.FACT_STOCK_PRICES
    ),
    month_end_prices AS (
        SELECT p.SECURITYID, DATE_TRUNC('month', p.PRICE_DATE) AS MONTH_DATE, p.PRICE_CLOSE
        FROM {database_name}.{market_data}.FACT_STOCK_PRICES p
        WHERE p.PRICE_CLOSE > 0
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY p.SECURITYID, DATE_TRUNC('month', p.PRICE_DATE) ORDER BY p.PRICE_DATE DESC
        ) = 1
    ),
    raw_returns AS (
        SELECT SECURITYID, MONTH_DATE, PRICE_CLOSE,
            LAG(PRICE_CLOSE) OVER (PARTITION BY SECURITYID ORDER BY MONTH_DATE) AS PREV_CLOSE,
            PRICE_CLOSE / NULLIF(LAG(PRICE_CLOSE) OVER (PARTITION BY SECURITYID ORDER BY MONTH_DATE), 0) - 1 AS RET
        FROM month_end_prices
    )"""


def _factor_regression_ctes(c: Dict[str, Any]) -> str:
    """CTEs ending in with_tstat (MONTH_DATE, FACTOR, RAW_SLOPE, FACTOR_RETURN, TSTAT, R2).

    Scores are standardised cross-sectionally per month with median/MAD scaling and
    winsorised at +/- score_clip, so each slope is a return per robust standard
    deviation of exposure. Forward returns are winsorised at the configured
    percentiles. FACTOR_RETURN applies a sanity bound that only genuine outliers hit.
    """
    return f"""
    WITH {_monthly_returns_ctes(c['database_name'], c['market_data'])},
    bounds AS (
        SELECT MONTH_DATE,
            PERCENTILE_CONT({c['winsor_lo']}) WITHIN GROUP (ORDER BY RET) AS LO,
            PERCENTILE_CONT({c['winsor_hi']}) WITHIN GROUP (ORDER BY RET) AS HI
        FROM raw_returns
        WHERE RET IS NOT NULL
        GROUP BY MONTH_DATE
    ),
    fwd_returns AS (
        SELECT r.SECURITYID, DATEADD('month', -1, r.MONTH_DATE) AS SCORE_MONTH,
            GREATEST(b.LO, LEAST(b.HI, r.RET)) AS FWD_RETURN
        FROM raw_returns r
        JOIN bounds b ON b.MONTH_DATE = r.MONTH_DATE
        CROSS JOIN last_px lp
        WHERE r.RET IS NOT NULL
          AND r.PREV_CLOSE >= 1
          AND LAST_DAY(r.MONTH_DATE) <= DATEADD('day', 5, lp.D)
    ),
    scores AS (
        SELECT s.SECURITYID, f.MONTH_DATE,
            {c['score_cols']}
        FROM {c['ml_ref']}.FACT_FACTOR_SCORES f
        JOIN {c['database_name']}.{c['curated']}.DIM_SECURITY s
            ON s.TICKER = f.TICKER AND s.AssetClass = 'Equity'
    ),
    panel AS (
        SELECT sc.*, fr.FWD_RETURN
        FROM scores sc
        JOIN fwd_returns fr ON fr.SECURITYID = sc.SECURITYID AND fr.SCORE_MONTH = sc.MONTH_DATE
    ),
    long_panel AS (
        SELECT MONTH_DATE, FWD_RETURN, FACTOR, SCORE
        FROM panel UNPIVOT (SCORE FOR FACTOR IN ({c['factor_list']}))
        WHERE SCORE IS NOT NULL
    ),
    score_centre AS (
        SELECT MONTH_DATE, FACTOR, MEDIAN(SCORE) AS MED, STDDEV_SAMP(SCORE) AS SD
        FROM long_panel
        GROUP BY MONTH_DATE, FACTOR
    ),
    score_scale AS (
        SELECT lp.MONTH_DATE, lp.FACTOR, sc.MED, sc.SD,
            1.4826 * MEDIAN(ABS(lp.SCORE - sc.MED)) AS MAD
        FROM long_panel lp
        JOIN score_centre sc ON sc.MONTH_DATE = lp.MONTH_DATE AND sc.FACTOR = lp.FACTOR
        GROUP BY lp.MONTH_DATE, lp.FACTOR, sc.MED, sc.SD
    ),
    robust_panel AS (
        SELECT lp.MONTH_DATE, lp.FACTOR, lp.FWD_RETURN,
            GREATEST(-{c['score_clip']}, LEAST({c['score_clip']},
                (lp.SCORE - ss.MED) / NULLIF(COALESCE(NULLIF(ss.MAD, 0), ss.SD), 0)
            )) AS Z
        FROM long_panel lp
        JOIN score_scale ss ON ss.MONTH_DATE = lp.MONTH_DATE AND ss.FACTOR = lp.FACTOR
    ),
    regressions AS (
        SELECT MONTH_DATE, FACTOR,
            REGR_SLOPE(FWD_RETURN, Z) AS SLOPE,
            REGR_R2(FWD_RETURN, Z) AS R2,
            REGR_COUNT(FWD_RETURN, Z) AS N,
            STDDEV_SAMP(FWD_RETURN) AS SY,
            STDDEV_SAMP(Z) AS SX
        FROM robust_panel
        WHERE Z IS NOT NULL
        GROUP BY MONTH_DATE, FACTOR
        HAVING REGR_COUNT(FWD_RETURN, Z) >= {c['min_names']} AND STDDEV_SAMP(Z) > 0
    ),
    with_tstat AS (
        SELECT MONTH_DATE, FACTOR,
            SLOPE AS RAW_SLOPE,
            GREATEST(-{c['max_abs_return']}, LEAST({c['max_abs_return']}, SLOPE)) AS FACTOR_RETURN,
            SLOPE / NULLIF(SQRT(GREATEST(1 - R2, 0) / (N - 2)) * SY / SX, 0) AS TSTAT,
            R2
        FROM regressions
    )"""


def _factor_regression_config() -> Dict[str, Any]:
    standin = config.ML_CONFIG.get('factor_standin', {})
    return {
        'ml_ref': get_ml_schema_ref(),
        'database_name': config.DATABASE['name'],
        'curated': config.DATABASE['schemas']['curated'],
        'market_data': config.DATABASE['schemas']['market_data'],
        'min_names': standin.get('min_names_per_month', 50),
        'winsor_lo': standin.get('return_winsor_lower', 0.01),
        'winsor_hi': standin.get('return_winsor_upper', 0.99),
        'max_abs_return': standin.get('max_abs_factor_return', 0.10),
        'score_clip': standin.get('score_clip', 3),
        'score_cols': ',\n            '.join(f"f.{name}_SCORE AS {name}" for name in STANDIN_FACTORS),
        'factor_list': ', '.join(STANDIN_FACTORS),
    }


def factor_return_clip_stats(session: Session) -> Dict[str, Any]:
    c = _factor_regression_config()
    row = session.sql(f"""
    {_factor_regression_ctes(c)}
    SELECT COUNT(*) AS N,
        COUNT_IF(ABS(RAW_SLOPE) > {c['max_abs_return']}) AS CLIPPED,
        MEDIAN(ABS(RAW_SLOPE)) AS MEDIAN_ABS,
        MAX(ABS(RAW_SLOPE)) AS MAX_ABS
    FROM with_tstat
    """).collect()[0]
    n = row['N'] or 0
    return {
        'factor_months': n,
        'clipped': row['CLIPPED'] or 0,
        'clipped_fraction': (row['CLIPPED'] or 0) / n if n else 0.0,
        'median_abs_return': row['MEDIAN_ABS'],
        'max_abs_return': row['MAX_ABS'],
        'bound': c['max_abs_return'],
    }


def populate_factor_returns(session: Session) -> int:
    c = _factor_regression_config()
    ml_ref = c['ml_ref']
    return_cols = ',\n        '.join(
        f"MAX(IFF(FACTOR = '{name}', FACTOR_RETURN, NULL)) AS {name}_RETURN" for name in STANDIN_FACTORS
    )
    tstat_cols = ',\n        '.join(
        f"MAX(IFF(FACTOR = '{name}', TSTAT, NULL)) AS {name}_TSTAT" for name in STANDIN_FACTORS
    )

    session.sql(f"""
    INSERT OVERWRITE INTO {ml_ref}.FACT_FACTOR_RETURNS (
        MONTH_DATE,
        {', '.join(f'{n}_RETURN' for n in STANDIN_FACTORS)},
        {', '.join(f'{n}_TSTAT' for n in STANDIN_FACTORS)},
        R_SQUARED
    )
    {_factor_regression_ctes(c)}
    SELECT
        MONTH_DATE,
        {return_cols},
        {tstat_cols},
        AVG(R2) AS R_SQUARED
    FROM with_tstat
    GROUP BY MONTH_DATE
    HAVING COUNT(*) = {len(STANDIN_FACTORS)}
    """).collect()

    stats = factor_return_clip_stats(session)
    message = (
        f"  Factor returns: {stats['clipped']}/{stats['factor_months']} factor-months "
        f"({stats['clipped_fraction']:.1%}) hit the +/-{stats['bound']:.0%} sanity bound"
    )
    if stats['clipped_fraction'] > 0.10:
        log_warning(message)
    else:
        log_detail(message)
    return session.sql(f"SELECT COUNT(*) AS N FROM {ml_ref}.FACT_FACTOR_RETURNS").collect()[0]['N']


def populate_optimal_portfolio(session: Session) -> int:
    ml_ref = get_ml_schema_ref()
    database_name = config.DATABASE['name']
    curated = config.DATABASE['schemas']['curated']
    market_data = config.DATABASE['schemas']['market_data']
    standin = config.ML_CONFIG.get('factor_standin', {})
    n_names = standin.get('optimal_portfolio_names', 20)
    max_weight = standin.get('optimal_portfolio_max_weight', 0.10)
    lookback = standin.get('covariance_lookback_months', 36)
    min_history = standin.get('min_history_months', 30)
    min_price = standin.get('min_price', 5)
    max_monthly_move = standin.get('max_monthly_move', 0.30)
    max_abs_return = standin.get('max_abs_factor_return', 0.05)

    session.sql(f"""
    INSERT OVERWRITE INTO {ml_ref}.FACT_OPTIMAL_PORTFOLIO (TICKER, MONTH_DATE, WEIGHT, EXPECTED_RETURN, RISK_CONTRIBUTION)
    WITH {_monthly_returns_ctes(database_name, market_data)},
    latest_month AS (
        SELECT MAX(MONTH_DATE) AS M FROM {ml_ref}.FACT_ML_FACTOR_PREDICTIONS
    ),
    history AS (
        SELECT r.SECURITYID, r.MONTH_DATE, r.RET
        FROM raw_returns r
        CROSS JOIN latest_month lm
        WHERE r.RET IS NOT NULL
          AND r.MONTH_DATE > DATEADD('month', -{lookback}, lm.M)
          AND r.MONTH_DATE <= lm.M
    ),
    eligible AS (
        SELECT SECURITYID, STDDEV_SAMP(RET) AS VOL
        FROM history
        GROUP BY SECURITYID
        HAVING COUNT(*) >= {min_history} AND MAX(ABS(RET)) < {max_monthly_move}
    ),
    last_close AS (
        SELECT r.SECURITYID, r.PRICE_CLOSE
        FROM raw_returns r
        CROSS JOIN latest_month lm
        WHERE r.MONTH_DATE = lm.M
    ),
    candidates AS (
        SELECT p.TICKER, s.SECURITYID, lm.M AS MONTH_DATE,
            GREATEST(-{max_abs_return}, LEAST({max_abs_return}, p.PREDICTED_RETURN)) AS EXPECTED_RETURN,
            e.VOL
        FROM {ml_ref}.FACT_ML_FACTOR_PREDICTIONS p
        CROSS JOIN latest_month lm
        JOIN {database_name}.{curated}.DIM_SECURITY s ON s.TICKER = p.TICKER AND s.AssetClass = 'Equity'
        JOIN eligible e ON e.SECURITYID = s.SECURITYID
        JOIN last_close lc ON lc.SECURITYID = s.SECURITYID
        WHERE p.MONTH_DATE = lm.M AND lc.PRICE_CLOSE >= {min_price} AND e.VOL > 0
        QUALIFY ROW_NUMBER() OVER (ORDER BY p.PREDICTED_RETURN / e.VOL DESC) <= {n_names}
    ),
    raw_weights AS (
        SELECT c.*, (1 / c.VOL) / SUM(1 / c.VOL) OVER () AS W0
        FROM candidates c
    ),
    weights AS (
        SELECT TICKER, SECURITYID, MONTH_DATE, EXPECTED_RETURN,
            LEAST(W0, {max_weight}) / SUM(LEAST(W0, {max_weight})) OVER () AS WEIGHT
        FROM raw_weights
    ),
    demeaned AS (
        SELECT h.SECURITYID, h.MONTH_DATE, h.RET - AVG(h.RET) OVER (PARTITION BY h.SECURITYID) AS DRET
        FROM history h
        JOIN weights w ON w.SECURITYID = h.SECURITYID
    ),
    covariance AS (
        SELECT a.SECURITYID AS SID_I, b.SECURITYID AS SID_J,
            SUM(a.DRET * b.DRET) / NULLIF(COUNT(*) - 1, 0) AS COV
        FROM demeaned a
        JOIN demeaned b ON a.MONTH_DATE = b.MONTH_DATE
        GROUP BY a.SECURITYID, b.SECURITYID
    ),
    marginal AS (
        SELECT c.SID_I, SUM(c.COV * w.WEIGHT) AS SIGMA_W
        FROM covariance c
        JOIN weights w ON w.SECURITYID = c.SID_J
        GROUP BY c.SID_I
    )
    SELECT w.TICKER, w.MONTH_DATE, ROUND(w.WEIGHT, 8), w.EXPECTED_RETURN,
        w.WEIGHT * m.SIGMA_W / NULLIF(SUM(w.WEIGHT * m.SIGMA_W) OVER (), 0)
    FROM weights w
    JOIN marginal m ON m.SID_I = w.SECURITYID
    """).collect()
    return session.sql(f"SELECT COUNT(*) AS N FROM {ml_ref}.FACT_OPTIMAL_PORTFOLIO").collect()[0]['N']


def populate_factor_standins(session: Session) -> None:
    ml_ref = get_ml_schema_ref()
    create_factor_tables(session)
    score_rows = session.sql(f"SELECT COUNT(*) AS N FROM {ml_ref}.FACT_FACTOR_SCORES").collect()[0]['N']
    if not score_rows:
        log_warning("FACT_FACTOR_SCORES is empty; factor return and optimal portfolio stand-ins skipped")
        return
    return_rows = populate_factor_returns(session)
    log_detail(f"  Populated FACT_FACTOR_RETURNS stand-in: {return_rows} months")
    prediction_rows = session.sql(
        f"SELECT COUNT(*) AS N FROM {ml_ref}.FACT_ML_FACTOR_PREDICTIONS"
    ).collect()[0]['N']
    if not prediction_rows:
        log_warning("FACT_ML_FACTOR_PREDICTIONS is empty; optimal portfolio stand-in skipped")
        return
    portfolio_rows = populate_optimal_portfolio(session)
    log_detail(f"  Populated FACT_OPTIMAL_PORTFOLIO stand-in: {portfolio_rows} names")


def build_factor_scenario(session: Session):
    log_info("Building factor workflow scenario scaffolding...")
    create_factor_tables(session)
    log_info("Factor workflow scaffolding complete")
