"""
exp_016: Competing Risks — Cause-Specific Cox Models

Runs separate Cox models for each closure type (forced revocation,
voluntary liquidation, reorganisation), treating other types as censored.

Requires: closure_types.csv from extract_closure_types.py
"""

import yaml
import mlflow
import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.tracking import setup_experiment
from mlflow_utils.quarterly_window_loader import QuarterlyWindowDataLoader
from lifelines import CoxTimeVaryingFitter
from lifelines.utils import concordance_index
from visualisations.cox_stargazer_new import (
    create_single_column_stargazer,
    create_single_column_stargazer_hr,
)
from visualisations.cox_interpretation import generate_interpretation_report
from sklearn.preprocessing import StandardScaler

EXP_DIR = os.path.dirname(os.path.abspath(__file__))

OWNERSHIP_FEATURES = [
    'family_connection_ratio', 'family_ownership_pct',
    'state_ownership_pct', 'foreign_ownership_total_pct',
]
NETWORK_FEATURES = ['rw_page_rank_4q_lag', 'rw_out_degree_4q_lag']
CAMEL_FEATURES = ['camel_roa', 'camel_npl_ratio', 'camel_tier1_capital_ratio']
BASE_FEATURES = OWNERSHIP_FEATURES + NETWORK_FEATURES + CAMEL_FEATURES

MODELS = {
    'M1_all_closures': {
        'name': 'M1: All closures (baseline)',
        'closure_filter': None,
        'extra_features': [],
    },
    'M2_revocation': {
        'name': 'M2: Forced revocation only',
        'closure_filter': 'revocation',
        'extra_features': [],
    },
    'M3_voluntary': {
        'name': 'M3: Voluntary liquidation only',
        'closure_filter': 'voluntary',
        'extra_features': [],
    },
    'M4_reorganisation': {
        'name': 'M4: Reorganisation only',
        'closure_filter': 'reorganisation',
        'extra_features': [],
    },
    'M5_revocation_crisis': {
        'name': 'M5: Revocation + crisis interactions',
        'closure_filter': 'revocation',
        'extra_features': ['crisis_2004', 'crisis_2008', 'crisis_2014',
                           'family_connection_ratio_x_crisis_2008',
                           'family_connection_ratio_x_crisis_2014'],
    },
}

CRISIS_PERIODS = {
    'crisis_2004': ('2004-07-01', '2004-08-31'),
    'crisis_2008': ('2008-09-01', '2009-12-31'),
    'crisis_2014': ('2014-03-01', '2015-12-31'),
}


def collapse_small_communities(df, community_col='rw_community_louvain_4q_lag', min_size=5):
    def extract_coarsest(val):
        if isinstance(val, (list, np.ndarray)):
            return float(val[0]) if len(val) > 0 else -1.0
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return -1.0
        return float(val)

    df['community_scalar'] = df[community_col].apply(extract_coarsest)
    community_counts = df.groupby('community_scalar')['regn'].nunique()
    small = community_counts[community_counts < min_size].index
    df['community_collapsed'] = df['community_scalar'].copy()
    df.loc[df['community_scalar'].isin(small), 'community_collapsed'] = -1
    return df


def aggregate_temporal_communities(df, community_col='community_collapsed'):
    bank_stable = (
        df[df[community_col].notna()]
        .groupby('regn')[community_col]
        .agg(lambda x: x.value_counts().index[0] if len(x) > 0 else -1)
    )
    df[community_col] = df['regn'].map(bank_stable)
    return df


def load_closure_types():
    path = os.path.join(EXP_DIR, 'closure_types.csv')
    df = pd.read_csv(path)
    return df[['regn', 'closure_type']].dropna(subset=['regn'])


