"""Quick fix for run_cox.py main function"""

main_function_code = '''def main():
    print("="*70)
    print("EXP_007_TEMPORAL_FCR: LAGGED NETWORK EFFECTS WITH TEMPORAL FCR")
    print("="*70)
    
    # Set up MLflow experiment (use local file tracking)
    mlflow.set_tracking_uri("file:///Users/alexandersoldatkin/projects/cos_rewrite_mlflow/mlruns")
    setup_experiment("exp_007_temporal_fcr")
    
    # Load data with 2-period biannual lag (= 4-year lag, comparable to original 4-quarter lag)
    print("\\n1. Loading temporal FCR data with 2-period biannual lag...")
    print("   Note: lag_periods=2 means 4-year lag (2 × 2-year periods)")
    print("   CAMEL merge: Skipped for initial test (can add later)")
    
    loader = TemporalFCRLoader(gds_client=None)  # No GDS client = skip CAMEL merge
    df = loader.load_with_lags(lag_periods=2, start_year=2014, end_year=2020, merge_camel=False)
    
    print(f"\\n✅ Loaded {len(df):,} observations")
    print(f"   Unique banks: {df['regn'].nunique()}")
    print(f"   Date range: {df['DT'].min()} to {df['DT'].max()}")
    print(f"   FCR column: {'family_connection_ratio_temporal' if 'family_connection_ratio_temporal' in df.columns else 'MISSING'}")
    
    # Diagnostic: Check FCR time-variance
    if 'family_connection_ratio_temporal' in df.columns:
        fcr_col = 'family_connection_ratio_temporal'
        fcr_varying_pct = (df.groupby('regn')[fcr_col].nunique() > 1).mean()
        print(f"   FCR time-varying banks: {fcr_varying_pct:.1%} (vs 0.2% in static)")
        print(f"   FCR mean: {df[fcr_col].mean():.3f}, std: {df[fcr_col].std():.3f}")
    
    # Model 2: Simple Lagged Network (Primary specification)
    print("\\n2. Running Model 2: Simple Lagged Network with Temporal FCR...")
    df_cox_m2, features_m2 = prepare_cox_data(df, use_lagged_network=True)
    
    model_m2 = run_model(
        "M2: Temporal FCR + Lagged Network (4-year lag)",
        df_cox_m2,
        features_m2,
        lag_periods=2,
        lag_years=4,
        specification="temporal_fcr_lagged_network",
        fcr_source="temporal_fcr_biannual"
    )
    
    print(f"\\n{'='*70}")
    print("EXP_007_TEMPORAL_FCR COMPLETE")
    print(f"{'='*70}")
    print(f"\\nMLflow URI: {mlflow.get_tracking_uri()}")
    print(f"Check experiment: exp_007_temporal_fcr")
'''

print(main_function_code)
