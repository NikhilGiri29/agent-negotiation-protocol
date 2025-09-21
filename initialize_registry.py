import asyncio
import aiohttp
import os
from shared.schema import BankRegister, CompanyRegister
from shared.config import config
from shared.dynamic_loader import load_banks_from_csv, load_companies_from_csv

# Load data from CSV files using dynamic loader
BANKS = []
COMPANIES = []

def load_banks():
    """Load banks from CSV file using dynamic loader"""
    global BANKS
    bank_configs = load_banks_from_csv()
    BANKS = []
    for bank_config in bank_configs:
        BANKS.append(BankRegister(
            bank_id=bank_config.bank_id,
            bank_name=bank_config.bank_name,
            max_loan_amount=bank_config.max_loan_amount,
            min_interest_rate=bank_config.min_interest_rate,
            api_url=f"http://localhost:{bank_config.port}/a2a"
        ))
    return BANKS

def load_companies():
    """Load companies from CSV file using dynamic loader"""
    global COMPANIES
    COMPANIES = load_companies_from_csv()
    return COMPANIES

# Load data from CSV files
BANKS = load_banks()
COMPANIES = load_companies()

# Save port assignments for reference
def save_port_assignments():
    """Save port assignments to a file for reference"""
    assignments = {
        "banks": [{"bank_id": b.bank_id, "bank_name": b.bank_name, 
                  "port": int(b.api_url.split(':')[2].split('/')[0])} 
                 for b in BANKS],
        "companies": [{"company_id": c.company_id, "company_name": c.company_name, 
                      "port": int(c.api_url.split(':')[2].split('/')[0])} 
                     for c in COMPANIES]
    }
    
    port_file = os.path.join(os.path.dirname(__file__), "data", "registry", "port_assignments.json")
    with open(port_file, "w") as f:
        import json
        json.dump(assignments, f, indent=2)

async def register_entities():
    """Register all banks and companies with the registry"""
    # Save port assignments before registration
    save_port_assignments()
    
    async with aiohttp.ClientSession() as session:
        # First check if registry is up
        try:
            async with session.get(f"http://localhost:{config.REGISTRY_PORT}/health") as response:
                if response.status != 200:
                    print("Registry service is not responding. Make sure it's running.")
                    return
                print("Registry service is healthy, proceeding with registration...")
        except aiohttp.ClientError:
            print("Could not connect to registry service. Make sure it's running.")
            return

        # Register banks
        print("\nRegistering banks...")
        for bank in BANKS:
            try:
                async with session.post(
                    f"http://localhost:{config.REGISTRY_PORT}/bankRegister",
                    json=bank.model_dump()
                ) as response:
                    if response.status == 200:
                        print(f"OK: Successfully registered {bank.bank_name}")
                    else:
                        print(f"ERROR: Failed to register {bank.bank_name}: {response.status}")
            except Exception as e:
                print(f"ERROR: Error registering {bank.bank_name}: {str(e)}")

        # Register companies
        print("\nRegistering companies...")
        for company in COMPANIES:
            try:
                async with session.post(
                    f"http://localhost:{config.REGISTRY_PORT}/companyRegister",
                    json=company.model_dump()
                ) as response:
                    if response.status == 200:
                        print(f"OK: Successfully registered {company.company_name}")
                    else:
                        print(f"ERROR: Failed to register {company.company_name}: {response.status}")
            except Exception as e:
                print(f"ERROR: Error registering {company.company_name}: {str(e)}")

        # Verify final state
        print("\nVerifying registry state...")
        async with session.get(f"http://localhost:{config.REGISTRY_PORT}/health") as response:
            health_data = await response.json()
            print(f"Registry Health Check:")
            print(f"- Registered Banks: {health_data.get('registered_banks', 0)}")
            print(f"- Registered Companies: {health_data.get('registered_companies', 0)}")
            print(f"- Active Tokens: {health_data.get('active_tokens', 0)}")

if __name__ == "__main__":
    print("Starting registry initialization...")
    asyncio.run(register_entities())
