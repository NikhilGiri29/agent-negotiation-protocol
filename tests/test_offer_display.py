#!/usr/bin/env python3
"""
Test script to verify offer display structure
"""
import requests
import json
from datetime import datetime

def test_offer_structure():
    """Test the structure of offers returned by the system"""
    print("🧪 Testing Offer Structure")
    print("=" * 50)
    
    # Test credit intent
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
    
    print("📋 Testing with Company: Company A (cmp123)")
    
    # Test broadcasting
    try:
        response = requests.post(
            'http://localhost:4000/wfap/broadcast-intent',
            json=test_intent,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Broadcasting Successful: {data.get('count', 0)} offers received")
            
            offers = data.get('offers', [])
            if offers:
                print(f"\n📊 Sample Offer Structure:")
                print(f"Number of offers: {len(offers)}")
                
                # Show first offer structure
                first_offer = offers[0]
                print(f"\n🏦 First Offer Details:")
                print(f"  Bank Name: {first_offer.get('bank_name', 'N/A')}")
                print(f"  Bank ID: {first_offer.get('bank_id', 'N/A')}")
                print(f"  Approved Amount: ${first_offer.get('approved_amount', 0):,.2f}")
                print(f"  Interest Rate: {first_offer.get('interest_rate', 0):.2f}%")
                print(f"  ESG-Adjusted Rate: {first_offer.get('carbon_adjusted_rate', 0):.2f}%")
                print(f"  Processing Fee: ${first_offer.get('processing_fee', 0):,.2f}")
                print(f"  Collateral Required: {first_offer.get('collateral_required', False)}")
                
                # ESG Score details
                esg_score = first_offer.get('esg_score', {})
                print(f"\n🌱 ESG Score Details:")
                print(f"  Environmental: {esg_score.get('environmental_score', 0):.1f}/10")
                print(f"  Social: {esg_score.get('social_score', 0):.1f}/10")
                print(f"  Governance: {esg_score.get('governance_score', 0):.1f}/10")
                print(f"  Overall: {esg_score.get('overall_score', 0):.1f}/10")
                print(f"  Carbon Footprint: {esg_score.get('carbon_footprint_category', 'Unknown')}")
                
                # Risk Assessment details
                risk_assessment = first_offer.get('risk_assessment', {})
                print(f"\n🔍 Risk Assessment Details:")
                print(f"  Risk Rating: {risk_assessment.get('overall_risk_rating', risk_assessment.get('risk_rating', 'Unknown'))}")
                print(f"  Confidence: {risk_assessment.get('confidence_score', 0)}/100")
                
                # Terms and conditions
                print(f"\n📋 Terms & Conditions:")
                print(f"  Repayment Schedule: {first_offer.get('repayment_schedule', 'Monthly')}")
                print(f"  Grace Period: {first_offer.get('grace_period_days', 30)} days")
                print(f"  Early Repayment Penalty: {first_offer.get('early_repayment_penalty', False)}")
                
                # Additional fields
                if first_offer.get('esg_summary'):
                    print(f"  ESG Summary: {first_offer['esg_summary']}")
                if first_offer.get('pricing_rationale'):
                    print(f"  Pricing Rationale: {first_offer['pricing_rationale']}")
                
                print(f"\n✅ Offer structure is compatible with updated UI!")
            else:
                print("❌ No offers received")
        else:
            print(f"❌ Broadcasting Failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_offer_structure()
