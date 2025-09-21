import asyncio
import time
from multiprocessing import Process
from .registry_util import run_registry
from .creditBureau import start_credit_api
from .marketInfo import start_market_info_api
from .esgRegulator import start_esg_api

def start_apis_in_separate_processes():
    """Start each API in its own process"""
    processes = []
    
    try:
        # Create and start processes
        print("Starting third-party services...")
        
        # Registry service
        registry_process = Process(target=run_registry, name="Registry")
        registry_process.start()
        processes.append(registry_process)
        print("OK: Registry service started on port 8005")
        
        # Credit Bureau service
        credit_process = Process(target=start_credit_api, name="CreditBureau")
        credit_process.start()
        processes.append(credit_process)
        print("OK: Credit Bureau service started on port 8006")
        
        # Market Info service
        market_process = Process(target=start_market_info_api, name="MarketInfo")
        market_process.start()
        processes.append(market_process)
        print("OK: Market Info service started on port 8008")
        
        # ESG Regulator service
        esg_process = Process(target=start_esg_api, name="ESGRegulator")
        esg_process.start()
        processes.append(esg_process)
        print("OK: ESG Regulator service started on port 8007")
        
        print("\nAll third-party services are running!")
        print("Service Summary:")
        print("   - Registry: http://localhost:8005")
        print("   - Credit Bureau: http://localhost:8006")
        print("   - ESG Regulator: http://localhost:8007")
        print("   - Market Info: http://localhost:8008")
        print("\nYou can now run 'python initialize_registry.py' to register banks and companies")
        print("Press Ctrl+C to stop all services")
        
        # Wait for all processes
        for process in processes:
            process.join()
            
    except KeyboardInterrupt:
        # Handle graceful shutdown
        print("\nShutting down services...")
        for process in processes:
            if process.is_alive():
                print(f"   Stopping {process.name}...")
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    print(f"   Force killing {process.name}...")
                    process.kill()
        print("All services stopped")
    except Exception as e:
        print(f"ERROR: Error starting services: {str(e)}")
        # Clean up any started processes
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=2)

if __name__ == "__main__":
    start_apis_in_separate_processes()
