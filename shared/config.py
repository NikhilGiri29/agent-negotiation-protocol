import os
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class BankConfig:
    bank_id: str
    bank_name: str
    base_rate: float
    esg_multiplier: float
    risk_appetite: str  # conservative|moderate|aggressive
    port: int
    
@dataclass
class SystemConfig:
    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "AIzaSyA-pTSsrB4tSWCvf7nG_x1N20mL7AzDaFQ")
    
    # A2A Configuration
    A2A_DISCOVERY_URL: str = "http://localhost:8000/discovery"
    
    # Company Agent
    COMPANY_AGENT_PORT: int = 8001
    COMPANY_AGENT_HOST: str = "localhost"
    
    # Bank Configurations
    BANKS: List[BankConfig] = None
    
    # Streamlit UI
    STREAMLIT_PORT: int = 8501
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    def __post_init__(self):
        if self.BANKS is None:
            self.BANKS = [
                BankConfig(
                    bank_id="BANK_A",
                    bank_name="GreenTech Bank",
                    base_rate=4.5,
                    esg_multiplier=0.8,  # Lower rates for good ESG
                    risk_appetite="conservative",
                    port=8002
                ),
                BankConfig(
                    bank_id="BANK_B", 
                    bank_name="EcoFinance Corp",
                    base_rate=4.2,
                    esg_multiplier=0.7,
                    risk_appetite="moderate",
                    port=8003
                ),
                BankConfig(
                    bank_id="BANK_C",
                    bank_name="Sustainable Credit Union",
                    base_rate=4.8,
                    esg_multiplier=0.9,
                    risk_appetite="aggressive",
                    port=8004
                )
            ]

# Global configuration instance
config = SystemConfig()