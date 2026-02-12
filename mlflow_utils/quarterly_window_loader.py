"""
Quarterly Window Data Loader for exp_007 Lagged Network Effects.

Loads quarterly network snapshots with flexible lag specifications 
for addressing network metric endogeneity.

Usage:
    from mlflow_utils.quarterly_window_loader import QuarterlyWindowDataLoader
    
    loader = QuarterlyWindowDataLoader()
    df = loader.load_with_lags(lag_quarters=4)  # 1-year lag
"""

import os
import sys
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

class QuarterlyWindowDataLoader:
    """
    Loads accounting data with quarterly network metrics and flexible lag support.
    
    Enables analysis of network metrics at t-k quarters predicting survival at time t,
    establishing temporal precedence to address endogeneity concerns.
    """
    
    def __init__(self, 
                 quarterly_dir: str = 'rolling_windows/output/quarterly_2004_2020',
                 accounting_path: Optional[str] = None):
        """
        Initialize loader with quarterly network data.
        
        Args:
            quarterly_dir: Directory containing quarterly network snapshots
            accounting_path: Path to accounting data (default from env)
        """
        load_dotenv()
        
        # Ensure quarterly_dir is absolute path from project root
        if not os.path.isabs(quarterly_dir):
            # Find project root (where .env is)
            current_dir = Path(__file__).parent
            while current_dir != current_dir.parent:
                if (current_dir / '.env').exists():
                    quarterly_dir = current_dir / quarterly_dir
                    break
                current_dir = current_dir.parent
        
        self.quarterly_dir = Path(quarterly_dir)
        
        # Get accounting path - check both ACCOUNTING_PATH and ACCOUNTING_DIR
        if accounting_path:
            self.accounting_path = Path(accounting_path)
        else:
            accounting_dir = os.getenv('ACCOUNTING_DIR') or os.getenv('ACCOUNTING_PATH')
            if accounting_dir:
                accounting_dir = Path(accounting_dir)
                # If it's a directory, find the parquet file
                if accounting_dir.is_dir():
                    parquet_files = list(accounting_dir.glob('*.parquet'))
                    if parquet_files:
                        self.accounting_path = parquet_files[0]  # Use first parquet file
                    else:
                        self.accounting_path = None
                else:
                    self.accounting_path = accounting_dir
            else:
                self.accounting_path = None
        
        if not self.quarterly_dir.exists():
            raise FileNotFoundError(
                f"Quarterly directory not found: {quarterly_dir}\n"
                f"Run execute_quarterly_efficient.py first to generate snapshots."
            )
    
    def _load_quarterly_network_data(self) -> pd.DataFrame:
        """
        Load all quarterly network snapshots and combine into single DataFrame.
        
        Returns:
            DataFrame with columns:
                - Id: Bank UUID
                - regn_cbr: Bank registration number
                - window_name: e.g., "Q1_2010"
                - quarter: Period object (e.g., 2010Q1)
                - window_start_year, window_end_year: Integer years
                - rw_page_rank, rw_in_degree, rw_out_degree, rw_degree
                - rw_wcc, rw_community_louvain
        """
        print(f"Loading quarterly network snapshots from: {self.quarterly_dir}")
        
        # Find all parquet files
        parquet_files = sorted(self.quarterly_dir.glob("node_features_Q*.parquet"))
        
        if not parquet_files:
            raise FileNotFoundError(
                f"No quarterly parquet files found in {self.quarterly_dir}"
            )
        
        print(f"  Found {len(parquet_files)} quarterly windows")
        
        # Load and combine all quarters
        dfs = []
        for f in parquet_files:
            df = pd.read_parquet(f)
            dfs.append(df)
        
        df_all = pd.concat(dfs, ignore_index=True)
        
        # Create quarter period for temporal matching
        # Extract quarter number from window_name (e.g., "Q1_2010" -> 2010Q1)
        df_all['quarter'] = pd.PeriodIndex(
            year=df_all['window_start_year'],
            quarter=df_all['quarter'],
            freq='Q'
        )
        
        print(f"  Loaded {len(df_all):,} bank-quarter observations")
        print(f"  Date range: {df_all['quarter'].min()} to {df_all['quarter'].max()}")
        print(f"  Unique banks (Id): {df_all['Id'].nunique():,}")
        print(f"  Unique banks (regn_cbr): {df_all['regn_cbr'].nunique():,}")
        
        return df_all
    
    
    def _load_accounting_data(self, 
                             start_year: int = 2004,
                             end_year: int = 2020) -> pd.DataFrame:
        """
        Load accounting data from parquet file.
        
        Args:
            start_year: Start year for filtering
            end_year: End year for filtering
        
        Returns:
            DataFrame with accounting variables
        """
        if not self.accounting_path or not Path(self.accounting_path).exists():
            raise FileNotFoundError(
                f"Accounting data not found: {self.accounting_path}\n"
                f"Set ACCOUNTING_PATH in .env file or pass accounting_path to constructor."
            )
        
        print(f"  Loading from: {self.accounting_path}")
        
        df = pd.read_parquet(self.accounting_path)
        
        # Convert date
        df['DT'] = pd.to_datetime(df['DT'])
        
        # Normalize column names - handle both REGN and regn
        if 'REGN' in df.columns and 'regn' not in df.columns:
            df['regn'] = df['REGN']
        
        # Filter by year
        df = df[(df['DT'].dt.year >= start_year) & (df['DT'].dt.year <= end_year)].copy()
        
        # Map to exp_006 naming convention for CAMEL ratios
        df['camel_roa'] = df['ROA']
        df['camel_npl_ratio'] = df['npl_ratio']
        
        # Compute tier1 capital ratio (equity / assets as proxy)
        df['camel_tier1_capital_ratio'] = df['total_equity'] / df['total_assets']
        
        print(f"  Loaded {len(df):,} accounting observations")
        print(f"  Date range: {df['DT'].min()} to {df['DT'].max()}")
        print(f"  Unique banks (regn): {df['regn'].nunique()}")
        print(f"  ✅ Mapped CAMEL ratios: camel_roa, camel_npl_ratio, camel_tier1_capital_ratio")
        
        return df
    
    def load_with_lags(self, 
                      lag_quarters: int = 4,
                      start_year: int = 2014,
                      end_year: int = 2020) -> pd.DataFrame:
        """
        Load accounting data with lagged network metrics.
        
        Args:
            lag_quarters: Number of quarters to lag network metrics (default: 4 = 1 year)
            start_year: Start year for analysis period
            end_year: End year for analysis period
        
        Returns:
            DataFrame with:
                - Current accounting variables (camel_*, family_*, etc.)
                - Lagged network metrics (network_*_{lag_quarters}q_lag)
                - Current community (for stratification if needed)
                
        Example:
            >>> loader = QuarterlyWindowDataLoader()
            >>> df = loader.load_with_lags(lag_quarters=4)  # 1-year lag
            >>> # df now has network_out_degree_4q_lag, network_page_rank_4q_lag, etc.
        """
        print(f"\n{'='*70}")
        print(f"LOADING DATA WITH {lag_quarters}-QUARTER LAG")
        print(f"{'='*70}")
        
        # Load Neo4j bank population (death dates, family, foreign)
        print("\n1. Loading bank population from Neo4j...")
        from graphdatascience import GraphDataScience
        gds = GraphDataScience(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )
        
        query_path = Path(__file__).parent.parent / "queries" / "cypher" / "001_get_all_banks.cypher"
        with open(query_path, 'r') as f:
            cypher_query = f.read()
        
        banks_df = gds.run_cypher(cypher_query)
        print(f"   Found {len(banks_df)} banks from Neo4j")
        
        # Normalize regn for merging (convert to int to match accounting)
        banks_df['regn'] = pd.to_numeric(banks_df['regn_cbr'], errors='coerce').astype('Int64')
        
        # Load accounting data 
        print("\n2. Loading accounting data...")
        df_accounting = self._load_accounting_data(start_year=start_year, end_year=end_year)
        
        # Create quarter period from accounting date
        df_accounting['quarter'] = df_accounting['DT'].dt.to_period('Q')
        
        print(f"   Accounting obs: {len(df_accounting):,}")
        print(f"   Date range: {df_accounting['DT'].min()} to {df_accounting['DT'].max()}")
        print(f"   Quarter range: {df_accounting['quarter'].min()} to {df_accounting['quarter'].max()}")
        
        # Merge accounting with Neo4j bank population
        print("\n3. Merging accounting with Neo4j population...")
        df_accounting = df_accounting.merge(banks_df, on='regn', how='inner')
        print(f"   Merged: {len(df_accounting):,} observations")
        
        # Map Neo4j features to exp_006 naming convention
        # Family features
        df_accounting['family_rho_F'] = df_accounting['family_connection_ratio'].fillna(0)
        df_accounting['family_FOP'] = df_accounting['family_ownership_pct'].fillna(0)
        
        # Foreign features  
        df_accounting['foreign_FEC_d'] = (df_accounting['foreign_entity_count'] > 0).astype(int)
        
        print(f"   ✅ Mapped family/foreign features from Neo4j")

        # Load quarterly network snapshots
        print("\n4. Loading quarterly network snapshots...")
        df_network = self._load_quarterly_network_data()
        
        # Create lagged network metrics
        print(f"\n5. Creating {lag_quarters}-quarter lagged network metrics...")
        
        # Shift quarters forward by lag amount (so t-4 network matches t accounting)
        df_network_lagged = df_network.copy()
        df_network_lagged['quarter'] = df_network_lagged['quarter'] + lag_quarters
        
        # Convert regn_cbr to integer to match accounting regn type
        df_network_lagged['regn_cbr'] = pd.to_numeric(df_network_lagged['regn_cbr'], errors='coerce').astype('Int64')
        
        # Rename network columns to indicate they are lagged
        network_cols = [
            'rw_page_rank', 'rw_in_degree', 'rw_out_degree', 'rw_degree',
            'rw_wcc', 'rw_community_louvain'
        ]
        
        rename_map = {col: f"{col}_{lag_quarters}q_lag" for col in network_cols}
        df_network_lagged = df_network_lagged.rename(columns=rename_map)
        
        # Keep only necessary columns for merge
        merge_cols = ['Id', 'regn_cbr', 'quarter'] + list(rename_map.values())
        df_network_lagged = df_network_lagged[merge_cols]
        
        print(f"   Lagged network obs: {len(df_network_lagged):,}")
        print(f"   Lagged quarter range: {df_network_lagged['quarter'].min()} to {df_network_lagged['quarter'].max()}")
        
        # Merge accounting (current) with lagged network
        print("\n6. Merging accounting_t with network_{t-lag}...")
        
        # Merge on regn (accounting) = regn_cbr (network) + quarter
        df_merged = df_accounting.merge(
            df_network_lagged,
            left_on=['regn', 'quarter'],
            right_on=['regn_cbr', 'quarter'],
            how='left',
            suffixes=('', '_netlag')
        )
        
        # Check match rate
        network_matched = df_merged[f'rw_page_rank_{lag_quarters}q_lag'].notna().sum()
        match_rate = 100 * network_matched / len(df_merged)
        
        print(f"   Merged obs: {len(df_merged):,}")
        print(f"   Network matches: {network_matched:,} ({match_rate:.1f}%)")
        
        if match_rate < 50:
            print(f"\n⚠️  WARNING: Low match rate ({match_rate:.1f}%)")
            print(f"   Possible issues:")
            print(f"   - Lag too large (not enough historical data)")
            print(f"   - Id mismatch between accounting and network")
            print(f"   - Quarterly data missing for some periods")
        
        # Create event indicator following exp_004 pattern
        # event=1 ONLY for the LAST observation of each dead bank
        print("\n7. Creating event indicators (exp_004 pattern)...")
        df_merged['event'] = 0
        
        # Find dead banks
        dead_banks = df_merged[df_merged['is_dead'] == True]['regn'].unique()
        
        # Mark ONLY the last observation for each dead bank as event=1
        mask_last = df_merged.groupby('regn')['DT'].transform('max') == df_merged['DT']
        df_merged.loc[mask_last & df_merged['regn'].isin(dead_banks), 'event'] = 1
        
        events_count = df_merged['event'].sum()
        events_pct = 100 * df_merged['event'].mean()
        print(f"   Dead banks: {len(dead_banks)}")
        print(f"   Events (last obs only): {events_count:,} ({events_pct:.1f}%)")
        
        # Add metadata
        df_merged['lag_quarters'] = lag_quarters
        df_merged['lag_years'] = lag_quarters / 4
        
        print(f"\n✅ Data loading complete!")
        print(f"   Total observations: {len(df_merged):,}")
        print(f"   Unique banks: {df_merged['regn'].nunique():,}")
        print(f"   Date range: {df_merged['DT'].min()} to {df_merged['DT'].max()}")
        print(f"   Lag specification: {lag_quarters} quarters ({lag_quarters/4:.1f} years)")
        
        return df_merged
    
    def create_delta_features(self, 
                             df: pd.DataFrame,
                             lag_quarters: int = 4) -> pd.DataFrame:
        """
        Create delta (change) features for Arellano-Bond style specifications.
        
        Adds columns like:
            - network_out_degree_delta_4q = network_out_degree - network_out_degree_4q_lag
        
        Args:
            df: DataFrame from load_with_lags()
            lag_quarters: Lag used (must match what was used in load_with_lags)
        
        Returns:
            DataFrame with added delta columns
        """
        print(f"\nCreating delta features (Δ from t-{lag_quarters} to t)...")
        
        # Network metrics to create deltas for
        network_vars = ['page_rank', 'out_degree', 'in_degree', 'degree']
        
        delta_cols_created = []
        for var in network_vars:
            current_col = f'rw_{var}'
            lagged_col = f'rw_{var}_{lag_quarters}q_lag'
            delta_col = f'rw_{var}_delta_{lag_quarters}q'
            
            if current_col in df.columns and lagged_col in df.columns:
                df[delta_col] = df[current_col] - df[lagged_col]
                delta_cols_created.append(delta_col)
        
        print(f"   Created {len(delta_cols_created)} delta features:")
        for col in delta_cols_created:
            print(f"     - {col}")
        
        return df
    
    def compute_autocorrelation(self,
                               df: pd.DataFrame,
                               variable: str = 'rw_out_degree',
                               lag_quarters: int = 4) -> float:
        """
        Compute autocorrelation of a network variable at specified lag.
        
        Args:
            df: DataFrame from load_with_lags()
            variable: Variable to check (e.g., 'rw_out_degree')
            lag_quarters: Lag to check
        
        Returns:
            Correlation coefficient
        """
        current_col = variable
        lagged_col = f"{variable}_{lag_quarters}q_lag"
        
        if current_col not in df.columns or lagged_col not in df.columns:
            raise ValueError(f"Columns not found: {current_col}, {lagged_col}")
        
        # Compute correlation on non-missing pairs
        valid = df[[current_col, lagged_col]].dropna()
        
        if len(valid) == 0:
            return float('nan')
        
        corr = valid[current_col].corr(valid[lagged_col])
        
        print(f"\nAutocorrelation: {variable} (t vs t-{lag_quarters})")
        print(f"  Correlation: {corr:.3f}")
        print(f"  Valid pairs: {len(valid):,}")
        
        return corr

