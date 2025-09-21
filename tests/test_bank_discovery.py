#!/usr/bin/env python3
"""
Test bank discovery to verify bank names are displayed correctly
"""

import requests
import json

def test_bank_discovery():
    """Test bank discovery and display results"""
    print("🧪 Testing Bank Discovery")
    print("=" * 50)
    
    # Test company agent discovery
    company_agent_url = "http://localhost:4000"
    
    try:
        print("📡 Discovering banks...")
        response = requests.post(
            f"{company_agent_url}/wfap/discover-banks",
            json={},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Discovery successful: {result.get('count', 0)} banks found")
            
            banks = result.get('banks', [])
            print("\n🏦 Discovered Banks:")
            print("-" * 30)
            
            for i, bank in enumerate(banks, 1):
                bank_name = bank.get('bank_details', {}).get('bank_name', bank.get('name', 'Unknown Bank'))
                bank_id = bank.get('agent_id', 'Unknown ID')
                print(f"{i}. {bank_name} (ID: {bank_id})")
                
                # Show bank details
                bank_details = bank.get('bank_details', {})
                if bank_details:
                    print(f"   - Bank Name: {bank_details.get('bank_name', 'N/A')}")
                    print(f"   - Bank ID: {bank_details.get('bank_id', 'N/A')}")
                    print(f"   - Risk Appetite: {bank_details.get('risk_appetite', 'N/A')}")
                    print(f"   - Min Interest Rate: {bank_details.get('min_interest_rate', 'N/A')}%")
                print()
        else:
            print(f"❌ Discovery failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_bank_discovery()
