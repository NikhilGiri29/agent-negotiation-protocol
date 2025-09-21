from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
import json
import aiohttp
import asyncio
from typing import List, Dict, Any
from shared.schema import CreditIntent, CreditOffer, OfferEvaluation
from shared.config import config
import logging

logger = logging.getLogger(__name__)

class CompanyFinanceAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=config.GEMINI_API_KEY,
            temperature=0.3
        )
        
        self.tools = [
            Tool(
                name="create_credit_intent",
                description="Create a structured credit request based on company needs",
                func=self.create_credit_intent
            ),
            Tool(
                name="evaluate_offers",
                description="Evaluate and rank multiple bank offers using multi-criteria analysis",
                func=self.evaluate_offers
            ),
            Tool(
                name="generate_decision_reasoning", 
                description="Generate human-readable explanation for offer selection",
                func=self.generate_decision_reasoning
            )
        ]
        
        self.agent_prompt = PromptTemplate.from_template("""
        You are a sophisticated AI finance agent representing a company seeking credit facilities.
        Your role is to:
        1. Create optimal credit requests based on company requirements
        2. Evaluate bank offers using financial and ESG criteria
        3. Make data-driven decisions that balance cost, terms, and sustainability
        
        Available tools: {tools}
        Tool names: {tool_names}
        
        Human: {input}
        
        Thought: {agent_scratchpad}
        """)
        
    def create_credit_intent(self, requirements: str) -> str:
        """Create structured credit intent from natural language requirements"""
        prompt = f"""
        Based on these company requirements, create a structured credit intent:
        {requirements}
        
        Consider:
        - Appropriate credit amount and duration
        - Business purpose and industry context  
        - ESG preferences that might reduce borrowing costs
        - Urgency level based on business needs
        
        Return a JSON object with all necessary fields for CreditIntent.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            # Parse and validate the response
            intent_data = json.loads(response.content)
            intent = CreditIntent(**intent_data)
            return json.dumps(intent.dict(), default=str)
        except Exception as e:
            logger.error(f"Error creating credit intent: {e}")
            return json.dumps({"error": str(e)})
    
    def evaluate_offers(self, offers_json: str) -> str:
        """Evaluate multiple bank offers using multi-criteria analysis"""
        try:
            offers_data = json.loads(offers_json)
            offers = [CreditOffer(**offer) for offer in offers_data]
            
            evaluations = []
            for offer in offers:
                evaluation = self._evaluate_single_offer(offer)
                evaluations.append(evaluation)
            
            # Rank offers by total score
            evaluations.sort(key=lambda x: x.total_score, reverse=True)
            
            return json.dumps([eval.dict() for eval in evaluations], default=str)
            
        except Exception as e:
            logger.error(f"Error evaluating offers: {e}")
            return json.dumps({"error": str(e)})
    
    def _evaluate_single_offer(self, offer: CreditOffer) -> OfferEvaluation:
        """Evaluate a single offer using weighted criteria"""
        
        # Financial criteria (40% weight)
        financial_score = self._calculate_financial_score(offer)
        
        # ESG criteria (35% weight)  
        esg_score = self._calculate_esg_score(offer)
        
        # Terms criteria (25% weight)
        terms_score = self._calculate_terms_score(offer)
        
        # Weighted total score
        total_score = (
            financial_score * 0.40 + 
            esg_score * 0.35 + 
            terms_score * 0.25
        )
        
        # Generate recommendation
        recommendation = "accept" if total_score >= 75 else "negotiate" if total_score >= 60 else "reject"
        
        # Generate reasoning using LLM
        reasoning = self._generate_reasoning(offer, financial_score, esg_score, terms_score, total_score)
        
        return OfferEvaluation(
            offer_id=offer.offer_id,
            total_score=total_score,
            financial_score=financial_score,
            esg_score=esg_score,
            terms_score=terms_score,
            recommendation=recommendation,
            reasoning=reasoning
        )
    
    def _calculate_financial_score(self, offer: CreditOffer) -> float:
        """Calculate financial attractiveness score (0-100)"""
        # Lower carbon-adjusted rate is better
        rate_score = max(0, 100 - (offer.carbon_adjusted_rate - 3.0) * 10)
        
        # Higher approved amount is better (up to requested amount)
        amount_score = min(100, (offer.approved_amount / 1000000) * 50)  # Assuming 1M target
        
        # Lower fees are better
        fee_score = max(0, 100 - offer.processing_fee / 1000)
        
        return (rate_score * 0.6 + amount_score * 0.3 + fee_score * 0.1)
    
    def _calculate_esg_score(self, offer: CreditOffer) -> float:
        """Calculate ESG alignment score (0-100)"""
        return offer.esg_score.overall_score * 10  # Convert 0-10 to 0-100
    
    def _calculate_terms_score(self, offer: CreditOffer) -> float:
        """Calculate terms attractiveness score (0-100)"""
        # No collateral is better
        collateral_score = 100 if not offer.collateral_required else 50
        
        # No early repayment penalty is better
        penalty_score = 100 if not offer.early_repayment_penalty else 70
        
        # Longer grace period is better
        grace_score = min(100, offer.grace_period_days * 2)
        
        return (collateral_score * 0.4 + penalty_score * 0.3 + grace_score * 0.3)
    
    def _generate_reasoning(self, offer: CreditOffer, financial_score: float, 
                          esg_score: float, terms_score: float, total_score: float) -> str:
        """Generate human-readable reasoning for the evaluation"""
        
        prompt = f"""
        Generate a concise explanation for why this bank offer received a score of {total_score:.1f}/100:
        
        Bank: {offer.bank_name}
        Financial Score: {financial_score:.1f}/100
        ESG Score: {esg_score:.1f}/100  
        Terms Score: {terms_score:.1f}/100
        
        Key Details:
        - Interest Rate: {offer.interest_rate}% (Carbon-adjusted: {offer.carbon_adjusted_rate}%)
        - Approved Amount: ${offer.approved_amount:,.2f}
        - ESG Overall Score: {offer.esg_score.overall_score}/10
        - Collateral Required: {offer.collateral_required}
        - Processing Fee: ${offer.processing_fee:,.2f}
        
        Provide a 2-3 sentence explanation focusing on the key strengths and weaknesses.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            return f"Standard evaluation based on rate ({offer.carbon_adjusted_rate}%), ESG score ({offer.esg_score.overall_score}/10), and terms."
    
    def generate_decision_reasoning(self, evaluation_results: str) -> str:
        """Generate overall decision reasoning for the best offer"""
        prompt = f"""
        Based on these offer evaluations, provide a clear explanation of why the top-ranked offer 
        was selected and how it aligns with the company's financial and ESG objectives:
        
        {evaluation_results}
        
        Provide a comprehensive but concise explanation suitable for executive review.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error generating decision reasoning: {e}")
            return "Decision based on optimal balance of financial terms, ESG alignment, and contract flexibility."

# Global agent instance
company_agent = CompanyFinanceAgent()