from fastapi import FastAPI
from shared.schema import MarketInquiry, MarketData
from shared.config import config
import uvicorn
from fastapi import FastAPI
import uvicorn
sample_market_data = {
    "companyA": {
        "company_id": "companyA",
        "is_public": True,
        "curr_stock_price": 150.75,
        "market_cap": 5000000000.0,
        "pe_ratio": 25.0
    },
    "companyB": {
        "company_id": "companyB",
        "is_public": True,
        "curr_stock_price": 120.50,
        "market_cap": 3000000000.0,
        "pe_ratio": 20.0
    },
}

app = FastAPI(title="Market Inquiry API", version="0.1")

@app.post("/inquiry", response_model=MarketData)
def market_inquiry(payload: MarketInquiry):
    """
    Perform a Market inquiry and return market details.
    """
    market_data = sample_market_data.get(payload.company_id)

    if not market_data:
        return MarketData(
            company_id=payload.company_id,
            is_public=False,
            curr_stock_price=None,
            market_cap=None,
            pe_ratio=None
        )

    return MarketData(**market_data)

def start_market_info_api():
    print(f"[ThirdParty] MarketInfo-API started on port: {config.MARKET_INFO_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=config.MARKET_INFO_PORT, reload=False)

def stop_market_info_api():
    pass
