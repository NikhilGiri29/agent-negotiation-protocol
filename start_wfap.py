#!/usr/bin/env python3
"""
WFAP System Startup Script
Starts all third-party services, banks, and companies dynamically from CSV data
"""
import asyncio
import subprocess
import time
import logging
import sys
import os
from datetime import datetime
from multiprocessing import Process
import threading

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from shared.config import config
from shared.dynamic_loader import load_banks_from_csv, load_companies_from_csv, initialize_dynamic_config

# Setup comprehensive logging
log_filename = f"wfap_startup_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def log_section(message: str):
    """Log a section header"""
    logger.info("=" * 80)
    logger.info(f"  {message}")
    logger.info("=" * 80)

def log_step(step: int, message: str):
    """Log a step"""
    logger.info(f"STEP {step}: {message}")
    logger.info("-" * 60)

def run_thirdparty_services():
    """Run third-party services in a separate process"""
    try:
        logger.info("Starting third-party services...")
        from thirdparty import start_apis_in_separate_processes
        start_apis_in_separate_processes()
    except Exception as e:
        logger.error(f"Error in third-party services: {e}")

def run_registry_initialization():
    """Run registry initialization"""
    try:
        logger.info("Running registry initialization...")
        import initialize_registry
        asyncio.run(initialize_registry.register_entities())
    except Exception as e:
        logger.error(f"Error in registry initialization: {e}")

def run_bank_server(bank_id: str, bank_name: str, port: int):
    """Run a bank server"""
    try:
        logger.info(f"Starting {bank_name} ({bank_id}) on port {port}")
        from shared.server_template import start_entity_server
        start_entity_server("bank", bank_id)
    except Exception as e:
        logger.error(f"Error starting {bank_name}: {e}")

def run_company_server(company_id: str, company_name: str, port: int):
    """Run a company server"""
    try:
        logger.info(f"Starting {company_name} ({company_id}) on port {port}")
        from shared.server_template import start_entity_server
        start_entity_server("company", company_id)
    except Exception as e:
        logger.error(f"Error starting {company_name}: {e}")

async def wait_for_service(port: int, service_name: str, timeout: int = 30, is_third_party: bool = False) -> bool:
    """Wait for a service to be ready"""
    import aiohttp
    
    logger.info(f"Waiting for {service_name} on port {port}...")
    
    # Use different health endpoints for different service types
    health_endpoint = "/health" if is_third_party else "/a2a/health"
    
    for attempt in range(timeout):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{port}{health_endpoint}", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"OK: {service_name} is ready on port {port}")
                        return True
        except Exception as e:
            if attempt % 5 == 0:  # Log every 5 seconds
                logger.info(f"  Attempt {attempt + 1}/{timeout}: {str(e)}")
        await asyncio.sleep(1)
    
    logger.error(f"ERROR: {service_name} failed to start within {timeout} seconds")
    return False

