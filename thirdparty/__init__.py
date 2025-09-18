from .registry import start_registry_api
from .creditBureau import start_credit_api
from .marketInfo import start_market_info_api
from .esgRegulator import start_esg_api


def start_all_apis():
    """Initialize all third-party APIs"""
    start_registry_api()
    start_credit_api()
    start_market_info_api()
    start_esg_api()


if __name__ == "__main__":
    start_all_apis()
