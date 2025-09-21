"""
Dynamic loader for banks and companies from CSV files
"""
import csv
import os
from typing import List, Dict, Optional
from .config import config, BankConfig
from .schema import CompanyRegister

def load_banks_from_csv() -> List[BankConfig]:
    """Load banks from CSV file with dynamic port assignment"""
    banks = []
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "banks.csv")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Banks CSV file not found: {csv_path}")
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            # Assign ports dynamically starting from BANK_PORT_START
            port = config.BANK_PORT_START + idx
            
            bank = BankConfig(
                bank_id=row['bank_id'],
                bank_name=row['bank_name'],
                max_loan_amount=float(row['max_loan_amount']),
                min_interest_rate=float(row['min_interest_rate']),
                reputation_score=int(row.get('reputation_score', 5)),
                risk_appetite=row.get('risk_appetite', 'moderate'),
                port=port
            )
            banks.append(bank)
    
    return banks

def load_companies_from_csv() -> List[CompanyRegister]:
    """Load companies from CSV file with dynamic port assignment"""
    companies = []
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "companies.csv")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Companies CSV file not found: {csv_path}")
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            # Assign ports dynamically starting from COMPANY_PORT_START
            port = config.COMPANY_PORT_START + idx
            
            company = CompanyRegister(
                company_id=row['company_id'],
                company_name=row['company_name'],
                annual_revenue=float(row['annual_revenue']),
                industry=row['industry'],
                api_url=f"http://localhost:{port}/a2a"
            )
            companies.append(company)
    
    return companies

def get_bank_by_id(bank_id: str) -> Optional[BankConfig]:
    """Get bank configuration by ID"""
    banks = load_banks_from_csv()
    return next((bank for bank in banks if bank.bank_id == bank_id), None)

def get_bank_by_port(port: int) -> Optional[BankConfig]:
    """Get bank configuration by port"""
    banks = load_banks_from_csv()
    return next((bank for bank in banks if bank.port == port), None)

def initialize_dynamic_config():
    """Initialize the global config with dynamic bank data"""
    try:
        config.BANKS = load_banks_from_csv()
        print(f"Loaded {len(config.BANKS)} banks from CSV")
        for bank in config.BANKS:
            print(f"  - {bank.bank_name} ({bank.bank_id}) on port {bank.port}")
    except Exception as e:
        print(f"Error loading banks: {e}")
        config.BANKS = []
