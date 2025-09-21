from fastapi import FastAPI, HTTPException
from shared.schema import CreditInquiry, CreditBureau
from shared.config import config
import uvicorn
import csv
import os
import json
from typing import Dict, Any

# Load data from CSV file
def load_credit_bureau_data() -> Dict[str, Dict[str, Any]]:
    """Load credit bureau data from CSV file"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    csv_file = os.path.join(data_dir, "credit_bureau.csv")
    
    credit_data = {}
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                credit_score = int(row['credit_score'])
                # Ensure credit score is valid (0-850 range)
                if credit_score < 0:
                    credit_score = 0
                elif credit_score > 850:
                    credit_score = 850
                    
                credit_data[row['company_id']] = {
                    "company_id": row['company_id'],
                    "credit_score": credit_score,
                    "rating": row['rating'],
                    "history_summary": row['history_summary']
                }
        print(f"[Credit Bureau] Loaded {len(credit_data)} companies from CSV")
    except FileNotFoundError:
        print(f"[Credit Bureau] Warning: CSV file not found at {csv_file}")
    except Exception as e:
        print(f"[Credit Bureau] Error loading CSV: {str(e)}")
    
    return credit_data

# Load data on startup
CREDIT_BUREAU_DATA = load_credit_bureau_data()

app = FastAPI(title="Credit Bureau API", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "Credit Bureau",
            "companies_loaded": len(CREDIT_BUREAU_DATA),
            "port": config.CREDIT_BUREAU_PORT
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/companies")
async def get_all_companies():
    """Get all companies in the credit bureau"""
    return {
        "companies": list(CREDIT_BUREAU_DATA.keys()),
        "count": len(CREDIT_BUREAU_DATA)
    }

@app.post("/inquiry", response_model=CreditBureau)
def credit_inquiry(payload: CreditInquiry):
    """
    Perform a credit inquiry and return company details.
    """
    bureau_data = CREDIT_BUREAU_DATA.get(payload.company_id)

    if not bureau_data:
        return CreditBureau(
            company_id=payload.company_id,
            credit_score=0,  # Use 0 instead of -1 for not found companies
            rating="Unknown",
            history_summary="Company not found in credit bureau"
        )

    return CreditBureau(**bureau_data)

def start_credit_api():
    """Start the credit bureau API"""
    print(f"[ThirdParty] Credit-API started on port: {config.CREDIT_BUREAU_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=config.CREDIT_BUREAU_PORT, reload=False)

if __name__ == "__main__":
    start_credit_api()
