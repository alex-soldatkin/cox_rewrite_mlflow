
from typing import List, Optional
from datetime import date
import pandas as pd
# Will import AnalysisDatasetRow later when we have the fetching logic connected
# from data_models.analysis import AnalysisDatasetRow

from typing import List, Optional
from datetime import date
import pandas as pd
import os
from graphdatascience import GraphDataScience
from dotenv import load_dotenv

class ExperimentDataLoader:
    """
    Loads analysis-ready data using Neo4j GDS and other sources.
    """
    def __init__(self):
        load_dotenv()
        # Initialize GDS connection
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = os.environ.get("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "")
        
        try:
            self.gds = GraphDataScience(uri, auth=(user, password))
        except Exception as e:
            print(f"Failed to connect to Neo4j GDS: {e}")
            raise e

    def load_training_data(self, start_date: str = "2015-01-01", end_date: str = "2020-01-01") -> pd.DataFrame:
        """
        Loads training data merging Neo4j population and Accounting features.
        """
        # 1. Fetch Population (Banks)
        query_path = os.path.join(os.path.dirname(__file__), "../queries/cypher/001_get_all_banks.cypher")
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
        # Ensure DT is datetime
        acc_df['DT'] = pd.to_datetime(acc_df['DT'])
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        acc_df = acc_df[(acc_df['DT'] >= start_dt) & (acc_df['DT'] <= end_dt)]
        
        # 3. Merge
        # Neo4j has 'regn_cbr' (str), Accounting has 'REGN' (int)
        # User confirmed regn is a string. Standardize on string.
        banks_df['regn'] = banks_df['regn_cbr'].astype(str)
        acc_df['regn'] = acc_df['REGN'].astype(str)
        
        merged_df = pd.merge(acc_df, banks_df, on='regn', how='inner')
        print(f"Merged Data Shape: {merged_df.shape}")
        
        if merged_df.empty:
            print("Warning: Merged dataframe is empty! Check REGN overlap.")
            return pd.DataFrame()

        print("Constructing AnalysisDatasetRow objects...")
        # 4. Construct Analysis Rows via Pydantic
        # This "Systematizes" the linking as requested.
        
        from data_models.accounting import AccountingRecord
        from data_models.analysis import AnalysisDatasetRow, FamilyOwnershipMetrics, NetworkTopologyMetrics, ForeignOwnershipMetrics, StateOwnershipMetrics
        
        analysis_rows = []
        
        import numpy as np
        
        def _safe_get(val, default=None):
            if pd.isna(val):
                return default
            return val
            
        # Iterate over DataFrame rows (performance note: for 85k rows this might take ~10-20s, irrelevant for batch jobs)
        for _, row in merged_df.iterrows():
            # Create Accounting Record
            # Mapping columns explicitly ensures safety
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
            
            # Create Neo4j/Graph Object Maps
            # Family Metrics
            family_metrics = FamilyOwnershipMetrics(
                rho_F=_safe_get(row.get('family_connection_ratio')),
                FOP=_safe_get(row.get('family_ownership_pct')),
                FOV_d=_safe_get(row.get('family_owned_value_direct')),
                D_b=_safe_get(row.get('direct_owners_count')),
                F_b=_safe_get(row.get('family_connections_count')),
                C_F=_safe_get(row.get('family_controlled_companies'))
            )
            
            # Foreign Metrics
            foreign_metrics = ForeignOwnershipMetrics(
                FOP_d=_safe_get(row.get('foreign_ownership_direct_pct')),
                FOP_t=_safe_get(row.get('foreign_ownership_total_pct')),
                FEC_d=_safe_get(row.get('foreign_entity_count')),
                FCC=_safe_get(row.get('foreign_controlled_companies')),
                FCD=_safe_get(row.get('foreign_country_diversity'))
            )
            
            # State Metrics
            state_metrics = StateOwnershipMetrics(
                SOP=_safe_get(row.get('state_ownership_pct')),
                SCC=_safe_get(row.get('state_controlled_companies')),
                SCP=_safe_get(row.get('state_control_paths'))
            )
            
            # Network Metrics (from Graph Node props)
            network_metrics = NetworkTopologyMetrics(
                in_degree=_safe_get(row.get('in_degree')),
                out_degree=_safe_get(row.get('out_degree')),
                page_rank=_safe_get(row.get('page_rank')),
                betweenness=_safe_get(row.get('betweenness')),
                closeness=_safe_get(row.get('closeness')),
                eigenvector=_safe_get(row.get('eigenvector')),
                C_b=_safe_get(row.get('ownership_complexity_score'))
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
            # Manually inject network metrics if create_row creates a default one
            # create_row initializes default NetworkTopologyMetrics if not passed options
            # We can modify create_row to take network_metrics as arg or set it here.
            # AnalysisDatasetRow has 'network' field.
            analysis_row.network = network_metrics
            
            # To avoid modifying the schema right now, we will perform the Pydantic validation
            # and then re-attach the survival metadata (dates, is_dead) when converting back to DF.
            
            row_dict = analysis_row.model_dump(by_alias=True)
            # Flatten nested models (camel, family, etc.)
            flat_row = {}
            for k, v in row_dict.items():
                if isinstance(v, dict):
                    for sub_k, sub_v in v.items():
                        flat_row[f"{k}_{sub_k}"] = sub_v # e.g. camel_roa
                else:
                    flat_row[k] = v
                    
            # Re-attach survival metadata needed for Cox
            flat_row['is_dead'] = row.get('is_dead')
            flat_row['death_date'] = row.get('death_date')
            flat_row['registration_date'] = row.get('registration_date')
            
            analysis_rows.append(flat_row)
            
        print(f"Validated {len(analysis_rows)} rows via AnalysisDatasetRow.")
        return pd.DataFrame(analysis_rows)

