import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from shared.schema import CreditIntent, CreditPurpose, ESGPreferences
from shared.config import config
import asyncio
import aiohttp
import os

# Page configuration
st.set_page_config(
    page_title="WFAP Dashboard",
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
    .status-success { color: #28a745; font-weight: bold; }
    .status-processing { color: #ffc107; font-weight: bold; }
    .status-error { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

class WFAPDashboard:
    def __init__(self):
        self.company_agent_url = f"http://{config.COMPANY_AGENT_HOST}:{config.COMPANY_AGENT_PORT}"
        
        # Initialize session state
        if 'page' not in st.session_state:
            st.session_state.page = 'admin'
        if 'request_history' not in st.session_state:
            st.session_state.request_history = []
        if 'current_request' not in st.session_state:
            st.session_state.current_request = None
        if 'discovered_banks' not in st.session_state:
            st.session_state.discovered_banks = []
            
    def load_registry_data(self):
        """Load data from registry files"""
        registry_dir = os.path.join(os.path.dirname(__file__), "data", "registry")
        try:
            # Load banks
            with open(os.path.join(registry_dir, "registry_banks.json"), 'r') as f:
                banks = json.load(f)
            
            # Load companies
            with open(os.path.join(registry_dir, "registry_companies.json"), 'r') as f:
                companies = json.load(f)
            
            # Load tokens
            with open(os.path.join(registry_dir, "registry_tokens.json"), 'r') as f:
                tokens = json.load(f)
                
            # Load port assignments
            with open(os.path.join(registry_dir, "port_assignments.json"), 'r') as f:
                ports = json.load(f)
                
            return banks, companies, tokens, ports
        except Exception as e:
            st.error(f"Error loading registry data: {str(e)}")
            return {}, {}, {}, {}

    def render_header(self):
        """Render main application header"""
        st.markdown("""
        <div class="main-header">
            <h1>🏦 WFAP Dashboard</h1>
        </div>
        """, unsafe_allow_html=True)

    def render_sidebar(self):
        """Render sidebar with navigation and controls"""
        st.sidebar.markdown("## 🎛️ Navigation")
        
        # Dashboard selection
        dashboard = st.sidebar.radio(
            "Select Dashboard",
            ["Admin Dashboard", "Company Dashboard"],
            key="dashboard_selection"
        )
        
        st.session_state.page = 'admin' if dashboard == "Admin Dashboard" else 'company'
        
        if st.session_state.page == 'admin':
            st.sidebar.markdown("### 🔧 Admin Tools")
            if st.sidebar.button("🔄 Refresh Registry Data"):
                self.load_registry_data()
        else:
            # Company selection for company dashboard
            companies = self.load_companies()
            selected_company = st.sidebar.selectbox(
                "Select Company",
                options=[comp["company_name"] for comp in companies],
                key="company_selection"
            )

    def render_admin_dashboard(self):
        """Render the admin dashboard"""
        st.markdown("## 👨‍💼 Admin Dashboard")
        
        # Load registry data
        banks, companies, tokens, ports = self.load_registry_data()
        
        # System Overview
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Active Banks", len(banks))
        with col2:
            st.metric("Registered Companies", len(companies))
        with col3:
            st.metric("Active Tokens", len(tokens))
        with col4:
            active_sessions = len([t for t in tokens.values() 
                                if datetime.fromisoformat(t['expiry']) > datetime.now()])
            st.metric("Active Sessions", active_sessions)

        # Detailed Analysis Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "Bank Analysis", 
            "Company Overview", 
            "Transaction History",
            "System Health"
        ])
        
        with tab1:
            st.markdown("### 🏦 Bank Analysis")
            
            # Bank metrics visualization
            if banks:
                # Create a port lookup dictionary from the ports list
                bank_ports = {bank['bank_id']: bank['port'] for bank in ports.get('banks', [])}
                
                bank_df = pd.DataFrame([{
                    'Bank Name': data['bank_name'],
                    'Max Loan': float(data['max_loan_amount']),
                    'Min Rate': float(data['min_interest_rate']),
                    'Port': bank_ports.get(bank_id, 'N/A')
                } for bank_id, data in banks.items()])
                
                fig = px.bar(
                    bank_df,
                    x='Bank Name',
                    y='Max Loan',
                    text='Min Rate',
                    title='Bank Lending Capacity & Rates',
                    labels={'Max Loan': 'Maximum Loan Amount ($)', 'Min Rate': 'Minimum Interest Rate (%)'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Bank details table
                st.dataframe(bank_df)
            
        with tab2:
            st.markdown("### 🏢 Company Overview")
            
            if companies:
                # Create a port lookup dictionary from the ports list
                company_ports = {company['company_id']: company['port'] for company in ports.get('companies', [])}
                
                company_df = pd.DataFrame([{
                    'Company Name': data['company_name'],
                    'Industry': data['industry'],
                    'Annual Revenue': float(data['annual_revenue']),
                    'Port': company_ports.get(company_id, 'N/A')
                } for company_id, data in companies.items()])
                
                # Industry distribution
                fig = px.pie(
                    company_df,
                    names='Industry',
                    title='Company Distribution by Industry'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Company details table
                st.dataframe(company_df)
        
        with tab3:
            st.markdown("### 📊 Transaction History")
            
            # Token analysis
            if tokens:
                token_df = pd.DataFrame([{
                    'Token ID': tid,
                    'Company ID': t['company_id'],
                    'Bank ID': t['bank_id'],
                    'Expiry': datetime.fromisoformat(t['expiry']),
                    'Status': 'Active' if datetime.fromisoformat(t['expiry']) > datetime.now() else 'Expired'
                } for tid, t in tokens.items()])
                
                # Token status chart
                fig = px.pie(
                    token_df,
                    names='Status',
                    title='Token Status Distribution'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Recent transactions table
                st.dataframe(token_df.sort_values('Expiry', ascending=False).head(10))
        
        with tab4:
            st.markdown("### ⚡ System Health")
            
            # Port usage analysis
            if ports:
                st.markdown("#### 🔌 Port Usage")
                # Create DataFrames from the ports lists
                bank_ports = pd.DataFrame(ports.get('banks', []))
                company_ports = pd.DataFrame(ports.get('companies', []))
                
                if not bank_ports.empty and not company_ports.empty:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Bank Ports**")
                        st.dataframe(bank_ports[['bank_id', 'bank_name', 'port']] if 'bank_id' in bank_ports.columns else bank_ports)
                    with col2:
                        st.markdown("**Company Ports**")
                        st.dataframe(company_ports[['company_id', 'company_name', 'port']] if 'company_id' in company_ports.columns else company_ports)
                else:
                    st.info("No port assignments found")
            
            # Service health checks
            st.markdown("#### 🚥 Service Status")
            health_status = self.check_system_health()
            for service, status in health_status.items():
                st.markdown(f"{'✅' if status else '❌'} {service}")

    def check_system_health(self) -> Dict[str, bool]:
        """Check health status of system components"""
        return {
            "Registry Service": self.check_service_health(config.REGISTRY_PORT),
            "Credit Bureau": self.check_service_health(config.CREDIT_BUREAU_PORT),
            "ESG Regulator": self.check_service_health(config.ESG_REGUATOR_PORT),
            "Market Info": self.check_service_health(config.MARKET_INFO_PORT)
        }
    
    def check_service_health(self, port: int) -> bool:
        """Check health of a specific service"""
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def load_companies(self):
        """Load company data from registry"""
        registry_dir = os.path.join(os.path.dirname(__file__), "data", "registry")
        try:
            with open(os.path.join(registry_dir, "registry_companies.json"), 'r') as f:
                companies = json.load(f)
            return [{"company_id": k, **v} for k, v in companies.items()]
        except:
            return []

    def main(self):
        """Main application entry point"""
        self.render_header()
        self.render_sidebar()
        
        if st.session_state.page == 'admin':
            self.render_admin_dashboard()
        else:
            # Import and use the existing company dashboard
            from streamlit_app import WFAPDemo
            company_dashboard = WFAPDemo()
            company_dashboard.render_credit_request_form()

if __name__ == "__main__":
    dashboard = WFAPDashboard()
    dashboard.main()
