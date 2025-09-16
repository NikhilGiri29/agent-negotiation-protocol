import asyncio
from fastapi import HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain.schema import HumanMessage
from langchain.prompts import PromptTemplate
import json
import random
from typing import Dict, Any
from datetime import datetime, timedelta
from shared.schemas import CreditIntent, CreditOffer, ESGScore
from shared.config import config, BankConfig
import logging

logger = logging.getLogger(__name__)

class BankFinanceAgent:
    def __init__(self, bank_config: BankConfig):
        self.bank_config = bank_config
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=config.GEMINI_API_KEY,
            temperature=0.4
        )
        
        self.tools = [
            Tool(
                name="assess_credit_risk",
                description="Assess credit risk for a loan application",
                func=self._assess_credit_risk
            ),
            Tool(
                name="calculate_esg_score",
                description="Calculate ESG score and generate sustainability summary",
                func=self._calculate_esg_score
            ),
            Tool(
                name="determine_pricing",
                description="Determine loan pricing based on risk and ESG factors",
                func=self._determine_pricing
            )
        ]
    
    async def process_credit_intent(self, intent: CreditIntent) -> CreditOffer:
        """Process credit intent and generate offer"""
        try:
            logger.info(f"Bank {self.bank_config.bank_name} processing credit request for {intent.company_name}")
            
            # Step 1: Verify identity (simulated)
            identity_verified = await self._verify_company_identity(intent)
            if not identity_verified:
                raise ValueError("Company identity verification failed")
            
            # Step 2: Assess credit risk
            risk_assessment = await self._assess_credit_risk(intent)
            
            # Step 3: Calculate ESG score
            esg_score = await self._calculate_esg_score(intent)
            
            # Step 4: Determine pricing
            pricing = await self._determine_pricing(intent, risk_assessment, esg_score)
            
            # Step 5: Generate offer
            offer = await self._generate_offer(intent, risk_assessment, esg_score, pricing)
            
            logger.info(f"Generated offer {offer.offer_id} with rate {offer.carbon_adjusted_rate}%")
            return offer
            
        except Exception as e:
            logger.error(f"Error processing credit intent: {e}")
            raise e
    
    async def _verify_company_identity(self, intent: CreditIntent) -> bool:
        """Simulate company identity verification"""
        # In real implementation, this would:
        # - Verify digital signatures
        # - Check company registry
        # - Validate business documents
        
        # For hackathon, always return True with random delay
        await asyncio.sleep(random.uniform(0.5, 1.5))
        return True
    
    async def _assess_credit_risk(self, intent: CreditIntent) -> Dict[str, Any]:
        """Assess credit risk using LLM and bank's risk appetite"""
        
        prompt = f"""
        As a {self.bank_config.risk_appetite} bank's risk assessment AI, evaluate this credit application:
        
        Company: {intent.company_name}
        Industry: {intent.industry or 'Unknown'}
        Requested Amount: ${intent.amount:,.2f}
        Duration: {intent.duration_months} months
        Purpose: {intent.purpose}
        Annual Revenue: ${intent.annual_revenue or 0:,.2f}
        
        Provide a detailed risk assessment including:
        1. Overall risk rating (low/medium/high)
        2. Key risk factors
        3. Mitigating factors
        4. Recommended maximum exposure
        5. Confidence score (0-100)
        
        Format the response as a JSON object.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        risk_assessment = json.loads(response.content)
        
        return risk_assessment
    
    async def _calculate_esg_score(self, intent: CreditIntent) -> ESGScore:
        """Calculate ESG score based on company data and preferences"""
        prompt = f"""
        As an ESG analyst, evaluate this company's sustainability profile:
        
        Company: {intent.company_name}
        Industry: {intent.industry or 'Unknown'}
        ESG Preferences:
        - Environmental Focus: {intent.esg_preferences.environmental_focus}
        - Social Impact: {intent.esg_preferences.social_impact}
        - Governance Standards: {intent.esg_preferences.governance_standards}
        
        Provide an ESG assessment including:
        1. Environmental score (0-100)
        2. Social score (0-100)
        3. Governance score (0-100)
        4. Key sustainability initiatives
        5. Areas for improvement
        
        Format the response as a JSON object.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        esg_data = json.loads(response.content)
        
        return ESGScore(
            environmental=esg_data['environmental_score'],
            social=esg_data['social_score'],
            governance=esg_data['governance_score'],
            initiatives=esg_data['key_sustainability_initiatives'],
            improvements=esg_data['areas_for_improvement']
        )
    
    async def _determine_pricing(
        self, 
        intent: CreditIntent, 
        risk_assessment: Dict[str, Any], 
        esg_score: ESGScore
    ) -> Dict[str, float]:
        """Calculate loan pricing based on risk and ESG factors"""
        
        # Base rate adjustment based on risk rating
        risk_adjustments = {
            'low': -0.25,
            'medium': 0.0,
            'high': 0.50
        }
        
        risk_adjustment = risk_adjustments.get(
            risk_assessment['risk_rating'].lower(), 
            0.0
        )
        
        # ESG score adjustment
        avg_esg_score = (esg_score.environmental + esg_score.social + esg_score.governance) / 3
        esg_adjustment = (100 - avg_esg_score) / 100 * self.bank_config.esg_multiplier
        
        # Calculate final rates
        base_rate = self.bank_config.base_rate
        risk_adjusted_rate = base_rate + risk_adjustment
        carbon_adjusted_rate = risk_adjusted_rate - esg_adjustment
        
        return {
            'base_rate': base_rate,
            'risk_adjusted_rate': risk_adjusted_rate,
            'carbon_adjusted_rate': carbon_adjusted_rate,
            'risk_adjustment': risk_adjustment,
            'esg_adjustment': esg_adjustment
        }
    
    async def _generate_offer(
        self, 
        intent: CreditIntent,
        risk_assessment: Dict[str, Any],
        esg_score: ESGScore,
        pricing: Dict[str, float]
    ) -> CreditOffer:
        """Generate final credit offer"""
        
        # Calculate offer expiry
        expiry = datetime.now() + timedelta(days=7)
        
        return CreditOffer(
            offer_id=f"{self.bank_config.bank_id}-{int(datetime.now().timestamp())}",
            bank_id=self.bank_config.bank_id,
            bank_name=self.bank_config.bank_name,
            intent_id=intent.intent_id,
            amount=min(intent.amount, risk_assessment['recommended_maximum_exposure']),
            duration_months=intent.duration_months,
            base_rate=pricing['base_rate'],
            risk_adjusted_rate=pricing['risk_adjusted_rate'],
            carbon_adjusted_rate=pricing['carbon_adjusted_rate'],
            risk_assessment=risk_assessment,
            esg_score=esg_score,
            expires_at=expiry
        )

