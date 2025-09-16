import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime
from typing import Dict, List, Any
from shared.schemas import CreditIntent, CreditPurpose, ESGPreferences
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
        self.company_agent_url = f"http://{config.COMPANY_AGENT_HOST}:{config.COMPANY_AGENT_PORT}"
        self.banks_discovered = False
        
        if 'request_history' not in st.session_state:
            st.session_state.request_history = []
        if 'current_request' not in st.session_state:
            st.session_state.current_request = None
        if 'discovered_banks' not in st.session_state:
            st.session_state.discovered_banks = []
    
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
        
        # System status
        if st.sidebar.button("🔍 Discover Bank Agents", key="discover_banks"):
            with st.spinner("Discovering bank agents..."):
                self.discover_banks()
        
        # Get banks from the response structure
        discovered_banks = st.session_state.discovered_banks.get('banks', []) if isinstance(st.session_state.discovered_banks, dict) else []
        
        st.sidebar.markdown(f"**Banks Discovered:** {len(discovered_banks)}")
        
        # Display discovered banks
        if discovered_banks:
            st.sidebar.markdown("### 🏛️ Available Banks")
            for bank in discovered_banks:
                bank_details = bank.get('bank_details', {})
                st.sidebar.markdown(f"""
                - **{bank_details.get('bank_name', 'Unknown Bank')}**
                - Base Rate: {bank_details.get('base_rate', 'N/A')}%
                - Risk Appetite: {bank_details.get('risk_appetite', 'N/A')}
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
        st.markdown("## 📝 Credit Request Form")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Company Information")
            company_name = st.text_input("Company Name", value="GreenTech Solutions Inc.")
            company_id = st.text_input("Company ID", value="COMP_12345")
            industry = st.selectbox(
                "Industry", 
                ["Technology", "Manufacturing", "Healthcare", "Finance", "Retail", "Energy", "Other"]
            )
            annual_revenue = st.number_input(
                "Annual Revenue ($)", 
                min_value=0, 
                value=5000000, 
                step=100000,
                format="%d"
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
            if not st.session_state.discovered_banks:
                st.warning("Please discover bank agents first!")
                return
            
            # Create credit intent
            esg_preferences = ESGPreferences(
                min_esg_score=min_esg_score,
                carbon_neutral_preference=carbon_neutral_preference,
                social_impact_weight=social_impact_weight,
                governance_weight=governance_weight
            )
            
            intent = CreditIntent(
                company_name=company_name,
                company_id=company_id,
                amount=amount,
                duration_months=duration_months,
                purpose=purpose,
                annual_revenue=annual_revenue,
                industry=industry,
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
            
            response = requests.post(
                f"{self.company_agent_url}/wfap/broadcast-intent",
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
        """Display credit request results"""
        st.markdown("## 📊 Credit Offers Analysis")
        
        if result['status'] != 'success':
            st.error(f"Request failed: {result.get('message', 'Unknown error')}")
            return
        
        analysis_result = result['result']
        
        if 'error' in analysis_result:
            st.error(f"Analysis failed: {analysis_result['error']}")
            return
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Offers Received", 
                analysis_result.get('total_offers_received', 0),
                delta=None
            )
        
        with col2:
            best_rate = analysis_result['best_offer']['carbon_adjusted_rate']
            st.metric(
                "Best Rate", 
                f"{best_rate}%",
                delta=f"-{5.0 - best_rate:.1f}% vs 5.0%"
            )
        
        with col3:
            best_esg = analysis_result['best_offer']['esg_score']['overall_score']
            st.metric(
                "Best ESG Score", 
                f"{best_esg}/10",
                delta=f"+{best_esg - 7.0:.1f} vs 7.0 target"
            )
        
        with col4:
            approved_amount = analysis_result['best_offer']['approved_amount']
            requested_amount = result['intent']['amount']
            approval_ratio = (approved_amount / requested_amount) * 100
            st.metric(
                "Approval Ratio",
                f"{approval_ratio:.1f}%",
                delta=f"{approval_ratio - 100:.1f}% vs requested"
            )
        
        # Best offer highlight
        self.display_best_offer(analysis_result['best_offer'], analysis_result['evaluation'])
        
        # All offers comparison
        self.display_offers_comparison(analysis_result['all_evaluations'])
        
        # Decision reasoning
        st.markdown("### 🧠 Decision Reasoning")
        st.info(analysis_result['decision_reasoning'])
        
        # Offer acceptance
        if st.button("✅ Accept Best Offer", type="primary"):
            self.accept_offer(analysis_result['best_offer'])
    
    def display_best_offer(self, best_offer: Dict, evaluation: Dict):
            """Display the best offer details"""
            st.markdown("### 🏆 Best Offer Selected")
            
            st.markdown(f"""
            <div class="offer-card best-offer">
                <h4>🏛️ {best_offer['bank_name']}</h4>
                <p><strong>Approved Amount:</strong> ${best_offer['approved_amount']:,.2f}</p>
                <p><strong>Rate:</strong> {best_offer['carbon_adjusted_rate']}%</p>
                <p><strong>Duration:</strong> {best_offer['duration_months']} months</p>
                <p><strong>ESG Score:</strong> {best_offer['esg_score']['overall_score']}/10</p>
            </div>
            """, unsafe_allow_html=True)

    def display_offers_comparison(self, evaluations: List[Dict]):
        """Display comparison of all received offers"""
        st.markdown("### 📊 Offers Comparison")
        
        # Convert evaluations to DataFrame for plotting
        df = pd.DataFrame(evaluations)
        
        # Create tabs for different visualizations
        tab1, tab2 = st.tabs(["Rate Comparison", "ESG Analysis"])
        
        with tab1:
            fig = px.bar(
                df,
                x='bank_name',
                y='carbon_adjusted_rate',
                title='Interest Rates by Bank',
                labels={'carbon_adjusted_rate': 'Interest Rate (%)', 'bank_name': 'Bank'},
                color='carbon_adjusted_rate',
                color_continuous_scale='RdYlGn_r'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            fig = px.scatter(
                df,
                x='esg_score',
                y='carbon_adjusted_rate',
                size='approved_amount',
                color='bank_name',
                title='ESG Score vs Interest Rate',
                labels={
                    'esg_score': 'ESG Score',
                    'carbon_adjusted_rate': 'Interest Rate (%)',
                    'approved_amount': 'Approved Amount'
                }
            )
            st.plotly_chart(fig, use_container_width=True)

    def accept_offer(self, offer: Dict):
        """Accept the selected offer"""
        try:
            response = requests.post(
                f"{self.company_agent_url}/wfap/accept-offer",
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
        """Discover available bank agents"""
        try:
            response = requests.get(
                f"{self.company_agent_url}/wfap/discover-banks",
                timeout=30
            )
            
            if response.status_code == 200:
                st.session_state.discovered_banks = response.json()
                discovered_banks = st.session_state.discovered_banks.get('banks', []) if isinstance(st.session_state.discovered_banks, dict) else []
                st.success(f"✨ Discovered {len(discovered_banks)} bank agents!")
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
            response = requests.get(f"{self.company_agent_url}/health", timeout=5)
            health_status["Company Agent"] = response.status_code == 200
            
            # Check network by pinging a reliable host
            response = requests.get("https://api.github.com", timeout=5)
            health_status["Network"] = response.status_code == 200
            
            # Database health check (assuming it's implemented in the company agent)
            response = requests.get(f"{self.company_agent_url}/db-health", timeout=5)
            health_status["Database"] = response.status_code == 200
            
        except:
            pass
        
        return health_status

if __name__ == "__main__":
    demo = WFAPDemo()
    demo.render_header()
    demo.render_sidebar()
    demo.render_credit_request_form()

