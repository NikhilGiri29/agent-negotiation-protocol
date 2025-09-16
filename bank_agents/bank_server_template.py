from fastapi import FastAPI, HTTPException
# from a2a_sdk import Agent
import asyncio
from typing import Dict, Any
import json
import logging
from datetime import datetime
from shared.schemas import CreditIntent, CreditOffer, WFAPBankCard, BankConfig
from shared.config import config
from .bank_agent import create_bank_agent
import uvicorn

# Setup logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class BankAgentServer:
    def __init__(self, bank_config: BankConfig):
        self.bank_config = bank_config
        self.bank_agent = create_bank_agent(bank_config)
        
        # FastAPI app
        self.app = FastAPI(
            title=f"WFAP {bank_config.bank_name} Agent",
            version="1.0.0"
        )
        
        # A2A Agent setup
        # self.a2a_agent = Agent(
        #     name=f"WFAP-{bank_config.bank_id}-Agent",
        #     description=f"{bank_config.bank_name} automated lending agent",
        #     version="1.0.0"
        # )
        
        # Agent card for discovery
        self.agent_card = WFAPBankCard(
            agent_id=f"wfap-bank-{bank_config.bank_id.lower()}",
            name=f"WFAP {bank_config.bank_name} Agent",
            endpoints=[f"http://localhost:{bank_config.port}/a2a"],
            bank_details={
                "bank_id": bank_config.bank_id,
                "bank_name": bank_config.bank_name,
                "base_rate": bank_config.base_rate,
                "risk_appetite": bank_config.risk_appetite
            }
        )
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        # A2A Protocol Endpoints
        @self.app.post("/a2a/task")
        async def handle_a2a_task(task_data: Dict[str, Any]):
            """Handle incoming A2A tasks"""
            try:
                logger.info(f"Received A2A task: {task_data.get('skill', 'unknown')}")
                
                skill = task_data.get("skill")
                input_data = task_data.get("input_data", {})
                
                if skill == "credit_assessment":
                    # Process credit intent
                    intent = CreditIntent(**input_data)
                    offer = await self.bank_agent.process_credit_intent(intent)
                    
                    return {
                        "status": "completed",
                        "skill": skill,
                        "offer_data": offer.dict(),
                        "task_id": task_data.get("task_id"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Unsupported skill: {skill}"
                    }
                    
            except Exception as e:
                logger.error(f"Error handling A2A task: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/a2a/card")
        async def get_agent_card():
            """Return agent card for A2A discovery"""
            return self.agent_card.dict()
        
        @self.app.get("/a2a/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy", 
                "agent": self.agent_card.agent_id,
                "bank": self.bank_config.bank_name
            }
        
        # WFAP Direct Endpoints (for testing)
        @self.app.post("/wfap/assess-credit")
        async def assess_credit_direct(intent: CreditIntent):
            """Direct credit assessment endpoint (bypassing A2A)"""
            try:
                offer = await self.bank_agent.process_credit_intent(intent)
                return {"status": "success", "offer": offer.dict()}
            except Exception as e:
                logger.error(f"Error in direct credit assessment: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/wfap/status")
        async def get_bank_status():
            """Get bank agent status"""
            return {
                "bank_id": self.bank_config.bank_id,
                "bank_name": self.bank_config.bank_name,
                "base_rate": self.bank_config.base_rate,
                "risk_appetite": self.bank_config.risk_appetite,
                "agent_id": self.agent_card.agent_id,
                "endpoint": f"http://localhost:{self.bank_config.port}"
            }
    
    def run(self):
        """Run the bank agent server"""
        logger.info(f"Starting {self.bank_config.bank_name} agent on port {self.bank_config.port}")
        uvicorn.run(
            self.app,
            host="localhost",
            port=self.bank_config.port,
            log_level=config.LOG_LEVEL.lower()
        )

# Individual Bank Server Files
def create_bank_server(bank_config: BankConfig):
    """Factory function to create bank server"""
    return BankAgentServer(bank_config)

# For direct execution
if __name__ == "__main__":
    # This would be customized for each bank
    import sys
    
    if len(sys.argv) > 1:
        bank_id = sys.argv[1].upper()
        bank_config = next(
            (bank for bank in config.BANKS if bank.bank_id == bank_id), 
            None
        )
        if bank_config:
            server = create_bank_server(bank_config)
            server.run()
        else:
            print(f"Unknown bank ID: {bank_id}")
    else:
        print("Usage: python bank_server_template.py <BANK_ID>")
        print("Available banks:", [bank.bank_id for bank in config.BANKS])