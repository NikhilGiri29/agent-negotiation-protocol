from shared.config import config
from .bank_server_template import create_bank_server

if __name__ == "__main__":
    # Get Bank B configuration
    bank_b_config = next(bank for bank in config.BANKS if bank.bank_id == "BANK_B")
    
    # Create and run server
    server = create_bank_server(bank_b_config)
    server.run()