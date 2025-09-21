#!/usr/bin/env python3
"""
Test script to verify the complete credit intent flow
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from shared.schema import CreditIntent, ESGPreferences, CreditPurpose
from shared.config import config

async def test_credit_intent_flow():
    """Test the complete credit intent flow from company to banks"""
    print("🧪 Testing Credit Intent Flow")
    print("=" * 60)
    
    # Create a test credit intent
    esg_preferences = ESGPreferences(
        min_esg_score=7.0,
        carbon_neutral_preference=True,
        social_impact_weight=0.3,
        governance_weight=0.2
    )
    
    intent = CreditIntent(
        company_id="cmp123",
        company_name="Test Company",
        amount=1000000.0,
        duration_months=24,
        purpose=CreditPurpose.WORKING_CAPITAL,
        annual_revenue=5000000.0,
        industry="Technology",
        esg_preferences=esg_preferences,
        urgency="normal"
    )
    
    print(f"📝 Test Credit Intent:")
    print(f"   Company: {intent.company_name} (ID: {intent.company_id})")
    print(f"   Amount: ${intent.amount:,.2f}")
    print(f"   Duration: {intent.duration_months} months")
    print(f"   Purpose: {intent.purpose}")
    print(f"   Industry: {intent.industry}")
    
    # Test 1: Check if company agent is running
    print(f"\n🔍 Step 1: Checking Company Agent Health")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://localhost:4000/a2a/health", timeout=5) as response:
                if response.status == 200:
                    print(f"   ✅ Company Agent is healthy")
                else:
                    print(f"   ❌ Company Agent returned status {response.status}")
                    return
    except Exception as e:
        print(f"   ❌ Company Agent not reachable: {e}")
        return
    
    # Test 2: Discover banks through company agent
    print(f"\n🔍 Step 2: Discovering Banks")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://localhost:4000/wfap/discover-banks", timeout=10) as response:
                if response.status == 200:
                    discovery_data = await response.json()
                    banks = discovery_data.get('banks', [])
                    print(f"   ✅ Discovered {len(banks)} banks")
                    for bank in banks:
                        print(f"      - {bank.get('name', 'Unknown')} (Port: {bank.get('bank_details', {}).get('port', 'N/A')})")
                else:
                    print(f"   ❌ Bank discovery failed with status {response.status}")
                    return
    except Exception as e:
        print(f"   ❌ Bank discovery error: {e}")
        return
    
    # Test 3: Check if third-party services are running
    print(f"\n🔍 Step 3: Checking Third-Party Services")
    services = [
        ("Registry", config.REGISTRY_PORT),
        ("Credit Bureau", config.CREDIT_BUREAU_PORT),
        ("ESG Regulator", config.ESG_REGUATOR_PORT),
        ("Market Info", config.MARKET_INFO_PORT)
    ]
    
    async with aiohttp.ClientSession() as session:
        for service_name, port in services:
            try:
                async with session.get(f"http://localhost:{port}/health", timeout=5) as response:
                    if response.status == 200:
                        print(f"   ✅ {service_name} is healthy")
                    else:
                        print(f"   ❌ {service_name} returned status {response.status}")
            except Exception as e:
                print(f"   ❌ {service_name} not reachable: {e}")
    
    # Test 4: Check if bank agents are running
    print(f"\n🔍 Step 4: Checking Bank Agents")
    for bank in config.BANKS:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{bank.port}/health", timeout=5) as response:
                    if response.status == 200:
                        print(f"   ✅ {bank.bank_name} is healthy")
                    else:
                        print(f"   ❌ {bank.bank_name} returned status {response.status}")
        except Exception as e:
            print(f"   ❌ {bank.bank_name} not reachable: {e}")
    
    # Test 5: Send credit intent to company agent
    print(f"\n🚀 Step 5: Sending Credit Intent")
    try:
        intent_data = {
            **intent.model_dump(),
            'timestamp': datetime.now().isoformat()
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://localhost:4000/wfap/broadcast-intent",
                json=intent_data,
                timeout=60
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Credit intent processed successfully")
                    print(f"   Status: {result.get('status', 'unknown')}")
                    
                    offers = result.get('offers', [])
                    print(f"   Offers received: {len(offers)}")
                    
                    for i, offer in enumerate(offers, 1):
                        if offer:
                            print(f"\n   📋 Offer {i}:")
                            print(f"      Bank: {offer.get('bank_name', 'Unknown')}")
                            print(f"      Amount: ${offer.get('approved_amount', 0):,.2f}")
                            print(f"      Rate: {offer.get('carbon_adjusted_rate', 0):.2f}%")
                            print(f"      Duration: {offer.get('duration_months', 0)} months")
                            print(f"      Offer ID: {offer.get('offer_id', 'N/A')}")
                        else:
                            print(f"   ❌ Offer {i}: Failed to process")
                else:
                    print(f"   ❌ Credit intent failed with status {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
    except Exception as e:
        print(f"   ❌ Credit intent error: {e}")
    
    print(f"\n🎉 Test completed!")

async def main():
    """Main test function"""
    try:
        await asyncio.wait_for(test_credit_intent_flow(), timeout=120)
    except asyncio.TimeoutError:
        print("❌ Test timed out after 2 minutes")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    print("🧪 WFAP Credit Intent Flow Test")
    print("Make sure all services are running before running this test.")
    print("Run: python start_thirdparty_services.py")
    print("Then: python initialize_registry.py")
    print("Then: python start_servers.py")
    print("=" * 60)
    
    asyncio.run(main())
