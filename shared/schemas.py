from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
import uuid

class CreditPurpose(str, Enum):
    WORKING_CAPITAL = "working_capital"
    EQUIPMENT_PURCHASE = "equipment_purchase"
    EXPANSION = "expansion"
    REFINANCING = "refinancing"

class ESGPreferences(BaseModel):
    """ESG preferences for credit evaluation"""
    min_esg_score: Optional[float] = Field(default=7.0, ge=0, le=10)
    carbon_neutral_preference: bool = Field(default=True)
    social_impact_weight: float = Field(default=0.3, ge=0, le=1)
    governance_weight: float = Field(default=0.2, ge=0, le=1)

class CreditIntent(BaseModel):
    """WFAP Credit Intent - Company's credit request"""
    intent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = Field(..., description="Unique company identifier")
    company_name: str = Field(..., description="Company legal name")
    amount: float = Field(..., gt=0, description="Requested credit amount")
    currency: str = Field(default="USD", description="Currency code")
    duration_months: int = Field(..., gt=0, le=120, description="Loan duration")
    purpose: CreditPurpose = Field(..., description="Purpose of credit")
    annual_revenue: Optional[float] = Field(None, gt=0)
    industry: Optional[str] = None
    esg_preferences: ESGPreferences = Field(default_factory=ESGPreferences)
    urgency: str = Field(default="normal", description="normal|high|urgent")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    digital_signature: Optional[str] = None
    
    # A2A specific fields
    task_id: Optional[str] = None
    requesting_agent: Optional[str] = None

class ESGScore(BaseModel):
    """ESG scoring breakdown"""
    environmental_score: float = Field(..., ge=0, le=10)
    social_score: float = Field(..., ge=0, le=10)
    governance_score: float = Field(..., ge=0, le=10)
    overall_score: float = Field(..., ge=0, le=10)
    carbon_footprint_category: str = Field(default="medium")
    sustainability_notes: str = Field(default="")

class CreditOffer(BaseModel):
    """WFAP Credit Offer - Bank's response"""
    offer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bank_id: str = Field(..., description="Bank identifier")
    bank_name: str = Field(..., description="Bank display name")
    intent_id: str = Field(..., description="Original intent ID")
    
    # Financial terms
    approved_amount: float = Field(..., gt=0)
    interest_rate: float = Field(..., gt=0, description="Annual interest rate %")
    carbon_adjusted_rate: float = Field(..., gt=0, description="ESG-adjusted rate %")
    processing_fee: float = Field(default=0, ge=0)
    collateral_required: bool = Field(default=False)
    
    # ESG information
    esg_score: ESGScore
    esg_summary: str = Field(..., description="Human-readable ESG impact")
    
    # Terms and conditions
    repayment_schedule: str = Field(default="monthly")
    early_repayment_penalty: bool = Field(default=False)
    grace_period_days: int = Field(default=30, ge=0)
    
    # Validity and compliance
    offer_valid_until: datetime
    regulatory_compliance: Dict[str, Any] = Field(default_factory=dict)
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    
    # A2A specific fields
    task_id: Optional[str] = None
    responding_agent: Optional[str] = None
    digital_signature: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class OfferEvaluation(BaseModel):
    """Offer evaluation results"""
    offer_id: str
    total_score: float = Field(..., ge=0, le=100)
    financial_score: float = Field(..., ge=0, le=100)
    esg_score: float = Field(..., ge=0, le=100)
    terms_score: float = Field(..., ge=0, le=100)
    recommendation: str = Field(..., description="accept|reject|negotiate")
    reasoning: str = Field(..., description="Decision explanation")

# A2A Agent Cards for WFAP
class WFAPCompanyCard(BaseModel):
    """A2A Agent Card for Company Agent"""
    agent_id: str = "wfap-company-agent"
    name: str = "WFAP Company Finance Agent"
    description: str = "Automated company agent for credit discovery and evaluation"
    skills: List[str] = [
        "credit_intent_creation",
        "offer_evaluation", 
        "multi_bank_comparison",
        "esg_preference_matching"
    ]
    version: str = "1.0.0"
    endpoints: List[str] = ["http://localhost:8001/a2a"]

class WFAPBankCard(BaseModel):
    """A2A Agent Card for Bank Agent"""
    agent_id: str
    name: str
    description: str = "Automated bank agent for credit assessment and offer generation"
    skills: List[str] = [
        "credit_assessment",
        "risk_analysis",
        "esg_scoring",
        "competitive_pricing",
        "regulatory_compliance"
    ]
    version: str = "1.0.0"
    endpoints: List[str]
    bank_details: Dict[str, Any] = Field(default_factory=dict)