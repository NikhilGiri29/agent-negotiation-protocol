import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid

from shared.a2a_agent import A2AAgent
from shared.a2a_schema import (
    AgentRole,
    MessageType,
    AgentSkill,
    AgentEndpoint,
    AgentMessage
)
from shared.schema import (
    CreditIntent,
    CreditOffer,
    ESGScore,
    CreditBureau,
    MarketData,
    Bank
)
from shared.config import BankConfig

class WFAPBankAgent(A2AAgent):
    """WFAP Bank Agent implementation with A2A protocol support"""

    def __init__(self, config: BankConfig):
        super().__init__(
            agent_id=f"bank-{config.bank_id.lower()}",
            name=config.bank_name,
            role=AgentRole.BANK,
            description="WFAP Bank Agent for credit assessment and offer generation"
        )
        self.config = config
        self.initialize_capabilities()
        self.logger.info(f"Initialized WFAP Bank Agent for {config.bank_name}")

    def initialize_capabilities(self):
        """Initialize bank agent specific capabilities"""
        # Add skills
        skills = [
            AgentSkill(
                skill_name="credit_assessment",
                description="Assess credit applications and generate offers",
                parameters={
                    "max_loan_amount": self.config.base_rate,
                    "base_rate": self.config.base_rate,
                    "risk_appetite": self.config.risk_appetite
                }
            ),
            AgentSkill(
                skill_name="esg_scoring",
                description="Evaluate ESG factors and adjust rates",
                parameters={
                    "esg_multiplier": self.config.esg_multiplier
                }
            )
        ]
        for skill in skills:
            self.add_skill(skill)

        # Add endpoints
        self.add_endpoint(
            AgentEndpoint(
                url=f"http://localhost:{self.config.port}/a2a",
                authentication_required=True
            )
        )

        # Add supported message types
        self.support_message_type(MessageType.CREDIT_INTENT)
        self.support_message_type(MessageType.CREDIT_OFFER)

    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """Handle incoming A2A messages"""
        # First validate using parent class
        validation_result = await super().validate_message(message)
        if not validation_result.is_valid:
            return {
                "status": "error",
                "errors": [e.dict() for e in validation_result.errors]
            }

        # Handle specific message types
        if message.message_type == MessageType.CREDIT_INTENT:
            return await self._handle_credit_intent(message)
        else:
            return await super().handle_message(message)

    async def _handle_credit_intent(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle credit intent message and generate offer"""
        try:
            # Parse credit intent
            credit_intent = CreditIntent(**message.payload)
            self.logger.info(f"Processing credit intent {credit_intent.intent_id}")

            # Get credit bureau data
            credit_data = await self._get_credit_data(credit_intent.company_id)
            if not credit_data:
                return {
                    "status": "error",
                    "message": "Unable to retrieve credit data"
                }

            # Get market data
            market_data = await self._get_market_data(credit_intent.company_id)
            if not market_data:
                return {
                    "status": "error",
                    "message": "Unable to retrieve market data"
                }

            # Generate credit offer
            offer = await self._generate_credit_offer(credit_intent, credit_data, market_data)
            
            # Send response
            response_payload = {
                "status": "success",
                "offer": offer.dict()
            }

            self.logger.info(f"Generated offer {offer.offer_id} for intent {credit_intent.intent_id}")
            return response_payload

        except Exception as e:
            self.logger.error(f"Error processing credit intent: {str(e)}")
            return {
                "status": "error",
                "message": f"Internal error: {str(e)}"
            }

    async def _get_credit_data(self, company_id: str) -> Optional[CreditBureau]:
        """Retrieve credit data from credit bureau"""
        try:
            # Send message to credit bureau
            success, response = await self.send_message(
                recipient_id="credit-bureau",
                recipient_role=AgentRole.CREDIT_BUREAU,
                message_type=MessageType.CREDIT_INTENT,
                payload={"company_id": company_id}
            )

            if success and response and "credit_data" in response:
                return CreditBureau(**response["credit_data"])
            return None

        except Exception as e:
            self.logger.error(f"Error getting credit data: {str(e)}")
            return None

    async def _get_market_data(self, company_id: str) -> Optional[MarketData]:
        """Retrieve market data"""
        try:
            # Send message to market data provider
            success, response = await self.send_message(
                recipient_id="market-data",
                recipient_role=AgentRole.MARKET_DATA,
                message_type=MessageType.CREDIT_INTENT,
                payload={"company_id": company_id}
            )

            if success and response and "market_data" in response:
                return MarketData(**response["market_data"])
            return None

        except Exception as e:
            self.logger.error(f"Error getting market data: {str(e)}")
            return None

    async def _generate_credit_offer(
        self,
        intent: CreditIntent,
        credit_data: CreditBureau,
        market_data: MarketData
    ) -> CreditOffer:
        """Generate credit offer based on intent and data"""
        # Calculate base rate
        base_rate = self.config.base_rate
        
        # Adjust for credit score
        if credit_data.credit_score >= 750:
            rate_adjustment = -0.5
        elif credit_data.credit_score >= 650:
            rate_adjustment = 0
        else:
            rate_adjustment = 0.5
        
        # Adjust for market conditions
        if market_data.is_public and market_data.pe_ratio:
            if market_data.pe_ratio < 10:
                market_adjustment = 0.3
            elif market_data.pe_ratio > 20:
                market_adjustment = -0.2
            else:
                market_adjustment = 0
        else:
            market_adjustment = 0.1  # Private company premium
        
        # Calculate final rate
        final_rate = base_rate + rate_adjustment + market_adjustment
        
        # ESG adjustment
        esg_rate = final_rate * self.config.esg_multiplier
        
        # Generate offer
        return CreditOffer(
            offer_id=str(uuid.uuid4()),
            bank_id=self.config.bank_id,
            bank_name=self.config.bank_name,
            intent_id=intent.intent_id,
            approved_amount=min(intent.amount, self.config.max_loan_amount),
            interest_rate=final_rate,
            carbon_adjusted_rate=esg_rate,
            processing_fee=0.1 * intent.amount,  # 0.1% processing fee
            collateral_required=intent.amount > 1_000_000,
            esg_score=ESGScore(
                environmental_score=8.5,
                social_score=7.5,
                governance_score=9.0,
                overall_score=8.3,
                carbon_footprint_category="low",
                sustainability_notes="Strong ESG performance"
            ),
            esg_summary="Favorable ESG profile with strong governance",
            offer_valid_until=datetime.utcnow() + timedelta(days=7),
            regulatory_compliance={
                "kyc_verified": True,
                "compliance_checks_passed": True
            },
            risk_assessment={
                "risk_score": "moderate",
                "risk_factors": ["market_volatility", "industry_cycle"]
            }
        )
