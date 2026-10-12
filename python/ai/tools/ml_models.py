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
Build-trained ML models for SAM Demo

Trains, registers and batch-scores the market regime GMM and the credit risk
PD model so the agent scenarios that read their outputs work without running
the notebooks first. The build logs a new version of the same model names the
notebooks use and moves the PRODUCTION alias onto it; every consumer (batch
scoring, PREDICT_BORROWER_PD) resolves PRODUCTION.
"""

import json
import os
import pickle
import tempfile
from datetime import datetime
from typing import Dict, List, Optional

from snowflake.snowpark import Session
import config
from utils.logging import log_detail, log_info, log_phase, log_phase_complete, log_step, log_success, log_warning
from .ml_common import get_ml_schema_ref, ensure_ml_schema
from .credit_risk import create_credit_risk_tables
from .regime_detection import create_regime_prediction_table
from .factor_engine import populate_factor_standins


def _sql_array(values: List[str]) -> str:
    return "[" + ", ".join(f"'{v}'" for v in values) + "]"


def _model_ref(model_key: str) -> str:
    return f"{get_ml_schema_ref()}.{config.ML_CONFIG[model_key]['name']}"


def _alias() -> str:
    return config.ML_CONFIG['production_alias']


def create_feature_views(session: Session) -> None:
    database_name = config.DATABASE['name']
    ml_ref = get_ml_schema_ref()
    regime_cfg = config.ML_CONFIG['regime_model']
    credit_cfg = config.ML_CONFIG['credit_risk_model']
    rating_scale = _sql_array(credit_cfg['rating_scale'])
    regime_scale = _sql_array(credit_cfg['regime_scale'])
    stress_headroom = credit_cfg['stress_headroom_pct']

    session.sql(f"""
    CREATE OR REPLACE VIEW {ml_ref}.{regime_cfg['features_view']}
    COMMENT = 'Daily market regime features (20/60 trading-day windows) shared by training and scoring'
    AS
    WITH base AS (
        SELECT v.DATE, v.VIX_CLOSE AS VIX_LEVEL, r.DAILY_RETURN, s.SECTOR_DISPERSION
        FROM {database_name}.MARKET_DATA.FACT_VIX_DAILY v
        JOIN {database_name}.MARKET_DATA.FACT_BENCHMARK_RETURNS r
          ON r.DATE = v.DATE AND r.BENCHMARK_CODE = '{regime_cfg['benchmark_code']}'
        LEFT JOIN (
            SELECT DATE, STDDEV(SECTOR_RETURN) AS SECTOR_DISPERSION
            FROM {database_name}.MARKET_DATA.FACT_SECTOR_RETURNS
            GROUP BY DATE
        ) s ON s.DATE = v.DATE
    ),
    windowed AS (
        SELECT
            DATE,
            VIX_LEVEL,
            AVG(VIX_LEVEL) OVER (ORDER BY DATE ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS VIX_20D_MA,
            STDDEV(DAILY_RETURN) OVER (ORDER BY DATE ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS REALISED_VOL_20D,
            STDDEV(DAILY_RETURN) OVER (ORDER BY DATE ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) AS REALISED_VOL_60D,
            SUM(DAILY_RETURN) OVER (ORDER BY DATE ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS MOMENTUM_20D,
            SUM(DAILY_RETURN) OVER (ORDER BY DATE ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) AS MOMENTUM_60D,
            SECTOR_DISPERSION,
            ROW_NUMBER() OVER (ORDER BY DATE) AS RowNum
        FROM base
    )
    SELECT
        DATE,
        VIX_LEVEL::FLOAT AS VIX_LEVEL,
        VIX_20D_MA::FLOAT AS VIX_20D_MA,
        REALISED_VOL_20D::FLOAT AS REALISED_VOL_20D,
        REALISED_VOL_60D::FLOAT AS REALISED_VOL_60D,
        MOMENTUM_20D::FLOAT AS MOMENTUM_20D,
        MOMENTUM_60D::FLOAT AS MOMENTUM_60D,
        COALESCE(SECTOR_DISPERSION, 0)::FLOAT AS SECTOR_DISPERSION,
        (VIX_LEVEL - REALISED_VOL_20D * SQRT(252) * 100)::FLOAT AS VOL_RISK_PREMIUM
    FROM windowed
    WHERE RowNum >= 60
    """).collect()
    log_detail(f"  Created view: {regime_cfg['features_view']}")

    session.sql(f"""
    CREATE OR REPLACE VIEW {ml_ref}.{credit_cfg['features_view']}
    COMMENT = 'Borrower-quarter PD features plus the forward-looking NEXT_QUARTER_STRESS label'
    AS
    WITH fin AS (
        SELECT
            f.BORROWERID,
            f.BORROWERNAME,
            TO_DATE(f.REPORTDATE) AS QUARTER_DATE,
            f.TOTALLEVERAGE, f.NETLEVERAGE, f.INTERESTCOVERAGE, f.FIXEDCHARGECOVERAGE, f.EBITDA_MARGIN,
            DIV0NULL(f.FREECASHFLOW_MM, NULLIF(f.REVENUE_MM, 0)) AS FCF_MARGIN,
            DIV0NULL(f.CAPEX_MM, NULLIF(f.EBITDA_MM, 0)) AS CAPEX_INTENSITY,
            f.FREECASHFLOW_MM, f.CASHONHAND_MM, f.REVOLVERAVAILABILITY_MM
        FROM {database_name}.CURATED.FACT_CREDIT_BORROWER_FINANCIALS f
    ),
    cov AS (
        SELECT
            BORROWERID,
            TO_DATE(TESTDATE) AS QUARTER_DATE,
            AVG(HEADROOM_PCT) AS AVG_COVENANT_HEADROOM,
            MIN(HEADROOM_PCT) AS MIN_COVENANT_HEADROOM,
            COUNT_IF(BREACHFLAG) AS BREACH_COUNT
        FROM {database_name}.CURATED.FACT_CREDIT_COVENANT_TRACKING
        GROUP BY BORROWERID, TO_DATE(TESTDATE)
    ),
    regime AS (
        SELECT DATE::TIMESTAMP_NTZ AS RegimeTs, REGIME_LABEL
        FROM {ml_ref}.FACT_REGIME_PREDICTIONS
    ),
    joined AS (
        SELECT
            fin.BORROWERID,
            fin.BORROWERNAME,
            fin.QUARTER_DATE,
            fin.TOTALLEVERAGE::FLOAT AS TOTALLEVERAGE,
            fin.NETLEVERAGE::FLOAT AS NETLEVERAGE,
            fin.INTERESTCOVERAGE::FLOAT AS INTERESTCOVERAGE,
            fin.FIXEDCHARGECOVERAGE::FLOAT AS FIXEDCHARGECOVERAGE,
            fin.EBITDA_MARGIN::FLOAT AS EBITDA_MARGIN,
            COALESCE(fin.FCF_MARGIN, 0)::FLOAT AS FCF_MARGIN,
            COALESCE(fin.CAPEX_INTENSITY, 0)::FLOAT AS CAPEX_INTENSITY,
            fin.FREECASHFLOW_MM::FLOAT AS FREECASHFLOW_MM,
            fin.CASHONHAND_MM::FLOAT AS CASHONHAND_MM,
            fin.REVOLVERAVAILABILITY_MM::FLOAT AS REVOLVERAVAILABILITY_MM,
            cov.AVG_COVENANT_HEADROOM::FLOAT AS AVG_COVENANT_HEADROOM,
            cov.MIN_COVENANT_HEADROOM::FLOAT AS MIN_COVENANT_HEADROOM,
            cov.BREACH_COUNT::FLOAT AS BREACH_COUNT,
            COALESCE(ARRAY_POSITION(b.CREDITRATING::VARIANT, {rating_scale}), -1)::FLOAT AS RATING_ORDINAL,
            COALESCE(ARRAY_POSITION(regime.REGIME_LABEL::VARIANT, {regime_scale}), -1)::FLOAT AS REGIME_ORDINAL,
            IFF(cov.BREACH_COUNT > 0 OR cov.MIN_COVENANT_HEADROOM < {stress_headroom}, 1, 0) AS STRESS_FLAG
        FROM fin
        JOIN {database_name}.CURATED.DIM_CREDIT_BORROWER b ON b.BORROWERID = fin.BORROWERID
        JOIN cov ON cov.BORROWERID = fin.BORROWERID AND cov.QUARTER_DATE = fin.QUARTER_DATE
        ASOF JOIN regime MATCH_CONDITION (fin.QUARTER_DATE::TIMESTAMP_NTZ >= regime.RegimeTs)
    )
    SELECT
        *,
        LEAD(STRESS_FLAG) OVER (PARTITION BY BORROWERID ORDER BY QUARTER_DATE) AS NEXT_QUARTER_STRESS
    FROM joined
    """).collect()
    log_detail(f"  Created view: {credit_cfg['features_view']}")


def _version_name() -> str:
    return f"{config.ML_CONFIG['build_version_prefix']}{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"


def _get_registry(session: Session):
    from snowflake.ml.registry import Registry
    return Registry(
        session=session,
        database_name=config.ML_CONFIG['model_registry_database'],
        schema_name=config.ML_CONFIG['model_registry_schema'],
    )


def _promote(session: Session, model_key: str, version_name: str) -> None:
    model_ref = _model_ref(model_key)
    alias = _alias()
    current = resolve_production_version(session, model_key)
    if current and current != version_name:
        session.sql(f"ALTER MODEL {model_ref} VERSION {alias} UNSET ALIAS").collect()
    if current != version_name:
        session.sql(f"ALTER MODEL {model_ref} VERSION {version_name} SET ALIAS = {alias}").collect()
    session.sql(f"ALTER MODEL {model_ref} SET DEFAULT_VERSION = '{version_name}'").collect()
    runtime_role = config.RBAC['demo_runtime_role']
    session.sql(f"GRANT USAGE ON MODEL {model_ref} TO ROLE {runtime_role}").collect()
    log_detail(f"  {model_ref}: {alias} -> {version_name}")


def resolve_production_version(session: Session, model_key: str) -> Optional[str]:
    ml_ref = get_ml_schema_ref()
    name = config.ML_CONFIG[model_key]['name']
    if not session.sql(f"SHOW MODELS LIKE '{name}' IN SCHEMA {ml_ref}").collect():
        return None
    alias = _alias()
    for row in session.sql(f"SHOW VERSIONS IN MODEL {ml_ref}.{name}").collect():
        aliases = json.loads(row['aliases'] or '[]')
        if alias in aliases:
            return row['name']
    return None


def _build_regime_model_class():
    from snowflake.ml.model import custom_model
    import pandas as pd

    class RegimeGMM(custom_model.CustomModel):
        def __init__(self, context: custom_model.ModelContext) -> None:
            super().__init__(context)
            with open(self.context['pipeline'], 'rb') as handle:
                bundle = pickle.load(handle)
            self.scaler = bundle['scaler']
            self.gmm = bundle['gmm']
            self.features = bundle['features']
            self.order = bundle['order']
            self.labels = bundle['labels']

        @custom_model.inference_api
        def predict(self, input_df: pd.DataFrame) -> pd.DataFrame:
            scaled = self.scaler.transform(input_df[self.features].astype(float).values)
            probs = self.gmm.predict_proba(scaled)[:, self.order]
            best = probs.argmax(axis=1)
            out = pd.DataFrame({
                'REGIME_LABEL': [self.labels[i] for i in best],
                'REGIME_PROBABILITY': probs.max(axis=1),
            })
            for i in range(probs.shape[1]):
                out[f'CLUSTER_{i}_PROB'] = probs[:, i]
            return out

    return RegimeGMM


def train_regime_model(session: Session) -> str:
    import numpy as np
    from sklearn.mixture import GaussianMixture
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score
    from snowflake.ml.model import custom_model

    regime_cfg = config.ML_CONFIG['regime_model']
    features = regime_cfg['features']
    ml_ref = get_ml_schema_ref()
    feature_df = session.table(f"{ml_ref}.{regime_cfg['features_view']}").select(features)
    pdf = feature_df.to_pandas().dropna()

    scaler = StandardScaler()
    scaled = scaler.fit_transform(pdf[features].astype(float).values)
    gmm = GaussianMixture(
        n_components=regime_cfg['n_components'],
        covariance_type='full',
        n_init=regime_cfg['n_init'],
        random_state=config.ML_CONFIG['random_seed'],
    ).fit(scaled)
    clusters = gmm.predict(scaled)
    vix_means = [pdf['VIX_LEVEL'].values[clusters == c].mean() if (clusters == c).any() else np.inf
                 for c in range(regime_cfg['n_components'])]
    order = [int(i) for i in np.argsort(vix_means)]
    labels = regime_cfg['labels_by_vix']

    metrics = {
        'silhouette_score': float(silhouette_score(scaled, clusters)),
        'bic': float(gmm.bic(scaled)),
        'aic': float(gmm.aic(scaled)),
        'n_samples': int(len(pdf)),
    }
    for rank, cluster in enumerate(order):
        metrics[f'{labels[rank].lower()}_share'] = float((clusters == cluster).mean())
        metrics[f'{labels[rank].lower()}_mean_vix'] = float(vix_means[cluster])

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'regime_pipeline.pkl')
        with open(path, 'wb') as handle:
            pickle.dump({'scaler': scaler, 'gmm': gmm, 'features': features, 'order': order, 'labels': labels}, handle)
        model = _build_regime_model_class()(custom_model.ModelContext(artifacts={'pipeline': path}))
        version_name = _version_name()
        _get_registry(session).log_model(
            model,
            model_name=regime_cfg['name'],
            version_name=version_name,
            sample_input_data=feature_df.limit(20),
            conda_dependencies=['scikit-learn', 'pandas'],
            target_platforms=['WAREHOUSE'],
            metrics=metrics,
            comment='Build-trained GMM market regime model (RISK_ON / TRANSITIONAL / RISK_OFF ordered by mean VIX)',
        )
    _promote(session, 'regime_model', version_name)
    log_info(f"  Regime model {version_name}: silhouette={metrics['silhouette_score']:.3f}, n={metrics['n_samples']}")
    return version_name


def score_regime(session: Session) -> int:
    ml_ref = get_ml_schema_ref()
    regime_cfg = config.ML_CONFIG['regime_model']
    model_ref = _model_ref('regime_model')
    alias = _alias()
    version_name = resolve_production_version(session, 'regime_model')
    if not version_name:
        log_warning("  No PRODUCTION regime model; skipping regime scoring")
        return 0
    cols = ", ".join(f"f.{c}" for c in regime_cfg['features'])

    session.sql(f"DELETE FROM {ml_ref}.FACT_REGIME_PREDICTIONS").collect()
    session.sql(f"""
    INSERT INTO {ml_ref}.FACT_REGIME_PREDICTIONS
        (DATE, REGIME_LABEL, REGIME_PROBABILITY, CLUSTER_0_PROB, CLUSTER_1_PROB, CLUSTER_2_PROB,
         VIX_LEVEL, MOMENTUM_20D, REALISED_VOL_20D, MODEL_VERSION)
    WITH scored AS (
        SELECT f.DATE, f.VIX_LEVEL, f.MOMENTUM_20D, f.REALISED_VOL_20D,
               MODEL({model_ref}, {alias})!PREDICT({cols}) AS P
        FROM {ml_ref}.{regime_cfg['features_view']} f
    )
    SELECT DATE, P:REGIME_LABEL::VARCHAR, P:REGIME_PROBABILITY::FLOAT,
           P:CLUSTER_0_PROB::FLOAT, P:CLUSTER_1_PROB::FLOAT, P:CLUSTER_2_PROB::FLOAT,
           VIX_LEVEL, MOMENTUM_20D, REALISED_VOL_20D, '{version_name}'
    FROM scored
    """).collect()
    count = session.sql(f"SELECT COUNT(*) AS N FROM {ml_ref}.FACT_REGIME_PREDICTIONS").collect()[0]['N']
    log_detail(f"  FACT_REGIME_PREDICTIONS: {count} rows ({version_name})")
    return count


def train_credit_risk_model(session: Session) -> str:
    import numpy as np
    import xgboost as xgb
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import roc_auc_score, f1_score

    credit_cfg = config.ML_CONFIG['credit_risk_model']
    features = credit_cfg['features']
    ml_ref = get_ml_schema_ref()
    view = session.table(f"{ml_ref}.{credit_cfg['features_view']}")
    labelled = view.filter("NEXT_QUARTER_STRESS IS NOT NULL")
    pdf = labelled.select(['QUARTER_DATE'] + features + ['NEXT_QUARTER_STRESS']).to_pandas()
    pdf = pdf.sort_values('QUARTER_DATE').reset_index(drop=True)
    X = pdf[features].astype(float)
    y = pdf['NEXT_QUARTER_STRESS'].astype(int)
    positive_rate = float(y.mean())

    params = dict(credit_cfg['xgb_params'])
    params['scale_pos_weight'] = (1 - positive_rate) / max(positive_rate, 0.01)
    params['random_state'] = config.ML_CONFIG['random_seed']

    aucs, f1s = [], []
    for train_idx, test_idx in TimeSeriesSplit(n_splits=credit_cfg['cv_splits']).split(X):
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        if y_train.nunique() < 2 or y_test.nunique() < 2:
            continue
        fold = xgb.XGBClassifier(**params).fit(X.iloc[train_idx], y_train)
        probs = fold.predict_proba(X.iloc[test_idx])[:, 1]
        aucs.append(roc_auc_score(y_test, probs))
        f1s.append(f1_score(y_test, (probs >= 0.5).astype(int)))

    model = xgb.XGBClassifier(**params).fit(X, y)
    metrics = {
        'mean_auc': float(np.mean(aucs)) if aucs else -1.0,
        'mean_f1': float(np.mean(f1s)) if f1s else -1.0,
        'evaluated_folds': len(aucs),
        'n_samples': int(len(pdf)),
        'positive_rate': positive_rate,
    }

    version_name = _version_name()
    _get_registry(session).log_model(
        model,
        model_name=credit_cfg['name'],
        version_name=version_name,
        sample_input_data=labelled.select(features).limit(20),
        conda_dependencies=['xgboost', 'shap'],
        target_platforms=['WAREHOUSE'],
        options={'enable_explainability': True},
        metrics=metrics,
        comment='Build-trained XGBoost PD model: P(covenant breach or headroom < 5% next quarter)',
    )
    _promote(session, 'credit_risk_model', version_name)
    log_info(f"  Credit risk model {version_name}: AUC={metrics['mean_auc']:.3f} over {metrics['evaluated_folds']} folds, n={metrics['n_samples']}, positive rate={positive_rate:.1%}")
    return version_name


def _risk_rating_case(pd_expr: str) -> str:
    bands = config.ML_CONFIG['credit_risk_model']['risk_bands']
    whens = " ".join(f"WHEN {pd_expr} < {upper} THEN '{label}'" for upper, label in bands)
    return f"CASE {whens} ELSE '{bands[-1][1]}' END"


def score_credit_risk(session: Session) -> int:
    ml_ref = get_ml_schema_ref()
    credit_cfg = config.ML_CONFIG['credit_risk_model']
    features = credit_cfg['features']
    model_ref = _model_ref('credit_risk_model')
    alias = _alias()
    version_name = resolve_production_version(session, 'credit_risk_model')
    if not version_name:
        log_warning("  No PRODUCTION credit risk model; skipping credit risk scoring")
        return 0
    view = f"{ml_ref}.{credit_cfg['features_view']}"
    cols = ", ".join(f"f.{c}" for c in features)
    shap_obj = ", ".join(f"'{c}', e.{c}_EXPLANATION" for c in features)
    value_obj = ", ".join(f"'{c}', f.{c}" for c in features)
    top_n = credit_cfg['shap_top_n']

    staging = f"{ml_ref}.TMP_CREDIT_SHAP_STAGING"
    session.sql(f"""
    CREATE OR REPLACE TEMPORARY TABLE {staging} AS
    WITH pd_model AS MODEL {model_ref} VERSION {alias}
    SELECT f.BORROWERID, f.QUARTER_DATE,
           OBJECT_CONSTRUCT({shap_obj}) AS ShapValues,
           OBJECT_CONSTRUCT({value_obj}) AS FeatureValues
    FROM {view} f,
         TABLE(pd_model!EXPLAIN({cols})) e
    """).collect()

    session.sql(f"DELETE FROM {ml_ref}.FACT_CREDIT_SHAP_EXPLANATIONS").collect()
    session.sql(f"""
    INSERT INTO {ml_ref}.FACT_CREDIT_SHAP_EXPLANATIONS (BORROWER_ID, QUARTER_DATE, FEATURE_NAME, SHAP_VALUE, FEATURE_VALUE)
    SELECT x.BORROWERID, x.QUARTER_DATE, s.KEY, s.VALUE::FLOAT, x.FeatureValues[s.KEY]::FLOAT
    FROM {staging} x, LATERAL FLATTEN(INPUT => x.ShapValues) s
    """).collect()
    session.sql(f"DROP TABLE IF EXISTS {staging}").collect()

    session.sql(f"DELETE FROM {ml_ref}.FACT_CREDIT_RISK_SCORES").collect()
    session.sql(f"""
    INSERT INTO {ml_ref}.FACT_CREDIT_RISK_SCORES
        (BORROWER_ID, QUARTER_DATE, PD_SCORE, RISK_RATING, SHAP_TOP_FEATURES, MODEL_VERSION)
    WITH scored AS (
        SELECT f.BORROWERID, f.QUARTER_DATE,
               MODEL({model_ref}, {alias})!PREDICT_PROBA({cols}):output_feature_1::FLOAT AS PdScore
        FROM {view} f
    ),
    top_drivers AS (
        SELECT BORROWER_ID, QUARTER_DATE,
               ARRAY_AGG(OBJECT_CONSTRUCT('feature', FEATURE_NAME, 'shap_value', ROUND(SHAP_VALUE, 4), 'feature_value', FEATURE_VALUE))
                   WITHIN GROUP (ORDER BY ABS(SHAP_VALUE) DESC) AS Drivers
        FROM {ml_ref}.FACT_CREDIT_SHAP_EXPLANATIONS
        GROUP BY BORROWER_ID, QUARTER_DATE
    )
    SELECT s.BORROWERID, s.QUARTER_DATE, s.PdScore, {_risk_rating_case('s.PdScore')},
           ARRAY_SLICE(t.Drivers, 0, {top_n}), '{version_name}'
    FROM scored s
    LEFT JOIN top_drivers t ON t.BORROWER_ID = s.BORROWERID AND t.QUARTER_DATE = s.QUARTER_DATE
    """).collect()
    count = session.sql(f"SELECT COUNT(*) AS N FROM {ml_ref}.FACT_CREDIT_RISK_SCORES").collect()[0]['N']
    log_detail(f"  FACT_CREDIT_RISK_SCORES: {count} rows ({version_name})")
    return count


def create_pd_what_if_tool(session: Session) -> None:
    database_name = config.DATABASE['name']
    ai_schema = config.DATABASE['schemas']['ai']
    ml_ref = get_ml_schema_ref()
    credit_cfg = config.ML_CONFIG['credit_risk_model']
    features = credit_cfg['features']
    model_ref = _model_ref('credit_risk_model')
    alias = _alias()
    view = f"{ml_ref}.{credit_cfg['features_view']}"
    feature_list = _sql_array(features)
    base_obj = ", ".join(f"'{c}', f.{c}" for c in features)
    base_args = ", ".join(f"b:{c}::FLOAT" for c in features)
    stress_args = ", ".join(f"s:{c}::FLOAT" for c in features)
    explain_args = ", ".join(f"r.v:{c}::FLOAT" for c in features)
    shap_obj = ", ".join(f"'{c}', e.{c}_EXPLANATION" for c in features)
    top_n = credit_cfg['shap_top_n']
    model_name = credit_cfg['name']
    stress_headroom = credit_cfg['stress_headroom_pct']
    baseline_rating = _risk_rating_case(':baseline_pd')
    stressed_rating = _risk_rating_case(':stressed_pd')
    covenant_map = credit_cfg['covenant_metric_map']
    metric_case = " ".join(f"WHEN '{cov}' THEN '{metric}'" for cov, (metric, _) in covenant_map.items())
    direction_case = " ".join(f"WHEN '{cov}' THEN '{direction}'" for cov, (_, direction) in covenant_map.items())
    database_name_q = database_name

    session.sql(f"""
CREATE OR REPLACE PROCEDURE {database_name}.{ai_schema}.PREDICT_BORROWER_PD(BORROWER_NAME VARCHAR, OVERRIDES VARCHAR)
RETURNS VARIANT
LANGUAGE SQL
COMMENT = 'Live what-if PD scoring against the PRODUCTION credit risk model'
EXECUTE AS CALLER
AS
$$
DECLARE
    matched_id NUMBER;
    matched_name VARCHAR;
    match_count NUMBER;
    overrides_obj VARIANT;
    unknown_keys ARRAY;
    quarter_date DATE;
    baseline VARIANT;
    stressed VARIANT;
    baseline_pd FLOAT;
    stressed_pd FLOAT;
    baseline_shap VARIANT;
    stressed_shap VARIANT;
    baseline_drivers ARRAY;
    stressed_drivers ARRAY;
    covenant_impact ARRAY;
    result VARIANT;
BEGIN
    SELECT COUNT(DISTINCT BORROWERID), MIN(BORROWERID), MIN(BORROWERNAME)
      INTO :match_count, :matched_id, :matched_name
      FROM {view}
     WHERE UPPER(BORROWERNAME) = UPPER(:BORROWER_NAME);
    IF (match_count = 0) THEN
        SELECT COUNT(DISTINCT BORROWERID), MIN(BORROWERID), MIN(BORROWERNAME)
          INTO :match_count, :matched_id, :matched_name
          FROM {view}
         WHERE BORROWERNAME ILIKE '%' || :BORROWER_NAME || '%';
    END IF;
    IF (match_count <> 1) THEN
        SELECT ARRAY_AGG(DISTINCT BORROWERNAME) INTO :unknown_keys FROM {view};
        RETURN OBJECT_CONSTRUCT('error', IFF(match_count = 0, 'Borrower not found', 'Borrower name is ambiguous'),
                                'requested', :BORROWER_NAME, 'valid_borrowers', :unknown_keys);
    END IF;

    overrides_obj := COALESCE(TRY_PARSE_JSON(NULLIF(TRIM(:OVERRIDES), '')), OBJECT_CONSTRUCT());
    IF (NOT IS_OBJECT(:overrides_obj)) THEN
        RETURN OBJECT_CONSTRUCT('error', 'OVERRIDES must be a JSON object', 'valid_features', {feature_list});
    END IF;
    SELECT ARRAY_AGG(o.KEY) INTO :unknown_keys
      FROM TABLE(FLATTEN(INPUT => :overrides_obj)) o
     WHERE NOT ARRAY_CONTAINS(UPPER(o.KEY)::VARIANT, {feature_list});
    IF (ARRAY_SIZE(:unknown_keys) > 0) THEN
        RETURN OBJECT_CONSTRUCT('error', 'Unknown override features', 'unknown', :unknown_keys, 'valid_features', {feature_list});
    END IF;
    SELECT COALESCE(OBJECT_AGG(UPPER(o.KEY), o.VALUE), OBJECT_CONSTRUCT()) INTO :overrides_obj
      FROM TABLE(FLATTEN(INPUT => :overrides_obj)) o;

    SELECT f.QUARTER_DATE, OBJECT_CONSTRUCT({base_obj})
      INTO :quarter_date, :baseline
      FROM {view} f
     WHERE f.BORROWERID = :matched_id
    QUALIFY ROW_NUMBER() OVER (ORDER BY f.QUARTER_DATE DESC) = 1;

    SELECT OBJECT_AGG(b.KEY,
               (CASE
                   WHEN o.VALUE IS NULL THEN b.VALUE::FLOAT
                   WHEN IS_VARCHAR(o.VALUE) AND ENDSWITH(TRIM(o.VALUE::VARCHAR), '%')
                       THEN b.VALUE::FLOAT * (1 + TRY_TO_DOUBLE(RTRIM(TRIM(o.VALUE::VARCHAR), '%')) / 100)
                   WHEN IS_VARCHAR(o.VALUE) AND LEFT(TRIM(o.VALUE::VARCHAR), 1) IN ('+', '-')
                       THEN b.VALUE::FLOAT + TRY_TO_DOUBLE(TRIM(o.VALUE::VARCHAR))
                   ELSE TRY_TO_DOUBLE(o.VALUE::VARCHAR)
               END)::VARIANT)
      INTO :stressed
      FROM TABLE(FLATTEN(INPUT => :baseline)) b
      LEFT JOIN TABLE(FLATTEN(INPUT => :overrides_obj)) o ON UPPER(o.KEY) = b.KEY;

    IF (NOT (ARRAY_CONTAINS('MIN_COVENANT_HEADROOM'::VARIANT, OBJECT_KEYS(:overrides_obj))
             OR ARRAY_CONTAINS('AVG_COVENANT_HEADROOM'::VARIANT, OBJECT_KEYS(:overrides_obj))
             OR ARRAY_CONTAINS('BREACH_COUNT'::VARIANT, OBJECT_KEYS(:overrides_obj)))) THEN
        WITH tests AS (
            SELECT c.COVENANTTYPE, c.COVENANTTHRESHOLD, c.ACTUALVALUE, c.HEADROOM_PCT, c.BREACHFLAG,
                   CASE c.COVENANTTYPE {metric_case} END AS Metric,
                   CASE c.COVENANTTYPE {direction_case} END AS Direction
            FROM {database_name_q}.CURATED.FACT_CREDIT_COVENANT_TRACKING c
            WHERE c.BORROWERID = :matched_id AND TO_DATE(c.TESTDATE) = :quarter_date
        ),
        shocked AS (
            SELECT COVENANTTYPE, COVENANTTHRESHOLD, HEADROOM_PCT, BREACHFLAG, Metric,
                   IFF(Metric IS NULL, ACTUALVALUE,
                       ACTUALVALUE * DIV0NULL(GET(:stressed, Metric)::FLOAT, GET(:baseline, Metric)::FLOAT)) AS StressedActual,
                   CASE
                       WHEN Metric IS NULL THEN HEADROOM_PCT
                       WHEN Direction = 'max' THEN (COVENANTTHRESHOLD - StressedActual) / COVENANTTHRESHOLD * 100
                       ELSE (StressedActual - COVENANTTHRESHOLD) / COVENANTTHRESHOLD * 100
                   END AS StressedHeadroom
            FROM tests
        )
        SELECT OBJECT_INSERT(OBJECT_INSERT(OBJECT_INSERT(:stressed,
                   'MIN_COVENANT_HEADROOM', MIN(StressedHeadroom)::VARIANT, TRUE),
                   'AVG_COVENANT_HEADROOM', AVG(StressedHeadroom)::VARIANT, TRUE),
                   'BREACH_COUNT', SUM(IFF(BREACHFLAG OR StressedHeadroom < 0, 1, 0))::FLOAT::VARIANT, TRUE),
               ARRAY_AGG(IFF(Metric IS NULL, NULL, OBJECT_CONSTRUCT('covenant', COVENANTTYPE, 'threshold', COVENANTTHRESHOLD,
                   'tested_value', ROUND(StressedActual, 3),
                   'headroom_pct_before', HEADROOM_PCT, 'headroom_pct_after', ROUND(StressedHeadroom, 2))))
          INTO :stressed, :covenant_impact
          FROM shocked
        HAVING COUNT(*) > 0;
    END IF;

    SELECT MODEL({model_ref}, {alias})!PREDICT_PROBA({base_args}):output_feature_1::FLOAT,
           MODEL({model_ref}, {alias})!PREDICT_PROBA({stress_args}):output_feature_1::FLOAT
      INTO :baseline_pd, :stressed_pd
      FROM (SELECT :baseline AS b, :stressed AS s);

    LET rs RESULTSET := (
        WITH pd_model AS MODEL {model_ref} VERSION {alias}
        SELECT r.Scenario, OBJECT_CONSTRUCT({shap_obj}) AS Shap
        FROM (SELECT 'baseline' AS Scenario, :baseline AS v
              UNION ALL
              SELECT 'stressed', :stressed) r,
             TABLE(pd_model!EXPLAIN({explain_args})) e
    );
    FOR rec IN rs DO
        IF (rec.Scenario = 'baseline') THEN
            baseline_shap := rec.Shap;
        ELSE
            stressed_shap := rec.Shap;
        END IF;
    END FOR;

    SELECT ARRAY_SLICE(ARRAY_AGG(OBJECT_CONSTRUCT('feature', s.KEY, 'shap_value', ROUND(s.VALUE::FLOAT, 4)))
               WITHIN GROUP (ORDER BY ABS(s.VALUE::FLOAT) DESC), 0, {top_n})
      INTO :baseline_drivers
      FROM TABLE(FLATTEN(INPUT => :baseline_shap)) s;
    SELECT ARRAY_SLICE(ARRAY_AGG(OBJECT_CONSTRUCT('feature', s.KEY, 'shap_value', ROUND(s.VALUE::FLOAT, 4)))
               WITHIN GROUP (ORDER BY ABS(s.VALUE::FLOAT) DESC), 0, {top_n})
      INTO :stressed_drivers
      FROM TABLE(FLATTEN(INPUT => :stressed_shap)) s;

    SELECT OBJECT_CONSTRUCT(
        'borrower', :matched_name,
        'borrower_id', :matched_id,
        'quarter_date', :quarter_date,
        'model', '{model_name}',
        'model_alias', '{alias}',
        'pd_definition', 'Probability of a covenant breach or headroom below {stress_headroom}% in the next quarter',
        'overrides_applied', :overrides_obj,
        'covenant_propagation', COALESCE(:covenant_impact, ARRAY_CONSTRUCT()),
        'baseline', OBJECT_CONSTRUCT('pd', ROUND(:baseline_pd, 4), 'risk_rating', {baseline_rating},
                                     'features', :baseline, 'top_drivers', :baseline_drivers),
        'stressed', OBJECT_CONSTRUCT('pd', ROUND(:stressed_pd, 4), 'risk_rating', {stressed_rating},
                                     'features', :stressed, 'top_drivers', :stressed_drivers),
        'pd_change', ROUND(:stressed_pd - :baseline_pd, 4))
      INTO :result;

    RETURN result;
END;
$$
    """).collect()
    log_detail(f"  Created procedure: {database_name}.{ai_schema}.PREDICT_BORROWER_PD")


def score_ml_models(session: Session) -> Dict[str, int]:
    create_feature_views(session)
    regime_rows = score_regime(session)
    credit_rows = score_credit_risk(session)
    populate_factor_standins(session)
    return {'regime': regime_rows, 'credit_risk': credit_rows}


def build_ml_models(session: Session) -> Dict[str, str]:
    log_phase("ML Models (train, register, score)")
    ensure_ml_schema(session)
    create_regime_prediction_table(session)
    create_credit_risk_tables(session)

    log_step("Creating feature views")
    create_feature_views(session)

    log_step("Training market regime model")
    regime_version = train_regime_model(session)
    score_regime(session)

    log_step("Training credit risk PD model")
    credit_version = train_credit_risk_model(session)
    score_credit_risk(session)

    log_step("Creating PD what-if procedure")
    create_pd_what_if_tool(session)

    log_step("Populating factor return and optimal portfolio stand-ins")
    populate_factor_standins(session)

    log_success(f"ML models built: regime={regime_version}, credit_risk={credit_version}")
    log_phase_complete("ML models ready")
    return {'regime': regime_version, 'credit_risk': credit_version}
