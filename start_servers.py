import subprocess
import time
import logging
import sys
from shared.config import config
import psutil
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('server_startup.log', encoding='utf-8')
    ]
)

def start_process(command, name):
    """Start a process and return the process object with metadata"""
    logging.info(f"Starting {name}...")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            bufsize=1,
            universal_newlines=True
        )
        
        time.sleep(2)
        
        if process.poll() is None:
            logging.info(f"[OK] {name} started successfully")
            return {
                'process': process,
                'name': name,
                'command': command,
                'start_time': time.time()
            }
        else:
            stderr_output = process.stderr.read()
            logging.error(f"[ERROR] Failed to start {name}")
            logging.error(f"Error output: {stderr_output}")
            return None
    except Exception as e:
        logging.error(f"[ERROR] Error starting {name}: {str(e)}")
        return None

def monitor_process_output(process_info):
    """Monitor process output for errors"""
    process = process_info['process']
    name = process_info['name']
    
    while True:
        output = process.stdout.readline()
        if output:
            print(f"[{name}] {output.strip()}")
        error = process.stderr.readline()
        if error:
            logging.error(f"[{name}] {error.strip()}")
        
        if process.poll() is not None:
            remaining_error = process.stderr.read()
            if remaining_error:
                logging.error(f"[{name}] Final error output: {remaining_error}")
            return False
        
        if not output and not error:
            break
    
    return True

def kill_process_on_port(port):
    """Kill any process running on the specified port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            for conn in psutil.net_connections():
                if hasattr(conn.laddr, 'port') and conn.laddr.port == port:
                    try:
                        process = psutil.Process(conn.pid)
                        logging.info(f"Killing process {process.name()} (PID: {conn.pid}) on port {port}")
                        process.terminate()
                        process.wait(timeout=3)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        pass
    except Exception as e:
        logging.error(f"Error while trying to kill process on port {port}: {str(e)}")

def main():
    # Kill existing processes on required ports
    ports_to_check = [
        config.COMPANY_AGENT_PORT
    ] + [bank.port for bank in config.BANKS]
    
    for port in ports_to_check:
        kill_process_on_port(port)
    
    processes = []
    
    # # Start Company Agent
    # company_agent = start_process(
    #     f"python -m company_agent.agent --port {config.COMPANY_AGENT_PORT}",
    #     "Company Agent"
    # )
    # if company_agent:
    #     processes.append(company_agent)
    # else:
    #     logging.error("Failed to start Company Agent. Exiting...")
    #     sys.exit(1)
    
    # Start Bank Agents
    for bank in config.BANKS:
        bank_process = start_process(
            f"python -m bank_agents.bank_agent --bank-id {bank.bank_id} --port {bank.port}",
            f"Bank Agent - {bank.bank_name}"
        )
        if bank_process:
            processes.append(bank_process)
        else:
            logging.error(f"Failed to start {bank.bank_name}. Continuing with available banks...")
    
    logging.info("\n🚀 Backend services started!")
    logging.info(f"Company Agent running on port: {config.COMPANY_AGENT_PORT}")
    logging.info("Bank Agents running on ports: " + 
                 ", ".join([f"{bank.bank_name}: {bank.port}" for bank in config.BANKS]))
    logging.info("\nTo start the UI, run in a new terminal:")
    logging.info(f"streamlit run streamlit_app.py --server.port {config.STREAMLIT_PORT}")
    
    try:
        while True:
            for process_info in processes:
                if not monitor_process_output(process_info):
                    logging.error(f"Process {process_info['name']} has terminated unexpectedly!")
                    logging.error("Shutting down all services...")
                    cleanup(processes)
                    sys.exit(1)
            time.sleep(0.1)
    except KeyboardInterrupt:
        logging.info("\nShutting down all services...")
        cleanup(processes)
        logging.info("Backend services stopped.")

def cleanup(processes):
    """Terminate all running processes"""
    for process_info in processes:
        process = process_info['process']
        name = process_info['name']
        if process.poll() is None:
            logging.info(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logging.warning(f"Force killing {name}...")
                process.kill()

if __name__ == "__main__":
    main()