"""
ML Common Utilities for SAM Demo

Shared helpers for Feature Store, Model Registry, Experiment Tracking,
Model Monitor, and batch inference used across market regime, factor
workflow, and credit risk ML scenarios.
"""

from snowflake.snowpark import Session, DataFrame
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import config
from utils.logging import log_detail, log_info, log_warning, log_error


def get_ml_schema_ref() -> str:
    return f"{config.DATABASE['name']}.{config.DATABASE['schemas']['ml']}"


def get_ml_date_range() -> tuple:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=config.YEARS_OF_HISTORY * 365)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


def ensure_ml_schema(session: Session):
    ml_ref = get_ml_schema_ref()
    session.sql(f"CREATE SCHEMA IF NOT EXISTS {ml_ref}").collect()
    log_detail(f"  ML schema ensured: {ml_ref}")


def get_feature_store(session: Session):
    from snowflake.ml.feature_store import FeatureStore
    return FeatureStore(
        session=session,
        database=config.DATABASE['name'],
        name=config.DATABASE['schemas']['ml'],
        default_warehouse=config.ML_CONFIG['feature_store_warehouse']
    )


def register_entity(session: Session, name: str, join_keys: List[str]):
    from snowflake.ml.feature_store import Entity
    fs = get_feature_store(session)
    entity = Entity(name=name, join_keys=join_keys)
    fs.register_entity(entity)
    log_detail(f"  Entity registered: {name} (keys: {join_keys})")
    return entity


def register_feature_view(
    session: Session,
    name: str,
    entities: list,
    feature_df: DataFrame,
    version: str = "v1",
    timestamp_col: Optional[str] = None,
    refresh_freq: Optional[str] = None,
    desc: str = ""
):
    from snowflake.ml.feature_store import FeatureView
    fs = get_feature_store(session)

    fv = FeatureView(
        name=name,
        entities=entities,
        feature_df=feature_df,
        timestamp_col=timestamp_col,
        refresh_freq=refresh_freq or config.ML_CONFIG['refresh_freq'],
        warehouse=config.ML_CONFIG['feature_store_warehouse'],
        desc=desc
    )
    registered_fv = fs.register_feature_view(fv, version=version)
    log_detail(f"  FeatureView registered: {name}/{version} (refresh: {refresh_freq or config.ML_CONFIG['refresh_freq']})")
    return registered_fv


def log_model(
    session: Session,
    model: Any,
    model_name: str,
    version_name: str,
    sample_input_data: Optional[DataFrame] = None,
    metrics: Optional[Dict[str, float]] = None,
    conda_dependencies: Optional[List[str]] = None,
    task: Optional[str] = None,
    target_platforms: Optional[List[str]] = None,
    comment: str = ""
):
    from snowflake.ml.registry import Registry

    registry = Registry(
        session=session,
        database_name=config.ML_CONFIG['model_registry_database'],
        schema_name=config.ML_CONFIG['model_registry_schema']
    )

    log_kwargs = {
        'model': model,
        'model_name': model_name,
        'version_name': version_name,
        'comment': comment,
        'target_platforms': target_platforms or config.ML_CONFIG['default_target_platforms'],
    }

    if sample_input_data is not None:
        log_kwargs['sample_input_data'] = sample_input_data
    if metrics is not None:
        log_kwargs['metrics'] = metrics
    if conda_dependencies is not None:
        log_kwargs['conda_dependencies'] = conda_dependencies
    if task is not None:
        log_kwargs['task'] = task

    model_version = registry.log_model(**log_kwargs)
    log_info(f"  Model logged: {model_name}/{version_name} (platforms: {log_kwargs['target_platforms']})")
    if metrics:
        log_detail(f"    Metrics: {metrics}")
    return model_version


def get_model_version(session: Session, model_name: str, version_name: str):
    from snowflake.ml.registry import Registry
    registry = Registry(
        session=session,
        database_name=config.ML_CONFIG['model_registry_database'],
        schema_name=config.ML_CONFIG['model_registry_schema']
    )
    model = registry.get_model(model_name)
    return model.version(version_name)


