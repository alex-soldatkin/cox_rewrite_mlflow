"""
Quick check: What columns are available in the loaded data?
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mlflow_utils.quarterly_window_loader import QuarterlyWindowDataLoader

loader = QuarterlyWindowDataLoader()
df = loader.load_with_lags(lag_quarters=4, start_year=2010, end_year=2020)

print("\nAvailable columns:")
print(df.columns.tolist())

print("\nDeath-related columns:")
death_cols = [col for col in df.columns if 'death' in col.lower() or 'dead' in col.lower() or 'event' in col.lower()]
print(death_cols)

print("\nis_dead distribution:")
print(df['is_dead'].value_counts())

print("\nevent distribution:")
print(df['event'].value_counts())

print("\nSample of dead banks:")
dead_sample = df[df['is_dead'] == True].groupby('regn').first()[['DT', 'is_dead', 'event']].head(10)
print(dead_sample)
