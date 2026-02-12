"""
Mechanism Data Loader for Experiment 010.
Extends QuarterlyWindowDataLoader with specific proxies for transaction cost mechanisms.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List
from .quarterly_window_loader import QuarterlyWindowDataLoader
from graphdatascience import GraphDataScience

class MechanismDataLoader(QuarterlyWindowDataLoader):
    """
    Extends base loader with proxies for:
    1. Political Embeddedness (Bank Region)
    2. Tax Optimization (Stake Fragmentation)
    3. Internal Capital Markets (Family Company Count/Assets)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gds = GraphDataScience(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )

    def _get_mechanism_features_snapshot(self) -> pd.DataFrame:
        """
        Queries Neo4j for structural mechanism features.
        Since we lack specific time-varying ownership snapshots for these proxies,
        we use the current state as a proxy or calculate them based on bank properties.
        
        Note: fragmentation and company count are based on the latest Neo4j state.
        For H1 (Embeddedness), we use Bank.region.
        """
        print("\n--- Fetching Mechanism Features from Neo4j ---")
        
        # 1. Stake Fragmentation (HHI)
        # 2. Threshold Proximity
        # 3. Family Company Assets (Internal Capital Market Size)
        # Note: We use ownership nodes and family relations.
        
        cypher = """
        MATCH (b:Bank)
        OPTIONAL MATCH (b)<-[r:OWNERSHIP]-(p:Person)
        WITH b, p, r, 
             EXISTS { (p)-[:FAMILY]-(:Person) } AS is_family
        WHERE p IS NOT NULL
        
        WITH b, collect({stake: r.Size, is_family: is_family}) AS owners
        WITH b, [o IN owners WHERE o.is_family] AS family_owners
        
        WITH b, family_owners,
             reduce(s = 0.0, fo IN family_owners | s + fo.stake) AS total_family_stake
        
        // Fragmentation index: only if total_family_stake > 0
        WITH b, family_owners, total_family_stake,
             CASE 
               WHEN total_family_stake > 0 THEN [fo IN family_owners | (fo.stake / total_family_stake)^2]
               ELSE [] 
             END AS squared_shares
        
        WITH b, total_family_stake,
             CASE 
               WHEN total_family_stake > 0 THEN (1.0 - reduce(hhi = 0.0, ss IN squared_shares | hhi + ss))
               ELSE NULL 
             END AS stake_fragmentation_index,
             [fo IN family_owners WHERE fo.stake >= 18.0 AND fo.stake <= 22.0] AS near_20_count,
             [fo IN family_owners WHERE fo.stake >= 48.0 AND fo.stake <= 52.0] AS near_50_count
        
        // Internal Capital Market Expansion (H3+)
        OPTIONAL MATCH (b)<-[:OWNERSHIP]-(p_owner:Person)
        WHERE EXISTS { (p_owner)-[:FAMILY]-(:Person) }
        OPTIONAL MATCH (p_owner)-[:FAMILY]-(f:Person)
        OPTIONAL MATCH (f)-[:OWNERSHIP]->(c:Company)
        
        WITH b, stake_fragmentation_index, total_family_stake, 
             size(near_20_count) AS family_near_20, 
             size(near_50_count) AS family_near_50,
             count(DISTINCT c) AS family_company_count,
             collect(DISTINCT c) as family_cos

        // Aggregate Financial and Sector data
        UNWIND (CASE WHEN size(family_cos) > 0 THEN family_cos ELSE [null] END) as comp
        WITH b, stake_fragmentation_index, total_family_stake, family_near_20, family_near_50, family_company_count,
             comp,
             CASE WHEN comp.MainActivityType_Code IS NOT NULL AND comp.MainActivityType_Code <> '-1' 
                  THEN left(toString(comp.MainActivityType_Code), 2) 
                  ELSE NULL END as sector
        
        WITH b, stake_fragmentation_index, total_family_stake, family_near_20, family_near_50, family_company_count,
             sum(CASE WHEN comp.AuthorisedCapital <> -1 THEN comp.AuthorisedCapital ELSE 0 END + 
                 CASE WHEN comp.Capital <> -1 THEN comp.Capital ELSE 0 END) as group_total_capital,
             count(DISTINCT sector) as group_sector_count,
             collect(sector) as all_sectors
        
        // Final selection and primary sector logic
        UNWIND (CASE WHEN size(all_sectors) > 0 THEN all_sectors ELSE [null] END) as s
        WITH b, stake_fragmentation_index, total_family_stake, family_near_20, family_near_50, family_company_count, 
             group_total_capital, group_sector_count, s, count(*) as sector_freq
        ORDER BY sector_freq DESC
        
        WITH b, stake_fragmentation_index, total_family_stake, family_near_20, family_near_50, family_company_count, 
             group_total_capital, group_sector_count, collect(s)[0] as group_primary_sector
        
        RETURN b.regn_cbr AS regn_cbr,
               b.region AS bank_region,
               stake_fragmentation_index,
               total_family_stake,
               family_near_20,
               family_near_50,
               family_company_count,
               group_total_capital,
               group_sector_count,
               group_primary_sector
        """
        
        df_mech = self.gds.run_cypher(cypher)
        print(f"   Fetched mechanism features for {len(df_mech)} banks")
        
        # regn conversion
        df_mech['regn'] = pd.to_numeric(df_mech['regn_cbr'], errors='coerce').astype('Int64')
        
        return df_mech

    def _load_epu_data(self) -> pd.DataFrame:
        """
        Loads and aggregates Russian Economic Policy Uncertainty data from Excel.
        """
        epu_path = Path("Russia_Policy_Uncertainty_Data.xlsx")
        if not epu_path.exists():
            print(f"   WARNING: EPU data not found at {epu_path}")
            return pd.DataFrame()

        print("   Loading EPU data from Excel...")
        df_epu = pd.read_excel(epu_path)
        
        # Clean footer: drop rows where 'Year' is not a number
        df_epu = df_epu[pd.to_numeric(df_epu['Year'], errors='coerce').notnull()].copy()
        df_epu['Year'] = df_epu['Year'].astype(int)
        df_epu['Month'] = df_epu['Month'].astype(int)
        
        # Create quarter column as Period[Q-DEC]
        df_epu['date'] = pd.to_datetime({'year': df_epu['Year'], 'month': df_epu['Month'], 'day': 1})
        df_epu['quarter'] = df_epu['date'].dt.to_period('Q')
        
        # Aggregate to quarterly (mean)
        df_q = df_epu.groupby('quarter')['News-Based Policy Uncertainty Index'].mean().reset_index()
        df_q.rename(columns={'News-Based Policy Uncertainty Index': 'epu_index'}, inplace=True)
        
        return df_q

    def load_mechanism_data(self, 
                            lag_quarters: int = 4,
                            start_year: int = 2014,
                            end_year: int = 2020) -> pd.DataFrame:
        """
        Main method to load data with baseline controls + lagged network + mechanism proxies.
        """
        # 1. Load baseline (Accounting + Lagged Network + Basic Family % from QuarterlyWindowDataLoader)
        df = super().load_with_lags(lag_quarters=lag_quarters, start_year=start_year, end_year=end_year)
        
        # 2. Fetch structural mechanism features
        df_mech = self._get_mechanism_features_snapshot()
        
        # 3. Load EPU data
        df_epu = self._load_epu_data()
        
        # 4. Merge
        print(f"\nMerging mechanism proxies and EPU...")
        
        # Merge structural features from Neo4j
        df = df.merge(df_mech.drop(columns=['regn_cbr']), on='regn', how='left')
        
        if not df_epu.empty:
            # Ensure types match for merging.
            df['quarter_str'] = df['quarter'].astype(str)
            df_epu['quarter_str'] = df_epu['quarter'].astype(str)
            df = df.merge(df_epu.drop(columns=['quarter']), on='quarter_str', how='left')
            df.drop(columns=['quarter_str'], inplace=True)
        
        # 5. Final cleaning for mechanism features
        df['stake_fragmentation_index'] = df['stake_fragmentation_index'].fillna(0).infer_objects(copy=False)
        
        # New H3+ features
        h3_plus_cols = ['group_total_capital', 'group_sector_count']
        df[h3_plus_cols] = df[h3_plus_cols].fillna(0).infer_objects(copy=False)
        df['group_primary_sector'] = df['group_primary_sector'].fillna("Unknown")
        
        mech_cols = [
            'family_near_20', 'family_near_50', 'family_company_count'
        ]
        df[mech_cols] = df[mech_cols].fillna(0).infer_objects(copy=False)
        
        if 'epu_index' in df.columns:
            df['epu_index'] = df['epu_index'].ffill().bfill()
        else:
            print("   CRITICAL: epu_index column not found after merge!")
        
        print(f"   Final obs: {len(df):,}")
        print(f"   Mechanism features added: ['stake_fragmentation_index', 'epu_index', 'group_total_capital', 'group_sector_count', 'group_primary_sector'] + {mech_cols}")
        
        return df

if __name__ == "__main__":
    # Test
    loader = MechanismDataLoader()
    df = loader.load_mechanism_data(lag_quarters=4)
    print("\nSample Columns:")
    print(df.columns.tolist())
    print("\nFragmentation distribution:")
    print(df['stake_fragmentation_index'].describe())