def get_experiment_tracker(session: Session, experiment_name: str):
    from snowflake.ml.experiment import ExperimentTracking
    return ExperimentTracking(
        session=session,
        experiment_name=experiment_name,
        database_name=config.ML_CONFIG['model_registry_database'],
        schema_name=config.ML_CONFIG['model_registry_schema']
    )


def create_xgboost_callback(experiment_tracker):
    from snowflake.ml.experiment import SnowflakeXgboostCallback
    return SnowflakeXgboostCallback(experiment_tracker)


def create_model_monitor(
    session: Session,
    monitor_name: str,
    model_name: str,
    version_name: str,
    source_table: str,
    timestamp_column: str,
    prediction_columns: List[str],
    label_columns: Optional[List[str]] = None,
    id_columns: Optional[List[str]] = None,
    baseline_table: Optional[str] = None,
    refresh_interval: Optional[str] = None,
    aggregation_window: Optional[str] = None,
    warehouse: Optional[str] = None,
):
    ml_ref = get_ml_schema_ref()
    full_monitor = f"{ml_ref}.{monitor_name}"
    model_ref = f"{ml_ref}.{model_name}"
    wh = warehouse or config.ML_CONFIG['feature_store_warehouse']
    interval = refresh_interval or config.ML_CONFIG['monitor_refresh_interval']
    window = aggregation_window or config.ML_CONFIG['monitor_aggregation_window']

    sql_parts = [
        f"CREATE OR REPLACE MODEL MONITOR {full_monitor}",
        f"WITH",
        f"  MODEL = {model_ref} VERSION = '{version_name}'",
        f"  SOURCE = {source_table}",
        f"  WAREHOUSE = {wh}",
        f"  REFRESH_INTERVAL = '{interval}'",
        f"  AGGREGATION_WINDOW = '{window}'",
        f"  TIMESTAMP_COLUMN = {timestamp_column}",
        f"  PREDICTION_SCORE_COLUMNS = ({', '.join(prediction_columns)})",
    ]

    if label_columns:
        sql_parts.append(f"  LABEL_COLUMNS = ({', '.join(label_columns)})")
    if id_columns:
        sql_parts.append(f"  ID_COLUMNS = ({', '.join(id_columns)})")
    if baseline_table:
        sql_parts.append(f"  BASELINE = {baseline_table}")

    sql = "\n".join(sql_parts)
    session.sql(sql).collect()
    log_info(f"  Model Monitor created: {full_monitor} (refresh: {interval}, window: {window})")
    return full_monitor


def get_model_inference_sql(
    model_name: str,
    version_name: str,
    columns: List[str],
    source_table: str,
    alias: str = "prediction",
) -> str:
    ml_ref = get_ml_schema_ref()
    cols = ", ".join(columns)
    return (
        f"SELECT *, MODEL({ml_ref}.{model_name}, '{version_name}')!predict({cols}) AS {alias} "
        f"FROM {source_table}"
    )


def validate_ml_date_filter(query_df: DataFrame, date_col: str = "DATE") -> DataFrame:
    start_date, end_date = get_ml_date_range()
    return query_df.filter(
        f"{date_col} >= '{start_date}' AND {date_col} <= '{end_date}'"
    )


def get_ml_scenario_dependencies() -> Dict[str, List[str]]:
    return {
        'market_regime_ml': [],
        'factor_workflow_ml': ['market_regime_ml'],
        'credit_risk_ml': ['market_regime_ml'],
    }


def resolve_ml_build_order(scenarios: List[str]) -> List[str]:
    deps = get_ml_scenario_dependencies()
    ordered = []
    resolved = set()

    def _resolve(scenario):
        if scenario in resolved:
            return
        for dep in deps.get(scenario, []):
            if dep in scenarios or dep in deps:
                _resolve(dep)
        resolved.add(scenario)
        if scenario in scenarios:
            ordered.append(scenario)

    for s in scenarios:
        if s in deps:
            _resolve(s)
    return ordered
