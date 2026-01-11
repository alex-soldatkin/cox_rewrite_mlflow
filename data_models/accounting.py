from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class AccountingRecord(BaseModel):
    """
    Represents a single record of imputed banking accounting data.
    Derived from CBR Forms 101 (Balance Sheet) and 102 (Income Statement).
    """
    
    # Identifiers & Time
    regn: int = Field(..., description="Registration number of the bank (CBR identifier).")
    dt: datetime = Field(..., description="Date of the accounting record.")
    form: Optional[float] = Field(None, description="Source form identifier (101 or 102), if applicable.")

    # Balance Sheet - Assets
    total_assets: Optional[float] = Field(None, description="Total assets of the bank.")
    total_liquid_assets: Optional[float] = Field(None, description="Liquid assets (cash, equivalents, high-quality bonds).")
    
    # Balance Sheet - Liabilities & Equity
    total_liabilities: Optional[float] = Field(None, description="Total liabilities.")
    total_passives: Optional[float] = Field(None, description="Total passives (should equal Total Assets).")
    total_equity: Optional[float] = Field(None, description="Total equity capital.")
    state_equity: Optional[float] = Field(None, description="Equity held by state-controlled entities.")
    total_deposits: Optional[float] = Field(None, description="Total customer deposits.")

    # Loan Portfolio
    total_loans: Optional[float] = Field(None, description="Total loan portfolio volume.")
    state_loans: Optional[float] = Field(None, description="Loans issued to state-controlled entities.")
    individual_loans: Optional[float] = Field(None, description="Loans issued to individuals.")
    company_loans: Optional[float] = Field(None, description="Loans issued to companies.")
    
    # Credit Quality
    npl_amount: Optional[float] = Field(None, description="Non-Performing Loans (NPL) volume.")
    provision_amount: Optional[float] = Field(None, description="Loan loss provisions volume.")

    # Income Statement (Flows)
    interest_income: Optional[float] = Field(None, description="Interest income.")
    interest_expense: Optional[float] = Field(None, description="Interest expense.")
    net_interest_income: Optional[float] = Field(None, description="Net Interest Income (Interest Income - Interest Expense).")
    
    operating_income: Optional[float] = Field(None, description="Non-interest / Operating income.")
    operating_expense: Optional[float] = Field(None, description="Operating expenses.")
    
    net_income_amount: Optional[float] = Field(None, description="Net Income (Profit/Loss).")

    # Financial Ratios
    roa: Optional[float] = Field(None, alias="ROA", description="Return on Assets (%).")
    roe: Optional[float] = Field(None, alias="ROE", description="Return on Equity (%).")
    nim: Optional[float] = Field(None, alias="NIM", description="Net Interest Margin (%).")
    cost_to_income_ratio: Optional[float] = Field(None, description="Cost-to-Income Ratio (Operating Expense / Operating Income).")
    
    npl_ratio: Optional[float] = Field(None, description="NPL Ratio (NPL / Total Loans).")
    llp_to_loans_ratio: Optional[float] = Field(None, description="Loan Loss Provisions to Total Loans Ratio.")
    coverage_ratio: Optional[float] = Field(None, description="NPL Coverage Ratio (Provisions / NPL).")
    
    loan_to_deposit_ratio: Optional[float] = Field(None, description="Loan-to-Deposit Ratio.")
    liquid_assets_to_total_assets: Optional[float] = Field(None, description="Liquid Assets to Total Assets Ratio.")
    state_equity_pct: Optional[float] = Field(None, description="Percentage of equity held by the state.")

    # QC Metrics
    balance_gap: Optional[float] = Field(None, description="Accounting equation gap (Assets - (Liabilities + Equity)). Should be near zero.")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True 
    }
