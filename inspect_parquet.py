import pandas as pd
import os

path = '/Users/alexandersoldatkin/projects/factions-networks-thesis/drafts/accounting_cbr_imputed/final_banking_indicators_imputed.parquet'
df = pd.read_parquet(path)

print("Columns and Types:")
print(df.dtypes)

print("\nSample Data (first 2 rows):")
print(df.head(2).T)

print("\nDescription:")
print(df.describe().T)
