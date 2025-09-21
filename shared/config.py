import os
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class BankConfig:
    bank_id: str
    bank_name: str
    max_loan_amount: float
    min_interest_rate: float
    reputation_score: int
    risk_appetite: str  # conservative|moderate|aggressive
    port: int
    
@dataclass
class SystemConfig:
    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "AIzaSyBLT60I7gLU65NA1uYJJfzrL4S-RYN1dV0")
    
    # A2A Configuration
    A2A_DISCOVERY_URL: str = "http://localhost:8000/discovery"
    
    # Company Agent
    COMPANY_AGENT_PORT: int = 8001
    COMPANY_AGENT_HOST: str = "localhost"
    
    # Bank Configurations (loaded dynamically from CSV)
    BANKS: List[BankConfig] = None
    
    # Streamlit UI
    STREAMLIT_PORT: int = 8501
    
    # Logging
    LOG_LEVEL: str = "INFO"

    # Third Party Services (Fixed ports)
    REGISTRY_PORT: int = 8005
    CREDIT_BUREAU_PORT: int = 8006
    ESG_REGUATOR_PORT: int = 8007
    MARKET_INFO_PORT: int = 8008
    
    # Port ranges for dynamic assignment (avoiding third-party ports)
    BANK_PORT_START: int = 9000
    COMPANY_PORT_START: int = 4000

# Global configuration instance
config = SystemConfig()
