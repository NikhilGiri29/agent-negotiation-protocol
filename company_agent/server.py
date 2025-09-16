from datetime import datetime
from fastapi import FastAPI, HTTPException
# from a2a.server import Agent
from a2a.types import Task, AgentCard
import asyncio
import aiohttp
from typing import List, Dict, Any
import json
import logging
from shared.schemas import CreditIntent, CreditOffer, WFAPCompanyCard
from shared.config import config
from .agent import company_agent

# Setup logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="WFAP Company Agent", version="1.0.0")

# # A2A Agent setup
# a2a_agent = Agent(
#     name="WFAP-Company-Agent",
#     description="Company finance agent for automated credit discovery",
#     version="1.0.0"
# )

# Agent card for discovery
company_card = WFAPCompanyCard(
    endpoints=[f"http://{config.COMPANY_AGENT_HOST}:{config.COMPANY_AGENT_PORT}/a2a"]
)

class CompanyAgentServer:
    def __init__(self):
        self.discovered_banks: List[Dict] = []
        self.active_tasks: Dict[str, Task] = {}
        
    async def discover_bank_agents(self) -> List[Dict]:
        """Discover available bank agents using A2A discovery"""
        try:
            # In a real implementation, this would query the A2A discovery service
            # For hackathon, we'll simulate discovery
            bank_agents = []
            for bank in config.BANKS:
                bank_agent = {
                    "agent_id": f"wfap-bank-{bank.bank_id.lower()}",
                    "name": f"WFAP {bank.bank_name} Agent", 
                    "endpoint": f"http://localhost:{bank.port}/a2a",
                    "bank_details": {
                        "bank_id": bank.bank_id,
                        "bank_name": bank.bank_name,
                        "base_rate": bank.base_rate,
                        "risk_appetite": bank.risk_appetite,
                        "port": bank.port
                    }
                }
                bank_agents.append(bank_agent)
            
            self.discovered_banks = bank_agents
            logger.info(f"Discovered {len(bank_agents)} bank agents")
            return {
                "banks": bank_agents,
                "count": len(bank_agents),
                "timestamp": datetime.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"Error discovering bank agents: {e}")
            return {
                "banks": [],
                "count": 0,
                "error": str(e)
            }
    
    async def broadcast_credit_intent(self, intent: CreditIntent) -> List[CreditOffer]:
        """Broadcast credit intent to all discovered bank agents"""
        if not self.discovered_banks:
            await self.discover_bank_agents()
        
        offers = []
        tasks = []
        
        # Serialize the intent data
        intent_data = {
            **intent.model_dump(),  # Using model_dump() instead of dict()
            'timestamp': datetime.now().isoformat()
        }
        
        # Create async tasks for each bank
        async with aiohttp.ClientSession() as session:
            for bank in self.discovered_banks:
                task = asyncio.create_task(
                    self.request_offer_from_bank(bank, intent_data)
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            completed_offers = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out errors and collect valid offers
            for offer in completed_offers:
                if isinstance(offer, Exception):
                    logger.error(f"Bank request failed: {str(offer)}")
                elif offer:
                    offers.append(offer)
        
        logger.info(f"Received {len(offers)} offers from {len(self.discovered_banks)} banks")
        return offers
    
    async def request_offer_from_bank(self, bank: Dict, intent_data: Dict) -> CreditOffer:
        """Request credit offer from a specific bank"""
        try:
            bank_details = bank.get('bank_details', {})
            logger.info(f"Requesting offer from {bank_details.get('bank_name', 'Unknown Bank')}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://localhost:{bank_details['port']}/credit/assess",
                    json=intent_data,  # Already serialized data
                    timeout=30
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Bank returned error: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error requesting offer from {bank_details.get('bank_name', 'Unknown Bank')}: {str(e)}")
            return None
    
    async def evaluate_and_select_best_offer(self, offers: List[CreditOffer]) -> Dict[str, Any]:
        """Evaluate all offers and select the best one"""
        if not offers:
            return {"error": "No offers received"}
        
        try:
            # Convert offers to JSON for LangChain agent
            offers_json = json.dumps([offer.dict() for offer in offers], default=str)
            
            # Use LangChain agent to evaluate offers
            evaluation_results = company_agent.evaluate_offers(offers_json)
            evaluations = json.loads(evaluation_results)
            
            if "error" in evaluations:
                return evaluations
            
            # Get the best offer (first in sorted list)
            best_evaluation = evaluations[0]
            best_offer = next(offer for offer in offers if offer.offer_id == best_evaluation["offer_id"])
            
            # Generate decision reasoning
            reasoning = company_agent.generate_decision_reasoning(evaluation_results)
            
            return {
                "best_offer": best_offer.dict(),
                "evaluation": best_evaluation,
                "all_evaluations": evaluations,
                "decision_reasoning": reasoning,
                "total_offers_received": len(offers)
            }
            
        except Exception as e:
            logger.error(f"Error evaluating offers: {e}")
            return {"error": str(e)}
# Setup logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="WFAP Company Agent", version="1.0.0")

# Initialize server
server = CompanyAgentServer()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/db-health")
async def db_health():
    """Database health check endpoint"""
    return {"status": "connected"}

@app.get("/wfap/discover-banks")
async def discover_banks():
    """Discover available bank agents"""
    try:
        result = await server.discover_bank_agents()
        return {
            "status": "success",
            **result
        }
    except Exception as e:
        logger.error(f"Error discovering banks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/wfap/broadcast-intent")
async def broadcast_credit_intent(intent: CreditIntent):
    """Broadcast credit intent to all discovered banks"""
    try:
        offers = await server.broadcast_credit_intent(intent)
        return {
            "status": "success",
            "offers": offers
        }
    except Exception as e:
        logger.error(f"Error broadcasting credit intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wfap/card")
async def get_agent_card():
    """Get agent card for discovery"""
    return company_card

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=config.COMPANY_AGENT_PORT)