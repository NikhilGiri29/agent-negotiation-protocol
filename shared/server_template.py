#!/usr/bin/env python3
"""
Unified Server Template for Banks and Companies
"""
import sys
import os
from fastapi import FastAPI, HTTPException
from typing import Dict, Any, Optional
import uvicorn
import logging

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from shared.config import config
from shared.dynamic_loader import get_bank_by_id, load_companies_from_csv
from shared.schema import WFAPBankCard, WFAPCompanyCard

# Setup logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class UnifiedServer:
    """Unified server that can handle both banks and companies"""
    
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type  # 'bank' or 'company'
        self.entity_id = entity_id
        self.entity_data = None
        self.port = None
        
        # Load entity data
        if entity_type == 'bank':
            self.entity_data = get_bank_by_id(entity_id)
            if not self.entity_data:
                raise ValueError(f"Bank {entity_id} not found in CSV data")
            self.port = self.entity_data.port
        elif entity_type == 'company':
            companies = load_companies_from_csv()
            self.entity_data = next((c for c in companies if c.company_id == entity_id), None)
            if not self.entity_data:
                raise ValueError(f"Company {entity_id} not found in CSV data")
            self.port = int(self.entity_data.api_url.split(':')[2].split('/')[0])
        else:
            raise ValueError(f"Invalid entity type: {entity_type}")
        
        # Create FastAPI app
        self.app = FastAPI(
            title=f"WFAP {self.entity_data.bank_name if entity_type == 'bank' else self.entity_data.company_name} Agent",
            version="1.0.0"
        )
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes based on entity type"""
        
        # Common routes
        @self.app.get("/a2a/health")
        async def health_check():
            """Health check endpoint"""
            if self.entity_type == 'bank':
                return {
                    "status": "healthy",
                    "entity_type": "bank",
                    "bank_id": self.entity_data.bank_id,
                    "bank_name": self.entity_data.bank_name,
                    "port": self.port
                }
            else:
                return {
                    "status": "healthy",
                    "entity_type": "company",
                    "company_id": self.entity_data.company_id,
                    "company_name": self.entity_data.company_name,
                    "port": self.port
                }
        
        @self.app.get("/a2a/card")
        async def get_agent_card():
            """Return agent card for A2A discovery"""
            if self.entity_type == 'bank':
                card = WFAPBankCard(
                    agent_id=f"wfap-bank-{self.entity_data.bank_id.lower()}",
                    name=f"WFAP {self.entity_data.bank_name} Agent",
                    endpoints=[f"http://localhost:{self.port}/a2a"],
                    bank_details={
                        "bank_id": self.entity_data.bank_id,
                        "bank_name": self.entity_data.bank_name,
                        "max_loan_amount": self.entity_data.max_loan_amount,
                        "min_interest_rate": self.entity_data.min_interest_rate,
                        "reputation_score": self.entity_data.reputation_score,
                        "risk_appetite": self.entity_data.risk_appetite
                    }
                )
            else:
                card = WFAPCompanyCard(
                    endpoints=[f"http://localhost:{self.port}/a2a"]
                )
            
            return card.dict()
        
        # Bank-specific routes
        if self.entity_type == 'bank':
            @self.app.get("/wfap/status")
            async def get_bank_status():
                """Get bank status"""
                return {
                    "entity_type": "bank",
                    "bank_id": self.entity_data.bank_id,
                    "bank_name": self.entity_data.bank_name,
                    "max_loan_amount": self.entity_data.max_loan_amount,
                    "min_interest_rate": self.entity_data.min_interest_rate,
                    "reputation_score": self.entity_data.reputation_score,
                    "risk_appetite": self.entity_data.risk_appetite,
                    "port": self.port
                }
            
            @self.app.post("/wfap/assess-credit")
            async def assess_credit_direct(intent_data: Dict[str, Any]):
                """Direct credit assessment endpoint"""
                try:
                    # Import here to avoid circular imports
                    from bank_agents.bank_agent import BankFinanceAgent
                    from shared.schema import CreditIntent
                    
                    intent = CreditIntent(**intent_data)
                    bank_agent = BankFinanceAgent(self.entity_data)
                    offer = await bank_agent.process_credit_intent(intent)
                    return {"status": "success", "offer": offer.model_dump()}
                except Exception as e:
                    logger.error(f"Error in credit assessment: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
        
        # Company-specific routes
        else:
            @self.app.get("/wfap/status")
            async def get_company_status():
                """Get company status"""
                return {
                    "entity_type": "company",
                    "company_id": self.entity_data.company_id,
                    "company_name": self.entity_data.company_name,
                    "annual_revenue": self.entity_data.annual_revenue,
                    "industry": self.entity_data.industry,
                    "port": self.port
                }
            
            @self.app.post("/wfap/discover-banks")
            async def discover_banks():
                """Discover available bank agents"""
                try:
                    # Import here to avoid circular imports
                    from company_agent.agent import company_agent
                    result = await company_agent.discover_bank_agents()
                    return result
                except Exception as e:
                    logger.error(f"Error discovering banks: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
            
            @self.app.post("/wfap/broadcast-intent")
            async def broadcast_intent(intent_data: Dict[str, Any]):
                """Broadcast credit intent to all bank agents"""
                try:
                    # Import here to avoid circular imports
                    from company_agent.agent import company_agent
                    from shared.schema import CreditIntent
                    
                    intent = CreditIntent(**intent_data)
                    offers = await company_agent.broadcast_credit_intent(intent)
                    return {
                        "status": "success",
                        "offers": [offer.dict() for offer in offers],
                        "count": len(offers)
                    }
                except Exception as e:
                    logger.error(f"Error broadcasting intent: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
    
    def run(self):
        """Run the server"""
        entity_name = self.entity_data.bank_name if self.entity_type == 'bank' else self.entity_data.company_name
        logger.info(f"Starting {entity_name} ({self.entity_id}) on port {self.port}")
        
        uvicorn.run(
            self.app,
            host="localhost",
            port=self.port,
            log_level=config.LOG_LEVEL.lower()
        )

def start_entity_server(entity_type: str, entity_id: str):
    """Start a server for the given entity"""
    try:
        server = UnifiedServer(entity_type, entity_id)
        server.run()
        return True
    except Exception as e:
        print(f"ERROR: Failed to start {entity_type} {entity_id}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python server_template.py <entity_type> <entity_id>")
        print("Examples:")
        print("  python server_template.py bank B001")
        print("  python server_template.py company cmp123")
        sys.exit(1)
    
    entity_type = sys.argv[1].lower()
    entity_id = sys.argv[2]
    
    if entity_type not in ['bank', 'company']:
        print("ERROR: entity_type must be 'bank' or 'company'")
        sys.exit(1)
    
    success = start_entity_server(entity_type, entity_id)
    sys.exit(0 if success else 1)

