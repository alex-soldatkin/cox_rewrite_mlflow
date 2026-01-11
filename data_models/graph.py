from datetime import datetime, date
from typing import Optional, List, Any, Dict, Union
from pydantic import BaseModel, Field

# --- Base Models ---

class Neo4jNode(BaseModel):
    """Base model for all Neo4j nodes."""
    id: Optional[int] = Field(None, description="Internal Neo4j ID (elementId).")
    neo4j_import_id: Optional[str] = Field(None, alias="neo4jImportId", description="Stable import identifier.")
    labels: List[str] = Field(default_factory=list, description="Node labels.")
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "extra": "allow" 
    }

class GraphEnrichedNode(Neo4jNode):
    """
    Nodes enriched with graph algorithmic metrics and embeddings.
    """
    # Centrality & Community
    page_rank: Optional[float] = Field(None, description="PageRank score.")
    betweenness: Optional[float] = Field(None, description="Betweenness centrality.")
    eigenvector: Optional[float] = Field(None, description="Eigenvector centrality.")
    harmonic_centrality: Optional[float] = Field(None, description="Harmonic centrality.")
    community_louvain: Optional[float] = Field(None, description="Louvain community ID.")
    hdbscan_community: Optional[float] = Field(None, description="HDBSCAN community ID.")
    
    # Embeddings (Lists of floats)
    fastrp_embedding_no_weight: Optional[List[float]] = Field(None, description="FastRP embedding (unweighted).")
    fastrp_embedding_with_weight_bank_feats: Optional[List[float]] = Field(None, description="FastRP embedding (weighted + bank feats).")
    fastrp_embedding_with_weight_no_bank_feats: Optional[List[float]] = Field(None, description="FastRP embedding (weighted, no bank feats).")
    
    node2vec_embedding: Optional[List[float]] = Field(None, description="Node2Vec embedding.")
    
    hash_gnn_embedding: Optional[List[float]] = Field(None, description="HashGNN embedding.")
    
    # Feature Vectors
    network_feats: Optional[List[float]] = Field(None, description="Network feature vector.")
    bank_feats: Optional[List[float]] = Field(None, description="Bank feature vector (often propagated).")

class LegalEntity(GraphEnrichedNode):
    """
    Base for Bank, Company, and other organizations.
    """
    name: Optional[str] = Field(None, alias="Name", description="Primary name.")
    full_name: Optional[str] = Field(None, description="Full legal name.")
    short_name: Optional[str] = Field(None, description="Short name.")
    
    inn: Optional[str] = Field(None, alias="Inn", description="Taxpayer Identification Number (INN).")
    ogrn: Optional[str] = Field(None, alias="Ogrn", description="Primary State Registration Number (OGRN).")
    kpp: Optional[str] = Field(None, alias="Kpp", description="Tax Registration Reason Code (KPP).")
    okpo: Optional[str] = Field(None, alias="Okpo", description="All-Russian Classifier of Enterprises and Organizations (OKPO).")
    
    address: Optional[Union[float, str]] = Field(None, alias="Address", description="Registered address.")
    status_text: Optional[str] = Field(None, alias="StatusText", description="Textual description of status.")
    is_actual: Optional[bool] = Field(None, alias="IsActual", description="Is the entity currently active/actual?")
    
    registration_date: Optional[str] = Field(None, alias="RegistrationDate", description="Date of registration.")
    
    activity_types: Optional[List[str]] = Field(None, alias="ActivityTypes", description="List of activity type codes/names.")
    
    authorized_capital: Optional[float] = Field(None, alias="AuthorisedCapital", description="Authorized capital amount.")

# --- Specific Node Models ---

class Bank(LegalEntity):
    """Represents a Bank node."""
    regn: Optional[str] = Field(None, alias="bank_regn", description="CBR Registration number.")
    cbr_id: Optional[str] = Field(None, description="Internal CBR ID.")
    license_date_cbr: Optional[str] = Field(None, description="Date of license issuance.")
    
    def __init__(self, **data):
        super().__init__(**data)
        if "Bank" not in self.labels:
            self.labels.append("Bank")

