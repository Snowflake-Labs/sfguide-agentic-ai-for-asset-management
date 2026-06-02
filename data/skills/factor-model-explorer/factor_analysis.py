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

import pandas as pd
import numpy as np


def _spearman_r(x, y):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean()
    ry -= ry.mean()
    denom = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    if denom < 1e-15:
        return 0.0
    return float((rx * ry).sum() / denom)


def compute_cross_sectional_ic(factor_returns_df: pd.DataFrame, factor_cols: list, return_col: str = "FORWARD_RETURN") -> pd.DataFrame:
    results = []
    for col in factor_cols:
        monthly_ics = []
        for month, grp in factor_returns_df.groupby("MONTH_DATE"):
            mask = grp[col].notna() & grp[return_col].notna()
            if mask.sum() >= 10:
                ic = _spearman_r(grp.loc[mask, col].values, grp.loc[mask, return_col].values)
                monthly_ics.append({"MONTH_DATE": month, "IC": ic})
        if monthly_ics:
            ic_df = pd.DataFrame(monthly_ics)
            results.append({
                "FACTOR": col,
                "MEAN_IC": ic_df["IC"].mean(),
                "IC_TSTAT": ic_df["IC"].mean() / (ic_df["IC"].std() / np.sqrt(len(ic_df))),
                "N_MONTHS": len(ic_df),
                "HIT_RATE": (ic_df["IC"] > 0).mean()
            })
    return pd.DataFrame(results).sort_values("MEAN_IC", key=abs, ascending=False)


def compute_factor_correlations(factor_df: pd.DataFrame, factor_cols: list) -> pd.DataFrame:
    return factor_df[factor_cols].corr(method="spearman")


def compute_rolling_sharpe(factor_returns_df: pd.DataFrame, factor_cols: list, window: int = 12) -> pd.DataFrame:
    result = pd.DataFrame({"MONTH_DATE": factor_returns_df["MONTH_DATE"]})
    for col in factor_cols:
        rolling_mean = factor_returns_df[col].rolling(window, min_periods=3).mean()
        rolling_std = factor_returns_df[col].rolling(window, min_periods=3).std()
        result[col] = (rolling_mean / rolling_std.clip(lower=1e-10)) * np.sqrt(12)
    return result


def test_factor_combination(factor_returns_df: pd.DataFrame, weights: dict) -> dict:
    cols = list(weights.keys())
    w = np.array([weights[c] for c in cols])
    combined = factor_returns_df[cols].fillna(0).values @ w
    ann_return = combined.mean() * 12
    ann_vol = combined.std() * np.sqrt(12)
    sharpe = ann_return / max(ann_vol, 1e-10)
    return {"annualised_return": ann_return, "annualised_vol": ann_vol, "sharpe": sharpe}
