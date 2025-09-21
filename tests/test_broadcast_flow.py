#!/usr/bin/env python3
"""
Test the complete broadcast flow from company to banks
"""
import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from shared.schema import CreditIntent, CreditPurpose, ESGPreferences
from shared.dynamic_loader import load_companies_from_csv, load_banks_from_csv

async def test_complete_flow():
    """Test the complete broadcast flow"""
    print("🧪 Testing Complete Broadcast Flow")
    print("=" * 50)
    
    # Load test data
    companies = load_companies_from_csv()
    banks = load_banks_from_csv()
    
    if not companies or not banks:
        print("❌ No companies or banks found in CSV data")
        return False
    
    # Use first company for testing
    company = companies[0]
    # The company URL includes /a2a, but the WFAP endpoints are at the base port
    company_base_url = f"http://localhost:{company.api_url.split(':')[2].split('/')[0]}"
    print(f"📋 Testing with Company: {company.company_name} ({company.company_id})")
    print(f"🌐 Company Base URL: {company_base_url}")
    print(f"🌐 Company API URL: {company.api_url}")
    
    # Test 1: Company Agent Health Check
    print("\n1️⃣ Testing Company Agent Health...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{company_base_url}/a2a/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Company Agent Health: {data.get('status', 'unknown')}")
                else:
                    print(f"❌ Company Agent Health Failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Company Agent Health Error: {e}")
        return False
    
    # Test 2: Bank Discovery
    print("\n2️⃣ Testing Bank Discovery...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{company_base_url}/wfap/discover-banks", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    bank_count = data.get('count', 0)
                    print(f"✅ Discovered {bank_count} banks")
                    if bank_count == 0:
                        print("⚠️ No banks discovered - this may cause issues")
                else:
                    print(f"❌ Bank Discovery Failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Bank Discovery Error: {e}")
        return False
    
    # Test 3: Credit Intent Validation
    print("\n3️⃣ Testing Credit Intent Validation...")
    test_intent = CreditIntent(
        company_name=company.company_name,
        company_id=company.company_id,
        amount=1000000,
        duration_months=24,
        purpose=CreditPurpose.WORKING_CAPITAL,
        annual_revenue=float(company.annual_revenue),
        industry=company.industry,
        esg_preferences=ESGPreferences(
            min_esg_score=7.0,
            carbon_neutral_preference=True,
            social_impact_weight=0.3,
            governance_weight=0.2
        ),
        urgency="normal"
    )
    
    # Test registry validation directly
    try:
        # Convert datetime to ISO string for JSON serialization
        intent_data = test_intent.model_dump()
        intent_data['timestamp'] = test_intent.timestamp.isoformat()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://localhost:8005/validate-credit-intent",
                json=intent_data,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('valid', False):
                        print(f"✅ Credit Intent Validation: {data.get('message', 'Valid')}")
                    else:
                        print(f"❌ Credit Intent Validation Failed: {data.get('errors', [])}")
                        return False
                else:
                    print(f"❌ Registry Validation Failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Registry Validation Error: {e}")
        return False
    
    # Test 4: Credit Intent Broadcasting
    print("\n4️⃣ Testing Credit Intent Broadcasting...")
    try:
        # Convert datetime to ISO string for JSON serialization
        intent_data = test_intent.model_dump()
        intent_data['timestamp'] = test_intent.timestamp.isoformat()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{company_base_url}/wfap/broadcast-intent",
                json=intent_data,
                timeout=60
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'success':
                        offer_count = data.get('count', 0)
                        print(f"✅ Broadcasting Successful: {offer_count} offers received")
                        
                        # Display offers
                        offers = data.get('offers', [])
                        if offers:
                            print("\n📊 Received Offers:")
                            for i, offer in enumerate(offers, 1):
                                print(f"  {i}. {offer.get('bank_name', 'Unknown Bank')}")
                                print(f"     Amount: ${offer.get('approved_amount', 0):,.2f}")
                                print(f"     Rate: {offer.get('carbon_adjusted_rate', 0)}%")
                                print(f"     ESG: {offer.get('esg_score', {}).get('overall_score', 0)}/10")
                        else:
                            print("⚠️ No offers received from banks")
                    else:
                        print(f"❌ Broadcasting Failed: {data.get('message', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ Broadcasting Request Failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Broadcasting Error: {e}")
        return False
    
    print("\n🎉 Complete Flow Test Successful!")
    return True

async def test_bank_agents():
    """Test individual bank agents"""
    print("\n🏦 Testing Bank Agents...")
    banks = load_banks_from_csv()
    
    for bank in banks[:2]:  # Test first 2 banks
        print(f"\nTesting {bank.bank_name} on port {bank.port}...")
        try:
            async with aiohttp.ClientSession() as session:
                # Test health
                async with session.get(f"http://localhost:{bank.port}/a2a/health", timeout=5) as response:
                    if response.status == 200:
                        print(f"✅ {bank.bank_name} Health: OK")
                    else:
                        print(f"❌ {bank.bank_name} Health: Failed ({response.status})")
        except Exception as e:
            print(f"❌ {bank.bank_name} Error: {e}")

if __name__ == "__main__":
    print("Starting Broadcast Flow Test...")
    print(f"Test time: {datetime.now().isoformat()}")
    
    # Run tests
    success = asyncio.run(test_complete_flow())
    asyncio.run(test_bank_agents())
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
