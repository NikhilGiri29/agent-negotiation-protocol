#!/usr/bin/env python3
"""
Test script for the WFAP system
"""
import asyncio
import aiohttp
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from shared.dynamic_loader import load_banks_from_csv, load_companies_from_csv

async def test_service(port: int, service_name: str, is_third_party: bool = False) -> bool:
    """Test if a service is running"""
    try:
        # Use different health endpoints for different service types
        health_endpoint = "/health" if is_third_party else "/a2a/health"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://localhost:{port}{health_endpoint}", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"OK: {service_name} on port {port} - {data.get('status', 'unknown')}")
                    return True
                else:
                    print(f"ERROR: {service_name} on port {port} - Status {response.status}")
                    return False
    except Exception as e:
        print(f"ERROR: {service_name} on port {port} - {str(e)}")
        return False

async def main():
    """Test all services"""
    print("Testing WFAP System")
    print("=" * 50)
    
    # Test third-party services
    print("\nThird-Party Services:")
    from shared.config import config
    
    await test_service(config.REGISTRY_PORT, "Registry Service", is_third_party=True)
    await test_service(config.CREDIT_BUREAU_PORT, "Credit Bureau", is_third_party=True)
    await test_service(config.ESG_REGUATOR_PORT, "ESG Regulator", is_third_party=True)
    await test_service(config.MARKET_INFO_PORT, "Market Info", is_third_party=True)
    
    # Test dynamic banks
    print("\nBank Agents:")
    banks = load_banks_from_csv()
    for bank in banks:
        await test_service(bank.port, f"Bank - {bank.bank_name}")
    
    # Test dynamic companies
    print("\nCompany Agents:")
    companies = load_companies_from_csv()
    for company in companies:
        company_port = int(company.api_url.split(':')[2].split('/')[0])
        await test_service(company_port, f"Company - {company.company_name}")
    
    print("\nTest Complete!")

if __name__ == "__main__":
    asyncio.run(main())
