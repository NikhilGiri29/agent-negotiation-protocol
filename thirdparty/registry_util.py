from fastapi import FastAPI, HTTPException
from shared.schema import (
    RegistryBankList, BankRegister, CompanyRegister,
    AuthToken, CreditIntent
)
from shared.config import config
import uvicorn
from datetime import datetime, timedelta
import uuid
import json
import os

REGISTRY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "registry")
BANKS_FILE = os.path.join(REGISTRY_DIR, "registry_banks.json")
COMPANIES_FILE = os.path.join(REGISTRY_DIR, "registry_companies.json")
TOKENS_FILE = os.path.join(REGISTRY_DIR, "registry_tokens.json")

def load_data(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4, default=str)


app = FastAPI(title="Registry API", version="0.1")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        banks = load_data(BANKS_FILE)
        companies = load_data(COMPANIES_FILE)
        tokens = load_data(TOKENS_FILE)
        return {
            "status": "healthy",
            "registered_banks": len(banks),
            "registered_companies": len(companies),
            "active_tokens": len(tokens)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post("/bankRegister", response_model=str)
def bank_register(payload: BankRegister):
    """
    Register a Bank
    """
    banks = load_data(BANKS_FILE)

    if payload.bank_id in banks:
        raise HTTPException(status_code=400, detail="Bank already registered")

    banks[payload.bank_id] = payload.model_dump()
    save_data(BANKS_FILE, banks)

    return f"Bank {payload.bank_name} registered successfully."

@app.post("/discovery")
async def discover_agents(request: dict):
    """Handle agent discovery requests"""
    try:
        banks = load_data(BANKS_FILE)
        companies = load_data(COMPANIES_FILE)
        
        agents = []
        # Add bank agents
        for bank_id, bank_data in banks.items():
            agents.append({
                "agent_id": f"bank-{bank_id.lower()}",
                "name": bank_data["bank_name"],
                "role": "bank",
                "api_url": bank_data["api_url"]
            })
            
        # Add company agents
        for company_id, company_data in companies.items():
            agents.append({
                "agent_id": f"company-{company_id.lower()}",
                "name": company_data["company_name"],
                "role": "company",
                "api_url": company_data["api_url"]
            })
            
        return {"agents": agents}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Discovery error: {str(e)}"
        )

@app.post("/companyRegister", response_model=str)
def company_register(payload: CompanyRegister):
    """
    Register a Company
    """
    companies = load_data(COMPANIES_FILE)

    if payload.company_id in companies:
        raise HTTPException(status_code=400, detail="Company already registered")

    companies[payload.company_id] = payload.model_dump()

    save_data(COMPANIES_FILE, companies)

    return f"Company {payload.company_name} registered successfully."


@app.post("/getBankList", response_model=RegistryBankList)
def get_bank_list(payload: CreditIntent):
    """
    Check valid company from registry
    Search for available banks that can fulfill the intent
    Create a token, and store it associated with company and bank
    """
    banks = load_data(BANKS_FILE)
    companies = load_data(COMPANIES_FILE)
    tokens = load_data(TOKENS_FILE)

    if payload.company_id not in companies:
        raise HTTPException(status_code=404, detail="Company not registered")

    eligible_banks = []
    api_urls = []
    auth_tokens = []

    for bank_id, bank in banks.items():
        if payload.amount <= bank["max_loan_amount"]:
            # Basic filtering logic (can add ESG/interest rate later)
            token = AuthToken(
                token_id=str(uuid.uuid4()),
                company_id=payload.company_id,
                bank_id=bank_id,
                request_id=payload.intent_id,
                expiry=datetime.now() + timedelta(minutes=10),
                issued_by="Registry",
                scope="credit_offer"
            )
            eligible_banks.append(bank_id)
            api_urls.append(bank.get("api_url",""))
            auth_tokens.append(token.model_dump(mode="json"))

            tokens[token.token_id] = token.model_dump(mode="json")

    save_data(TOKENS_FILE, tokens)

    return RegistryBankList(
        bank_ids=eligible_banks,
        api_urls=api_urls,
        auth_tokens=[AuthToken(**t) for t in auth_tokens]
    )


@app.post("/validateToken", response_model=str)
def validate_token(payload: AuthToken):
    """
    Validate Token sent by company to bank
    """
    tokens = load_data(TOKENS_FILE)
    token = tokens.get(payload.token_id)

    if not token:
        raise HTTPException(status_code=404, detail="Invalid token")

    if datetime.fromisoformat(token["expiry"]) < datetime.now():
        raise HTTPException(status_code=400, detail="Token expired")

    return "Valid token"

@app.post("/validate-credit-intent")
async def validate_credit_intent(intent_data: dict):
    """Validate credit intent schema and business rules"""
    try:
        # Validate using Pydantic model
        intent = CreditIntent(**intent_data)
        
        # Business rule validations
        validation_errors = []
        
        # Check amount range
        if intent.amount < 1000:
            validation_errors.append("Minimum loan amount is $1,000")
        if intent.amount > 10000000:  # 10M max
            validation_errors.append("Maximum loan amount is $10,000,000")
        
        # Check duration range
        if intent.duration_months < 6:
            validation_errors.append("Minimum loan duration is 6 months")
        if intent.duration_months > 120:
            validation_errors.append("Maximum loan duration is 120 months")
        
        # Check revenue ratio
        if intent.annual_revenue and intent.annual_revenue > 0:
            debt_ratio = intent.amount / intent.annual_revenue
            if debt_ratio > 5.0:  # 5x revenue max
                validation_errors.append("Loan amount cannot exceed 5x annual revenue")
        
        if validation_errors:
            return {
                "valid": False,
                "errors": validation_errors,
                "message": "Credit intent validation failed"
            }
        else:
            return {
                "valid": True,
                "message": "Credit intent is valid",
                "intent_id": f"intent_{intent.company_id}_{intent.timestamp.strftime('%Y%m%d_%H%M%S')}"
            }
            
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Schema validation error: {str(e)}"],
            "message": "Invalid credit intent format"
        }

def create_registry_app():
    """Create the FastAPI application"""
    return app

async def start_registry_api():
    """Start the registry API asynchronously"""
    config = uvicorn.Config(app, host="127.0.0.1", port=config.REGISTRY_PORT, reload=False)
    server = uvicorn.Server(config)
    print(f"[ThirdParty] Registry-API starting on port: {config.REGISTRY_PORT}")
    await server.serve()

def initialize_registry_files():
    """Initialize registry files with empty data"""
    print("[ThirdParty] Initializing registry files...")
    for file in [BANKS_FILE, COMPANIES_FILE, TOKENS_FILE]:
        with open(file, "w") as f:
            json.dump({}, f, indent=4)
    print("[ThirdParty] Registry files initialized")

def run_registry():
    """Run the registry API (blocking)"""
    print(f"[ThirdParty] Registry-API starting on port: {config.REGISTRY_PORT}")
    initialize_registry_files()
    uvicorn.run(app, host="127.0.0.1", port=config.REGISTRY_PORT, reload=False)

if __name__ == "__main__":
    run_registry()
