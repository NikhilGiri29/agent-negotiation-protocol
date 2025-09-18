from fastapi import FastAPI
from shared.schema import ESGInquiry, ESGRegulator
from shared.config import config
import uvicorn
from fastapi import FastAPI
import uvicorn

sample_esg_data = {
    "bankA": {
        "bank_id": "bankA",
        "environmental_score": 8.2,
        "social_score": 7.5,
        "governance_score": 8.0,
        "overall_score": 7.9,
        "carbon_footprint_category": "low",
        "sustainability_notes": "Strong renewable investment portfolio"
    },
    "bankB": {
        "bank_id": "bankB",
        "environmental_score": 5.5,
        "social_score": 6.0,
        "governance_score": 5.0,
        "overall_score": 5.5,
        "carbon_footprint_category": "high",
        "sustainability_notes": "Heavy exposure to coal sector"
    },
}

app = FastAPI(title="ESG Inquiry API", version="0.1")

@app.post("/inquiry", response_model=ESGRegulator)
def esg_inquiry(payload: ESGInquiry):
    """
    Perform an ESG inquiry and return regulator details.
    """
    esg_data = sample_esg_data.get(payload.bank_id)

    if not esg_data:
        return ESGRegulator(
            bank_id=payload.bank_id,
            environmental_score=-1,
            social_score=-1,
            governance_score=-1,
            overall_score=-1,
            carbon_footprint_category="unknown",
            sustainability_notes="No record found"
        )

    return ESGRegulator(**esg_data)

def start_esg_api():
    print(f"[ThirdParty] ESG-API started on port: {config.ESG_REGUATOR_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=config.ESG_REGUATOR_PORT, reload=False)

def stop_esg_api():
    pass
