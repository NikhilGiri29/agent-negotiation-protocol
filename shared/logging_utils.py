import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import os
from pathlib import Path

class WFAPLogger:
    """Centralized logging system for WFAP A2A interactions"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self._setup_log_directory()
        self._setup_loggers()

    def _setup_log_directory(self):
        """Create log directory if it doesn't exist"""
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        for subdir in ["a2a", "transactions", "errors", "debug"]:
            Path(f"{self.log_dir}/{subdir}").mkdir(parents=True, exist_ok=True)

    def _setup_loggers(self):
        """Setup different loggers for different purposes"""
        # A2A interaction logger
        self.a2a_logger = logging.getLogger("WFAP.A2A")
        a2a_handler = logging.FileHandler(f"{self.log_dir}/a2a/interactions.log")
        a2a_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s"
            )
        )
        self.a2a_logger.addHandler(a2a_handler)
        self.a2a_logger.setLevel(logging.INFO)

        # Transaction logger
        self.transaction_logger = logging.getLogger("WFAP.Transactions")
        transaction_handler = logging.FileHandler(
            f"{self.log_dir}/transactions/transactions.log"
        )
        transaction_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s"
            )
        )
        self.transaction_logger.addHandler(transaction_handler)
        self.transaction_logger.setLevel(logging.INFO)

        # Error logger
        self.error_logger = logging.getLogger("WFAP.Errors")
        error_handler = logging.FileHandler(f"{self.log_dir}/errors/errors.log")
        error_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s\n%(exc_info)s"
            )
        )
        self.error_logger.addHandler(error_handler)
        self.error_logger.setLevel(logging.ERROR)

        # Debug logger
        self.debug_logger = logging.getLogger("WFAP.Debug")
        debug_handler = logging.FileHandler(f"{self.log_dir}/debug/debug.log")
        debug_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s"
            )
        )
        self.debug_logger.addHandler(debug_handler)
        self.debug_logger.setLevel(logging.DEBUG)

    def log_a2a_message(
        self,
        message_type: str,
        sender_id: str,
        recipient_id: str,
        payload: Dict[str, Any],
        conversation_id: Optional[str] = None
    ):
        """Log A2A message interactions"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message_type": message_type,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "conversation_id": conversation_id,
            "payload": payload
        }
        self.a2a_logger.info(json.dumps(log_entry))

        # Also log to debug with more detail
        self.debug_logger.debug(
            f"A2A Message:\n"
            f"Type: {message_type}\n"
            f"From: {sender_id} -> To: {recipient_id}\n"
            f"Conversation: {conversation_id}\n"
            f"Payload: {json.dumps(payload, indent=2)}"
        )

    def log_transaction(
        self,
        transaction_type: str,
        company_id: str,
        bank_id: str,
        amount: float,
        status: str,
        details: Dict[str, Any]
    ):
        """Log financial transactions"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "transaction_type": transaction_type,
            "company_id": company_id,
            "bank_id": bank_id,
            "amount": amount,
            "status": status,
            "details": details
        }
        self.transaction_logger.info(json.dumps(log_entry))

    def log_error(
        self,
        error_type: str,
        source: str,
        error_message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log errors with detailed information"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "source": source,
            "error_message": error_message,
            "details": details or {}
        }
        self.error_logger.error(json.dumps(log_entry))

    def log_debug(
        self,
        component: str,
        action: str,
        details: Dict[str, Any]
    ):
        """Log debug information"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "component": component,
            "action": action,
            "details": details
        }
        self.debug_logger.debug(json.dumps(log_entry))

    def get_conversation_logs(self, conversation_id: str) -> list:
        """Retrieve all logs for a specific conversation"""
        conversation_logs = []
        
        # Read A2A logs
        with open(f"{self.log_dir}/a2a/interactions.log", "r") as f:
            for line in f:
                try:
                    log_entry = json.loads(line.split(" - ")[-1])
                    if log_entry.get("conversation_id") == conversation_id:
                        conversation_logs.append(log_entry)
                except:
                    continue
                    
        return sorted(
            conversation_logs,
            key=lambda x: x["timestamp"]
        )

    def get_transaction_history(
        self,
        company_id: Optional[str] = None,
        bank_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list:
        """Retrieve transaction history with optional filters"""
        transactions = []
        
        with open(f"{self.log_dir}/transactions/transactions.log", "r") as f:
            for line in f:
                try:
                    log_entry = json.loads(line.split(" - ")[-1])
                    
                    # Apply filters
                    if company_id and log_entry["company_id"] != company_id:
                        continue
                    if bank_id and log_entry["bank_id"] != bank_id:
                        continue
                        
                    timestamp = datetime.fromisoformat(log_entry["timestamp"])
                    if start_date and timestamp < start_date:
                        continue
                    if end_date and timestamp > end_date:
                        continue
                        
                    transactions.append(log_entry)
                except:
                    continue
                    
        return sorted(
            transactions,
            key=lambda x: x["timestamp"]
        )

    def get_error_logs(
        self,
        error_type: Optional[str] = None,
        source: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list:
        """Retrieve error logs with optional filters"""
        errors = []
        
        with open(f"{self.log_dir}/errors/errors.log", "r") as f:
            for line in f:
                try:
                    log_entry = json.loads(line.split(" - ")[-1])
                    
                    # Apply filters
                    if error_type and log_entry["error_type"] != error_type:
                        continue
                    if source and log_entry["source"] != source:
                        continue
                        
                    timestamp = datetime.fromisoformat(log_entry["timestamp"])
                    if start_date and timestamp < start_date:
                        continue
                    if end_date and timestamp > end_date:
                        continue
                        
                    errors.append(log_entry)
                except:
                    continue
                    
        return sorted(
            errors,
            key=lambda x: x["timestamp"]
        )

# Create global logger instance
wfap_logger = WFAPLogger()

# Helper functions for common logging patterns
def log_api_request(
    endpoint: str,
    method: str,
    params: Dict[str, Any],
    response_status: int,
    response_body: Dict[str, Any]
):
    """Log API request details"""
    wfap_logger.debug_logger.debug(
        json.dumps({
            "type": "api_request",
            "endpoint": endpoint,
            "method": method,
            "params": params,
            "response": {
                "status": response_status,
                "body": response_body
            }
        })
    )

def log_validation_error(
    component: str,
    validation_errors: list,
    input_data: Dict[str, Any]
):
    """Log validation error details"""
    wfap_logger.error_logger.error(
        json.dumps({
            "type": "validation_error",
            "component": component,
            "errors": validation_errors,
            "input_data": input_data
        })
    )

def log_agent_state_change(
    agent_id: str,
    old_state: Dict[str, Any],
    new_state: Dict[str, Any],
    change_reason: str
):
    """Log agent state changes"""
    wfap_logger.debug_logger.debug(
        json.dumps({
            "type": "state_change",
            "agent_id": agent_id,
            "old_state": old_state,
            "new_state": new_state,
            "reason": change_reason
        })
    )
