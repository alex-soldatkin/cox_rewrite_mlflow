from datetime import date as dt_date
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

from data_models.accounting import AccountingRecord
from data_models.graph import GraphEnrichedNode
from data_models.rolling_windows import RollingWindowNodeFeatures

# --- Component Models ---

class CamelIndicators(BaseModel):
    """
    CAMEL financial performance indicators.
    Source: Aggregated from Form 101/102.
    """
    # Capital
    tier1_capital_ratio: Optional[float] = Field(None, description="Tier 1 capital / Total Assets")
    leverage_ratio: Optional[float] = Field(None, description="Equity / Total Assets")
    
    # Asset Quality
    npl_ratio: Optional[float] = Field(None, description="Non-performing loans / Total Loans")
    llp_ratio: Optional[float] = Field(None, description="Loan loss provisions / Total Loans")
    
    # Management
    cost_to_income: Optional[float] = Field(None, description="Operating expenses / Operating income")
    non_interest_expense_ratio: Optional[float] = Field(None, description="Non-interest expense / Total Assets")
    
    # Earnings
    roa: Optional[float] = Field(None, description="Return on Assets")
    roe: Optional[float] = Field(None, description="Return on Equity")
    nim: Optional[float] = Field(None, description="Net Interest Margin")
    asset_turnover: Optional[float] = Field(None, description="Revenue / Assets")
    
    # Liquidity
    liquid_assets_ratio: Optional[float] = Field(None, description="Liquid Assets / Total Assets")
    loan_to_deposit_ratio: Optional[float] = Field(None, description="Total Loans / Total Deposits")

    @classmethod
    def from_accounting_record(cls, record: AccountingRecord) -> "CamelIndicators":
        """
        Map fields from AccountingRecord to CamelIndicators.
        """
        assets = record.total_assets or 1.0  # Avoid division by zero
        
        # Calculate derived ratios if not explicitly in record
        tier1_est = (record.total_equity / assets) if record.total_equity else None
        lev_ratio = (record.total_equity / assets) if record.total_equity else None
        
        return cls(
            # Capital
            tier1_capital_ratio=tier1_est,
            leverage_ratio=lev_ratio,
            
            # Asset Quality
            npl_ratio=record.npl_ratio,
            llp_ratio=record.llp_to_loans_ratio,
            
            # Management
            cost_to_income=record.cost_to_income_ratio,
            # NIE / Assets approx
            non_interest_expense_ratio=(record.operating_expense / assets) if record.operating_expense else None,
            
            # Earnings
            roa=record.roa,
            roe=record.roe,
            nim=record.nim,
            asset_turnover=(record.operating_income / assets) if record.operating_income else None, # Approx
            
            # Liquidity
            liquid_assets_ratio=record.liquid_assets_to_total_assets,
            loan_to_deposit_ratio=record.loan_to_deposit_ratio
        )

class FamilyOwnershipMetrics(BaseModel):
    """
    Metrics capturing family ownership and kinship networks.
    Source: Neo4j Graph Algorithms & Queries.
    """
    direct_family_owned_value: Optional[float] = Field(None, alias="FOV_d", description="Total ownership value held by family-connected owners.")
    total_direct_owned_value: Optional[float] = Field(None, alias="TOV", description="Sum of all direct ownership stakes.")
    family_ownership_pct: Optional[float] = Field(None, alias="FOP", description="(FOV_d / TOV) * 100")
    
    direct_owner_count: Optional[int] = Field(None, alias="D_b", description="Number of direct shareholders.")
    total_family_connections: Optional[int] = Field(None, alias="F_b", description="Count of family relationships among direct owners.")
    family_connection_ratio: Optional[float] = Field(None, alias="rho_F", description="F_b / D_b")
    
    family_controlled_companies: Optional[int] = Field(None, alias="C_F", description="Count of companies controlled by families with stakes in the bank.")

class ForeignOwnershipMetrics(BaseModel):
    """
    Metrics capturing foreign ownership and international connections.
    """
    direct_foreign_ownership_pct: Optional[float] = Field(None, alias="FOP_d", description="Direct foreign ownership %.")
    total_foreign_ownership_pct: Optional[float] = Field(None, alias="FOP_t", description="Total (direct + indirect) foreign ownership %.")
    
    foreign_entity_count: Optional[int] = Field(None, alias="FEC_d", description="Number of foreign direct owners.")
    foreign_controlled_companies: Optional[int] = Field(None, alias="FCC", description="Number of foreign-controlled intermediate companies.")
    foreign_country_diversity: Optional[int] = Field(None, alias="FCD", description="Number of unique foreign countries represented.")

class StateOwnershipMetrics(BaseModel):
    """
    Metrics capturing state/government ownership.
    """
    state_ownership_pct: Optional[float] = Field(None, alias="SOP", description="Direct state ownership %.")
    state_controlled_companies: Optional[int] = Field(None, alias="SCC", description="Number of state-controlled entities with stakes.")
    state_control_paths: Optional[int] = Field(None, alias="SCP", description="Number of ownership paths from state to bank.")

