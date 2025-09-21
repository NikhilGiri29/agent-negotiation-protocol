# WFAP - Wells Fargo Agent Protocol
# Polished Streamlit UI for Company Dashboard
# Step 2: Basic structure and styling

import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configure page
st.set_page_config(
    page_title="WFAP Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for futuristic styling
st.markdown("""
<style>
    /* Import futuristic fonts */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600;700&display=swap');
    
    /* Main theme colors */
    :root {
        --primary-color: #00d4ff;
        --secondary-color: #ff6b35;
        --accent-color: #7c3aed;
        --bg-dark: #0a0a0a;
        --bg-card: #1a1a1a;
        --text-primary: #ffffff;
        --text-secondary: #b0b0b0;
        --success-color: #00ff88;
        --warning-color: #ffaa00;
        --error-color: #ff3366;
    }
    
    /* Global styles */
    .main {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
        color: var(--text-primary);
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Orbitron', monospace;
        color: var(--primary-color);
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
    }
    
    /* Cards */
    .card {
        background: rgba(26, 26, 26, 0.8);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(45deg, var(--primary-color), var(--accent-color));
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 25px;
        font-family: 'Exo 2', sans-serif;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 212, 255, 0.5);
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 100%);
    }
    
    /* Metrics */
    .metric-card {
        background: rgba(0, 212, 255, 0.1);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin: 5px;
    }
    
    /* Animations */
    @keyframes glow {
        0% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.3); }
        50% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.6); }
        100% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.3); }
    }
    
    .glow {
        animation: glow 2s ease-in-out infinite alternate;
    }
</style>
""", unsafe_allow_html=True)

# Step 3: Main application class and basic structure

class WFAPDemo:
    def __init__(self):
        self.registry_url = "http://localhost:8005"
        self.company_agents = {
            "Company A": {"id": "cmp123", "port": 4000},
            "Company B": {"id": "cmp456", "port": 4001},
            "Company C": {"id": "cmp789", "port": 4002},
            "Company D": {"id": "cmp101", "port": 4003},
            "Company E": {"id": "cmp112", "port": 4004}
        }
        
    def get_company_agent_url(self, company_name: str) -> str:
        """Get the base URL for the selected company agent"""
        if company_name not in self.company_agents:
            return ""
        
        port = self.company_agents[company_name]["port"]
        return f"http://localhost:{port}"
    
    def run(self):
        """Main application runner"""
        self.render_header()
        self.render_sidebar()
        self.render_main_content()
    
    def render_header(self):
        """Render the futuristic header"""
        st.markdown("""
        <div style="text-align: center; padding: 20px 0; margin-bottom: 30px;">
            <h1 style="font-size: 3.5rem; margin: 0; background: linear-gradient(45deg, #00d4ff, #7c3aed, #ff6b35);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                       text-shadow: 0 0 30px rgba(0, 212, 255, 0.5);">
                🏦 WFAP DASHBOARD
            </h1>
            <p style="font-size: 1.2rem; color: #b0b0b0; margin: 10px 0; font-family: 'Exo 2', sans-serif;">
                Wells Fargo Agent Protocol - Intelligent Financial Negotiation
            </p>
            <div style="width: 200px; height: 2px; background: linear-gradient(90deg, #00d4ff, #7c3aed, #ff6b35);
                        margin: 20px auto; border-radius: 1px; box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);">
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render the futuristic sidebar"""
        with st.sidebar:
            st.markdown("""
            <div style="padding: 20px 0; text-align: center;">
                <h3 style="color: #00d4ff; margin-bottom: 20px;">🎯 CONTROL PANEL</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Company selection
            st.markdown("### 🏢 Select Company")
            selected_company = st.selectbox(
                "Choose your company agent:",
                list(self.company_agents.keys()),
                key="company_selection"
            )
            
            # Store in session state
            st.session_state.selected_company = selected_company
            
            # Company info card
            if selected_company:
                company_info = self.company_agents[selected_company]
                st.markdown(f"""
                <div class="card" style="margin: 15px 0;">
                    <h4 style="color: #00d4ff; margin: 0 0 10px 0;">{selected_company}</h4>
                    <p style="color: #b0b0b0; margin: 5px 0;"><strong>ID:</strong> {company_info['id']}</p>
                    <p style="color: #b0b0b0; margin: 5px 0;"><strong>Port:</strong> {company_info['port']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # System status
            st.markdown("### 🔍 System Status")
            self.render_system_status()
            
            # Quick actions
            st.markdown("### ⚡ Quick Actions")
            if st.button("🔄 Refresh Status", key="refresh_status"):
                st.rerun()
            
            if st.button("🧹 Clear Data", key="clear_data"):
                self.clear_session_data()
                st.rerun()
    
    def render_system_status(self):
        """Render system status indicators"""
        company_agent_url = self.get_company_agent_url(st.session_state.get('selected_company', ''))
        
        if company_agent_url:
            try:
                response = requests.get(f"{company_agent_url}/a2a/health", timeout=5)
                if response.status_code == 200:
                    st.markdown("""
                    <div style="background: rgba(0, 255, 136, 0.1); border: 1px solid #00ff88; 
                                border-radius: 10px; padding: 10px; margin: 10px 0;">
                        <p style="color: #00ff88; margin: 0; font-weight: bold;">✅ Company Agent: Online</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: rgba(255, 51, 102, 0.1); border: 1px solid #ff3366; 
                                border-radius: 10px; padding: 10px; margin: 10px 0;">
                        <p style="color: #ff3366; margin: 0; font-weight: bold;">❌ Company Agent: Offline</p>
                    </div>
                    """, unsafe_allow_html=True)
            except:
                st.markdown("""
                <div style="background: rgba(255, 170, 0, 0.1); border: 1px solid #ffaa00; 
                            border-radius: 10px; padding: 10px; margin: 10px 0;">
                    <p style="color: #ffaa00; margin: 0; font-weight: bold;">⚠️ Company Agent: Unknown</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Bank discovery status
        if 'discovered_banks' in st.session_state:
            bank_count = 0
            if isinstance(st.session_state.discovered_banks, dict):
                bank_count = st.session_state.discovered_banks.get('count', 0)
            
            if bank_count > 0:
                st.markdown(f"""
                <div style="background: rgba(0, 212, 255, 0.1); border: 1px solid #00d4ff; 
                            border-radius: 10px; padding: 10px; margin: 10px 0;">
                    <p style="color: #00d4ff; margin: 0; font-weight: bold;">🏦 Banks Discovered: {bank_count}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(255, 170, 0, 0.1); border: 1px solid #ffaa00; 
                            border-radius: 10px; padding: 10px; margin: 10px 0;">
                    <p style="color: #ffaa00; margin: 0; font-weight: bold;">⚠️ No Banks Discovered</p>
                </div>
                """, unsafe_allow_html=True)
    
    def clear_session_data(self):
        """Clear all session data"""
        keys_to_clear = ['discovered_banks', 'offers', 'selected_offers', 'comparison_offers', 'best_offer_shown', 'form_data']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def render_main_content(self):
        """Render the main content area"""
        if not st.session_state.get('selected_company'):
            st.markdown("""
            <div style="text-align: center; padding: 50px; color: #b0b0b0;">
                <h3>👈 Please select a company from the sidebar to begin</h3>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Main content tabs
        tab1, tab2, tab3 = st.tabs(["🎯 Credit Request", "📊 Market Analysis", "⚙️ Settings"])
        
        with tab1:
            self.render_credit_request_tab()
        
        with tab2:
            self.render_market_analysis_tab()
        
        with tab3:
            self.render_settings_tab()
    
    def render_credit_request_tab(self):
        """Render the credit request tab with fixed progress bar"""
        st.markdown("### 💰 Request Credit Line")
        
        # Step 1: Discover Banks
        st.markdown("#### Step 1: Discover Bank Agents")
        if st.button("🔍 Discover Banks", key="discover_banks"):
            self.discover_banks()
        
        # Step 2: Credit Request Form
        st.markdown("#### Step 2: Submit Credit Request")
        self.render_credit_form()
        
        # Step 3: Results
        if 'offers' in st.session_state and st.session_state.offers:
            st.markdown("#### Step 3: Review Offers")
            
            # Show best offer first (only if not already shown)
            offers = st.session_state.offers
            if offers and not st.session_state.get('best_offer_shown', False):
                best_offer = min(offers, key=lambda x: x.get('carbon_adjusted_rate', 999))
                self.display_best_offer(best_offer)
                st.session_state.best_offer_shown = True
            
            # Then show all offers
            self.render_offers()
    
    def discover_banks(self):
        """Discover available bank agents with progress tracking"""
        company_agent_url = self.get_company_agent_url(st.session_state.selected_company)
        
        if not company_agent_url:
            st.error("No company agent selected")
            return
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔍 Discovering bank agents...")
            progress_bar.progress(20)
            
            # Use company agent's discovery endpoint
            response = requests.post(
                f"{company_agent_url}/wfap/discover-banks",
                json={},
                timeout=30
            )
            
            progress_bar.progress(60)
            status_text.text("📡 Processing discovery results...")
            
            if response.status_code == 200:
                result = response.json()
                st.session_state.discovered_banks = result
                progress_bar.progress(100)
                status_text.text("✅ Bank discovery completed!")
                
                bank_count = result.get('count', 0)
                st.success(f"Discovered {bank_count} bank agents!")
                
                # Show discovered banks
                if bank_count > 0:
                    banks = result.get('banks', [])
                    st.markdown("#### 🏦 Discovered Banks:")
                    for bank in banks:
                        bank_name = bank.get('bank_details', {}).get('bank_name', bank.get('name', 'Unknown Bank'))
                        bank_id = bank.get('agent_id', 'Unknown ID')
                        st.markdown(f"""
                        <div style="background: rgba(0, 212, 255, 0.1); border: 1px solid rgba(0, 212, 255, 0.3); 
                                    border-radius: 10px; padding: 15px; margin: 10px 0;">
                            <h4 style="color: #00d4ff; margin: 0 0 5px 0;">🏦 {bank_name}</h4>
                            <p style="color: #b0b0b0; margin: 0; font-size: 0.9rem;">ID: {bank_id}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                progress_bar.progress(100)
                status_text.text("❌ Bank discovery failed!")
                st.error(f"Failed to discover banks: {response.status_code}")
                
        except Exception as e:
            progress_bar.progress(100)
            status_text.text("❌ Bank discovery failed!")
            st.error(f"Error discovering banks: {str(e)}")
        
        # Clear progress after 2 seconds
        time.sleep(2)
        progress_bar.empty()
        status_text.empty()
    
    def render_credit_form(self):
        """Render the credit request form"""
        # Initialize session state for form data
        if 'form_data' not in st.session_state:
            st.session_state.form_data = {
                'amount': 1000000,
                'duration': 24,
                'purpose': 'working_capital',
                'annual_revenue': 15000000,
                'industry': 'Technology',
                'urgency': 'normal',
                'min_esg_score': 7.0,
                'carbon_neutral': True,
                'social_impact_weight': 0.3,
                'governance_weight': 0.2
            }
        
        col1, col2 = st.columns(2)
        
        with col1:
            amount = st.number_input(
                "💰 Amount ($)",
                min_value=10000,
                max_value=10000000,
                value=st.session_state.form_data['amount'],
                step=10000,
                format="%d",
                key="form_amount"
            )
            
            duration = st.selectbox(
                "📅 Duration (months)",
                [6, 12, 18, 24, 36, 48, 60],
                index=[6, 12, 18, 24, 36, 48, 60].index(st.session_state.form_data['duration']),
                key="form_duration"
            )
            
            purpose = st.selectbox(
                "🎯 Purpose",
                ["working_capital", "expansion", "equipment", "inventory", "refinancing"],
                index=["working_capital", "expansion", "equipment", "inventory", "refinancing"].index(st.session_state.form_data['purpose']),
                key="form_purpose"
            )
        
        with col2:
            annual_revenue = st.number_input(
                "💵 Annual Revenue ($)",
                min_value=100000,
                max_value=1000000000,
                value=st.session_state.form_data['annual_revenue'],
                step=100000,
                format="%d",
                key="form_revenue"
            )
            
            industry = st.selectbox(
                "🏭 Industry",
                ["Technology", "Finance", "Manufacturing", "Healthcare", "Retail", "Energy"],
                index=["Technology", "Finance", "Manufacturing", "Healthcare", "Retail", "Energy"].index(st.session_state.form_data['industry']),
                key="form_industry"
            )
            
            urgency = st.selectbox(
                "⚡ Urgency",
                ["low", "normal", "high", "urgent"],
                index=["low", "normal", "high", "urgent"].index(st.session_state.form_data['urgency']),
                key="form_urgency"
            )
        
        # ESG Preferences
        st.markdown("#### 🌱 ESG Preferences")
        col3, col4 = st.columns(2)
        
        with col3:
            min_esg_score = st.slider(
                "Minimum ESG Score",
                min_value=0.0,
                max_value=10.0,
                value=st.session_state.form_data['min_esg_score'],
                step=0.1,
                key="form_esg_score"
            )
            
            carbon_neutral = st.checkbox(
                "Carbon Neutral Preference", 
                value=st.session_state.form_data['carbon_neutral'],
                key="form_carbon_neutral"
            )
        
        with col4:
            social_impact_weight = st.slider(
                "Social Impact Weight",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.form_data['social_impact_weight'],
                step=0.1,
                key="form_social_weight"
            )
            
            governance_weight = st.slider(
                "Governance Weight",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.form_data['governance_weight'],
                step=0.1,
                key="form_governance_weight"
            )
        
        # Submit button (outside form)
        if st.button("🚀 Submit Credit Request", key="submit_credit_request", use_container_width=True):
            self.submit_credit_request(
                amount, duration, purpose, annual_revenue,
                industry, urgency, min_esg_score, carbon_neutral,
                social_impact_weight, governance_weight
            )
    
    def submit_credit_request(self, amount, duration, purpose, annual_revenue, 
                            industry, urgency, min_esg_score, carbon_neutral,
                            social_impact_weight, governance_weight):
        """Submit credit request with progress tracking"""
        company_agent_url = self.get_company_agent_url(st.session_state.selected_company)
        
        if not company_agent_url:
            st.error("No company agent selected")
            return
        
        # Check if banks are discovered
        bank_count = 0
        if 'discovered_banks' in st.session_state:
            if isinstance(st.session_state.discovered_banks, dict):
                bank_count = st.session_state.discovered_banks.get('count', 0)
        
        if bank_count == 0:
            st.warning("Please discover bank agents first!")
            return
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Prepare credit intent
            credit_intent = {
                'company_name': st.session_state.selected_company,
                'company_id': self.company_agents[st.session_state.selected_company]['id'],
                'amount': amount,
                'duration_months': duration,
                'purpose': purpose,
                'annual_revenue': annual_revenue,
                'industry': industry,
                'esg_preferences': {
                    'min_esg_score': min_esg_score,
                    'carbon_neutral_preference': carbon_neutral,
                    'social_impact_weight': social_impact_weight,
                    'governance_weight': governance_weight
                },
                'urgency': urgency,
                'timestamp': datetime.now().isoformat()
            }
            
            status_text.text("📝 Preparing credit intent...")
            progress_bar.progress(20)
            
            # Broadcast credit intent
            status_text.text("📡 Broadcasting to bank agents...")
            progress_bar.progress(40)
            
            response = requests.post(
                f"{company_agent_url}/wfap/broadcast-intent",
                json=credit_intent,
                timeout=60
            )
            
            progress_bar.progress(80)
            status_text.text("📊 Processing offers...")
            
            if response.status_code == 200:
                result = response.json()
                offers = result.get('offers', [])
                st.session_state.offers = offers
                st.session_state.best_offer_shown = False  # Reset flag for new offers
                
                progress_bar.progress(100)
                status_text.text("✅ Credit request completed!")
                
                st.success(f"Received {len(offers)} offers from {result.get('banks_contacted', 0)} banks!")
                
                # Show quick summary and best offer
                if offers:
                    best_offer = min(offers, key=lambda x: x.get('carbon_adjusted_rate', 999))
                    self.display_best_offer(best_offer)
                    st.session_state.best_offer_shown = True
            else:
                progress_bar.progress(100)
                status_text.text("❌ Credit request failed!")
                st.error(f"Failed to submit credit request: {response.status_code}")
                
        except Exception as e:
            progress_bar.progress(100)
            status_text.text("❌ Credit request failed!")
            st.error(f"Error submitting credit request: {str(e)}")
        
        # Clear progress after 2 seconds
        time.sleep(2)
        progress_bar.empty()
        status_text.empty()
    
    def display_best_offer(self, best_offer):
        """Display the best offer in a prominent card"""
        st.markdown("#### 🏆 Best Offer Recommendation")
        
        bank_name = best_offer.get('bank_name', 'Unknown Bank')
        rate = best_offer.get('carbon_adjusted_rate', 0)
        amount = best_offer.get('approved_amount', 0)
        esg_score = best_offer.get('esg_score', {}).get('overall_score', 0)
        risk_rating = best_offer.get('risk_assessment', {}).get('overall_risk_rating', 'Unknown')
        confidence = best_offer.get('risk_assessment', {}).get('confidence_score', 0)
        
        # Create a prominent best offer display using Streamlit components
        st.markdown("---")
        
        # Header
        st.markdown("""
        <div style="text-align: center; margin: 20px 0;">
            <h2 style="color: #00d4ff; font-size: 2.5rem; text-shadow: 0 0 15px rgba(0, 212, 255, 0.5);">
                🏆 RECOMMENDED OFFER
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Main offer card using columns
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"""
            <div style="background: rgba(0, 212, 255, 0.1); border: 2px solid #00d4ff; 
                        border-radius: 15px; padding: 20px; text-align: center;">
                <h3 style="color: #00d4ff; margin: 0 0 10px 0;">🏦 {bank_name}</h3>
                <p style="color: #b0b0b0; margin: 0;">Bank ID: {best_offer.get('bank_id', 'Unknown')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: rgba(0, 255, 136, 0.1); border: 2px solid #00ff88; 
                        border-radius: 15px; padding: 20px; text-align: center;">
                <h3 style="color: #00ff88; margin: 0 0 10px 0; font-size: 3rem;">{rate:.2f}%</h3>
                <p style="color: #b0b0b0; margin: 0;">ESG-Adjusted Rate</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Metrics row
        col3, col4, col5, col6 = st.columns(4)
        
        with col3:
            st.metric("💰 Amount", f"${amount:,.0f}")
        
        with col4:
            st.metric("🌱 ESG Score", f"{esg_score:.1f}/10")
        
        with col5:
            st.metric("⚠️ Risk Rating", risk_rating.title())
        
        with col6:
            st.metric("🎯 Confidence", f"{confidence}/100")
        
        # Action button
        col7, col8, col9 = st.columns([1, 2, 1])
        with col8:
            # Create a unique key using timestamp and offer details
            import time
            unique_key = f"accept_best_offer_{int(time.time())}_{bank_name.replace(' ', '_')}_{rate}"
            if st.button("✅ ACCEPT THIS OFFER", key=unique_key, use_container_width=True):
                st.success(f"🎉 Offer accepted from {bank_name}!")
                st.balloons()
        
        st.markdown("---")
    
    def render_offers(self):
        """Render the offers with futuristic styling"""
        offers = st.session_state.offers
        
        if not offers:
            st.warning("No offers available")
            return
        
        # Overview metrics
        st.markdown("#### 📊 Offer Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Offers", len(offers))
        
        with col2:
            best_rate = min(offers, key=lambda x: x.get('carbon_adjusted_rate', 999))
            st.metric("Best Rate", f"{best_rate.get('carbon_adjusted_rate', 0):.2f}%")
        
        with col3:
            best_esg = max(offers, key=lambda x: x.get('esg_score', {}).get('overall_score', 0))
            st.metric("Best ESG", f"{best_esg.get('esg_score', {}).get('overall_score', 0):.1f}/10")
        
        with col4:
            avg_rate = sum(offer.get('carbon_adjusted_rate', 0) for offer in offers) / len(offers)
            st.metric("Average Rate", f"{avg_rate:.2f}%")
        
        # Offer cards
        st.markdown("#### 🏦 Available Offers")
        
        for i, offer in enumerate(offers, 1):
            with st.expander(f"🏦 {offer.get('bank_name', 'Unknown Bank')} - ${offer.get('approved_amount', 0):,.0f} at {offer.get('carbon_adjusted_rate', 0):.2f}%", expanded=(i==1)):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**💰 Amount:** ${offer.get('approved_amount', 0):,.2f}")
                    st.markdown(f"**📈 Interest Rate:** {offer.get('interest_rate', 0):.2f}%")
                    st.markdown(f"**🌱 ESG Rate:** {offer.get('carbon_adjusted_rate', 0):.2f}%")
                    st.markdown(f"**💳 Processing Fee:** ${offer.get('processing_fee', 0):,.2f}")
                    st.markdown(f"**🔒 Collateral:** {'Required' if offer.get('collateral_required', False) else 'Not Required'}")
                
                with col2:
                    esg_score = offer.get('esg_score', {})
                    st.markdown(f"**🌍 Environmental:** {esg_score.get('environmental_score', 0):.1f}/10")
                    st.markdown(f"**👥 Social:** {esg_score.get('social_score', 0):.1f}/10")
                    st.markdown(f"**⚖️ Governance:** {esg_score.get('governance_score', 0):.1f}/10")
                    st.markdown(f"**📊 Overall ESG:** {esg_score.get('overall_score', 0):.1f}/10")
                    
                    risk_assessment = offer.get('risk_assessment', {})
                    st.markdown(f"**⚠️ Risk Rating:** {risk_assessment.get('overall_risk_rating', 'Unknown')}")
                    st.markdown(f"**🎯 Confidence:** {risk_assessment.get('confidence_score', 0)}/100")
                
                # Action buttons
                col3, col4, col5 = st.columns(3)
                
                with col3:
                    bank_name = offer.get('bank_name', 'Unknown')
                    rate = offer.get('carbon_adjusted_rate', 0)
                    offer_id = offer.get('offer_id', f'offer_{i}')
                    if st.button(f"✅ Accept Offer", key=f"accept_{offer_id}_{i}"):
                        self.accept_offer(offer)
                
                with col4:
                    if st.button(f"📊 Compare", key=f"compare_{offer_id}_{i}"):
                        self.add_to_comparison(offer)
                
                with col5:
                    if st.button(f"📋 Details", key=f"details_{offer_id}_{i}"):
                        self.show_offer_details(offer)
    
    def accept_offer(self, offer):
        """Accept an offer"""
        st.success(f"✅ Offer accepted from {offer.get('bank_name', 'Unknown Bank')}!")
        st.balloons()
    
    def add_to_comparison(self, offer):
        """Add offer to comparison"""
        if 'comparison_offers' not in st.session_state:
            st.session_state.comparison_offers = []
        
        if offer not in st.session_state.comparison_offers:
            st.session_state.comparison_offers.append(offer)
            st.success(f"Added {offer.get('bank_name', 'Unknown Bank')} to comparison!")
        else:
            st.info("Offer already in comparison!")
    
    def show_offer_details(self, offer):
        """Show detailed offer information"""
        st.markdown("#### 📋 Detailed Offer Information")
        st.json(offer)
    
    def render_market_analysis_tab(self):
        """Render market analysis tab"""
        st.markdown("### 📊 Market Analysis")
        
        if 'offers' not in st.session_state or not st.session_state.offers:
            st.info("Submit a credit request to see market analysis")
            return
        
        offers = st.session_state.offers
        
        # Rate analysis chart
        st.markdown("#### 📈 Interest Rate Analysis")
        df = pd.DataFrame(offers)
        fig = px.bar(
            df, 
            x='bank_name', 
            y='carbon_adjusted_rate',
            title="Interest Rates by Bank",
            color='carbon_adjusted_rate',
            color_continuous_scale='viridis'
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # ESG analysis
        st.markdown("#### 🌱 ESG Score Analysis")
        esg_data = []
        for offer in offers:
            esg_score = offer.get('esg_score', {})
            esg_data.append({
                'Bank': offer.get('bank_name', 'Unknown'),
                'Environmental': esg_score.get('environmental_score', 0),
                'Social': esg_score.get('social_score', 0),
                'Governance': esg_score.get('governance_score', 0),
                'Overall': esg_score.get('overall_score', 0)
            })
        
        esg_df = pd.DataFrame(esg_data)
        fig = px.bar(
            esg_df,
            x='Bank',
            y=['Environmental', 'Social', 'Governance', 'Overall'],
            title="ESG Scores by Bank",
            barmode='group'
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def render_settings_tab(self):
        """Render settings tab"""
        st.markdown("### ⚙️ Settings")
        
        st.markdown("#### 🎨 Theme Settings")
        theme = st.selectbox("Select Theme", ["Futuristic", "Classic", "Dark"])
        
        st.markdown("#### 🔧 System Settings")
        auto_refresh = st.checkbox("Auto-refresh offers", value=False)
        notifications = st.checkbox("Enable notifications", value=True)
        
        st.markdown("#### 📊 Display Settings")
        show_esg_details = st.checkbox("Show detailed ESG information", value=True)
        show_risk_details = st.checkbox("Show detailed risk information", value=True)
        
        if st.button("💾 Save Settings"):
            st.success("Settings saved!")

# Main execution
if __name__ == "__main__":
    # Initialize the app
    app = WFAPDemo()
    
    # Run the app
    app.run()
