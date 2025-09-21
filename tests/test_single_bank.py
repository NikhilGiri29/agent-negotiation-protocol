#!/usr/bin/env python3
"""
Test a single bank to verify the fixes
"""
import requests
import json
from datetime import datetime

def test_single_bank():
    """Test a single bank agent directly"""
    print("🧪 Testing Single Bank Agent")
    print("=" * 40)
    
    # Test credit intent
    test_intent = {
        'company_name': 'Company A',
        'company_id': 'cmp123',
        'amount': 500000,
        'duration_months': 12,
        'purpose': 'working_capital',
        'annual_revenue': 2000000.0,
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
    
    print("📋 Testing with Bank A (port 9000)")
    
    try:
        response = requests.post(
            'http://localhost:9000/wfap/assess-credit',
            json=test_intent,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Bank A responded successfully")
            
            # Check key fields
            print(f"\n📊 Offer Details:")
            print(f"  Bank: {data.get('bank_name', 'Unknown')}")
            print(f"  Amount: ${data.get('approved_amount', 0):,.2f}")
            print(f"  Interest Rate: {data.get('interest_rate', 0):.2f}%")
            print(f"  Carbon-Adjusted Rate: {data.get('carbon_adjusted_rate', 0):.2f}%")
            
            # Check risk assessment
            risk_assessment = data.get('risk_assessment', {})
            print(f"  Risk Rating: {risk_assessment.get('overall_risk_rating', risk_assessment.get('risk_rating', 'Unknown'))}")
            print(f"  Confidence: {risk_assessment.get('confidence_score', 0)}/100")
            
            # Check ESG score
            esg_score = data.get('esg_score', {})
            print(f"  ESG Score: {esg_score.get('overall_score', 0):.1f}/10")
            
            # Validate carbon_adjusted_rate is positive
            carbon_rate = data.get('carbon_adjusted_rate', 0)
            if carbon_rate > 0:
                print("✅ Carbon-adjusted rate is positive")
            else:
                print(f"❌ Carbon-adjusted rate is invalid: {carbon_rate}")
            
            # Validate risk rating is not "unknown"
            risk_rating = risk_assessment.get('overall_risk_rating', risk_assessment.get('risk_rating', 'Unknown'))
            if risk_rating.lower() != 'unknown':
                print("✅ Risk rating is properly set")
            else:
                print(f"❌ Risk rating is unknown: {risk_rating}")
                
        else:
            print(f"❌ Bank A failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing Bank A: {e}")

if __name__ == "__main__":
    test_single_bank()
