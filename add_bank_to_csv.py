#!/usr/bin/env python3
"""
Script to add new banks to the CSV file
"""
import csv
import os
import sys

def add_bank_to_csv(bank_id: str, bank_name: str, max_loan_amount: float, 
                   min_interest_rate: float, reputation_score: int, risk_appetite: str):
    """Add a new bank to the CSV file"""
    csv_path = os.path.join("data", "banks.csv")
    
    # Check if bank already exists
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['bank_id'] == bank_id:
                print(f"ERROR: Bank {bank_id} already exists in CSV")
                return False
    
    # Add new bank
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([bank_id, bank_name, max_loan_amount, min_interest_rate, reputation_score, risk_appetite])
    
    print(f"OK: Added bank {bank_name} ({bank_id}) to CSV")
    return True

def main():
    if len(sys.argv) != 7:
        print("Usage: python add_bank_to_csv.py <bank_id> <bank_name> <max_loan_amount> <min_interest_rate> <reputation_score> <risk_appetite>")
        print("Example: python add_bank_to_csv.py B006 'New Bank' 250000000 1.8 8 moderate")
        return
    
    bank_id = sys.argv[1]
    bank_name = sys.argv[2]
    max_loan_amount = float(sys.argv[3])
    min_interest_rate = float(sys.argv[4])
    reputation_score = int(sys.argv[5])
    risk_appetite = sys.argv[6]
    
    add_bank_to_csv(bank_id, bank_name, max_loan_amount, min_interest_rate, reputation_score, risk_appetite)

if __name__ == "__main__":
    main()
