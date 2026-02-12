#!/usr/bin/env python3
"""Fix the lag column naming properly"""

with open('mlflow_utils/temporal_fcr_loader.py', 'r') as f:
    content = f.read()

# Replace the specific section
old_code = '''        # Create lags
        for feat in features_to_lag:
            lag_col = f"{feat}_lag"
            df[lag_col] = df.groupby('regn')[feat].shift(lag_periods)'''

new_code = '''        # Create lags with proper naming for experiment compatibility
        for feat in features_to_lag:
            # Map to rw_*_4q_lag naming for network metrics
            if feat == 'page_rank':
                lag_col = 'rw_page_rank_4q_lag'
            elif feat == 'out_degree':
                lag_col = 'rw_out_degree_4q_lag'
            elif feat == 'in_degree':
                lag_col = 'rw_in_degree_4q_lag'
            else:
                lag_col = f"{feat}_lag"
            
            df[lag_col] = df.groupby('regn')[feat].shift(lag_periods)'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('mlflow_utils/temporal_fcr_loader.py', 'w') as f:
        f.write(content)
    print("✓ Fixed lag column naming")
else:
    print("✗ Could not find expected code section")
    print("Looking for:", repr(old_code[:50]))
