from .registry_util import start_registry_api, run_registry
from .creditBureau import start_credit_api
from .marketInfo import start_market_info_api
from .esgRegulator import start_esg_api
from .__main__ import start_apis_in_separate_processes


def start_all_apis():
    """Initialize all third-party APIs (legacy function)"""
    print("⚠️  This function is deprecated. Use 'python -m thirdparty' instead.")
    start_apis_in_separate_processes()


if __name__ == "__main__":
    start_apis_in_separate_processes()
