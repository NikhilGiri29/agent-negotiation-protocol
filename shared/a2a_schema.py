from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class MessageType(str, Enum):
    """Types of messages that can be exchanged between agents"""
    DISCOVERY = "discovery"
    CREDIT_INTENT = "credit_intent"
    CREDIT_OFFER = "credit_offer"
    OFFER_EVALUATION = "offer_evaluation"
    ERROR = "error"

class AgentRole(str, Enum):
    """Roles that agents can play in the WFAP system"""
    COMPANY = "company"
    BANK = "bank"
    REGISTRY = "registry"
    CREDIT_BUREAU = "credit_bureau"
    ESG_REGULATOR = "esg_regulator"
    MARKET_DATA = "market_data"

class AgentMessage(BaseModel):
    """Base class for all A2A messages"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType
    sender_id: str
    sender_role: AgentRole
    recipient_id: str
    recipient_role: AgentRole
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    conversation_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    digital_signature: Optional[str] = None

class ErrorMessage(BaseModel):
    """Error message format"""
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None

class ValidationResult(BaseModel):
    """Result of message validation"""
    is_valid: bool
    errors: List[ErrorMessage] = Field(default_factory=list)

class AgentSkill(BaseModel):
    """Representation of an agent's capability"""
    skill_name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None
    required_role: Optional[AgentRole] = None

class AgentEndpoint(BaseModel):
    """Agent endpoint information"""
    url: str
    methods: List[str] = Field(default=["POST"])
    authentication_required: bool = True

class AgentCard(BaseModel):
    """Agent identity and capability description"""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str
    description: str
    role: AgentRole
    version: str
    skills: List[AgentSkill]
    endpoints: List[AgentEndpoint]
    supported_message_types: List[MessageType]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DiscoveryRequest(BaseModel):
    """Request to discover available agents"""
    requesting_agent_id: str
    required_role: Optional[AgentRole] = None
    required_skills: Optional[List[str]] = None

class DiscoveryResponse(BaseModel):
    """Response containing discovered agents"""
    agents: List[AgentCard]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
