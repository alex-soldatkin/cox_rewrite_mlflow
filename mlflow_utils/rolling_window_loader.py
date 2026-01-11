"""
Rolling Window Data Loader

Loads time-windowed network metrics from rolling window parquet files
and merges them with accounting data for time-varying survival analysis.
"""

from typing import List, Optional
from datetime import date, datetime
import pandas as pd
import os
import numpy as np
from graphdatascience import GraphDataScience
from dotenv import load_dotenv


class RollingWindowDataLoader:
    """
    Loads analysis-ready data using rolling window network features
    merged with Neo4j population and accounting sources.
    """
    
    def __init__(self):
        load_dotenv()
        
        # Initialize GDS connection for bank population
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = os.environ.get("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "")
        
        try:
            self.gds = GraphDataScience(uri, auth=(user, password))
        except Exception as e:
            print(f"Failed to connect to Neo4j GDS: {e}")
            raise e
        
        # Get rolling window directory
        self.rolling_window_dir = os.environ.get("ROLLING_WINDOW_DIR")
        if not self.rolling_window_dir:
            raise ValueError("ROLLING_WINDOW_DIR not set in .env")
            
        self.nodes_dir = os.path.join(self.rolling_window_dir, "output", "nodes")
        if not os.path.exists(self.nodes_dir):
            raise ValueError(f"Rolling window nodes directory not found: {self.nodes_dir}")
    
    def load_all_rolling_windows(self) -> pd.DataFrame:
        """
        Load all rolling window node feature parquet files and concatenate them.
        
        Returns:
            DataFrame with all rolling window features across all time periods.
        """
        print(f"Loading rolling window data from {self.nodes_dir}...")
        
        parquet_files = sorted([
            f for f in os.listdir(self.nodes_dir) 
            if f.endswith('.parquet') and f.startswith('node_features_rw_')
        ])
        
        if not parquet_files:
            raise ValueError(f"No rolling window parquet files found in {self.nodes_dir}")
        
        print(f"Found {len(parquet_files)} rolling window files")
        
        dfs = []
        for file in parquet_files:
            file_path = os.path.join(self.nodes_dir, file)
            df = pd.read_parquet(file_path)
            dfs.append(df)
            print(f"  Loaded {file}: {len(df)} rows")
        
        combined_df = pd.concat(dfs, ignore_index=True)
        print(f"Total rolling window observations: {len(combined_df)}")
        
        return combined_df
    
    def match_observation_to_window(
        self, 
        bank_id: str, 
        obs_date: datetime, 
        window_df: pd.DataFrame
    ) -> Optional[pd.Series]:
        """
        Find the rolling window that overlaps with the observation date for a given bank.
        
        Args:
            bank_id: Bank Id property (from Neo4j .Id, matches rolling window Id field)
            obs_date: Observation date (from accounting record)
            window_df: DataFrame with all rolling window features
            
        Returns:
            Series with rolling window features if match found, None otherwise.
        """
        # Filter by bank Id
        entity_windows = window_df[window_df['Id'] == bank_id]
        
        if entity_windows.empty:
            return None
        
        # Get observation year
        obs_year = obs_date.year
        
        # Find windows that overlap with observation year
        # Window overlaps if: window_start_year <= obs_year <= window_end_year_inclusive
        matching_windows = entity_windows[
            (entity_windows['window_start_year'] <= obs_year) &
            (entity_windows['window_end_year_inclusive'] >= obs_year)
        ]
        
        if matching_windows.empty:
            return None
        
        # If multiple matches (shouldn't happen with non-overlapping windows), take first
        if len(matching_windows) > 1:
            # Prefer the window where obs_year is closer to window_end
            matching_windows = matching_windows.copy()
            matching_windows['distance'] = abs(matching_windows['window_end_year_inclusive'] - obs_year)
            matching_windows = matching_windows.sort_values('distance')
        
        return matching_windows.iloc[0]
    
    def load_training_data_with_rolling_windows(
        self, 
        start_date: str = "2004-01-01", 
        end_date: str = "2025-12-31"
    ) -> pd.DataFrame:
        """
        Loads training data merging Neo4j population, Accounting features,
        and Rolling Window network metrics.
        
        Args:
            start_date: Start date for observation period (YYYY-MM-DD)
            end_date: End date for observation period (YYYY-MM-DD)
            
        Returns:
            DataFrame with merged data ready for analysis.
        """
        # 1. Fetch Bank Population from Neo4j
        query_path = os.path.join(
            os.path.dirname(__file__), 
            "../queries/cypher/001_get_all_banks.cypher"
        )
        with open(query_path, "r") as f:
            cypher_query = f.read()
        
        print("Fetching bank population from Neo4j...")
        banks_df = self.gds.run_cypher(cypher_query)
        print(f"Found {len(banks_df)} banks from Neo4j.")
        
        # 2. Load Accounting Data
        acc_dir = os.environ.get("ACCOUNTING_DIR")
        if not acc_dir:
            raise ValueError("ACCOUNTING_DIR not set in .env")
        
        acc_path = os.path.join(acc_dir, "final_final_banking_indicators.parquet")
        print(f"Loading accounting data from {acc_path}...")
        acc_df = pd.read_parquet(acc_path)
        
        # Filter by date range
        acc_df['DT'] = pd.to_datetime(acc_df['DT'])
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        acc_df = acc_df[(acc_df['DT'] >= start_dt) & (acc_df['DT'] <= end_dt)]
        
        print(f"Accounting data filtered to {len(acc_df)} observations in date range")
        
        # 3. Load Rolling Window Features
        rolling_df = self.load_all_rolling_windows()
        
        # 4. Merge Banking Population with Accounting
        banks_df['regn'] = banks_df['regn_cbr'].astype(str)
        acc_df['regn'] = acc_df['REGN'].astype(str)
        
        merged_df = pd.merge(acc_df, banks_df, on='regn', how='inner')
        print(f"Merged Accounting + Neo4j: {merged_df.shape}")
        
        if merged_df.empty:
            print("Warning: Merged dataframe is empty! Check REGN overlap.")
            return pd.DataFrame()
        
        # 5. Match Rolling Window Features Efficiently using Pandas Merge
        print("Matching rolling window features to observations...")
        
        # Add year column to merged_df for temporal joining
        merged_df['obs_year'] = merged_df['DT'].dt.year
        
        # Filter rolling window data to only Bank nodes
        # nodeLabels is a numpy array in parquet
        rolling_banks = rolling_df[
            rolling_df['nodeLabels'].apply(lambda x: 'Bank' in x if hasattr(x, '__iter__') else False)
        ].copy()
        
        print(f"Filtered to {len(rolling_banks)} bank nodes in rolling windows")
        
        # Merge on bank_id (from Neo4j) = Id (from rolling windows)
        # Then filter for temporal overlap: window_start_year <= obs_year <= window_end_year
        merged_with_rw = pd.merge(
            merged_df,
            rolling_banks,
            left_on='bank_id',
            right_on='Id',
            how='left',
            suffixes=('', '_rw')
        )
        
        print(f"After ID merge: {len(merged_with_rw)} rows")
        
        # Filter for temporal overlap
        matched_mask = (
            (merged_with_rw['window_start_year'] <= merged_with_rw['obs_year']) &
            (merged_with_rw['window_end_year_inclusive'] >= merged_with_rw['obs_year'])
        )
        
        # Keep only temporally matched rows, or original rows if no match
        # First, separate matched and unmatched
        matched_df = merged_with_rw[matched_mask].copy()
        unmatched_regns_dates = set(
            zip(merged_df['regn'], merged_df['DT'])
        ) - set(
            zip(matched_df['regn'], matched_df['DT'])
        )
        unmatched_df = merged_df[
            merged_df.apply(lambda r: (r['regn'], r['DT']) in unmatched_regns_dates, axis=1)
        ].copy()
        
        # Add null rw_ columns to unmatched
        rw_cols = [
            'in_degree', 'out_degree', 'degree', 'page_rank',
            'community_louvain', 'wcc', 'window_start_year', 'window_end_year_inclusive'
        ]
        for col in rw_cols:
            if col not in unmatched_df.columns:
                unmatched_df[col] = None
        
        # Rename rolling window columns in matched_df
        matched_df = matched_df.rename(columns={
            'in_degree': 'rw_in_degree',
            'out_degree': 'rw_out_degree',
            'degree': 'rw_degree',
            'page_rank': 'rw_page_rank',
            'community_louvain': 'rw_community_louvain',
            'wcc': 'rw_wcc',
            'window_start_year': 'rw_window_start_year',
            'window_end_year_inclusive': 'rw_window_end_year'
        })
        
        # Add null rw_ columns to unmatched
        for col in ['rw_in_degree', 'rw_out_degree', 'rw_degree', 'rw_page_rank',
                    'rw_community_louvain', 'rw_wcc', 'rw_window_start_year', 'rw_window_end_year']:
            if col not in unmatched_df.columns:
                unmatched_df[col] = None
        
        # Combine matched and unmatched
        final_df = pd.concat([matched_df, unmatched_df], ignore_index=True)
        
        # Sort to maintain original order
        final_df = final_df.sort_values(['regn', 'DT']).reset_index(drop=True)
        
        match_count = matched_mask.sum()
        print(f"Matched rolling window features for {match_count}/{len(merged_df)} observations ({100*match_count/len(merged_df):.1f}%)")
        
        
        # 6. Construct Analysis Rows via Pydantic
        print("Constructing AnalysisDatasetRow objects...")
        
        
        from data_models.accounting import AccountingRecord
        from data_models.analysis import (
            AnalysisDatasetRow, 
            FamilyOwnershipMetrics, 
            NetworkTopologyMetrics, 
            ForeignOwnershipMetrics, 
            StateOwnershipMetrics
        )
        
        analysis_rows = []
        
        def _safe_get(val, default=None):
            if pd.isna(val):
                return default
            return val
        
        for _, row in final_df.iterrows():
            # Create Accounting Record
            acc_record = AccountingRecord(
                regn=int(row['regn']),
                dt=row['DT'],
                total_assets=_safe_get(row.get('total_assets')),
                total_equity=_safe_get(row.get('total_equity')),
                operating_expense=_safe_get(row.get('operating_expense')),
                operating_income=_safe_get(row.get('operating_income')),
                npl_ratio=_safe_get(row.get('npl_ratio')),
                llp_to_loans_ratio=_safe_get(row.get('llp_to_loans_ratio')),
                cost_to_income_ratio=_safe_get(row.get('cost_to_income_ratio')),
                roa=_safe_get(row.get('ROA')),
                roe=_safe_get(row.get('ROE')),
                nim=_safe_get(row.get('NIM')),
                liquid_assets_to_total_assets=_safe_get(row.get('liquid_assets_to_total_assets')),
                loan_to_deposit_ratio=_safe_get(row.get('loan_to_deposit_ratio')),
                **{k: row[k] for k in ['total_loans', 'total_deposits'] if k in row}
            )
            
            # Family Metrics from Neo4j
            family_metrics = FamilyOwnershipMetrics(
                rho_F=_safe_get(row.get('family_connection_ratio')),
                FOP=_safe_get(row.get('family_ownership_pct')),
                FOV_d=_safe_get(row.get('family_owned_value_direct')),
                D_b=_safe_get(row.get('direct_owners_count')),
                F_b=_safe_get(row.get('family_connections_count')),
                C_F=_safe_get(row.get('family_controlled_companies'))
            )
            
            # Foreign Metrics from Neo4j
            foreign_metrics = ForeignOwnershipMetrics(
                FOP_d=_safe_get(row.get('foreign_ownership_direct_pct')),
                FOP_t=_safe_get(row.get('foreign_ownership_total_pct')),
                FEC_d=_safe_get(row.get('foreign_entity_count')),
                FCC=_safe_get(row.get('foreign_controlled_companies')),
                FCD=_safe_get(row.get('foreign_country_diversity'))
            )
            
            # State Metrics from Neo4j
            state_metrics = StateOwnershipMetrics(
                SOP=_safe_get(row.get('state_ownership_pct')),
                SCC=_safe_get(row.get('state_controlled_companies')),
                SCP=_safe_get(row.get('state_control_paths'))
            )
            
            # Network Metrics from ROLLING WINDOWS (time-varying!)
            network_metrics = NetworkTopologyMetrics(
                in_degree=_safe_get(row.get('rw_in_degree')),
                out_degree=_safe_get(row.get('rw_out_degree')),
                page_rank=_safe_get(row.get('rw_page_rank')),
                # Rolling windows don't have betweenness/closeness/eigenvector from current schema
                # Only degree-based centrality and PageRank
            )
            
            # Construct Final Row
            analysis_row = AnalysisDatasetRow.create_row(
                regn=int(row['regn']),
                date=row['DT'].date(),
                accounting=acc_record,
                family_metrics=family_metrics,
                foreign_metrics=foreign_metrics,
                state_metrics=state_metrics
            )
            
            # Override network metrics with rolling window features
            analysis_row.network = network_metrics
            
            # Convert to dict and flatten
            row_dict = analysis_row.model_dump(by_alias=True)
            flat_row = {}
            for k, v in row_dict.items():
                if isinstance(v, dict):
                    for sub_k, sub_v in v.items():
                        flat_row[f"{k}_{sub_k}"] = sub_v
                else:
                    flat_row[k] = v
            
            # Re-attach survival metadata
            flat_row['is_dead'] = row.get('is_dead')
            flat_row['death_date'] = row.get('death_date')
            flat_row['registration_date'] = row.get('registration_date')
            
            # Add rolling window metadata for debugging/verification
            flat_row['rw_window_start_year'] = row.get('rw_window_start_year')
            flat_row['rw_window_end_year'] = row.get('rw_window_end_year')
            
            # Extract scalar from community_louvain (stored as hierarchical array due to includeIntermediateCommunities=True)
            # Take the FIRST element which represents the coarsest-grained community assignment
            # This reduces fragmentation from 1,149 -> ~10-50 communities
            comm_val = row.get('rw_community_louvain')
            if comm_val is not None and hasattr(comm_val, '__iter__') and not isinstance(comm_val, str):
                # It's an array-like, extract FIRST element (coarsest community level)
                try:
                    flat_row['rw_community_louvain'] = float(comm_val[0]) if len(comm_val) > 0 else None
                except (TypeError, IndexError):
                    flat_row['rw_community_louvain'] = None
            else:
                flat_row['rw_community_louvain'] = comm_val
            
            # Extract scalar from wcc (same issue)
            wcc_val = row.get('rw_wcc')
            if wcc_val is not None and hasattr(wcc_val, '__iter__') and not isinstance(wcc_val, str):
                try:
                    flat_row['rw_wcc'] = float(wcc_val[-1]) if len(wcc_val) > 0 else None
                except (TypeError, IndexError):
                    flat_row['rw_wcc'] = None
            else:
                flat_row['rw_wcc'] = wcc_val
            
            analysis_rows.append(flat_row)
        
        print(f"Validated {len(analysis_rows)} rows via AnalysisDatasetRow.")
        
        # Convert to DataFrame
        df_result = pd.DataFrame(analysis_rows)
        
        # TEMPORAL COMMUNITY AGGREGATION:
        # Assign each bank a stable community based on most frequent community across time windows
        if 'rw_community_louvain' in df_result.columns and df_result['rw_community_louvain'].notna().any():
            print("\nAggregating temporal communities to stable bank-level assignments...")
            
            unique_temporal = df_result['rw_community_louvain'].nunique()
            
            # Calculate most frequent community per bank
            bank_stable_community = (
                df_result[df_result['rw_community_louvain'].notna()]
                .groupby('regn')['rw_community_louvain']
                .agg(lambda x: x.value_counts().index[0])
            )
            
            # Map all observations of each bank to its stable community
            df_result['rw_community_louvain'] = df_result['regn'].map(bank_stable_community)
            
            unique_stable = df_result['rw_community_louvain'].nunique()
            print(f"  Reduced from {unique_temporal} time-varying → {unique_stable} stable bank communities")
        
        return df_result
