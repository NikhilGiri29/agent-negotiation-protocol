#!/usr/bin/env python3
"""
Test Streamlit integration with the updated system
"""
import requests
import json
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from shared.dynamic_loader import load_companies_from_csv

def test_streamlit_integration():
    """Test Streamlit app integration points"""
    print("🧪 Testing Streamlit Integration")
    print("=" * 50)
    
    # Load test data
    companies = load_companies_from_csv()
    if not companies:
        print("❌ No companies found in CSV data")
        return False
    
    company = companies[0]
    company_base_url = f"http://localhost:{company.api_url.split(':')[2].split('/')[0]}"
    print(f"📋 Testing with Company: {company.company_name} ({company.company_id})")
    print(f"🌐 Company Base URL: {company_base_url}")
    
    # Test 1: Company Agent Health Check (Streamlit style)
    print("\n1️⃣ Testing Company Agent Health (Streamlit style)...")
    try:
        response = requests.get(f"{company_base_url}/a2a/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Company Agent Health: {data.get('status', 'unknown')}")
        else:
            print(f"❌ Company Agent Health Failed: {response.status}")
            return False
    except Exception as e:
        print(f"❌ Company Agent Health Error: {e}")
        return False
    
    # Test 2: Bank Discovery (Streamlit style)
    print("\n2️⃣ Testing Bank Discovery (Streamlit style)...")
    try:
        response = requests.post(f"{company_base_url}/wfap/discover-banks", json={}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            bank_count = data.get('count', 0)
            print(f"✅ Discovered {bank_count} banks")
            
            # Test the data structure that Streamlit expects
            if isinstance(data, dict) and 'banks' in data:
                print("✅ Discovery result has correct structure for Streamlit")
                banks = data.get('banks', [])
                if banks:
                    print(f"✅ First bank: {banks[0].get('name', 'Unknown')}")
                    print(f"✅ Bank endpoint: {banks[0].get('endpoint', 'N/A')}")
            else:
                print("❌ Discovery result structure incorrect for Streamlit")
                return False
        else:
            print(f"❌ Bank Discovery Failed: {response.status}")
            return False
    except Exception as e:
        print(f"❌ Bank Discovery Error: {e}")
        return False
    
    # Test 3: Credit Intent Broadcasting (Streamlit style)
    print("\n3️⃣ Testing Credit Intent Broadcasting (Streamlit style)...")
    try:
        # Create a test credit intent
        test_intent = {
            "company_name": company.company_name,
            "company_id": company.company_id,
            "amount": 1000000,
            "duration_months": 24,
            "purpose": "working_capital",
            "annual_revenue": float(company.annual_revenue),
            "industry": company.industry,
            "esg_preferences": {
                "min_esg_score": 7.0,
                "carbon_neutral_preference": True,
                "social_impact_weight": 0.3,
                "governance_weight": 0.2
            },
            "urgency": "normal",
            "timestamp": "2025-09-21T22:15:00.000000"
        }
        
        response = requests.post(
            f"{company_base_url}/wfap/broadcast-intent",
            json=test_intent,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                offer_count = data.get('count', 0)
                print(f"✅ Broadcasting Successful: {offer_count} offers received")
                
                # Test the data structure that Streamlit expects
                if 'offers' in data and isinstance(data['offers'], list):
                    print("✅ Response has correct structure for Streamlit")
                    if data['offers']:
                        offer = data['offers'][0]
                        print(f"✅ First offer: {offer.get('bank_name', 'Unknown Bank')}")
                        print(f"✅ Offer amount: ${offer.get('approved_amount', 0):,.2f}")
                        print(f"✅ Offer rate: {offer.get('carbon_adjusted_rate', 0)}%")
                else:
                    print("❌ Response structure incorrect for Streamlit")
                    return False
            else:
                print(f"❌ Broadcasting Failed: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ Broadcasting Request Failed: {response.status}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Broadcasting Error: {e}")
        return False
    
    print("\n🎉 Streamlit Integration Test Successful!")
    print("✅ All Streamlit integration points are working correctly")
    return True

if __name__ == "__main__":
    print("Starting Streamlit Integration Test...")
    
    success = test_streamlit_integration()
    
    if success:
        print("\n✅ Streamlit app is ready to use!")
        print("Run: streamlit run streamlit_app.py")
        sys.exit(0)
    else:
        print("\n❌ Streamlit integration issues found!")
        sys.exit(1)
