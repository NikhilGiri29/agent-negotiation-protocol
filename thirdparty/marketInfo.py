from fastapi import FastAPI, HTTPException
from shared.schema import MarketInquiry, MarketData
from shared.config import config
import uvicorn
import csv
import os
import json
from typing import Dict, Any, Optional

# Load data from CSV file
def load_market_data() -> Dict[str, Dict[str, Any]]:
    """Load market data from CSV file"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    csv_file = os.path.join(data_dir, "market_data.csv")
    
    market_data = {}
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle None values for non-public companies
                stock_price = float(row['weekly_stock_price_hist']) if row['weekly_stock_price_hist'] and row['weekly_stock_price_hist'] != 'None' else None
                market_cap = float(row['market_cap']) if row['market_cap'] and row['market_cap'] != 'None' else None
                pe_ratio = float(row['pe_ratio']) if row['pe_ratio'] and row['pe_ratio'] != 'None' else None
                
                market_data[row['company_id']] = {
                    "company_id": row['company_id'],
                    "is_public": row['is_public'].lower() == 'true',
                    "weekly_stock_price_hist": [stock_price] if stock_price else None,
                    "market_cap": market_cap,
                    "pe_ratio": pe_ratio
                }
        print(f"[Market Info] Loaded {len(market_data)} companies from CSV")
    except FileNotFoundError:
        print(f"[Market Info] Warning: CSV file not found at {csv_file}")
    except Exception as e:
        print(f"[Market Info] Error loading CSV: {str(e)}")
    
    return market_data

# Load data on startup
MARKET_DATA = load_market_data()

app = FastAPI(title="Market Info API", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "Market Info",
            "companies_loaded": len(MARKET_DATA),
            "port": config.MARKET_INFO_PORT
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/companies")
async def get_all_companies():
    """Get all companies in the market data database"""
    return {
        "companies": list(MARKET_DATA.keys()),
        "count": len(MARKET_DATA)
    }

@app.post("/inquiry", response_model=MarketData)
def market_inquiry(payload: MarketInquiry):
    """
    Perform a Market inquiry and return market details.
    """
    market_data = MARKET_DATA.get(payload.company_id)

    if not market_data:
        return MarketData(
            company_id=payload.company_id,
            is_public=False,
            weekly_stock_price_hist=None,
            market_cap=None,
            pe_ratio=None
        )

    return MarketData(**market_data)

def start_market_info_api():
    """Start the market info API"""
    print(f"[ThirdParty] MarketInfo-API started on port: {config.MARKET_INFO_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=config.MARKET_INFO_PORT, reload=False)

if __name__ == "__main__":
    start_market_info_api()
