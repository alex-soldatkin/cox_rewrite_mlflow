
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

accounting_path = os.getenv("ACCOUNTING_DIR")
# Assuming the file name based on previous logs:
# /Users/alexandersoldatkin/projects/factions-networks-thesis/drafts/accounting_cbr_imputed/final_final_banking_indicators.parquet
# But let's check what loader uses. 
# loader.py uses os.getenv("ACCOUNTING_DIR") variable? 
# Or hardcoded path?
# Let's just try to read the file referenced in previous logs.
file_path = "/Users/alexandersoldatkin/projects/factions-networks-thesis/drafts/accounting_cbr_imputed/final_final_banking_indicators.parquet"

try:
    df = pd.read_parquet(file_path, columns=['DT'])
    print(f"Min Date: {df['DT'].min()}")
    print(f"Max Date: {df['DT'].max()}")
except Exception as e:
    print(f"Error reading path {file_path}: {e}")
    # Fallback to checking env if that fails
    print(f"ACCOUNTING_DIR: {accounting_path}")
