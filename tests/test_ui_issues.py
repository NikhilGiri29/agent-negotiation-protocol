#!/usr/bin/env python3
"""
Test to verify UI issues are fixed
"""

import requests
import json

def test_ui_flow():
    """Test the complete UI flow"""
    print("🧪 Testing UI Flow")
    print("=" * 50)
    
    # Test 1: Bank Discovery
    print("1️⃣ Testing Bank Discovery...")
    try:
        response = requests.post("http://localhost:4000/wfap/discover-banks", json={}, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Bank discovery: {result.get('count', 0)} banks found")
            
            # Check bank names
            banks = result.get('banks', [])
            for bank in banks:
                bank_name = bank.get('bank_details', {}).get('bank_name', bank.get('name', 'Unknown Bank'))
                print(f"   - {bank_name}")
        else:
            print(f"❌ Bank discovery failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Bank discovery error: {e}")
    
    # Test 2: Credit Request
    print("\n2️⃣ Testing Credit Request...")
    try:
        credit_intent = {
            'company_name': 'Company A',
            'company_id': 'cmp123',
            'amount': 1000000,
            'duration_months': 24,
            'purpose': 'working_capital',
            'annual_revenue': 15000000,
            'industry': 'Technology',
            'esg_preferences': {
                'min_esg_score': 7.0,
                'carbon_neutral_preference': True,
                'social_impact_weight': 0.3,
                'governance_weight': 0.2
            },
            'urgency': 'normal',
            'timestamp': '2025-01-22T10:00:00'
        }
        
        response = requests.post("http://localhost:4000/wfap/broadcast-intent", json=credit_intent, timeout=60)
        if response.status_code == 200:
            result = response.json()
            offers = result.get('offers', [])
            print(f"✅ Credit request: {len(offers)} offers received")
            
            if offers:
                # Find best offer
                best_offer = min(offers, key=lambda x: x.get('carbon_adjusted_rate', 999))
                print(f"   🏆 Best offer: {best_offer.get('bank_name', 'Unknown')} at {best_offer.get('carbon_adjusted_rate', 0):.2f}%")
        else:
            print(f"❌ Credit request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Credit request error: {e}")
    
    print("\n✅ UI flow test completed!")

if __name__ == "__main__":
    test_ui_flow()
