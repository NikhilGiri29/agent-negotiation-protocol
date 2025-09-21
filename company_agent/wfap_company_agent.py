import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import asyncio

from shared.a2a_agent import A2AAgent
from shared.a2a_schema import (
    AgentRole,
    MessageType,
    AgentSkill,
    AgentEndpoint,
    AgentMessage,
    DiscoveryRequest
)
from shared.schema import (
    CreditIntent,
    CreditOffer,
    ESGPreferences,
    OfferEvaluation,
    Company
)
from shared.config import config

class WFAPCompanyAgent(A2AAgent):
    """WFAP Company Agent implementation with A2A protocol support"""

    def __init__(self, company_data: Company):
        super().__init__(
            agent_id=f"company-{company_data.company_id.lower()}",
            name=f"{company_data.company_name} Agent",
            role=AgentRole.COMPANY,
            description="WFAP Company Agent for credit discovery and evaluation"
        )
        self.company = company_data
        self.active_intents: Dict[str, CreditIntent] = {}
        self.received_offers: Dict[str, List[CreditOffer]] = {}
        self.initialize_capabilities()
        self.logger.info(f"Initialized WFAP Company Agent for {company_data.company_name}")

    def initialize_capabilities(self):
        """Initialize company agent specific capabilities"""
        # Add skills
        skills = [
            AgentSkill(
                skill_name="credit_intent_creation",
                description="Create and send credit intents to banks",
                parameters=None
            ),
            AgentSkill(
                skill_name="offer_evaluation",
                description="Evaluate and compare credit offers",
                parameters={
                    "evaluation_criteria": [
                        "interest_rate",
                        "esg_score",
                        "processing_fee",
                        "terms_flexibility"
                    ]
                }
            )
        ]
        for skill in skills:
            self.add_skill(skill)

        # Add endpoints
        self.add_endpoint(
            AgentEndpoint(
                url=f"http://localhost:{config.COMPANY_AGENT_PORT}/a2a",
                authentication_required=True
            )
        )

        # Add supported message types
        self.support_message_type(MessageType.CREDIT_OFFER)
        self.support_message_type(MessageType.CREDIT_INTENT)

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
        if message.message_type == MessageType.CREDIT_OFFER:
            return await self._handle_credit_offer(message)
        else:
            return await super().handle_message(message)

    async def create_credit_intent(
        self,
        amount: float,
        duration_months: int,
        purpose: str,
        esg_preferences: Optional[ESGPreferences] = None
    ) -> str:
        """Create and broadcast a credit intent to banks"""
        try:
            # Create intent
            intent = CreditIntent(
                company_id=self.company.company_id,
                company_name=self.company.company_name,
                amount=amount,
                duration_months=duration_months,
                purpose=purpose,
                annual_revenue=self.company.annual_revenue,
                industry=self.company.industry,
                esg_preferences=esg_preferences or ESGPreferences()
            )

            self.logger.info(f"Created credit intent {intent.intent_id}")
            self.active_intents[intent.intent_id] = intent

            # Discover banks
            bank_agents = await self._discover_banks()
            if not bank_agents:
                self.logger.error("No banks found for credit intent")
                return None

            # Broadcast to banks
            tasks = []
            for bank in bank_agents:
                tasks.append(
                    self.send_message(
                        recipient_id=bank.agent_id,
                        recipient_role=AgentRole.BANK,
                        message_type=MessageType.CREDIT_INTENT,
                        payload=intent.dict(),
                        conversation_id=intent.intent_id
                    )
                )

            # Wait for all messages to be sent
            results = await asyncio.gather(*tasks)
            success_count = sum(1 for success, _ in results if success)
            self.logger.info(f"Sent credit intent to {success_count}/{len(tasks)} banks")

            return intent.intent_id

        except Exception as e:
            self.logger.error(f"Error creating credit intent: {str(e)}")
            return None

    async def _handle_credit_offer(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle received credit offers"""
        try:
            # Parse offer
            offer = CreditOffer(**message.payload)
            
            # Store offer
            if offer.intent_id not in self.received_offers:
                self.received_offers[offer.intent_id] = []
            self.received_offers[offer.intent_id].append(offer)
            
            self.logger.info(
                f"Received offer {offer.offer_id} from {offer.bank_name} "
                f"for intent {offer.intent_id}"
            )

            # Evaluate offer
            evaluation = await self._evaluate_offer(offer)
            
            return {
                "status": "success",
                "message": "Offer received and evaluated",
                "evaluation": evaluation.dict()
            }

        except Exception as e:
            self.logger.error(f"Error handling credit offer: {str(e)}")
            return {
                "status": "error",
                "message": f"Internal error: {str(e)}"
            }

    async def _evaluate_offer(self, offer: CreditOffer) -> OfferEvaluation:
        """Evaluate a credit offer"""
        # Get original intent
        intent = self.active_intents.get(offer.intent_id)
        if not intent:
            self.logger.warning(f"No matching intent found for offer {offer.offer_id}")
            return OfferEvaluation(
                offer_id=offer.offer_id,
                total_score=0,
                financial_score=0,
                esg_score=0,
                terms_score=0,
                recommendation="reject",
                reasoning="No matching credit intent found"
            )

        # Calculate financial score (40% weight)
        financial_score = self._calculate_financial_score(offer, intent)

        # Calculate ESG score (30% weight)
        esg_score = self._calculate_esg_score(offer, intent)

        # Calculate terms score (30% weight)
        terms_score = self._calculate_terms_score(offer, intent)

        # Calculate total score
        total_score = (
            0.4 * financial_score +
            0.3 * esg_score +
            0.3 * terms_score
        )

        # Determine recommendation
        if total_score >= 80:
            recommendation = "accept"
            reasoning = "Excellent offer with favorable terms and strong ESG alignment"
        elif total_score >= 60:
            recommendation = "negotiate"
            reasoning = "Good offer but some terms could be improved"
        else:
            recommendation = "reject"
            reasoning = "Offer does not meet minimum requirements"

        return OfferEvaluation(
            offer_id=offer.offer_id,
            total_score=total_score,
            financial_score=financial_score,
            esg_score=esg_score,
            terms_score=terms_score,
            recommendation=recommendation,
            reasoning=reasoning
        )

    def _calculate_financial_score(self, offer: CreditOffer, intent: CreditIntent) -> float:
        """Calculate financial aspects score"""
        score = 100.0
        
        # Amount match
        amount_ratio = offer.approved_amount / intent.amount
        if amount_ratio < 0.8:
            score -= 30
        elif amount_ratio < 0.9:
            score -= 15

        # Interest rate evaluation
        if offer.interest_rate > 8:
            score -= 30
        elif offer.interest_rate > 6:
            score -= 15
        elif offer.interest_rate > 4:
            score -= 5

        # Processing fee impact
        fee_percentage = (offer.processing_fee / offer.approved_amount) * 100
        if fee_percentage > 1:
            score -= 20
        elif fee_percentage > 0.5:
            score -= 10

        return max(0, min(100, score))

    def _calculate_esg_score(self, offer: CreditOffer, intent: CreditIntent) -> float:
        """Calculate ESG alignment score"""
        score = 100.0
        
        # ESG score alignment
        if offer.esg_score.overall_score < intent.esg_preferences.min_esg_score:
            score -= 40
        
        # Carbon footprint alignment
        if (intent.esg_preferences.carbon_neutral_preference and 
            offer.esg_score.carbon_footprint_category != "low"):
            score -= 30

        # Social and governance alignment
        social_diff = abs(
            offer.esg_score.social_score - 
            (intent.esg_preferences.social_impact_weight * 10)
        )
        governance_diff = abs(
            offer.esg_score.governance_score - 
            (intent.esg_preferences.governance_weight * 10)
        )
        score -= (social_diff + governance_diff) * 2

        return max(0, min(100, score))

    def _calculate_terms_score(self, offer: CreditOffer, intent: CreditIntent) -> float:
        """Calculate terms and conditions score"""
        score = 100.0

        # Collateral requirement
        if offer.collateral_required:
            score -= 20

        # Early repayment penalty
        if offer.early_repayment_penalty:
            score -= 15

        # Grace period
        if offer.grace_period_days < 15:
            score -= 10
        elif offer.grace_period_days < 30:
            score -= 5

        # Repayment schedule flexibility
        if offer.repayment_schedule != "monthly":
            score -= 10

        # Offer validity
        days_valid = (offer.offer_valid_until - datetime.utcnow()).days
        if days_valid < 3:
            score -= 20
        elif days_valid < 7:
            score -= 10

        return max(0, min(100, score))

    async def _discover_banks(self) -> List[Any]:
        """Discover available bank agents"""
        try:
            success, response = await self.send_message(
                recipient_id="registry",
                recipient_role=AgentRole.REGISTRY,
                message_type=MessageType.DISCOVERY,
                payload=DiscoveryRequest(
                    requesting_agent_id=self.agent_id,
                    required_role=AgentRole.BANK
                ).dict()
            )

            if success and response and "agents" in response:
                return response["agents"]
            return []

        except Exception as e:
            self.logger.error(f"Error discovering banks: {str(e)}")
            return []
