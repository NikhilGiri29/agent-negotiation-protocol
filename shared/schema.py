from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import uuid

# ========== ENUMS ==========
class RegistryType(str, Enum):
    BANK = "Bank"
    COMPANY = "Company"
    CREDITBUREAU = "Credit Bureau"
    MARKETDATA = "Market Data"
    ESGREGULATOR = "ESG Regulator"

class CreditPurpose(str, Enum):
    WORKING_CAPITAL = "working_capital"
    EQUIPMENT_PURCHASE = "equipment_purchase"
    EXPANSION = "expansion"
    REFINANCING = "refinancing"


# ========== REGISTRY & THIRD PARTIES ==========
class Registry(BaseModel):
    """Registry representational schema"""
    type: RegistryType
    id: str = Field(..., description="Entity ID based on type")
    api_url: str = Field(..., description="Agent/API URL of the entity")

class CreditBureau(BaseModel):
    """Credit Bureau representational schema"""
    company_id: str
    credit_score: int = Field(..., ge=0, le=850)
    rating: str = Field(..., description="Credit grade e.g. AAA, BBB, etc.")
    history_summary: str = Field(default="No major defaults")

class ESGRegulator(BaseModel):
    """ESG Regulator representational schema"""
    bank_id: str
    environmental_score: float = Field(..., ge=0, le=10)
    social_score: float = Field(..., ge=0, le=10)
    governance_score: float = Field(..., ge=0, le=10)
    overall_score: float = Field(..., ge=0, le=10)
    carbon_footprint_category: str = Field(default="medium")
    sustainability_notes: str = Field(default="")

class MarketData(BaseModel):
    """Company's market info representational schema"""
    company_id: str
    is_public: bool = Field(default=False)
    weekly_stock_price_hist: Optional[List[float]] = Field(default = None, 
                                                           description="Past n week average stock price")
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None


# ========== CORE ENTITIES ==========
class Bank(BaseModel):
    """Bank representational schema"""
    bank_id: str
    bank_name: str
    max_loan_amount: float = Field(default=100_000_000)
    min_interest_rate: float = Field(default=1.0)
    reputation_score: Optional[int] = Field(default=5, ge=1, le=10)
    risk_appetite: str  # conservative|moderate|aggressive
    esg_data: ESGRegulator # self reported but needs to be verified by regulator

class Company(BaseModel):
    """Company representational schema"""
    company_id: str
    company_name: str
    annual_revenue: Optional[float] = None
    industry: Optional[str] = None


# ========== CREDIT REQUEST / RESPONSE ==========
class ESGPreferences(BaseModel):
    """ESG preferences for credit evaluation"""
    min_esg_score: Optional[float] = Field(default=7.0, ge=0, le=10)
    carbon_neutral_preference: bool = Field(default=True)
    social_impact_weight: float = Field(default=0.3, ge=0, le=1)
    governance_weight: float = Field(default=0.2, ge=0, le=1)

class CreditIntent(BaseModel):
    """Credit Intent submitted to bank/registry by Company"""
    intent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    company_name: str
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD")
    duration_months: int = Field(..., gt=0, le=120)
    purpose: CreditPurpose
    annual_revenue: Optional[float] = None
    industry: Optional[str] = None
    esg_preferences: ESGPreferences = Field(default_factory=ESGPreferences)
    urgency: str = Field(default="normal")  # normal|high|urgent
    timestamp: datetime = Field(default_factory=datetime.now)
    digital_signature: Optional[str] = None
    # A2A specific fields
    task_id: Optional[str] = None
    requesting_agent: Optional[str] = None

class AuthToken(BaseModel):
    """Authentication Token given by Registry"""
    token_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    bank_id: str
    request_id: str
    expiry: datetime = Field(default_factory=lambda: datetime.now() + timedelta(minutes=10))
    issued_by: str = "Registry"
    scope: Optional[str] = None

class RegistryBankList(BaseModel):
    """List of Banks offered by Registry matching Credit Intent, contains the Auth Token"""
    bank_ids: List[str]
    api_urls: List[str]
    auth_tokens: List[AuthToken]

class BankResponse(BaseModel):
    """Bank's response to Credit Intent"""
    offer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bank_id: str
    bank_name: str
    intent_id: str
    # Financial terms
    approved_amount: float = Field(..., gt=0)
    interest_rate: float = Field(..., gt=0)
    processing_fee: float = Field(default=0, ge=0)
    collateral_required: bool = Field(default=False)
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
    timestamp: datetime = Field(default_factory=datetime.now)


# ========== REGISTRATION ==========
class BankRegister(BaseModel):
    """Registration Request sent to Registry by Bank"""
    bank_id: str
    bank_name: str
    max_loan_amount: float
    min_interest_rate: float
    api_url: str = Field(..., description="Agent/API URL of the bank")

class CompanyRegister(BaseModel):
    """Registration Request sent to Registry by Company"""
    company_id: str
    company_name: str
    annual_revenue: Optional[float] = None
    industry: Optional[str] = None
    api_url: str = Field(..., description="Agent/API URL of the company")


# ========== INQUIRIES ==========
class CreditInquiry(BaseModel):
    """Credit Inquiry sent to Credit Bureau by Bank"""
    company_id: str

class ESGInquiry(BaseModel):
    """ESG Inquiry sent to ESG Regulator by Company"""
    bank_id: str

class MarketInquiry(BaseModel):
    """Market Inquiry sent to Market Data provider by Bank"""
    company_id: str


# ========== AGENT CARDS ==========
class WFAPCompanyCard(BaseModel):
    """A2A Agent Card for Company Agent"""
    agent_id: str = Field(default_factory=lambda: "wfap-company-" + str(uuid.uuid4()))
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
    agent_id: str = Field(default_factory=lambda: "wfap-bank-" + str(uuid.uuid4()))
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
