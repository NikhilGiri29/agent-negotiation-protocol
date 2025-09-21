import asyncio
import aiohttp
import json
from shared.schema import BankRegister, CompanyRegister
from shared.a2a_schema import DiscoveryRequest, AgentRole
from shared.config import config
import time

async def retry_with_backoff(func, max_retries=5, initial_delay=1):
    """Retry a function with exponential backoff"""
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed, retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2
            
    print(f"All attempts failed: {last_exception}")
    return None

async def test_registration_and_discovery():
    """Test agent registration and discovery process with retry logic"""
    async with aiohttp.ClientSession() as session:
        # 1. First check registry health
        print("\n=== Checking Registry Health ===")
        async def check_health():
            async with session.get("http://localhost:8005/health") as response:
                if response.status != 200:
                    raise Exception(f"Health check failed with status {response.status}")
                health_data = await response.json()
                print(f"Registry Health: {json.dumps(health_data, indent=2)}")
                return health_data

        health_data = await retry_with_backoff(check_health)
        if not health_data:
            return

        # 2. Register a test bank
        print("\n=== Registering Test Bank ===")
        test_bank = BankRegister(
            bank_id="TEST_BANK",
            bank_name="Test Bank",
            max_loan_amount=1000000,
            min_interest_rate=5.0,
            api_url="http://localhost:8002/a2a"
        )
        
        async def register_bank():
            async with session.post(
                "http://localhost:8005/bankRegister",
                json=test_bank.model_dump()
            ) as response:
                if response.status != 200:
                    print(response)
                    raise Exception(f"Bank registration failed with status {response.status}")
                reg_data = await response.json()
                print(f"Bank Registration: {json.dumps(reg_data, indent=2)}")
                return reg_data

        bank_reg = await retry_with_backoff(register_bank)
        if not bank_reg:
            return

        # 3. Register a test company
        print("\n=== Registering Test Company ===")
        test_company = CompanyRegister(
            company_id="TEST_COMPANY",
            company_name="Test Company",
            annual_revenue=5000000,
            industry="Technology",
            api_url="http://localhost:8001/a2a"
        )
        
        async def register_company():
            async with session.post(
                "http://localhost:8005/companyRegister",
                json=test_company.model_dump()
            ) as response:
                if response.status != 200:
                    raise Exception(f"Company registration failed with status {response.status}")
                reg_data = await response.json()
                print(f"Company Registration: {json.dumps(reg_data, indent=2)}")
                return reg_data

        company_reg = await retry_with_backoff(register_company)
        if not company_reg:
            return

        # 4. Test discovery - looking for banks
        print("\n=== Testing Bank Discovery ===")
        discovery_req = DiscoveryRequest(
            requesting_agent_id="test-company",
            required_role=AgentRole.BANK
        )
        
        async def discover_banks():
            async with session.post(
                "http://localhost:8005/discovery",
                json=discovery_req.model_dump()
            ) as response:
                if response.status != 200:
                    raise Exception(f"Discovery failed with status {response.status}")
                disc_data = await response.json()
                print(f"Discovery Results: {json.dumps(disc_data, indent=2)}")
                return disc_data

        disc_data = await retry_with_backoff(discover_banks)
        if disc_data:
            print("\n=== Test Completed Successfully ===")

async def main():
    """Main function with timeout"""
    try:
        await asyncio.wait_for(test_registration_and_discovery(), timeout=30)
    except asyncio.TimeoutError:
        print("Test timed out after 30 seconds")
    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    print("Starting registration and discovery test...")
    asyncio.run(main())