class NetworkTopologyMetrics(BaseModel):
    """
    Graph centrality and topology metrics.
    Source: Neo4j GDS projections.
    """
    in_degree: Optional[float] = Field(None, description="In-degree centrality.")
    out_degree: Optional[float] = Field(None, description="Out-degree centrality.")
    closeness: Optional[float] = Field(None, description="Closeness centrality.")
    betweenness: Optional[float] = Field(None, description="Betweenness centrality.")
    eigenvector: Optional[float] = Field(None, description="Eigenvector centrality.")
    page_rank: Optional[float] = Field(None, description="PageRank score.")
    
    ownership_complexity_score: Optional[float] = Field(None, alias="C_b", description="Complexity score based on unique owners and path lengths.")

    @classmethod
    def from_rolling_features(cls, feats: RollingWindowNodeFeatures) -> "NetworkTopologyMetrics":
        """
        Map fields from RollingWindowNodeFeatures to NetworkTopologyMetrics.
        """
        return cls(
            in_degree=feats.in_degree,
            out_degree=feats.out_degree,
            # Closeness/Betweenness/Eigen might not be in RW outputs directly if not computed
            # But we map what matches:
            page_rank=feats.page_rank,
            # ownership complexity might be in network_feats if calculated there
        )

    @classmethod
    def from_graph_node(cls, node: GraphEnrichedNode) -> "NetworkTopologyMetrics":
        """
        Map fields from GraphEnrichedNode.
        """
        return cls(
            betweenness=node.betweenness,
            eigenvector=node.eigenvector,
            page_rank=node.page_rank,
            # closeness not in EnrichedNode currently? Check schema.
        )

# --- Aggregated Analysis Model ---

class AnalysisDatasetRow(BaseModel):
    """
    Represents a single row in the final analysis dataset (Bank-Year or Bank-Quarter).
    """
    # Identifiers & Time
    regn: int = Field(..., description="Bank Registration Number (REGN).")
    date: dt_date = Field(..., description="Observation date (e.g. quarter end).")
    year: int = Field(..., description="Year.")
    is_crisis: bool = Field(False, description="Dummy for crisis years (2008-09, 2014-15).")
    
    # Outcome
    failed: bool = Field(False, description="Did the bank fail in this period?")
    survival_time: Optional[float] = Field(None, description="Time to failure or censoring.")
    
    # Controls
    bank_age: Optional[float] = Field(None, description="Years since registration.")
    log_assets: Optional[float] = Field(None, description="Log of total assets (Size control).")
    
    # Feature Sets
    camel: CamelIndicators = Field(default_factory=CamelIndicators)
    family: FamilyOwnershipMetrics = Field(default_factory=FamilyOwnershipMetrics)
    foreign: ForeignOwnershipMetrics = Field(default_factory=ForeignOwnershipMetrics)
    state: StateOwnershipMetrics = Field(default_factory=StateOwnershipMetrics)
    network: NetworkTopologyMetrics = Field(default_factory=NetworkTopologyMetrics)

    @classmethod
    def create_row(
        cls,
        regn: int,
        date: dt_date,
        accounting: Optional[AccountingRecord] = None,
        rolling_features: Optional[RollingWindowNodeFeatures] = None,
        graph_node: Optional[GraphEnrichedNode] = None,
        # Ownership metrics would likely be passed in as pre-computed objects or dictionaries
        # until logic to extract them from raw graph/features is finalized.
        family_metrics: Optional[FamilyOwnershipMetrics] = None,
        foreign_metrics: Optional[ForeignOwnershipMetrics] = None,
        state_metrics: Optional[StateOwnershipMetrics] = None,
        is_crisis: bool = False,
        failed: bool = False,
        survival_time: Optional[float] = None,
        bank_age: Optional[float] = None
    ) -> "AnalysisDatasetRow":
        """
        Factory method to assemble a complete analysis row from various source models.
        """
        # 1. CAMEL from Accounting
        camel = CamelIndicators.from_accounting_record(accounting) if accounting else CamelIndicators()
        
        # 2. Network from Rolling/Graph
        network = NetworkTopologyMetrics()
        if rolling_features:
            network = NetworkTopologyMetrics.from_rolling_features(rolling_features)
        elif graph_node:
            # Fallback or enrichment from static graph node
            network_from_node = NetworkTopologyMetrics.from_graph_node(graph_node)
            # Merge logic (simple override for now)
            if network_from_node.page_rank: network.page_rank = network_from_node.page_rank
            if network_from_node.betweenness: network.betweenness = network_from_node.betweenness
            if network_from_node.eigenvector: network.eigenvector = network_from_node.eigenvector

        # 3. Ownership / State / Family
        # These are complex aggregations. Unless simple mapping exists, we take them as args.
        # If 'state_feats' in rolling_features has a known schema, we could map it here.
        # For now, pass through.
        
        return cls(
            regn=regn,
            date=date,
            year=date.year,
            is_crisis=is_crisis,
            failed=failed,
            survival_time=survival_time,
            bank_age=bank_age,
            log_assets=None, # Todo: calculate from accounting if needed, e.g. np.log(accounting.total_assets)
            camel=camel,
            network=network,
            family=family_metrics or FamilyOwnershipMetrics(),
            foreign=foreign_metrics or ForeignOwnershipMetrics(),
            state=state_metrics or StateOwnershipMetrics()
        )

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }
