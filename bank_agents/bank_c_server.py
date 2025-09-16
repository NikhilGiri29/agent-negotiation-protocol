#!/usr/bin/env python3
from shared.config import config
from .bank_server_template import create_bank_server

if __name__ == "__main__":
    # Get Bank C configuration
    bank_c_config = next(bank for bank in config.BANKS if bank.bank_id == "BANK_C")
    
    # Create and run server
    server = create_bank_server(bank_c_config)
    server.run()