# Add main block for running the agent directly
if __name__ == "__main__":
    import argparse
    import uvicorn
    from fastapi import FastAPI
    
    parser = argparse.ArgumentParser(description='Start Bank Agent')
    parser.add_argument('--bank-id', required=True, help='Bank ID')
    parser.add_argument('--port', type=int, required=True, help='Port number')
    args = parser.parse_args()
    
    # Find bank config
    bank_config = next(
        (bank for bank in config.BANKS if bank.bank_id == args.bank_id),
        None
    )
    
    if not bank_config:
        raise ValueError(f"No configuration found for bank {args.bank_id}")
    
    # Create FastAPI app and bank agent
    app = FastAPI(title=f"WFAP Bank Agent - {bank_config.bank_name}")
    bank_agent = BankFinanceAgent(bank_config)
    
    # Add routes
    @app.post("/credit/assess")
    async def assess_credit(intent_data: Dict):
        """Process credit assessment request"""
        try:
            # Convert the serialized data back to CreditIntent
            intent = CreditIntent(
                **{k: v for k, v in intent_data.items() if k != 'timestamp'}
            )
            
            # Process the request
            offer = await bank_agent.process_credit_intent(intent)
            
            # Serialize the response
            return {
                **offer.model_dump(),
                'timestamp': datetime.now().isoformat(),
                'expiry': offer.expiry.isoformat() if hasattr(offer, 'expiry') else None
            }
            
        except Exception as e:
            logger.error(f"Error processing credit assessment: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=args.port)