#!/usr/bin/env python3
"""Fix the lag column naming in temporal_fcr_loader.py"""

with open('mlflow_utils/temporal_fcr_loader.py', 'r') as f:
    lines = f.readlines()

# Find and replace lines 218-221
# Line 218: "        # Create lags"
# Line 219: "        for feat in features_to_lag:"
# Line 220: "            lag_col = f"{feat}_lag""
# Line 221: "            df[lag_col] = df.groupby('regn')[feat].shift(lag_periods)"

new_section = """        # Create lags with proper naming for experiment compatibility
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
            
            df[lag_col] = df.groupby('regn')[feat].shift(lag_periods)
"""

# Replace lines 217-221 (0-indexed: 217-220)
new_lines = lines[:217] + [new_section] + lines[221:]

with open('mlflow_utils/temporal_fcr_loader.py', 'w') as f:
    f.writelines(new_lines)

print("✓ Fixed lag column naming")
