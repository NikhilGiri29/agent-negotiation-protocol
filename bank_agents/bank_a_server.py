from shared.config import config
from .bank_server_template import create_bank_server

if __name__ == "__main__":
    # Get Bank A configuration
    bank_a_config = next(bank for bank in config.BANKS if bank.bank_id == "BANK_A")
    
    # Create and run server
    server = create_bank_server(bank_a_config)
    server.run()