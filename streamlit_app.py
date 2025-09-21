import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from shared.schema import CreditIntent, CreditPurpose, ESGPreferences
from shared.config import config
import asyncio
import aiohttp

# Page configuration
st.set_page_config(
    page_title="WFAP Demo - Wise Finance Agent Protocol",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        text-align: center;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    .offer-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .best-offer {
        border: 2px solid #28a745;
        background: #f8fff9;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-processing {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class WFAPDemo:
    def __init__(self):
        self.registry_url = f"http://localhost:{config.REGISTRY_PORT}"
        self.banks_discovered = False
        
        # Initialize session state
        if 'request_history' not in st.session_state:
            st.session_state.request_history = []
        if 'current_request' not in st.session_state:
            st.session_state.current_request = None
        if 'discovered_banks' not in st.session_state:
            st.session_state.discovered_banks = []
        if 'selected_company' not in st.session_state:
            st.session_state.selected_company = None
        if 'companies' not in st.session_state:
            st.session_state.companies = self.load_companies()
            
    def get_company_agent_url(self):
        """Get the company agent URL for the selected company"""
        if not st.session_state.selected_company:
            return None
        # The api_url includes /a2a, but WFAP endpoints are at the base port
        api_url = st.session_state.selected_company.get('api_url')
        if api_url and '/a2a' in api_url:
            # Extract base URL (remove /a2a)
            base_url = api_url.replace('/a2a', '')
            return base_url
        return api_url
            
    def load_companies(self):
        """Load registered companies from registry"""
        try:
            registry_dir = os.path.join(os.path.dirname(__file__), "data", "registry")
            with open(os.path.join(registry_dir, "registry_companies.json"), 'r') as f:
                companies = json.load(f)
            return companies
        except Exception as e:
            st.error(f"Error loading companies: {str(e)}")
            return {}
    
    def render_header(self):
        """Render main application header"""
        st.markdown("""
        <div class="main-header">
            <h1>🏦 WFAP Demo - Wise Finance Agent Protocol</h1>
            <p style="text-align: center; color: #e8f4f8; margin: 0;">
                AI-Powered Multi-Bank Credit Discovery & Evaluation Platform
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render sidebar with system status and controls"""
        st.sidebar.markdown("## 🎛️ System Control")
        
        # Company Selection
        st.sidebar.markdown("### 🏢 Company Selection")
        companies = st.session_state.companies
        company_names = [(cid, data['company_name']) for cid, data in companies.items()]
        
        selected_company_tuple = st.sidebar.selectbox(
            "Select Company",
            options=company_names,
            format_func=lambda x: x[1],  # Show company name in dropdown
            key="company_selector"
        )
        
        if selected_company_tuple:
            st.session_state.selected_company = companies[selected_company_tuple[0]]
            
            # Show company details
            st.sidebar.markdown("#### Company Details")
            st.sidebar.markdown(f"""
            - **ID:** {selected_company_tuple[0]}
            - **Name:** {st.session_state.selected_company['company_name']}
            - **Industry:** {st.session_state.selected_company.get('industry', 'N/A')}
            - **Revenue:** ${float(st.session_state.selected_company.get('annual_revenue', 0)):,.2f}
            """)
            
            # System status
            if st.sidebar.button("🔍 Discover Bank Agents", key="discover_banks"):
                with st.spinner("Discovering bank agents..."):
                    self.discover_banks()
            
            # Get banks from the response structure
            if isinstance(st.session_state.discovered_banks, dict):
                bank_count = st.session_state.discovered_banks.get('count', 0)
                banks = st.session_state.discovered_banks.get('banks', [])
            else:
                bank_count = 0
                banks = []
            
            st.sidebar.markdown(f"**Banks Discovered:** {bank_count}")
            
            # Display discovered banks
            if banks:
                st.sidebar.markdown("### 🏛️ Available Banks")
                for bank in banks:
                    st.sidebar.markdown(f"""
                    - **{bank.get('name', 'Unknown Bank')}**
                    - Endpoint: {bank.get('endpoint', 'N/A')}
                    - Status: ✅ Online
                    """)
    
        
        # Request history
        st.sidebar.markdown("### 📊 Request History")
        if st.session_state.request_history:
            for i, req in enumerate(st.session_state.request_history[-5:], 1):
                timestamp = req.get('timestamp', datetime.now())
                company = req.get('company_name', 'Unknown')
                amount = req.get('amount', 0)
                st.sidebar.markdown(f"{i}. {company} - ${amount:,.0f}")
        else:
            st.sidebar.markdown("*No requests yet*")
        
        # System health
        st.sidebar.markdown("### ⚡ System Health")
        health_status = self.check_system_health()
        for service, status in health_status.items():
            icon = "✅" if status else "❌"
            st.sidebar.markdown(f"{icon} {service}")
    
    def render_credit_request_form(self):
        """Render credit request form"""
        if not st.session_state.selected_company:
            st.warning("Please select a company from the sidebar first.")
            return
            
        st.markdown("## 📝 Credit Request Form")
        
        col1, col2 = st.columns(2)
        
        # Get company details
        company = st.session_state.selected_company
        
        with col1:
            st.markdown("### Company Information")
            # Display company info as read-only fields
            st.text_input("Company Name", value=company['company_name'], disabled=True)
            st.text_input("Company ID", value=company['company_id'], disabled=True)
            st.text_input("Industry", value=company.get('industry', 'N/A'), disabled=True)
            st.number_input(
                "Annual Revenue ($)", 
                value=float(company.get('annual_revenue', 0)),
                disabled=True,
                format="%.2f"  # Use float format instead of integer
            )
        
        with col2:
            st.markdown("### Credit Requirements")
            amount = st.number_input(
                "Requested Amount ($)", 
                min_value=1000, 
                value=1000000, 
                step=10000,
                format="%d"
            )
            duration_months = st.slider("Duration (months)", 6, 120, 24)
            purpose = st.selectbox(
                "Purpose", 
                [purpose.value for purpose in CreditPurpose]
            )
            urgency = st.selectbox("Urgency", ["normal", "high", "urgent"])
        
        st.markdown("### ESG Preferences")
        col3, col4 = st.columns(2)
        
        with col3:
            min_esg_score = st.slider("Minimum ESG Score", 0.0, 10.0, 7.0, 0.1)
            carbon_neutral_preference = st.checkbox("Carbon Neutral Preference", value=True)
        
        with col4:
            social_impact_weight = st.slider("Social Impact Weight", 0.0, 1.0, 0.3, 0.1)
            governance_weight = st.slider("Governance Weight", 0.0, 1.0, 0.2, 0.1)
        
        # Submit button
        if st.button("🚀 Submit Credit Request", type="primary", key="submit_request"):
            # Check if banks have been discovered
            bank_count = 0
            if isinstance(st.session_state.discovered_banks, dict):
                bank_count = st.session_state.discovered_banks.get('count', 0)
            
            if bank_count == 0:
                st.warning("Please discover bank agents first!")
                return
            
            # Create credit intent
            esg_preferences = ESGPreferences(
                min_esg_score=min_esg_score,
                carbon_neutral_preference=carbon_neutral_preference,
                social_impact_weight=social_impact_weight,
                governance_weight=governance_weight
            )
            
            company = st.session_state.selected_company
            intent = CreditIntent(
                company_name=company['company_name'],
                company_id=company['company_id'],
                amount=amount,
                duration_months=duration_months,
                purpose=purpose,
                annual_revenue=float(company.get('annual_revenue', 0)),
                industry=company.get('industry', 'Other'),
                esg_preferences=esg_preferences,
                urgency=urgency
            )
            
            self.process_credit_request(intent)
    
    def process_credit_request(self, intent: CreditIntent):
        """Process credit request through company agent"""
        st.markdown("## 🔄 Processing Credit Request")
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Submit to company agent
            status_text.markdown("**Step 1:** Submitting credit intent...")
            progress_bar.progress(10)
            
            # Convert intent to dict and ensure datetime objects are serialized
            intent_data = {
                **intent.model_dump(),
                'timestamp': datetime.now().isoformat()  # Convert datetime to ISO format string
            }
            
            company_agent_url = self.get_company_agent_url()
            if not company_agent_url:
                st.error("No company selected or company agent URL not available")
                return
            
            response = requests.post(
                f"{company_agent_url}/wfap/broadcast-intent",
                json=intent_data,
                timeout=60
            )
            
            if response.status_code != 200:
                st.error(f"Error: {response.status_code} - {response.text}")
                return
            
            result = response.json()
            
            # Step 2: Processing by banks
            status_text.markdown("**Step 2:** Broadcasting to bank agents...")
            progress_bar.progress(30)
            time.sleep(2)  # Simulate processing time
            
            # Store results - ensure datetime is serialized
            st.session_state.current_request = {
                'intent': intent_data,
                'result': result,
                'timestamp': datetime.now().isoformat()  # Convert datetime to ISO format string
            }
            
            # Add to history - ensure datetime is serialized
            st.session_state.request_history.append({
                'company_name': intent.company_name,
                'amount': intent.amount,
                'timestamp': datetime.now().isoformat()  # Convert datetime to ISO format string
            })
            
            # Display results
            self.display_results(result)
            
        except requests.exceptions.Timeout:
            st.error("Request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            st.error(f"Network error: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
    
    def display_results(self, result: Dict[str, Any]):
        """Display credit request results with enhanced LLM response handling"""
        st.markdown("## 🏦 Credit Offers Analysis")
        
        if result['status'] != 'success':
            st.error(f"Request failed: {result.get('message', 'Unknown error')}")
            return
        
        offers = result.get('offers', [])
        count = result.get('count', 0)
        
        if count == 0:
            st.warning("No offers received from any banks. Please try again or check bank availability.")
            return
        
        # Enhanced overview with LLM insights
        self.display_offers_overview(offers, result)
        
        # Detailed offers section
        st.markdown("---")
        self.display_detailed_offers(offers)
        
        # Comparison section
        if 'comparison_offers' in st.session_state and st.session_state.comparison_offers:
            st.markdown("---")
            self.display_comparison()
    
    def display_offers_overview(self, offers: List[Dict], result: Dict[str, Any]):
        """Display comprehensive overview of all offers with LLM insights"""
        st.markdown("### 📈 Market Overview")
        
        # Key metrics row
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Offers", len(offers), delta=None)
        
        if offers:
            # Find best offers by different criteria
            best_rate_offer = min(offers, key=lambda x: x.get('carbon_adjusted_rate', 999))
            best_esg_offer = max(offers, key=lambda x: x.get('esg_score', {}).get('overall_score', 0))
            best_confidence_offer = max(offers, key=lambda x: x.get('risk_assessment', {}).get('confidence_score', 0))
            
            with col2:
                best_rate = best_rate_offer.get('carbon_adjusted_rate', 0)
                st.metric("Best Rate", f"{best_rate:.2f}%", 
                         delta=f"{best_rate_offer.get('bank_name', 'Bank')}")
            
            with col3:
                best_esg = best_esg_offer.get('esg_score', {}).get('overall_score', 0)
                st.metric("Best ESG", f"{best_esg:.1f}/10", 
                         delta=f"{best_esg_offer.get('bank_name', 'Bank')}")
            
            with col4:
                best_conf = best_confidence_offer.get('risk_assessment', {}).get('confidence_score', 0)
                st.metric("Best Confidence", f"{best_conf}/100", 
                         delta=f"{best_confidence_offer.get('bank_name', 'Bank')}")
            
            with col5:
                avg_rate = sum(offer.get('carbon_adjusted_rate', 0) for offer in offers) / len(offers)
                st.metric("Average Rate", f"{avg_rate:.2f}%", delta=None)
        
        # Market insights from LLM responses
        st.markdown("### 🤖 AI Market Analysis")
        self.display_market_insights(offers)
        
        # Quick comparison table
        st.markdown("### ⚡ Quick Comparison")
        self.display_quick_comparison(offers)
        
        # Recommendation section
        if offers:
            st.markdown("### 🎯 Our Recommendation")
            self.display_recommendation(offers, result)
    
    def display_market_insights(self, offers: List[Dict]):
        """Display AI-generated market insights from LLM responses"""
        if not offers:
            return
        
        # Analyze risk patterns
        risk_levels = {}
        esg_trends = {}
        rate_ranges = []
        
        for offer in offers:
            # Risk analysis
            risk_assessment = offer.get('risk_assessment', {})
            risk_rating = risk_assessment.get('overall_risk_rating', risk_assessment.get('risk_rating', 'unknown'))
            risk_levels[risk_rating] = risk_levels.get(risk_rating, 0) + 1
            
            # ESG analysis
            esg_score = offer.get('esg_score', {})
            overall_esg = esg_score.get('overall_score', 0)
            if overall_esg >= 8:
                esg_trends['high'] = esg_trends.get('high', 0) + 1
            elif overall_esg >= 6:
                esg_trends['medium'] = esg_trends.get('medium', 0) + 1
            else:
                esg_trends['low'] = esg_trends.get('low', 0) + 1
            
            # Rate analysis
            rate_ranges.append(offer.get('carbon_adjusted_rate', 0))
        
        # Display insights
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Risk Distribution**")
            for risk, count in risk_levels.items():
                percentage = (count / len(offers)) * 100
                st.markdown(f"• {risk.title()}: {count} banks ({percentage:.0f}%)")
        
        with col2:
            st.markdown("**ESG Performance**")
            for level, count in esg_trends.items():
                percentage = (count / len(offers)) * 100
                st.markdown(f"• {level.title()}: {count} banks ({percentage:.0f}%)")
        
        with col3:
            st.markdown("**Rate Analysis**")
            if rate_ranges:
                min_rate = min(rate_ranges)
                max_rate = max(rate_ranges)
                avg_rate = sum(rate_ranges) / len(rate_ranges)
                st.markdown(f"• Range: {min_rate:.2f}% - {max_rate:.2f}%")
                st.markdown(f"• Average: {avg_rate:.2f}%")
                st.markdown(f"• Spread: {max_rate - min_rate:.2f}%")
    
    def display_quick_comparison(self, offers: List[Dict]):
        """Display a quick comparison table of all offers"""
        if not offers:
            return
        
        # Create comparison data
        comparison_data = []
        for i, offer in enumerate(offers, 1):
            esg_score = offer.get('esg_score', {})
            risk_assessment = offer.get('risk_assessment', {})
            
            comparison_data.append({
                'Rank': i,
                'Bank': offer.get('bank_name', 'Unknown'),
                'Amount': f"${offer.get('approved_amount', 0):,.0f}",
                'Rate': f"{offer.get('carbon_adjusted_rate', 0):.2f}%",
                'ESG': f"{esg_score.get('overall_score', 0):.1f}/10",
                'Risk': risk_assessment.get('overall_risk_rating', risk_assessment.get('risk_rating', 'Unknown')),
                'Confidence': f"{risk_assessment.get('confidence_score', 0)}/100",
                'Collateral': 'Yes' if offer.get('collateral_required', False) else 'No'
            })
        
        # Display table with highlighting
        import pandas as pd
        df = pd.DataFrame(comparison_data)
        
        # Highlight best offers
        def highlight_best(row):
            styles = [''] * len(row)
            if row['Rate'] == df['Rate'].min():
                styles[3] = 'background-color: #d4edda'  # Green for best rate
            if row['ESG'] == df['ESG'].max():
                styles[4] = 'background-color: #d1ecf1'  # Blue for best ESG
            if row['Confidence'] == df['Confidence'].max():
                styles[6] = 'background-color: #fff3cd'  # Yellow for best confidence
            return styles
        
        styled_df = df.style.apply(highlight_best, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    def display_recommendation(self, offers: List[Dict], result: Dict[str, Any]):
        """Display AI-powered recommendation with reasoning"""
        if not offers:
            return
        
        # Find the best overall offer using weighted scoring
        best_offer = self.calculate_best_offer(offers)
        
        if best_offer:
            # Create recommendation card
            st.success("🎯 **Recommended Offer**")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**🏦 {best_offer.get('bank_name', 'Unknown Bank')}**")
                st.markdown(f"**💰 Amount:** ${best_offer.get('approved_amount', 0):,.2f}")
                st.markdown(f"**📊 Rate:** {best_offer.get('carbon_adjusted_rate', 0):.2f}%")
                
                esg_score = best_offer.get('esg_score', {})
                st.markdown(f"**🌱 ESG Score:** {esg_score.get('overall_score', 0):.1f}/10")
                
                risk_assessment = best_offer.get('risk_assessment', {})
                st.markdown(f"**🔍 Risk:** {risk_assessment.get('overall_risk_rating', risk_assessment.get('risk_rating', 'Unknown'))} (Confidence: {risk_assessment.get('confidence_score', 0)}/100)")
            
            with col2:
                # Recommendation reasoning
                st.markdown("**Why this offer?**")
                reasons = self.get_recommendation_reasons(best_offer, offers)
                for reason in reasons:
                    st.markdown(f"• {reason}")
                
                # Action button
                if st.button("✅ Accept Recommended Offer", type="primary", key="accept_recommended"):
                    self.accept_offer(best_offer)
    
    def calculate_best_offer(self, offers: List[Dict]) -> Dict:
        """Calculate the best offer using weighted scoring"""
        if not offers:
            return None
        
        scored_offers = []
        
        for offer in offers:
            score = 0
            
            # Rate score (lower is better) - 40% weight
            rate = offer.get('carbon_adjusted_rate', 999)
            max_rate = max(offer.get('carbon_adjusted_rate', 0) for offer in offers)
            min_rate = min(offer.get('carbon_adjusted_rate', 0) for offer in offers)
            if max_rate > min_rate:
                rate_score = 1 - ((rate - min_rate) / (max_rate - min_rate))
            else:
                rate_score = 1
            score += rate_score * 0.4
            
            # ESG score (higher is better) - 30% weight
            esg_score = offer.get('esg_score', {}).get('overall_score', 0)
            score += (esg_score / 10) * 0.3
            
            # Confidence score (higher is better) - 20% weight
            confidence = offer.get('risk_assessment', {}).get('confidence_score', 0)
            score += (confidence / 100) * 0.2
            
            # Approval amount (higher is better) - 10% weight
            approved_amount = offer.get('approved_amount', 0)
            max_amount = max(offer.get('approved_amount', 0) for offer in offers)
            if max_amount > 0:
                amount_score = approved_amount / max_amount
            else:
                amount_score = 1
            score += amount_score * 0.1
            
            scored_offers.append((score, offer))
        
        # Return the offer with the highest score
        scored_offers.sort(key=lambda x: x[0], reverse=True)
        return scored_offers[0][1] if scored_offers else None
    
    def get_recommendation_reasons(self, best_offer: Dict, all_offers: List[Dict]) -> List[str]:
        """Generate reasons why this offer is recommended"""
        reasons = []
        
        # Rate comparison
        best_rate = best_offer.get('carbon_adjusted_rate', 0)
        avg_rate = sum(offer.get('carbon_adjusted_rate', 0) for offer in all_offers) / len(all_offers)
        if best_rate < avg_rate:
            reasons.append(f"Competitive rate ({best_rate:.2f}% vs {avg_rate:.2f}% average)")
        
        # ESG comparison
        best_esg = best_offer.get('esg_score', {}).get('overall_score', 0)
        avg_esg = sum(offer.get('esg_score', {}).get('overall_score', 0) for offer in all_offers) / len(all_offers)
        if best_esg >= avg_esg:
            reasons.append(f"Strong ESG performance ({best_esg:.1f}/10)")
        
        # Confidence comparison
        best_conf = best_offer.get('risk_assessment', {}).get('confidence_score', 0)
        if best_conf >= 80:
            reasons.append(f"High confidence assessment ({best_conf}/100)")
        
        # Risk level
        risk_rating = best_offer.get('risk_assessment', {}).get('overall_risk_rating', best_offer.get('risk_assessment', {}).get('risk_rating', 'unknown'))
        if risk_rating.lower() == 'low':
            reasons.append("Low risk profile")
        
        # Approval amount
        approved_amount = best_offer.get('approved_amount', 0)
        if approved_amount > 0:
            reasons.append(f"Full amount approved (${approved_amount:,.0f})")
        
        return reasons[:4]  # Limit to 4 reasons
    
    def display_detailed_offers(self, offers: List[Dict]):
        """Display detailed view of all offers"""
        st.markdown("### 📋 Detailed Offers")
        
        # Toggle between list and grid view
        col1, col2 = st.columns([1, 4])
        with col1:
            view_mode = st.selectbox("View Mode", ["List", "Grid"], key="view_mode")
        
        if view_mode == "Grid":
            self.display_offers_grid(offers)
        else:
            self.display_offers_list(offers)
    
    def display_offers_grid(self, offers: List[Dict]):
        """Display offers in a grid layout"""
        if not offers:
            return
        
        # Calculate number of columns based on number of offers
        num_offers = len(offers)
        if num_offers <= 2:
            cols = 2
        elif num_offers <= 4:
            cols = 2
        else:
            cols = 3
        
        # Create grid
        for i in range(0, len(offers), cols):
            cols_list = st.columns(cols)
            for j, col in enumerate(cols_list):
                if i + j < len(offers):
                    offer = offers[i + j]
                    with col:
                        self.display_offer_card(offer, i + j + 1)
    
    def display_offer_card(self, offer: Dict, offer_num: int):
        """Display a single offer in a card format"""
        esg_score = offer.get('esg_score', {})
        risk_assessment = offer.get('risk_assessment', {})
        
        # Card header with key info
        st.markdown(f"### 🏦 {offer.get('bank_name', 'Unknown Bank')}")
        
        # Key metrics in a compact format
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Rate", f"{offer.get('carbon_adjusted_rate', 0):.2f}%")
            st.metric("Amount", f"${offer.get('approved_amount', 0):,.0f}")
        with col2:
            st.metric("ESG", f"{esg_score.get('overall_score', 0):.1f}/10")
            st.metric("Risk", risk_assessment.get('overall_risk_rating', risk_assessment.get('risk_rating', 'Unknown')))
        
        # Additional details in expander
        with st.expander("📋 Details", expanded=False):
            st.markdown(f"**Bank ID:** {offer.get('bank_id', 'N/A')}")
            st.markdown(f"**Base Rate:** {offer.get('interest_rate', 0):.2f}%")
            st.markdown(f"**Processing Fee:** ${offer.get('processing_fee', 0):,.2f}")
            st.markdown(f"**Collateral:** {'Yes' if offer.get('collateral_required', False) else 'No'}")
            
            # ESG breakdown
            st.markdown("**ESG Breakdown:**")
            st.markdown(f"• Environmental: {esg_score.get('environmental_score', 0):.1f}/10")
            st.markdown(f"• Social: {esg_score.get('social_score', 0):.1f}/10")
            st.markdown(f"• Governance: {esg_score.get('governance_score', 0):.1f}/10")
            
            # Risk details
            st.markdown(f"**Confidence:** {risk_assessment.get('confidence_score', 0)}/100")
            
            # Terms
            st.markdown("**Terms:**")
            st.markdown(f"• Repayment: {offer.get('repayment_schedule', 'Monthly')}")
            st.markdown(f"• Grace Period: {offer.get('grace_period_days', 30)} days")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ Accept", key=f"accept_card_{offer_num}", use_container_width=True):
                self.accept_offer(offer)
        with col2:
            if st.button(f"📊 Compare", key=f"compare_card_{offer_num}", use_container_width=True):
                if 'comparison_offers' not in st.session_state:
                    st.session_state.comparison_offers = []
                if offer not in st.session_state.comparison_offers:
                    st.session_state.comparison_offers.append(offer)
                    st.success(f"Added {offer.get('bank_name', 'Unknown Bank')} to comparison!")
                else:
                    st.info("Offer already in comparison!")
    
    def display_offers_list(self, offers: List[Dict]):
        """Display list of all received offers with enhanced LLM response details"""
        for i, offer in enumerate(offers, 1):
            # Determine if this is a recommended offer
            is_recommended = False
            if 'comparison_offers' not in st.session_state:
                st.session_state.comparison_offers = []
            
            # Check if this offer is in comparison (indicating user interest)
            if offer in st.session_state.comparison_offers:
                is_recommended = True
            
            # Create expander with enhanced header
            header_text = f"Offer {i}: {offer.get('bank_name', 'Unknown Bank')} - ${offer.get('approved_amount', 0):,.2f} at {offer.get('carbon_adjusted_rate', 0):.2f}%"
            if is_recommended:
                header_text = f"⭐ {header_text} (In Comparison)"
            
            with st.expander(header_text, expanded=is_recommended):
                # Key metrics at the top
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
                    st.metric("Rate", f"{offer.get('carbon_adjusted_rate', 0):.2f}%")
                with col2:
                    st.metric("Amount", f"${offer.get('approved_amount', 0):,.0f}")
                with col3:
                    esg_score = offer.get('esg_score', {})
                    st.metric("ESG", f"{esg_score.get('overall_score', 0):.1f}/10")
                with col4:
                    risk_assessment = offer.get('risk_assessment', {})
                    st.metric("Risk", risk_assessment.get('overall_risk_rating', risk_assessment.get('risk_rating', 'Unknown')))
                
                # Detailed information
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 💰 Financial Details")
                    st.markdown(f"**Bank:** {offer.get('bank_name', 'Unknown')}")
                    st.markdown(f"**Bank ID:** {offer.get('bank_id', 'N/A')}")
                    st.markdown(f"**Approved Amount:** ${offer.get('approved_amount', 0):,.2f}")
                    st.markdown(f"**Base Interest Rate:** {offer.get('interest_rate', 0):.2f}%")
                    st.markdown(f"**ESG-Adjusted Rate:** {offer.get('carbon_adjusted_rate', 0):.2f}%")
                    st.markdown(f"**Processing Fee:** ${offer.get('processing_fee', 0):,.2f}")
                    st.markdown(f"**Collateral Required:** {'Yes' if offer.get('collateral_required', False) else 'No'}")
        
        with col2:
                    st.markdown("#### 🌱 ESG & Risk")
                    st.markdown(f"**Environmental:** {esg_score.get('environmental_score', 0):.1f}/10")
                    st.markdown(f"**Social:** {esg_score.get('social_score', 0):.1f}/10")
                    st.markdown(f"**Governance:** {esg_score.get('governance_score', 0):.1f}/10")
                    st.markdown(f"**Overall ESG:** {esg_score.get('overall_score', 0):.1f}/10")
                    st.markdown(f"**Carbon Footprint:** {esg_score.get('carbon_footprint_category', 'Unknown')}")
                    st.markdown(f"**Risk Rating:** {risk_assessment.get('overall_risk_rating', risk_assessment.get('risk_rating', 'Unknown'))}")
                    st.markdown(f"**Confidence:** {risk_assessment.get('confidence_score', 0)}/100")
                
                # Terms and conditions
                st.markdown("#### 📋 Terms & Conditions")
                col3, col4 = st.columns(2)
        
        with col3:
                    st.markdown(f"**Repayment Schedule:** {offer.get('repayment_schedule', 'Monthly')}")
                    st.markdown(f"**Grace Period:** {offer.get('grace_period_days', 30)} days")
                    st.markdown(f"**Early Repayment Penalty:** {'Yes' if offer.get('early_repayment_penalty', False) else 'No'}")
        
        with col4:
                    offer_valid_until = offer.get('offer_valid_until')
                    if offer_valid_until:
                        if isinstance(offer_valid_until, str):
                            from datetime import datetime
                            try:
                                valid_until = datetime.fromisoformat(offer_valid_until.replace('Z', '+00:00'))
                                st.markdown(f"**Valid Until:** {valid_until.strftime('%Y-%m-%d %H:%M')}")
                            except:
                                st.markdown(f"**Valid Until:** {offer_valid_until}")
                        else:
                            st.markdown(f"**Valid Until:** {offer_valid_until}")
                    else:
                        st.markdown("**Valid Until:** Not specified")
                
                # LLM-generated insights
                if offer.get('esg_summary'):
                    st.markdown("#### 🤖 AI ESG Summary")
                    st.info(offer['esg_summary'])
                
                if offer.get('pricing_rationale'):
                    st.markdown("#### 💡 Pricing Rationale")
                    st.info(offer['pricing_rationale'])
                
                # Risk Assessment Details from LLM
                if risk_assessment:
                    st.markdown("#### 🔍 AI Risk Analysis")
                    if risk_assessment.get('key_risk_factors'):
                        st.markdown("**Key Risk Factors:**")
                        for factor in risk_assessment['key_risk_factors']:
                            if isinstance(factor, dict):
                                st.markdown(f"• **{factor.get('risk', 'Unknown')}:** {factor.get('description', 'No description')}")
                            else:
                                st.markdown(f"• {factor}")
                    
                    if risk_assessment.get('mitigating_factors'):
                        st.markdown("**Mitigating Factors:**")
                        for factor in risk_assessment['mitigating_factors']:
                            if isinstance(factor, dict):
                                st.markdown(f"• **{factor.get('factor', 'Unknown')}:** {factor.get('description', 'No description')}")
                            else:
                                st.markdown(f"• {factor}")
                
                # Action buttons
                col5, col6, col7 = st.columns(3)
                with col5:
                    if st.button(f"✅ Accept Offer {i}", key=f"accept_{i}", use_container_width=True):
                        self.accept_offer(offer)
                with col6:
                    if st.button(f"📊 Compare", key=f"compare_{i}", use_container_width=True):
                        if 'comparison_offers' not in st.session_state:
                            st.session_state.comparison_offers = []
                        if offer not in st.session_state.comparison_offers:
                            st.session_state.comparison_offers.append(offer)
                            st.success(f"Added {offer.get('bank_name', 'Unknown Bank')} to comparison!")
                        else:
                            st.info("Offer already in comparison!")
                with col7:
                    if st.button(f"📈 View Details", key=f"details_{i}", use_container_width=True):
                        st.info("Detailed view expanded above!")
    
    def display_comparison(self):
        """Display comparison of selected offers"""
        st.markdown("### 📊 Offer Comparison")
        
        comparison_offers = st.session_state.comparison_offers
        
        if len(comparison_offers) < 2:
            st.warning("Add at least 2 offers to compare them.")
            return
        
        # Create comparison table
        comparison_data = []
        for offer in comparison_offers:
            esg_score = offer.get('esg_score', {})
            risk_assessment = offer.get('risk_assessment', {})
            
            comparison_data.append({
                'Bank': offer.get('bank_name', 'Unknown'),
                'Amount': f"${offer.get('approved_amount', 0):,.0f}",
                'Base Rate': f"{offer.get('interest_rate', 0):.2f}%",
                'ESG Rate': f"{offer.get('carbon_adjusted_rate', 0):.2f}%",
                'ESG Score': f"{esg_score.get('overall_score', 0):.1f}/10",
                'Risk Rating': risk_assessment.get('overall_risk_rating', risk_assessment.get('risk_rating', 'Unknown')),
                'Confidence': f"{risk_assessment.get('confidence_score', 0)}/100",
                'Collateral': 'Yes' if offer.get('collateral_required', False) else 'No',
                'Processing Fee': f"${offer.get('processing_fee', 0):,.0f}"
            })
        
        # Display comparison table
        import pandas as pd
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True)
        
        # Clear comparison button
        if st.button("🗑️ Clear Comparison"):
            st.session_state.comparison_offers = []
            st.rerun()

    def accept_offer(self, offer: Dict):
        """Accept the selected offer"""
        try:
            company_agent_url = self.get_company_agent_url()
            if not company_agent_url:
                st.error("No company selected or company agent URL not available")
                return
                
            response = requests.post(
                f"{company_agent_url}/wfap/accept-offer",
                json={'offer_id': offer['offer_id']},
                timeout=30
            )
            
            if response.status_code == 200:
                st.success("🎉 Offer accepted successfully! The bank will contact you shortly.")
            else:
                st.error(f"Failed to accept offer: {response.text}")
        except Exception as e:
            st.error(f"Error accepting offer: {str(e)}")

    def discover_banks(self):
        """Discover available bank agents through company agent"""
        try:
            company_agent_url = self.get_company_agent_url()
            if not company_agent_url:
                st.error("No company selected or company agent URL not available")
                return
                
            # Use company agent's discovery endpoint
            response = requests.post(
                f"{company_agent_url}/wfap/discover-banks",
                json={},
                timeout=30
            )
            
            if response.status_code == 200:
                discovery_result = response.json()
                st.session_state.discovered_banks = discovery_result
                bank_count = discovery_result.get('count', 0)
                st.success(f"✨ Discovered {bank_count} bank agents!")
            else:
                st.error(f"Failed to discover banks: {response.text}")
        except Exception as e:
            st.error(f"Error discovering banks: {str(e)}")

    def check_system_health(self) -> Dict[str, bool]:
        """Check health status of system components"""
        health_status = {
            "Company Agent": False,
            "Network": False,
            "Database": False
        }
        
        try:
            # Check company agent
            company_agent_url = self.get_company_agent_url()
            if company_agent_url:
                response = requests.get(f"{company_agent_url}/a2a/health", timeout=5)
            health_status["Company Agent"] = response.status_code == 200
            else:
                health_status["Company Agent"] = False
            
            # Check network by pinging a reliable host
            response = requests.get("https://api.github.com", timeout=5)
            health_status["Network"] = response.status_code == 200
            
            # Database health check (assuming it's implemented in the company agent)
            if company_agent_url:
                response = requests.get(f"{company_agent_url}/db-health", timeout=5)
            health_status["Database"] = response.status_code == 200
            else:
                health_status["Database"] = False
            
        except:
            pass
        
        return health_status

if __name__ == "__main__":
    demo = WFAPDemo()
    demo.render_header()
    demo.render_sidebar()
    demo.render_credit_request_form()

