from fastapi import FastAPI, HTTPException
from shared.schema import ESGInquiry, ESGRegulator
from shared.config import config
import uvicorn
import csv
import os
import json
from typing import Dict, Any

# Load data from CSV file
def load_esg_data() -> Dict[str, Dict[str, Any]]:
    """Load ESG data from CSV file"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    csv_file = os.path.join(data_dir, "esg_regulator.csv")
    
    esg_data = {}
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                esg_data[row['bank_id']] = {
                    "bank_id": row['bank_id'],
                    "environmental_score": float(row['environmental_score']),
                    "social_score": float(row['social_score']),
                    "governance_score": float(row['governance_score']),
                    "overall_score": float(row['overall_score']),
                    "carbon_footprint_category": row['carbon_footprint_category'],
                    "sustainability_notes": row['sustainability_notes']
                }
        print(f"[ESG Regulator] Loaded {len(esg_data)} banks from CSV")
    except FileNotFoundError:
        print(f"[ESG Regulator] Warning: CSV file not found at {csv_file}")
    except Exception as e:
        print(f"[ESG Regulator] Error loading CSV: {str(e)}")
    
    return esg_data

# Load data on startup
ESG_DATA = load_esg_data()

app = FastAPI(title="ESG Regulator API", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "ESG Regulator",
            "banks_loaded": len(ESG_DATA),
            "port": config.ESG_REGUATOR_PORT
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/banks")
async def get_all_banks():
    """Get all banks in the ESG regulator database"""
    return {
        "banks": list(ESG_DATA.keys()),
        "count": len(ESG_DATA)
    }

@app.post("/inquiry", response_model=ESGRegulator)
def esg_inquiry(payload: ESGInquiry):
    """
    Perform an ESG inquiry and return regulator details.
    """
    esg_data = ESG_DATA.get(payload.bank_id)

    if not esg_data:
        return ESGRegulator(
            bank_id=payload.bank_id,
            environmental_score=-1,
            social_score=-1,
            governance_score=-1,
            overall_score=-1,
            carbon_footprint_category="unknown",
            sustainability_notes="Bank not found in ESG regulator database"
        )

    return ESGRegulator(**esg_data)

def start_esg_api():
    """Start the ESG regulator API"""
    print(f"[ThirdParty] ESG-API started on port: {config.ESG_REGUATOR_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=config.ESG_REGUATOR_PORT, reload=False)

if __name__ == "__main__":
    start_esg_api()
