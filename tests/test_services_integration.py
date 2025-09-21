#!/usr/bin/env python3
"""
Test script to verify all third-party services are working correctly
"""

import asyncio
import aiohttp
import json
import time
from shared.config import config

async def test_service_health(service_name: str, port: int, endpoint: str = "/health"):
    """Test if a service is healthy"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://localhost:{port}{endpoint}", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ {service_name} (port {port}): {data.get('status', 'unknown')}")
                    return True, data
                else:
                    print(f"❌ {service_name} (port {port}): HTTP {response.status}")
                    return False, None
    except Exception as e:
        print(f"❌ {service_name} (port {port}): {str(e)}")
        return False, None

async def test_service_endpoints():
    """Test all service endpoints"""
    print("🔍 Testing Third-Party Services")
    print("=" * 50)
    
    services = [
        ("Registry", config.REGISTRY_PORT, "/health"),
        ("Credit Bureau", config.CREDIT_BUREAU_PORT, "/health"),
        ("ESG Regulator", config.ESG_REGUATOR_PORT, "/health"),
        ("Market Info", config.MARKET_INFO_PORT, "/health")
    ]
    
    results = {}
    for service_name, port, endpoint in services:
        is_healthy, data = await test_service_health(service_name, port, endpoint)
        results[service_name] = {"healthy": is_healthy, "data": data}
    
    return results

async def test_registry_functionality():
    """Test registry-specific functionality"""
    print("\n🏛️ Testing Registry Functionality")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test discovery endpoint
            discovery_request = {
                "requesting_agent_id": "test-agent",
                "required_role": "bank"
            }
            
            async with session.post(
                f"http://localhost:{config.REGISTRY_PORT}/discovery",
                json=discovery_request,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Discovery endpoint working: {len(data.get('agents', []))} agents found")
                else:
                    print(f"❌ Discovery endpoint failed: HTTP {response.status}")
                    
    except Exception as e:
        print(f"❌ Registry functionality test failed: {str(e)}")

async def test_credit_bureau_functionality():
    """Test credit bureau functionality"""
    print("\n💳 Testing Credit Bureau Functionality")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test companies endpoint
            async with session.get(f"http://localhost:{config.CREDIT_BUREAU_PORT}/companies", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Companies endpoint: {data.get('count', 0)} companies loaded")
                else:
                    print(f"❌ Companies endpoint failed: HTTP {response.status}")
            
            # Test inquiry endpoint
            inquiry_request = {"company_id": "cmp123"}
            async with session.post(
                f"http://localhost:{config.CREDIT_BUREAU_PORT}/inquiry",
                json=inquiry_request,
                timeout=5
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Inquiry endpoint: Company {data.get('company_id')} has score {data.get('credit_score')}")
                else:
                    print(f"❌ Inquiry endpoint failed: HTTP {response.status}")
                    
    except Exception as e:
        print(f"❌ Credit Bureau functionality test failed: {str(e)}")

async def test_esg_regulator_functionality():
    """Test ESG regulator functionality"""
    print("\n🌱 Testing ESG Regulator Functionality")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test banks endpoint
            async with session.get(f"http://localhost:{config.ESG_REGUATOR_PORT}/banks", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Banks endpoint: {data.get('count', 0)} banks loaded")
                else:
                    print(f"❌ Banks endpoint failed: HTTP {response.status}")
            
            # Test inquiry endpoint
            inquiry_request = {"bank_id": "B001"}
            async with session.post(
                f"http://localhost:{config.ESG_REGUATOR_PORT}/inquiry",
                json=inquiry_request,
                timeout=5
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Inquiry endpoint: Bank {data.get('bank_id')} has ESG score {data.get('overall_score')}")
                else:
                    print(f"❌ Inquiry endpoint failed: HTTP {response.status}")
                    
    except Exception as e:
        print(f"❌ ESG Regulator functionality test failed: {str(e)}")

async def test_market_info_functionality():
    """Test market info functionality"""
    print("\n📈 Testing Market Info Functionality")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test companies endpoint
            async with session.get(f"http://localhost:{config.MARKET_INFO_PORT}/companies", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Companies endpoint: {data.get('count', 0)} companies loaded")
                else:
                    print(f"❌ Companies endpoint failed: HTTP {response.status}")
            
            # Test inquiry endpoint
            inquiry_request = {"company_id": "cmp123"}
            async with session.post(
                f"http://localhost:{config.MARKET_INFO_PORT}/inquiry",
                json=inquiry_request,
                timeout=5
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Inquiry endpoint: Company {data.get('company_id')} is public: {data.get('is_public')}")
                else:
                    print(f"❌ Inquiry endpoint failed: HTTP {response.status}")
                    
    except Exception as e:
        print(f"❌ Market Info functionality test failed: {str(e)}")

async def main():
    """Main test function"""
    print("🧪 WFAP Services Integration Test")
    print("=" * 60)
    print("This script tests all third-party services to ensure they're working correctly.")
    print("Make sure all services are running before running this test.\n")
    
    # Wait a moment for services to be ready
    print("⏳ Waiting for services to be ready...")
    await asyncio.sleep(2)
    
    # Test service health
    health_results = await test_service_endpoints()
    
    # Test specific functionality
    await test_registry_functionality()
    await test_credit_bureau_functionality()
    await test_esg_regulator_functionality()
    await test_market_info_functionality()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    healthy_services = sum(1 for result in health_results.values() if result["healthy"])
    total_services = len(health_results)
    
    print(f"Services tested: {total_services}")
    print(f"Healthy services: {healthy_services}")
    print(f"Unhealthy services: {total_services - healthy_services}")
    
    if healthy_services == total_services:
        print("\n🎉 All services are working correctly!")
        print("✅ You can now run 'python initialize_registry.py' to register banks and companies")
    else:
        print("\n⚠️  Some services are not working. Please check the logs above.")
        print("💡 Make sure all services are started with: python start_thirdparty_services.py")

if __name__ == "__main__":
    asyncio.run(main())