if __name__ == '__main__':
    # Test the loader
    print("Testing QuarterlyWindowDataLoader...")
    
    # Ensure .env is loaded from project root
    import os
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    load_dotenv(project_root / '.env')
    
    loader = QuarterlyWindowDataLoader()
    
    # Test with 4-quarter lag (1 year)
    df = loader.load_with_lags(lag_quarters=4, start_year=2014, end_year=2020)
    
    print(f"\n{'='*70}")
    print("SAMPLE DATA")
    print(f"{'='*70}")
    
    # Show columns available
    print(f"\nColumns in result:")
    for col in sorted(df.columns):
        if 'lag' in col or 'network' in col or col in ['regn', 'DT', 'quarter', 'camel_roa', 'event']:
            print(f"  - {col}")
    
    print(f"\nSample rows:")
    # Use actual columns that exist
    display_cols = ['regn', 'DT', 'quarter']
    
    # Add a few accounting columns if they exist
    accounting_cols = ['total_assets', 'total_equity', 'npl_amount']
    for col in accounting_cols:
        if col in df.columns:
            display_cols.append(col)
    
    # Add first 3 lagged network columns
    network_cols = [c for c in df.columns if 'lag' in c and 'rw_' in c][:3]
    display_cols.extend(network_cols)
    
    print(df[display_cols].head(10))
    
    # Test delta features
    df = loader.create_delta_features(df, lag_quarters=4)
    
    # Test autocorrelation
    loader.compute_autocorrelation(df, 'rw_out_degree', lag_quarters=4)
    
    print(f"\n✅ Loader test complete!")