def main():
    """Main startup function"""
    log_section("WFAP SYSTEM STARTUP")
    logger.info(f"Startup time: {datetime.now().isoformat()}")
    logger.info(f"Log file: {log_filename}")
    logger.info(f"Project root: {project_root}")
    
    processes = []
    start_time = time.time()
    
    try:
        # Step 1: Initialize dynamic configuration
        log_step(1, "Loading Dynamic Configuration")
        try:
            initialize_dynamic_config()
            banks = load_banks_from_csv()
            companies = load_companies_from_csv()
            
            logger.info(f"Loaded {len(banks)} banks from CSV:")
            for bank in banks:
                logger.info(f"  - {bank.bank_name} ({bank.bank_id}) -> Port {bank.port}")
            
            logger.info(f"Loaded {len(companies)} companies from CSV:")
            for company in companies:
                company_port = int(company.api_url.split(':')[2].split('/')[0])
                logger.info(f"  - {company.company_name} ({company.company_id}) -> Port {company_port}")
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return
        
        # Step 2: Start Third-Party Services
        log_step(2, "Starting Third-Party Services")
        thirdparty_process = Process(target=run_thirdparty_services, name="ThirdPartyServices")
        thirdparty_process.start()
        processes.append(thirdparty_process)
        logger.info("Third-party services started")
        
        # Wait for registry to be ready
        logger.info("Waiting for registry service to be ready...")
        if not asyncio.run(wait_for_service(config.REGISTRY_PORT, "Registry Service", is_third_party=True)):
            logger.error("Registry service not ready - cannot continue")
            return
        
        # Step 3: Register Banks and Companies
        log_step(3, "Registering Banks and Companies with Registry")
        registration_process = Process(target=run_registry_initialization, name="RegistryInit")
        registration_process.start()
        processes.append(registration_process)
        
        # Wait for registration to complete
        logger.info("Waiting for registration to complete...")
        time.sleep(5)
        logger.info("Registration completed")
        
        # Step 4: Start All Bank Agents
        log_step(4, "Starting All Bank Agents")
        logger.info(f"Starting {len(banks)} bank agents...")
        
        for bank in banks:
            bank_process = Process(
                target=run_bank_server,
                args=(bank.bank_id, bank.bank_name, bank.port),
                name=f"Bank-{bank.bank_id}"
            )
            bank_process.start()
            processes.append(bank_process)
            logger.info(f"OK: {bank.bank_name} started on port {bank.port}")
            time.sleep(1)  # Small delay between starts
        
        # Wait for all bank agents to be ready
        logger.info("Waiting for bank agents to be ready...")
        for bank in banks:
            if not asyncio.run(wait_for_service(bank.port, f"Bank - {bank.bank_name}", timeout=15)):
                logger.warning(f"Bank - {bank.bank_name} may not be ready")
        
        # Step 5: Start All Company Agents
        log_step(5, "Starting All Company Agents")
        logger.info(f"Starting {len(companies)} company agents...")
        
        for company in companies:
            company_port = int(company.api_url.split(':')[2].split('/')[0])
            company_process = Process(
                target=run_company_server,
                args=(company.company_id, company.company_name, company_port),
                name=f"Company-{company.company_id}"
            )
            company_process.start()
            processes.append(company_process)
            logger.info(f"OK: {company.company_name} started on port {company_port}")
            time.sleep(1)  # Small delay between starts
        
        # Wait for all company agents to be ready
        logger.info("Waiting for company agents to be ready...")
        for company in companies:
            company_port = int(company.api_url.split(':')[2].split('/')[0])
            if not asyncio.run(wait_for_service(company_port, f"Company - {company.company_name}", timeout=15)):
                logger.warning(f"Company - {company.company_name} may not be ready")
        
        # Step 6: System Status Summary
        log_section("SYSTEM STARTUP COMPLETE")
        end_time = time.time()
        startup_duration = end_time - start_time
        
        logger.info(f"Startup completed in {startup_duration:.2f} seconds")
        logger.info(f"Total processes started: {len(processes)}")
        logger.info(f"Log file saved: {log_filename}")
        
        logger.info("Service Status:")
        logger.info(f"  OK: Registry Service: http://localhost:{config.REGISTRY_PORT}")
        logger.info(f"  OK: Credit Bureau: http://localhost:{config.CREDIT_BUREAU_PORT}")
        logger.info(f"  OK: ESG Regulator: http://localhost:{config.ESG_REGUATOR_PORT}")
        logger.info(f"  OK: Market Info: http://localhost:{config.MARKET_INFO_PORT}")
        
        logger.info("Bank Agents:")
        for bank in banks:
            logger.info(f"  OK: {bank.bank_name} ({bank.bank_id}): http://localhost:{bank.port}")
        
        logger.info("Company Agents:")
        for company in companies:
            company_port = int(company.api_url.split(':')[2].split('/')[0])
            logger.info(f"  OK: {company.company_name} ({company.company_id}): http://localhost:{company_port}")
        
        logger.info("")
        logger.info("To test the system:")
        logger.info("  python test_wfap_system.py")
        logger.info("")
        logger.info("To start the UI:")
        logger.info("  streamlit run streamlit_app.py")
        logger.info("")
        logger.info("Press Ctrl+C to stop all services")
        
        # Monitor processes
        try:
            while True:
                for i, process in enumerate(processes):
                    if not process.is_alive():
                        logger.error(f"Process {i} ({process.name}) has terminated!")
                        return
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user...")
            log_section("SHUTTING DOWN ALL SERVICES")
            
            for i, process in enumerate(processes):
                logger.info(f"Stopping process {i} ({process.name})...")
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    logger.warning(f"Process {i} did not stop gracefully, forcing...")
                    process.kill()
                logger.info(f"Process {i} stopped")
            
            logger.info("All services stopped")
            logger.info(f"Final log saved: {log_filename}")
    
    except Exception as e:
        logger.error(f"Critical error during startup: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Cleanup
        logger.info("Cleaning up processes...")
        for process in processes:
            process.terminate()
        
        logger.error(f"Startup failed - see log file: {log_filename}")

if __name__ == "__main__":
    main()