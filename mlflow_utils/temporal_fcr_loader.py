"""
Temporal FCR Data Loader for Biannual Rolling Windows.

Loads temporal Family Connection Ratio (FCR) data from the rolling windows pipeline
(production_run_1990_2022_v6) with proper handling of biannual (2-year) windows.

Key features:
- Loads biannual windows (2-year periods)
- Uses gds_id for robust merging (see temporal_fcr_addendum.md)
- Creates lagged features with 2-year periods
- Merges CAMEL ratios from Neo4j
- Creates Cox time-varying event indicators
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np
from graphdatascience import GraphDataScience

logger = logging.getLogger(__name__)


class TemporalFCRLoader:
    """
    Load temporal FCR data from biannual rolling windows.
    
    Data source: data_processing/rolling_windows/output/production_run_1990_2022_v6/
    Windows: 2-year (biannual) periods from 1990-2022
    
    Key columns in output:
    - regn: Bank ID
    - DT: Observation date (window midpoint)
    - fcr_temporal: Temporal FCR (ground truth + imputed via link prediction)
    - fcr_temporal_lag: Lagged FCR
    - page_rank, page_rank_lag: PageRank centrality
    - out_degree, out_degree_lag: Out-degree centrality
    - camel_roa, camel_npl_ratio, camel_tier1_capital_ratio: Accounting ratios
    - is_dead: Bank death indicator
    - event: Cox TV event indicator (1 only for last obs of dead banks)
    - gds_id: Persistent Neo4j ID (for advanced use)
    """
    
    def __init__(
        self,
        base_dir: str = 'data_processing/rolling_windows/output/production_run_1990_2022_v6',
        gds_client: Optional[GraphDataScience] = None
    ):
        """
        Initialize loader.
        
        Args:
            base_dir: Path to temporal FCR data directory
            gds_client: Optional GDS client for CAMEL data fetching
        """
        self.base_dir = Path(base_dir)
        self.nodes_dir = self.base_dir / 'nodes'
        self.edges_dir = self.base_dir / 'edges'
        self.gds = gds_client
        
        if not self.nodes_dir.exists():
            raise FileNotFoundError(f"Nodes directory not found: {self.nodes_dir}")
    
    def load_with_lags(
        self,
        lag_periods: int = 2,
        start_year: int = 2014,
        end_year: int = 2020,
        merge_camel: bool = True
    ) -> pd.DataFrame:
        """
        Load temporal FCR data with biannual lags.
        
        Args:
            lag_periods: Number of 2-year periods to lag (default=2 → 4-year lag)
            start_year: Filter windows starting from this year
            end_year: Filter windows ending before this year
            merge_camel: Whether to merge CAMEL ratios from Neo4j
        
        Returns:
            DataFrame with biannual observations and lagged features
        """
        logger.info(
            "Loading temporal FCR data: lag_periods=%d, years=%d-%d",
            lag_periods, start_year, end_year
        )
        
        # 1. Load parquet files in range (with lag buffer)
        df = self._load_parquet_files(start_year, end_year, lag_periods)
        logger.info("Loaded %d raw observations from %d windows", len(df), df['window_graph_name'].nunique())
        
        # 2. Assign observation dates (window midpoint)
        df = self._assign_window_midpoints(df)
        
        # 3. Rename columns to match experiment expectations
        df = self._rename_columns(df)
        
        # 4. Create lagged features
        df = self._create_lagged_features(df, lag_periods)
        
        # 5. Merge CAMEL ratios (if requested)
        if merge_camel and self.gds is not None:
            df = self._merge_camel_data(df)
        elif merge_camel:
            logger.warning("CAMEL merge requested but no GDS client provided")
        
        # 6. Create Cox event indicators
        df = self._create_event_indicators(df)
        
        # 7. Filter to requested year range (after creating lags)
        df = df[
            (df['DT'].dt.year >= start_year) &
            (df['DT'].dt.year <= end_year)
        ].copy()
        
        logger.info(
            "Final dataset: %d observations, %d banks, years %d-%d",
            len(df),
            df['regn'].nunique(),
            df['DT'].dt.year.min(),
            df['DT'].dt.year.max()
        )
        
        return df
    
    def _load_parquet_files(
        self,
        start_year: int,
        end_year: int,
        lag_periods: int
    ) -> pd.DataFrame:
        """Load all parquet files in range, including lag buffer."""
        dfs = []
        lag_buffer_years = lag_periods * 2  # Convert periods to years
        
        for file in sorted(self.nodes_dir.glob('node_features_rw_*.parquet')):
            # Extract years from filename (e.g., node_features_rw_2014_2015.parquet)
            parts = file.stem.split('_')
            if len(parts) >= 4:
                window_start = int(parts[-2])
                window_end = int(parts[-1])
            else:
                logger.warning("Skipping file with unexpected name: %s", file.name)
                continue
            
            # Include files within range + lag buffer
            if window_end < start_year - lag_buffer_years:
                continue
            if window_start > end_year + 2:  # Small buffer for end
                continue
            
            logger.debug("Loading %s", file.name)
            df_window = pd.read_parquet(file)
            dfs.append(df_window)
        
        if not dfs:
            raise ValueError(f"No parquet files found for years {start_year}-{end_year}")
        
        return pd.concat(dfs, ignore_index=True)
    
    def _assign_window_midpoints(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assign window midpoint as observation date.
        Each 2-year window becomes a single biannual observation.
        """
        df['window_start'] = pd.to_datetime(df['window_start_ms'], unit='ms')
        df['window_end'] = pd.to_datetime(df['window_end_ms'], unit='ms')
        
        # Midpoint as observation date
        df['DT'] = df['window_start'] + (df['window_end'] - df['window_start']) / 2
        
        return df
    
    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rename columns and map gds_id to regn_cbr.
        
        The parquet files have entity_id which includes non-Bank nodes (GDS_X).
        We need to query Neo4j to get regn_cbr for Bank nodes only.
        """
        # FCR column (from pipeline.py line 480)
        if 'fcr_temporal' in df.columns:
            df = df.rename(columns={'fcr_temporal': 'family_connection_ratio_temporal'})
        
        # Get regn_cbr mapping from Neo4j if we have gds_id
        if 'gds_id' in df.columns and self.gds is not None:
            logger.info("Fetching regn_cbr mapping from Neo4j for GDS IDs...")
            
            # Get unique gds_ids from the DataFrame
            unique_gds_ids = df['gds_id'].unique().tolist()
            
            # Query Neo4j for regn_cbr for these gds_ids
            # We only care about nodes that are Banks and have a regn_cbr
            query = f"""
            MATCH (b:Bank)
            WHERE id(b) IN {unique_gds_ids} AND b.regn_cbr IS NOT NULL
            RETURN id(b) AS gds_id, b.regn_cbr AS regn_cbr
            """
            
            try:
                regn_map_df = self.gds.run_cypher(query)
                regn_map_df['gds_id'] = regn_map_df['gds_id'].astype('int64')
                
                logger.info("Fetched regn_cbr for %d GDS IDs", len(regn_map_df))
                
                # Merge regn_cbr into the main DataFrame
                df = df.merge(regn_map_df, on='gds_id', how='left')
                
                # Rename regn_cbr to regn
                df = df.rename(columns={'regn_cbr': 'regn'})
                
                # Drop rows where regn is NaN (i.e., not a Bank or no regn_cbr)
                initial_rows = len(df)
                df.dropna(subset=['regn'], inplace=True)
                if len(df) < initial_rows:
                    logger.warning(
                        "Dropped %d rows that were not identified as Banks or had no regn_cbr.",
                        initial_rows - len(df)
                    )
                
            except Exception as e:
                logger.error("Failed to fetch regn_cbr mapping from Neo4j: %s", e)
                # Fallback to entity_id if Neo4j query fails
                if 'entity_id' in df.columns:
                    df['regn'] = df['entity_id']
                else:
                    logger.warning("No 'entity_id' or 'gds_id' to use for 'regn' after Neo4j failure.")
                    df['regn'] = np.nan # Ensure 'regn' column exists, but with NaNs
        else:
            # If no gds_id or GDS client, fallback to entity_id
            if 'entity_id' in df.columns:
                df['regn'] = df['entity_id']
                logger.info("Using 'entity_id' as 'regn' (no gds_id or GDS client for mapping).")
            else:
                logger.warning("No 'entity_id' or 'gds_id' available to create 'regn' column.")
                df['regn'] = np.nan # Ensure 'regn' column exists, but with NaNs
        
        return df
    
    def _create_lagged_features(self, df: pd.DataFrame, lag_periods: int) -> pd.DataFrame:
        """
        Create lagged features (shift by lag_periods × 2 years).
        
        Lag is in biannual periods: lag_periods=2 → 4-year lag
        """
        # Sort by bank and date
        df = df.sort_values(['regn', 'DT']).copy()
        
        # Features to lag
        features_to_lag = [
            'family_connection_ratio_temporal',
            'page_rank',
            'out_degree',
            'in_degree'
        ]
        
        # Filter to only existing features
        features_to_lag = [f for f in features_to_lag if f in df.columns]
        
        
        # Create lags with proper naming for experiment compatibility
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
        
        logger.info("Created lagged features (lag_periods=%d): %s", lag_periods, features_to_lag)
        
        return df
    
    def _merge_camel_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge CAMEL ratios from Neo4j using gds_id for robust merging.
        
        Uses gds_id (persistent Neo4j id(n)) as join key.
        See temporal_fcr_addendum.md for details.
        """
        if self.gds is None:
            logger.warning("Cannot merge CAMEL: no GDS client provided")
            return df
        
        logger.info("Fetching CAMEL ratios from Neo4j using gds_id...")
        
        # Query Neo4j for CAMEL data
        # Note: This query should match the structure from quarterly_window_loader
        camel_query = """
        MATCH (b:Bank)
        WHERE b.regn_cbr IS NOT NULL
        OPTIONAL MATCH (b)-[:HAS_ACCOUNTING]->(a:Accounting)
        RETURN 
            id(b) AS gds_id,
            b.regn_cbr AS regn,
            coalesce(a.ROA, 0.0) AS camel_roa,
            coalesce(a.NPL_ratio, 0.0) AS camel_npl_ratio,
            coalesce(a.Tier1_capital_ratio, 0.0) AS camel_tier1_capital_ratio,
            coalesce(a.date, '') AS accounting_date
        """
        
        try:
            camel_df = self.gds.run_cypher(camel_query)
            camel_df['gds_id'] = camel_df['gds_id'].astype('int64')
            
            logger.info("Fetched CAMEL data for %d banks", len(camel_df))
            
            # Merge on gds_id (robust to nodeId renumbering)
            if 'gds_id' in df.columns:
                df['gds_id'] = df['gds_id'].astype('int64')
                
                # Merge
                df = df.merge(
                    camel_df[['gds_id', 'camel_roa', 'camel_npl_ratio', 'camel_tier1_capital_ratio']],
                    on='gds_id',
                    how='left',
                    suffixes=('', '_camel')
                )
                
                merged_count = df['camel_roa'].notna().sum()
                logger.info("Merged CAMEL for %d/%d observations", merged_count, len(df))
            else:
                logger.warning("gds_id column not found - cannot merge CAMEL using robust method")
                # Fallback: try merge on regn
                df = df.merge(
                    camel_df[['regn', 'camel_roa', 'camel_npl_ratio', 'camel_tier1_capital_ratio']],
                    on='regn',
                    how='left',
                    suffixes=('', '_camel')
                )
        
        except Exception as e:
            logger.error("Failed to merge CAMEL data: %s", e)
            # Add empty CAMEL columns
            for col in ['camel_roa', 'camel_npl_ratio', 'camel_tier1_capital_ratio']:
                if col not in df.columns:
                    df[col] = 0.0
        
        return df
    
    def _create_event_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create Cox time-varying event indicators.
        event=1 only for the LAST observation of dead banks.
        """
        df['event'] = 0
        
        if 'is_dead' in df.columns:
            # Find dead banks
            dead_banks = df[df['is_dead'] == True]['regn'].unique()
            
            # For each dead bank, mark last observation as event=1
            for bank in dead_banks:
                bank_df = df[df['regn'] == bank]
                last_date = bank_df['DT'].max()
                df.loc[(df['regn'] == bank) & (df['DT'] == last_date), 'event'] = 1
            
            event_count = (df['event'] == 1).sum()
            logger.info("Created event indicators: %d events (dead banks)", event_count)
        else:
            logger.warning("is_dead column not found - cannot create event indicators")
        
        return df
