#!/usr/bin/env python3
"""
Company Agent - Handles bank discovery and credit intent broadcasting
"""
import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict, Any
from shared.config import config
from shared.schema import CreditIntent, CreditOffer

# Setup logging
logger = logging.getLogger(__name__)

class CompanyAgent:
    """Company agent for discovering banks and broadcasting credit intents"""
    
    def __init__(self):
        self.discovered_banks: List[Dict] = []
        self.registry_url = f"http://localhost:{config.REGISTRY_PORT}"
    
    async def discover_bank_agents(self) -> Dict[str, Any]:
        """Discover available bank agents using registry service"""
        try:
            async with aiohttp.ClientSession() as session:
                discovery_request = {
                    "requesting_agent_id": "company-agent",
                    "required_role": "bank"
                }
                
                async with session.post(
                    f"{self.registry_url}/discovery",
                    json=discovery_request,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        discovery_data = await response.json()
                        bank_agents = discovery_data.get("agents", [])
                        
                        # Filter for bank agents and extract port information
                        filtered_banks = []
                        for agent in bank_agents:
                            if agent.get("role") == "bank":
                                # Extract port from agent api_url
                                api_url = agent.get("api_url", "")
                                if "localhost:" in api_url:
                                    port = int(api_url.split("localhost:")[1].split("/")[0])
                                    # Create base URL without /a2a for WFAP endpoints
                                    base_url = f"http://localhost:{port}"
                                    bank_agent = {
                                        "agent_id": agent.get("agent_id"),
                                        "name": agent.get("name"),
                                        "endpoint": base_url,
                                        "port": port,
                                        "bank_details": agent.get("bank_details", {})
                                    }
                                    filtered_banks.append(bank_agent)
                        
                        self.discovered_banks = filtered_banks
                        logger.info(f"Discovered {len(filtered_banks)} bank agents from registry")
                        return {
                            "banks": filtered_banks,
                            "count": len(filtered_banks),
                            "timestamp": datetime.now().isoformat(),
                            "source": "registry"
                        }
                    else:
                        logger.error(f"Registry discovery failed with status {response.status}")
                        return {
                            "banks": [],
                            "count": 0,
                            "error": "Registry discovery failed",
                            "timestamp": datetime.now().isoformat()
                        }
            
        except Exception as e:
            logger.error(f"Error discovering bank agents: {e}")
            return {
                "banks": [],
                "count": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def broadcast_credit_intent(self, intent: CreditIntent) -> List[CreditOffer]:
        """Broadcast credit intent to all discovered bank agents"""
        # First validate the intent through registry
        validation_result = await self._validate_credit_intent(intent)
        if not validation_result.get('valid', False):
            logger.error(f"Credit intent validation failed: {validation_result.get('errors', [])}")
            raise ValueError(f"Credit intent validation failed: {validation_result.get('message', 'Unknown error')}")
        
        if not self.discovered_banks:
            await self.discover_bank_agents()
        
        if not self.discovered_banks:
            logger.error("No bank agents available for credit intent")
            return []
        
        offers = []
        tasks = []
        
        # Create tasks for all bank agents
        for bank in self.discovered_banks:
            task = asyncio.create_task(
                self._send_credit_intent_to_bank(bank, intent)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error with bank {self.discovered_banks[i]['name']}: {result}")
            elif result:
                offers.append(result)
        
        logger.info(f"Received {len(offers)} offers from {len(self.discovered_banks)} banks")
        return offers
    
    async def _validate_credit_intent(self, intent: CreditIntent) -> Dict[str, Any]:
        """Validate credit intent through registry service"""
        try:
            # Convert datetime to ISO string for JSON serialization
            intent_data = intent.model_dump()
            intent_data['timestamp'] = intent.timestamp.isoformat()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.registry_url}/validate-credit-intent",
                    json=intent_data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Registry validation failed with status {response.status}")
                        return {"valid": False, "errors": ["Registry validation failed"]}
        except Exception as e:
            logger.error(f"Error validating credit intent: {e}")
            return {"valid": False, "errors": [str(e)]}
    
    async def _send_credit_intent_to_bank(self, bank: Dict, intent: CreditIntent) -> CreditOffer:
        """Send credit intent to a specific bank agent"""
        try:
            # Convert datetime to ISO string for JSON serialization
            intent_data = intent.model_dump()
            intent_data['timestamp'] = intent.timestamp.isoformat()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{bank['endpoint']}/wfap/assess-credit",
                    json=intent_data,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "success":
                            return CreditOffer(**data["offer"])
                        else:
                            logger.warning(f"Bank {bank['name']} returned error: {data.get('message')}")
                    else:
                        logger.warning(f"Bank {bank['name']} returned status {response.status}")
        except Exception as e:
            logger.error(f"Error communicating with bank {bank['name']}: {e}")
        
        return None

# Create global instance
company_agent = CompanyAgent()