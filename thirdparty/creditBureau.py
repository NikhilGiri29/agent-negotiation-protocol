from fastapi import FastAPI
from shared.schema import CreditInquiry, CreditBureau
from shared.config import config
import uvicorn

sample_credit_bureaus = {
    "companyA": {
        "company_id": "companyA",
        "credit_score": 720,
        "rating": "AAA",
        "history_summary": "Good standing"
    },
    "companyB": {
        "company_id": "companyB",
        "credit_score": 720,
        "rating": "AAA",
        "history_summary": "No major defaults"
    },
}

app = FastAPI(title="Credit Inquiry API", version="0.1")

@app.post("/inquiry", response_model=CreditBureau)
def credit_inquiry(payload: CreditInquiry):
    """
    Perform a credit inquiry and return company details.
    """
    bureau_data = sample_credit_bureaus.get(payload.company_id)

    if not bureau_data:
        return CreditBureau(company_id = payload.company_id,
                            credit_score = -1,
                            rating = "",
                            history_summary = "")

    return CreditBureau(**bureau_data)

def start_credit_api():
    print(f"[ThirdParty] Credit-API started on port: {config.CREDIT_BUREAU_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=config.CREDIT_BUREAU_PORT, reload=False)

def stop_credit_api():
    pass