class Company(LegalEntity):
    """Represents a Company/Entity node."""
    fips_applications: Optional[float] = Field(None, alias="FipsApplications", description="Count of FIPS applications.")
    contracts: Optional[float] = Field(None, alias="Contracts", description="Count of contracts.")
    founders: Optional[str] = Field(None, alias="Founders", description="Founders info (often text).")
    
    def __init__(self, **data):
        super().__init__(**data)
        if "Company" not in self.labels:
            self.labels.append("Company")

class Person(GraphEnrichedNode):
    """Represents a Person node."""
    name: Optional[str] = Field(None, alias="Name", description="Full name.")
    inn: Optional[str] = Field(None, alias="Inn", description="INN.")
    gender: Optional[str] = Field(None, alias="Gender", description="Gender.")
    birth_date: Optional[str] = Field(None, alias="BirthDate", description="Date of birth.")
    citizenship: Optional[str] = Field(None, description="Citizenship.")
    
    phones: Optional[List[str]] = Field(None, alias="Phones", description="Contact phones.")
    emails: Optional[List[str]] = Field(None, alias="Emails", description="Contact emails.")
    
    def __init__(self, **data):
        super().__init__(**data)
        if "Person" not in self.labels:
            self.labels.append("Person")

# --- Neo4j Relationships ---

class Neo4jRelationship(BaseModel):
    """Base model for all Neo4j relationships."""
    id: Optional[int] = Field(None, description="Internal Neo4j ID (elementId).")
    start_node_id: Optional[int] = Field(None, description="ID of the start node.")
    end_node_id: Optional[int] = Field(None, description="ID of the end node.")
    type: str = Field(..., description="Relationship type.")
    
    source: Optional[str] = Field(None, description="Data source.")
    date: Optional[Union[datetime, str, float]] = Field(None, description="Date associated with the relationship.")
    value: Optional[float] = Field(None, description="Generic value property.")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "extra": "allow"
    }

class Ownership(Neo4jRelationship):
    """OWNERSHIP relationship."""
    type: str = "OWNERSHIP"
    
    face_value: Optional[float] = Field(None, alias="FaceValue", description="Monetary value of the share.")
    share: Optional[float] = Field(None, alias="Share", description="Percentage share (0-100 or 0-1).")
    size: Optional[float] = Field(None, alias="Size", description="Size metric.")
    
    temporal_start: Optional[float] = Field(None, description="Start year/timestamp of ownership.")
    temporal_end: Optional[float] = Field(None, description="End year/timestamp of ownership.")
    is_actual: Optional[bool] = Field(None, alias="IsActual", description="Is the ownership currently active?")
    
    share_details: Optional[List[Any]] = Field(None, description="nested details about the share structure.")

class Management(Neo4jRelationship):
    """MANAGEMENT relationship."""
    type: str = "MANAGEMENT"
    
    position_name: Optional[str] = Field(None, alias="PositionName", description="Title of the position.")
    position_type: Optional[str] = Field(None, alias="PositionType", description="Type/Category of the position.")
    
    temporal_start: Optional[float] = Field(None, description="Start of tenure.")
    temporal_end: Optional[float] = Field(None, description="End of tenure.")
    is_actual: Optional[bool] = Field(None, alias="IsActual", description="Is currently in position?")

class Family(Neo4jRelationship):
    """FAMILY relationship."""
    type: str = "FAMILY"
    created_at: Optional[float] = Field(None, description="Creation timestamp.")
    temporal_start: Optional[float] = Field(None, description="Start of relationship validity.")
    temporal_end: Optional[float] = Field(None, description="End of relationship validity.")

class HasNews(Neo4jRelationship):
    """HAS_NEWS relationship."""
    type: str = "HAS_NEWS"
    title: Optional[str] = Field(None, description="News title.")
    url: Optional[str] = Field(None, description="News URL.")

# Dynamic / Other Relationships
# (Defined generically or add specific classes if they have unique props)
class GenericRelationship(Neo4jRelationship):
    """Fallback for other types."""
    pass