def apply_closure_filter(df, closure_types, target_type):
    """For cause-specific Cox: keep target type as events, censor other types."""
    merged = df.merge(closure_types, on='regn', how='left')
    merged['closure_type'] = merged['closure_type'].fillna('alive')

    if target_type is not None:
        # Banks that died from a DIFFERENT cause → censor (event=0)
        other_dead = (merged['closure_type'] != target_type) & (merged['closure_type'] != 'alive')
        merged.loc[other_dead, 'event'] = 0
        n_target = merged[merged['closure_type'] == target_type]['regn'].nunique()
        n_censored_other = merged[other_dead]['regn'].nunique()
        print(f"  Target type '{target_type}': {n_target} banks as events")
        print(f"  Other dead banks censored: {n_censored_other}")

    return merged


def create_crisis_features(df):
    df['DT'] = pd.to_datetime(df['DT'])
    crisis_cols = []
    for name, (start, end) in CRISIS_PERIODS.items():
        df[name] = ((df['DT'] >= pd.Timestamp(start)) & (df['DT'] <= pd.Timestamp(end))).astype(int)
        crisis_cols.append(name)
    # Interaction terms
    for crisis in crisis_cols:
        col = f'family_connection_ratio_x_{crisis}'
        df[col] = df['family_connection_ratio'] * df[crisis]
    return df


def prepare_cox_data(df, features):
    df_cox = df.copy()
    df_cox['date'] = pd.to_datetime(df_cox['DT'])
    df_cox = df_cox.sort_values(by=['regn', 'date'])
    df_cox['start'] = df_cox['date']
    df_cox['stop'] = df_cox.groupby('regn')['date'].shift(-1)
    mask_last = df_cox['stop'].isna()
    df_cox.loc[mask_last, 'stop'] = df_cox.loc[mask_last, 'start'] + pd.Timedelta(days=30)
    min_dates = df_cox.groupby('regn')['date'].transform('min')
    df_cox['start_t'] = (df_cox['start'] - min_dates).dt.days
    df_cox['stop_t'] = (df_cox['stop'] - min_dates).dt.days
    df_cox = df_cox[df_cox['stop_t'] > df_cox['start_t']]

    feat_cols = [c for c in features if c in df_cox.columns]
    df_cox[feat_cols] = df_cox[feat_cols].fillna(0)
    final = [c for c in feat_cols if df_cox[c].nunique() > 1]

    if final:
        scaler = StandardScaler()
        df_cox[final] = scaler.fit_transform(df_cox[final])
        for col in final:
            lo, hi = df_cox[col].min(), df_cox[col].max()
            if hi > lo:
                df_cox[col] = 100 * (df_cox[col] - lo) / (hi - lo)

    keep = ['regn', 'start_t', 'stop_t', 'event', 'community_collapsed'] + final
    keep = [c for c in keep if c in df_cox.columns]
    return df_cox[keep].copy(), final


def run_model(model_key, model_cfg, df_cox, features):
    name = model_cfg['name']
    print(f"\n{'=' * 70}")
    print(f"Running: {name}")
    print(f"{'=' * 70}")

    with mlflow.start_run(run_name=name):
        mlflow.log_param("model_type", "CoxTimeVarying")
        mlflow.log_param("model_key", model_key)
        mlflow.log_param("n_observations", len(df_cox))
        mlflow.log_param("n_banks", df_cox['regn'].nunique())
        mlflow.log_param("n_events", int(df_cox['event'].sum()))
        mlflow.log_param("closure_filter", model_cfg['closure_filter'] or 'all')
        mlflow.log_param("features", ", ".join(features))

        formula = " + ".join(features)
        print(f"Formula: event ~ {formula}")
        print(f"Observations: {len(df_cox):,}, Events: {int(df_cox['event'].sum())}")

        try:
            ctv = CoxTimeVaryingFitter(penalizer=0.01, l1_ratio=0.0)
            if 'community_collapsed' in df_cox.columns:
                ctv.fit(df_cox, id_col='regn', event_col='event',
                        start_col='start_t', stop_col='stop_t',
                        strata=['community_collapsed'], show_progress=True)
            else:
                ctv.fit(df_cox, id_col='regn', event_col='event',
                        start_col='start_t', stop_col='stop_t', show_progress=True)

            print("Model converged.")
            mlflow.log_metric("log_likelihood", ctv.log_likelihood_)
            mlflow.log_metric("aic_partial", ctv.AIC_partial_)

            try:
                ph = ctv.predict_partial_hazard(df_cox)
                c_idx = concordance_index(df_cox['stop_t'], -ph, df_cox['event'])
                mlflow.log_metric("c_index", c_idx)
            except Exception:
                c_idx = None

            n_subj = df_cox['regn'].nunique()

            stg = create_single_column_stargazer(ctv, c_index=c_idx, n_subjects=n_subj)
            stg_path = os.path.join(EXP_DIR, f'stargazer_{model_key}.csv')
            stg.to_csv(stg_path)
            mlflow.log_artifact(stg_path)

            hr = create_single_column_stargazer_hr(ctv, c_index=c_idx, n_subjects=n_subj)
            hr_path = os.path.join(EXP_DIR, f'stargazer_hr_{model_key}.csv')
            hr.to_csv(hr_path)
            mlflow.log_artifact(hr_path)

            interp = generate_interpretation_report(ctv, model_name=name)
            interp_path = os.path.join(EXP_DIR, f'interpretation_{model_key}.md')
            with open(interp_path, 'w') as f:
                f.write(interp)
            mlflow.log_artifact(interp_path)

            print(ctv.summary)
            return ctv, stg

        except Exception as e:
            print(f"Model failed: {e}")
            import traceback
            traceback.print_exc()
            mlflow.log_param("status", "failed")
            return None, None


def create_aggregated_stargazer(all_stg):
    """Combine per-model stargazer columns into a wide table."""
    if not all_stg:
        return
    dfs = []
    for key, stg in all_stg.items():
        col = stg.rename(columns={'Stargazer_Output': key})
        dfs.append(col)
    agg = pd.concat(dfs, axis=1)
    agg_path = os.path.join(EXP_DIR, 'stargazer_aggregated.csv')
    agg.to_csv(agg_path)
    print(f"\nSaved aggregated stargazer to {agg_path}")


def main():
    print("=" * 70)
    print("EXP_016: COMPETING RISKS — CAUSE-SPECIFIC COX MODELS")
    print("=" * 70)

    setup_experiment("exp_016_competing_risks")

    # Load data
    print("\n1. Loading data...")
    loader = QuarterlyWindowDataLoader(
        quarterly_dir='rolling_windows/output/quarterly_2004_2020'
    )
    df = loader.load_with_lags(lag_quarters=4, start_year=2004, end_year=2020)
    print(f"Loaded {len(df):,} observations, {df['regn'].nunique()} banks")

    # Communities
    df = collapse_small_communities(df)
    df = aggregate_temporal_communities(df)

    # Crisis features
    df = create_crisis_features(df)

    # Closure types
    print("\n2. Loading closure types...")
    closure_types = load_closure_types()
    print(f"Closure types for {len(closure_types)} banks")

    # Run models
    all_stg = {}
    for model_key, model_cfg in MODELS.items():
        df_model = apply_closure_filter(df.copy(), closure_types, model_cfg['closure_filter'])
        features = BASE_FEATURES + model_cfg['extra_features']
        df_cox, final_feats = prepare_cox_data(df_model, features)

        if df_cox['event'].sum() < 10:
            print(f"Skipping {model_cfg['name']}: only {int(df_cox['event'].sum())} events")
            continue

        ctv, stg = run_model(model_key, model_cfg, df_cox, final_feats)
        if stg is not None:
            all_stg[model_key] = stg

    create_aggregated_stargazer(all_stg)

    print(f"\n{'=' * 70}")
    print("EXP_016 COMPLETE")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
