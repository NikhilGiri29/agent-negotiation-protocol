import asyncio
import aiohttp
from fastapi import HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain.schema import HumanMessage
from langchain.prompts import PromptTemplate
import json
import random
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from shared.schema import CreditIntent, CreditOffer, ESGScore, CreditBureau, ESGRegulator, MarketData
from shared.config import config
from shared.dynamic_loader import BankConfig
import logging

logger = logging.getLogger(__name__)

class BankFinanceAgent:
    def __init__(self, bank_config: BankConfig):
        self.bank_config = bank_config
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
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
            print(f"\n{self.bank_config.bank_name} Processing Credit Request")
            print(f"   Company: {intent.company_name} (ID: {intent.company_id})")
            print(f"   Amount: ${intent.amount:,.2f} for {intent.duration_months} months")
            print(f"   Purpose: {intent.purpose}")
            print(f"   Industry: {intent.industry or 'Unknown'}")
            
            # Step 1: Verify identity (simulated)
            print(f"\nStep 1: Verifying company identity...")
            identity_verified = await self._verify_company_identity(intent)
            if not identity_verified:
                raise ValueError("Company identity verification failed")
            print(f"   OK: Identity verified")
            
            # Step 2: Assess credit risk
            print(f"\nStep 2: Assessing credit risk...")
            risk_assessment = await self._assess_credit_risk(intent)
            if risk_assessment is None:
                raise ValueError("Risk assessment returned None")
            print(f"   Risk Rating: {risk_assessment.get('overall_risk_rating', risk_assessment.get('risk_rating', 'unknown'))}")
            print(f"   Confidence: {risk_assessment.get('confidence_score', 0)}/100")
            max_exposure = risk_assessment.get('recommended_maximum_exposure', 0)
            if isinstance(max_exposure, dict):
                max_exposure = max_exposure.get('amount', 0)
                if isinstance(max_exposure, str) and max_exposure.startswith('$'):
                    max_exposure = float(max_exposure.replace('$', '').replace(',', ''))
            print(f"   Max Exposure: ${max_exposure:,.2f}")
            
            # Step 3: Calculate ESG score
            print(f"\nStep 3: Calculating ESG score...")
            esg_score = await self._calculate_esg_score(intent)
            if esg_score is None:
                raise ValueError("ESG score returned None")
            print(f"   Environmental: {esg_score.environmental_score}/10")
            print(f"   Social: {esg_score.social_score}/10")
            print(f"   Governance: {esg_score.governance_score}/10")
            print(f"   Overall: {esg_score.overall_score}/10")
            
            # Step 4: Determine pricing
            print(f"\nStep 4: Determining pricing...")
            pricing = await self._determine_pricing(intent, risk_assessment, esg_score)
            if pricing is None:
                raise ValueError("Pricing returned None")
            print(f"   Base Rate: {pricing.get('base_rate', 0):.2f}%")
            print(f"   Risk Adjustment: {pricing.get('risk_adjustment', 0):+.2f}%")
            print(f"   ESG Adjustment: {pricing.get('esg_adjustment', 0):+.2f}%")
            print(f"   Final Rate: {pricing.get('carbon_adjusted_rate', 0):.2f}%")
            print(f"   Pricing Confidence: {pricing.get('pricing_confidence', 0)}/100")
            
            # Step 5: Generate offer
            print(f"\nStep 5: Generating final offer...")
            offer = await self._generate_offer(intent, risk_assessment, esg_score, pricing)
            
            print(f"\nOFFER GENERATED:")
            print(f"   Offer ID: {offer.offer_id}")
            print(f"   Approved Amount: ${offer.approved_amount:,.2f}")
            print(f"   Interest Rate: {offer.carbon_adjusted_rate:.2f}%")
            print(f"   Duration: {intent.duration_months} months")
            print(f"   Expires: {offer.offer_valid_until.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Pricing Rationale: {pricing.get('pricing_rationale', 'N/A')}")
            
            return offer
            
        except Exception as e:
            print(f"\nERROR: {str(e)}")
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
    
    async def _get_credit_bureau_data(self, company_id: str) -> Optional[CreditBureau]:
        """Get credit bureau data for the company"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://localhost:{config.CREDIT_BUREAU_PORT}/inquiry",
                    json={"company_id": company_id},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return CreditBureau(**data)
                    else:
                        logger.warning(f"Credit bureau returned status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting credit bureau data: {e}")
            return None

    async def _get_esg_regulator_data(self, bank_id: str) -> Optional[ESGRegulator]:
        """Get ESG regulator data for the bank"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://localhost:{config.ESG_REGUATOR_PORT}/inquiry",
                    json={"bank_id": bank_id},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return ESGRegulator(**data)
                    else:
                        logger.warning(f"ESG regulator returned status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting ESG regulator data: {e}")
            return None

    async def _get_market_data(self, company_id: str) -> Optional[MarketData]:
        """Get market data for the company"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://localhost:{config.MARKET_INFO_PORT}/inquiry",
                    json={"company_id": company_id},
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return MarketData(**data)
                    else:
                        logger.warning(f"Market info returned status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None

    async def _assess_credit_risk(self, intent: CreditIntent) -> Dict[str, Any]:
        """Assess credit risk using LLM, bank's risk appetite, and third-party data"""
        
        # Get credit bureau data
        credit_data = await self._get_credit_bureau_data(intent.company_id)
        market_data = await self._get_market_data(intent.company_id)
        
        # Build dynamic prompt with real data
        credit_info = ""
        if credit_data:
            credit_info = f"""
        Credit Bureau Data:
        - Credit Score: {credit_data.credit_score}
        - Rating: {credit_data.rating}
        - History: {credit_data.history_summary}
        """
        
        market_info = ""
        if market_data:
            market_info = f"""
        Market Data:
        - Public Company: {market_data.is_public}
        - Stock Price: ${market_data.weekly_stock_price_hist[-1] if market_data.weekly_stock_price_hist else 'N/A'}
        - Market Cap: ${market_data.market_cap or 'N/A'}
        - P/E Ratio: {market_data.pe_ratio or 'N/A'}
        """
        
        prompt = f"""
        As a {self.bank_config.risk_appetite} bank's risk assessment AI, evaluate this credit application:
        
        Company: {intent.company_name} (ID: {intent.company_id})
        Industry: {intent.industry or 'Unknown'}
        Requested Amount: ${intent.amount:,.2f}
        Duration: {intent.duration_months} months
        Purpose: {intent.purpose}
        Annual Revenue: ${intent.annual_revenue or 0:,.2f}
        {credit_info}
        {market_info}
        
        Bank Profile: {self.bank_config.bank_name} ({self.bank_config.risk_appetite} risk appetite)
        Base Rate: {self.bank_config.min_interest_rate}%
        
        Provide a detailed risk assessment including:
        1. Overall risk rating (low/medium/high)
        2. Key risk factors
        3. Mitigating factors
        4. Recommended maximum exposure
        5. Confidence score (0-100)
        6. Data quality assessment
        
        Format the response as a JSON object.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        logger.info(f"LLM response content: {response.content}")
        
        # Extract JSON from markdown code blocks if present
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        if content.startswith("```"):
            content = content[3:]   # Remove ```
        if content.endswith("```"):
            content = content[:-3]  # Remove trailing ```
        content = content.strip()
        
        try:
            risk_assessment = json.loads(content)
            logger.info(f"Successfully parsed LLM risk assessment: {risk_assessment}")
            
            # Ensure required fields exist
            if 'overall_risk_rating' not in risk_assessment:
                risk_assessment['overall_risk_rating'] = risk_assessment.get('risk_rating', 'medium')
            if 'confidence_score' not in risk_assessment:
                risk_assessment['confidence_score'] = 70
            if 'recommended_maximum_exposure' not in risk_assessment:
                risk_assessment['recommended_maximum_exposure'] = intent.amount
            if 'key_risk_factors' not in risk_assessment:
                risk_assessment['key_risk_factors'] = []
            if 'mitigating_factors' not in risk_assessment:
                risk_assessment['mitigating_factors'] = []
                
        except json.JSONDecodeError as e:
            # Fallback if LLM doesn't return valid JSON
            logger.warning(f"LLM returned invalid JSON: {e}, using fallback risk assessment")
            logger.warning(f"Raw content that failed to parse: {content[:500]}...")
            risk_assessment = {
                "risk_score": 0.6,  # Medium risk
                "risk_level": "medium",
                "risk_rating": "medium",
                "overall_risk_rating": "medium",  # Add this field for compatibility
                "confidence_score": 70,
                "data_quality": "limited",
                "reasoning": "Fallback assessment due to LLM response format issue",
                "recommended_maximum_exposure": 1000000,  # Default to requested amount
                "key_risk_factors": [
                    {
                        "risk": "Limited Data",
                        "description": "Fallback assessment due to LLM response format issue"
                    }
                ],
                "mitigating_factors": [
                    {
                        "factor": "Standard Assessment",
                        "description": "Using standard risk assessment criteria"
                    }
                ]
            }
        
        # Add third-party data to assessment
        risk_assessment['credit_bureau_data'] = credit_data.dict() if credit_data else None
        risk_assessment['market_data'] = market_data.dict() if market_data else None
        
        return risk_assessment
    
    async def _calculate_esg_score(self, intent: CreditIntent) -> ESGScore:
        """Calculate ESG score based on company data, preferences, and bank's ESG profile"""
        
        # Get bank's ESG data from regulator
        bank_esg_data = await self._get_esg_regulator_data(self.bank_config.bank_id)
        
        # Build dynamic prompt with real ESG data
        bank_esg_info = ""
        if bank_esg_data:
            bank_esg_info = f"""
        Bank ESG Profile ({self.bank_config.bank_name}):
        - Environmental Score: {bank_esg_data.environmental_score}/10
        - Social Score: {bank_esg_data.social_score}/10
        - Governance Score: {bank_esg_data.governance_score}/10
        - Overall Score: {bank_esg_data.overall_score}/10
        - Carbon Footprint: {bank_esg_data.carbon_footprint_category}
        - Sustainability Notes: {bank_esg_data.sustainability_notes}
        """
        
        prompt = f"""
        As an ESG analyst, evaluate this company's sustainability profile and alignment with the bank's ESG standards:
        
        Company: {intent.company_name} (ID: {intent.company_id})
        Industry: {intent.industry or 'Unknown'}
        Company ESG Preferences:
        - Minimum ESG Score: {intent.esg_preferences.min_esg_score}/10
        - Carbon Neutral Preference: {intent.esg_preferences.carbon_neutral_preference}
        - Social Impact Weight: {intent.esg_preferences.social_impact_weight}
        - Governance Weight: {intent.esg_preferences.governance_weight}
        {bank_esg_info}
        
        Bank: {self.bank_config.bank_name} (Risk Appetite: {self.bank_config.risk_appetite})
        
        Provide an ESG assessment including:
        1. Environmental score (0-100)
        2. Social score (0-100)
        3. Governance score (0-100)
        4. Overall ESG score (0-100)
        5. ESG alignment with bank standards
        6. Key sustainability initiatives
        7. Areas for improvement
        8. ESG risk factors
        
        Format the response as a JSON object.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        # Extract JSON from markdown code blocks if present
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        if content.startswith("```"):
            content = content[3:]   # Remove ```
        if content.endswith("```"):
            content = content[:-3]  # Remove trailing ```
        content = content.strip()
        
        try:
            esg_data = json.loads(content)
        except json.JSONDecodeError:
            # Fallback if LLM doesn't return valid JSON
            logger.warning("LLM returned invalid JSON for ESG scoring, using fallback")
            esg_data = {
                "environmental_score": 7.5,
                "social_score": 7.0,
                "governance_score": 8.0,
                "overall_score": 7.5,
                "carbon_footprint_category": "medium",
                "sustainability_notes": "Basic ESG compliance with room for improvement"
            }
        
        # Convert scores from 0-100 to 0-10 if needed
        def normalize_score(score):
            if score is None:
                return 0.0
            if isinstance(score, dict):
                return 0.0  # Default for unexpected dict
            if isinstance(score, str):
                try:
                    score = float(score)
                except ValueError:
                    return 0.0
            if isinstance(score, (int, float)) and score > 10:
                return score / 10.0
            return float(score)
        
        return ESGScore(
            environmental_score=normalize_score(esg_data.get('environmental_score', 7.5)),
            social_score=normalize_score(esg_data.get('social_score', 7.0)),
            governance_score=normalize_score(esg_data.get('governance_score', 8.0)),
            overall_score=normalize_score(esg_data.get('overall_score', 7.5)),
            carbon_footprint_category=esg_data.get('carbon_footprint_category', 'medium'),
            sustainability_notes=esg_data.get('sustainability_notes', '')
        )
    
    async def _determine_pricing(
        self, 
        intent: CreditIntent, 
        risk_assessment: Dict[str, Any], 
        esg_score: ESGScore
    ) -> Dict[str, float]:
        """Calculate loan pricing based on risk, ESG factors, and market conditions using LLM"""
        
        prompt = f"""
        As a pricing analyst for {self.bank_config.bank_name}, determine optimal loan pricing for this credit application:
        
        Bank Profile:
        - Bank: {self.bank_config.bank_name}
        - Risk Appetite: {self.bank_config.risk_appetite}
        - Base Rate: {self.bank_config.min_interest_rate}%
        - Max Loan Amount: ${self.bank_config.max_loan_amount:,.2f}
        - Reputation Score: {self.bank_config.reputation_score}/10
        
        Credit Application:
        - Company: {intent.company_name} (ID: {intent.company_id})
        - Amount: ${intent.amount:,.2f}
        - Duration: {intent.duration_months} months
        - Purpose: {intent.purpose}
        - Industry: {intent.industry or 'Unknown'}
        
        Risk Assessment:
        - Risk Rating: {risk_assessment.get('risk_rating', 'medium')}
        - Confidence Score: {risk_assessment.get('confidence_score', 50)}/100
        - Key Risk Factors: {risk_assessment.get('key_risk_factors', 'N/A')}
        - Mitigating Factors: {risk_assessment.get('mitigating_factors', 'N/A')}
        
        ESG Profile:
        - Environmental Score: {esg_score.environmental_score}/10
        - Social Score: {esg_score.social_score}/10
        - Governance Score: {esg_score.governance_score}/10
        - Overall Score: {esg_score.overall_score}/10
        - Carbon Footprint: {esg_score.carbon_footprint_category}
        
        Third-Party Data:
        - Credit Bureau: {risk_assessment.get('credit_bureau_data', {}).get('credit_score', 'N/A')}
        - Market Data: {risk_assessment.get('market_data', {})}
        
        Calculate pricing including:
        1. Base rate (use bank's base rate)
        2. Risk adjustment (positive for high risk, negative for low risk)
        3. ESG adjustment (discount for good ESG, premium for poor ESG)
        4. Final carbon-adjusted rate
        5. Confidence in pricing decision
        
        Format the response as a JSON object with these exact fields:
        - base_rate: float
        - risk_adjustment: float
        - esg_adjustment: float
        - carbon_adjusted_rate: float
        - pricing_confidence: float (0-100)
        - pricing_rationale: string
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()
        except Exception as e:
            logger.warning(f"LLM call failed: {e}, using fallback pricing")
            content = "{}"  # Empty JSON to trigger fallback
        
        # Extract JSON from markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        if content.startswith("```"):
            content = content[3:]   # Remove ```
        if content.endswith("```"):
            content = content[:-3]  # Remove trailing ```
        content = content.strip()
        
        try:
            pricing_data = json.loads(content)
            
            # Ensure required fields exist
            if 'base_rate' not in pricing_data:
                pricing_data['base_rate'] = self.bank_config.min_interest_rate
            if 'risk_adjustment' not in pricing_data:
                pricing_data['risk_adjustment'] = 0.0
            if 'esg_adjustment' not in pricing_data:
                pricing_data['esg_adjustment'] = 0.0
            if 'carbon_adjusted_rate' not in pricing_data:
                pricing_data['carbon_adjusted_rate'] = pricing_data.get('base_rate', self.bank_config.min_interest_rate)
            if 'pricing_confidence' not in pricing_data:
                pricing_data['pricing_confidence'] = 75
            if 'pricing_rationale' not in pricing_data:
                pricing_data['pricing_rationale'] = "Standard pricing calculation"
                
        except json.JSONDecodeError:
            # Fallback if LLM doesn't return valid JSON
            logger.warning("LLM returned invalid JSON for pricing, using fallback")
            pricing_data = {
                "base_rate": self.bank_config.min_interest_rate,
                "risk_adjustment": 0.5,
                "esg_adjustment": -0.2,
                "carbon_adjusted_rate": self.bank_config.min_interest_rate + 0.3,
                "pricing_confidence": 75,
                "pricing_rationale": "Fallback pricing due to LLM response format issue"
            }
        
        # Ensure carbon_adjusted_rate is always positive and reasonable
        if pricing_data.get('carbon_adjusted_rate', 0) <= 0:
            logger.warning(f"Invalid carbon_adjusted_rate: {pricing_data.get('carbon_adjusted_rate')}, setting to minimum")
            pricing_data['carbon_adjusted_rate'] = max(0.1, self.bank_config.min_interest_rate)
        
        # Ensure carbon_adjusted_rate is not too high (max 50%)
        if pricing_data.get('carbon_adjusted_rate', 0) > 50:
            logger.warning(f"Carbon_adjusted_rate too high: {pricing_data.get('carbon_adjusted_rate')}, capping at 50%")
            pricing_data['carbon_adjusted_rate'] = 50.0
        
        return pricing_data
    
    async def _generate_offer(
        self, 
        intent: CreditIntent,
        risk_assessment: Dict[str, Any],
        esg_score: ESGScore,
        pricing: Dict[str, float]
    ) -> CreditOffer:
        """Generate final credit offer with comprehensive data"""
        
        # Calculate offer expiry
        expiry = datetime.now() + timedelta(days=7)
        
        # Determine approved amount based on risk assessment
        max_exposure = risk_assessment.get('recommended_maximum_exposure', intent.amount)
        if isinstance(max_exposure, dict):
            max_exposure = max_exposure.get('amount', intent.amount)
            if isinstance(max_exposure, str) and max_exposure.startswith('$'):
                max_exposure = float(max_exposure.replace('$', '').replace(',', ''))
        approved_amount = min(intent.amount, max_exposure)
        
        # Log the offer generation
        logger.info(f"Generating offer for {intent.company_name}:")
        logger.info(f"  - Requested: ${intent.amount:,.2f}")
        logger.info(f"  - Approved: ${approved_amount:,.2f}")
        logger.info(f"  - Rate: {pricing.get('carbon_adjusted_rate', 0):.2f}%")
        logger.info(f"  - Risk Rating: {risk_assessment.get('overall_risk_rating', risk_assessment.get('risk_rating', 'unknown'))}")
        logger.info(f"  - ESG Score: {getattr(esg_score, 'overall_score', 0)}/10")
        
        # Ensure all required fields are present and valid
        base_rate = pricing.get('base_rate', self.bank_config.min_interest_rate)
        carbon_rate = pricing.get('carbon_adjusted_rate', base_rate)
        
        # Ensure carbon_adjusted_rate is positive
        if carbon_rate <= 0:
            carbon_rate = max(0.1, base_rate)
        
        return CreditOffer(
            offer_id=f"{self.bank_config.bank_id}-{int(datetime.now().timestamp())}",
            bank_id=self.bank_config.bank_id,
            bank_name=self.bank_config.bank_name,
            intent_id=intent.intent_id,
            company_id=intent.company_id,
            company_name=intent.company_name,
            approved_amount=approved_amount,
            interest_rate=base_rate,
            carbon_adjusted_rate=carbon_rate,
            esg_score=esg_score,
            esg_summary=f"Environmental: {esg_score.environmental_score}/10, Social: {esg_score.social_score}/10, Governance: {esg_score.governance_score}/10",
            offer_valid_until=expiry,
            risk_assessment=risk_assessment,
            pricing_rationale=pricing.get('pricing_rationale', ''),
            pricing_confidence=pricing.get('pricing_confidence', 50)
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