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

import numpy as np
import pandas as pd


def predict_pd(model, features_df: pd.DataFrame) -> dict:
    proba = model.predict_proba(features_df)[:, 1]
    pd_score = float(proba[0])

    if pd_score < 0.10:
        rating = "LOW_RISK"
    elif pd_score < 0.20:
        rating = "MODERATE"
    elif pd_score < 0.50:
        rating = "ELEVATED"
    else:
        rating = "HIGH_RISK"

    return {"pd_score": pd_score, "risk_rating": rating}


def explain_with_shap(explainer, features_df: pd.DataFrame, feature_names: list, top_n: int = 10) -> pd.DataFrame:
    shap_values = explainer.shap_values(features_df)
    abs_shap = np.abs(shap_values[0])
    sorted_idx = np.argsort(abs_shap)[::-1][:top_n]

    results = []
    for idx in sorted_idx:
        results.append({
            "feature": feature_names[idx],
            "value": float(features_df.iloc[0, idx]),
            "shap_impact": float(shap_values[0][idx]),
            "direction": "Increases risk" if shap_values[0][idx] > 0 else "Decreases risk"
        })
    return pd.DataFrame(results)


def apply_scenario(features_df: pd.DataFrame, adjustments: dict) -> pd.DataFrame:
    adjusted = features_df.copy()
    for feature, change in adjustments.items():
        if feature in adjusted.columns:
            if isinstance(change, str) and change.endswith("%"):
                pct = float(change.rstrip("%")) / 100
                adjusted[feature] = adjusted[feature] * (1 + pct)
            else:
                adjusted[feature] = float(change)
    return adjusted
