import os
import requests
import json

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
}

def call_openrouter_chat(messages, model="mistralai/mistral-small-3.2-24b-instruct:free"):
    data = {
        "model": model,
        "messages": messages,
    }
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers=HEADERS,
        data=json.dumps(data),
    )
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content'].strip()

def generate_company_data(n = 5):
    prompt_text = f"""
Generate {n} rows of CSV data that matches the following dataclass:

class Company(BaseModel):
    company_id: str
    company_name: str
    annual_revenue: Optional[float] = None
    industry: Optional[str] = None

Use company_names from Company A, Company B, Company C, Company D with realistic annual revenues and industries related to companying or finance. Return only the CSV rows including headers:

company_id,company_name,annual_revenue,industry
Do not return anything other than the csv, no text or response of your own
No ```csv formatting etc. just a header and {n} comma separated rows.
"""
    messages = [{"role": "user", "content": [{"type":"text", "text": prompt_text}]}]
    return call_openrouter_chat(messages)

def generate_market_and_credit_data(company_csv):
    prompt_text = f"""
Given the following CSV data of Company:

{company_csv}

Generate CSV for two dataclasses consistent/cohesive with realistic values per company:

class MarketData(BaseModel):
    company_id: str
    is_public: bool = Field(default=False)
    weekly_stock_price_hist: Optional[List[float]] = Field(default = None, 
                                                           description="Past 5 week average stock price, represented as comma separated list of floats")
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None

class CreditBureau(BaseModel):
    company_id: str
    credit_score: int = Field(..., ge=0, le=850)
    rating: str = Field(..., description="Credit grade e.g. AAA, BBB, etc.")
    history_summary: str = Field(default="No major defaults")

Return two CSVs separated explicitly by lines with these markers:

===MARKETDATA===
company_id,is_public,weekly_stock_price_hist,market_cap,pe_ratio

===CREDITBUREAU===
company_id,credit_score,rating,history_summary

Make sure values are realistic and company_id match the original companies.
Make sure that the values per company are cohesive with each other for e.g.
the rating and history summary reflect the stock price and vice versa
Do not return anything other than the csv, and the markers, no text or response of your own
No ```csv formatting etc. just a marker, header and comma separated rows then next marker header and comma separated rows.
"""
    messages = [{"role": "user", "content": [{"type":"text", "text": prompt_text}]}]
    return call_openrouter_chat(messages)

def generate_bank_data(n = 5):
    prompt_text = f"""
Generate {n} rows of CSV data that matches the following dataclass:

class Bank(BaseModel):
    bank_id: str
    bank_name: str
    max_loan_amount: float = Field(default=100_000_000)
    min_interest_rate: float = Field(default=1.0)
    reputation_score: Optional[int] = Field(default=5, ge=1, le=10)
    risk_appetite: str  # conservative|moderate|aggressive
    esg_data: None #always empty

Use bank_name from Bank A, Bank B, Bank C, Bank D with realistic values. Return only the CSV rows including headers:

bank_id,bank_name,max_loan_amount,min_interest_rate,reputation_score,risk_appetite,esg_data
Do not return anything other than the csv, no text or response of your own
No ```csv formatting etc. just a header and {n} comma separated rows.
"""
    messages = [{"role": "user", "content": [{"type":"text", "text": prompt_text}]}]
    return call_openrouter_chat(messages)

def generate_esg_data(bank_csv):
    prompt_text = f"""
Given the following CSV data of Company:

{bank_csv}

Generate CSV for the dataclasse consistent/cohesive with realistic values per company:

class ESGRegulator(BaseModel):
    bank_id: str
    environmental_score: float = Field(..., ge=0, le=10)
    social_score: float = Field(..., ge=0, le=10)
    governance_score: float = Field(..., ge=0, le=10)
    overall_score: float = Field(..., ge=0, le=10)
    carbon_footprint_category: str = Field(default="medium")
    sustainability_notes: str = Field(default="")

Return a CSV with this header
bank_id,environmental_score,social_score,governance_score,overa,carbon_footprint_category,sustainability_notes

Make sure values are realistic and bank_id match the original banks.
Make sure that the values per bank are cohesive with each other 
Do not return anything other than the csv, no text or response of your own
No ```csv formatting etc. just a header and comma separated rows.
"""
    messages = [{"role": "user", "content": [{"type":"text", "text": prompt_text}]}]
    return call_openrouter_chat(messages)

def save_csv(filename, data):
    with open(filename, "w") as f:
        f.write(data)

def save_two_csv(data, market_file, credit_file):
    parts = data.split("===")
    market_csv = ""
    credit_csv = ""
    for i in range(len(parts)):
        part = parts[i]
        part_strip = part.strip()
        if part_strip.startswith("MARKETDATA"):
            market_csv = parts[i+1].split("\n", 1)[1].strip()
            i+=1
        elif part_strip.startswith("CREDITBUREAU"):
            credit_csv = parts[i+1].split("\n", 1)[1].strip()
            i+=1
    if market_csv:
        save_csv(market_file, market_csv)
    if credit_csv:
        save_csv(credit_file, credit_csv)

if __name__ == "__main__":
    companies = generate_company_data()
    save_csv("companies.csv", companies)
    print("Saved companies.csv")

    market_credit = generate_market_and_credit_data(companies)
    save_two_csv(market_credit, "market_data.csv", "credit_bureau.csv")
    print("Saved market_data.csv and credit_bureau.csv")

    banks = generate_bank_data()
    save_csv("banks.csv", banks)
    print("Saved banks.csv")

    esg_regulator = generate_esg_data(banks)
    save_csv("esg_regulator.csv", esg_regulator)
    print("Saved esg_regulator.csv")
