#!/usr/bin/env python3
"""
Test direct bank agent call
"""
import requests
import json
from datetime import datetime

def test_bank_direct():
    # Test direct call to bank agent
    test_intent = {
        'company_name': 'Company A',
        'company_id': 'cmp123',
        'amount': 1000000,
        'duration_months': 24,
        'purpose': 'working_capital',
        'annual_revenue': 5000000.0,
        'industry': 'Technology',
        'esg_preferences': {
            'min_esg_score': 7.0,
            'carbon_neutral_preference': True,
            'social_impact_weight': 0.3,
            'governance_weight': 0.2
        },
        'urgency': 'normal',
        'timestamp': datetime.now().isoformat()
    }

    print('Testing direct call to Bank A...')
    try:
        response = requests.post(
            'http://localhost:9000/wfap/assess-credit',
            json=test_intent,
            timeout=30
        )
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            print(f'Success: {data.get("status")}')
            if data.get('offer'):
                print(f'Offer: {data["offer"].get("bank_name")} - ${data["offer"].get("approved_amount"):,.2f}')
        else:
            print(f'Error: {response.text}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    test_bank_direct()
