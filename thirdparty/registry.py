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

BANKS_FILE = "registry_banks.json"
COMPANIES_FILE = "registry_companies.json"
TOKENS_FILE = "registry_tokens.json"

def load_data(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4, default=str)


app = FastAPI(title="Registry API", version="0.1")


@app.post("/bankRegister", response_model=str)
def bank_register(payload: BankRegister):
    """
    Register a Bank
    """
    banks = load_data(BANKS_FILE)

    if payload.bank_id in banks:
        raise HTTPException(status_code=400, detail="Bank already registered")

    banks[payload.bank_id] = payload.model_dump(mode="json")
    save_data(BANKS_FILE, banks)

    return f"Bank {payload.bank_name} registered successfully."


@app.post("/companyRegister", response_model=str)
def company_register(payload: CompanyRegister):
    """
    Register a Company
    """
    companies = load_data(COMPANIES_FILE)

    if payload.company_id in companies:
        raise HTTPException(status_code=400, detail="Company already registered")

    companies[payload.company_id] = payload.model_dump(mode="json")

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


def start_registry_api():
    print(f"[ThirdParty] Registry-API started on port: {config.REGISTRY_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=config.REGISTRY_PORT, reload=False)


def stop_registry_api():
    print("[ThirdParty] Registry-API stopped (manual termination required).")
    pass
