import logging
import json
import aiohttp
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from fastapi import HTTPException

from .a2a_schema import (
    AgentMessage,
    AgentRole,
    MessageType,
    ValidationResult,
    ErrorMessage,
    AgentCard,
    AgentSkill,
    AgentEndpoint,
    DiscoveryRequest,
    DiscoveryResponse
)
from .config import config

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class A2AAgent:
    """Base class for all WFAP agents implementing A2A protocol"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: AgentRole,
        description: str = "",
        version: str = "1.0.0"
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.description = description
        self.version = version
        self.logger = logging.getLogger(f"WFAP-{self.role}-{self.agent_id}")
        self.skills: List[AgentSkill] = []
        self.endpoints: List[AgentEndpoint] = []
        self.supported_message_types: List[MessageType] = []
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize agent with default capabilities"""
        # Add discovery skill by default
        self.add_skill(
            AgentSkill(
                skill_name="discovery",
                description="Ability to discover and interact with other agents",
                required_role=None
            )
        )
        # Support discovery messages by default
        self.supported_message_types.append(MessageType.DISCOVERY)
        # Log initialization
        self.logger.info(f"Initialized {self.role} agent: {self.name} ({self.agent_id})")

    def add_skill(self, skill: AgentSkill):
        """Add a new skill to the agent"""
        self.skills.append(skill)
        self.logger.debug(f"Added skill: {skill.skill_name}")

    def add_endpoint(self, endpoint: AgentEndpoint):
        """Add a new endpoint to the agent"""
        self.endpoints.append(endpoint)
        self.logger.debug(f"Added endpoint: {endpoint.url}")

    def support_message_type(self, message_type: MessageType):
        """Add support for a message type"""
        if message_type not in self.supported_message_types:
            self.supported_message_types.append(message_type)
            self.logger.debug(f"Added support for message type: {message_type}")

    def get_agent_card(self) -> AgentCard:
        """Generate agent's capability card"""
        return AgentCard(
            agent_id=self.agent_id,
            name=self.name,
            description=self.description,
            role=self.role,
            version=self.version,
            skills=self.skills,
            endpoints=self.endpoints,
            supported_message_types=self.supported_message_types,
            metadata={}
        )

    async def validate_message(self, message: AgentMessage) -> ValidationResult:
        """Validate incoming A2A message"""
        errors = []
        
        # Check if message type is supported
        if message.message_type not in self.supported_message_types:
            errors.append(
                ErrorMessage(
                    error_code="UNSUPPORTED_MESSAGE_TYPE",
                    error_message=f"Message type {message.message_type} is not supported"
                )
            )

        # Validate recipient
        if message.recipient_id != self.agent_id:
            errors.append(
                ErrorMessage(
                    error_code="INVALID_RECIPIENT",
                    error_message="Message is not intended for this agent"
                )
            )

        # Validate role
        if message.recipient_role != self.role:
            errors.append(
                ErrorMessage(
                    error_code="INVALID_ROLE",
                    error_message=f"Message requires role {message.recipient_role}, but agent has role {self.role}"
                )
            )

        # Log validation results
        if errors:
            self.logger.warning(f"Message validation failed: {len(errors)} errors")
            for error in errors:
                self.logger.warning(f"Validation error: {error.error_code} - {error.error_message}")
        else:
            self.logger.debug("Message validation successful")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    async def send_message(
        self,
        recipient_id: str,
        recipient_role: AgentRole,
        message_type: MessageType,
        payload: Dict[str, Any],
        conversation_id: Optional[str] = None,
        in_reply_to: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Send an A2A message to another agent"""
        try:
            # Create message
            message = AgentMessage(
                message_type=message_type,
                sender_id=self.agent_id,
                sender_role=self.role,
                recipient_id=recipient_id,
                recipient_role=recipient_role,
                conversation_id=conversation_id,
                in_reply_to=in_reply_to,
                payload=payload
            )

            # Get recipient endpoint from registry
            endpoint = await self._get_agent_endpoint(recipient_id, recipient_role)
            if not endpoint:
                raise HTTPException(status_code=404, detail=f"No endpoint found for agent {recipient_id}")

            # Send message
            async with aiohttp.ClientSession() as session:
                headers = {"Content-Type": "application/json"}
                async with session.post(
                    endpoint,
                    json=message.dict(),
                    headers=headers
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        self.logger.info(
                            f"Successfully sent {message_type} message to {recipient_role} {recipient_id}"
                        )
                        return True, response_data
                    else:
                        error_text = await response.text()
                        self.logger.error(
                            f"Failed to send message: Status {response.status} - {error_text}"
                        )
                        return False, None

        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            return False, None

    async def _get_agent_endpoint(self, agent_id: str, role: AgentRole) -> Optional[str]:
        """Get agent endpoint from registry"""
        try:
            # Create discovery request
            discovery_request = DiscoveryRequest(
                requesting_agent_id=self.agent_id,
                required_role=role
            )

            # Send request to discovery service
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config.A2A_DISCOVERY_URL,
                    json=discovery_request.dict()
                ) as response:
                    if response.status == 200:
                        discovery_data = await response.json()
                        discovery_response = DiscoveryResponse(**discovery_data)
                        
                        # Find matching agent
                        for agent in discovery_response.agents:
                            if agent.agent_id == agent_id:
                                # Return first endpoint
                                if agent.endpoints:
                                    return agent.endpoints[0].url
                        
                        self.logger.warning(f"Agent {agent_id} not found in discovery response")
                        return None
                    else:
                        self.logger.error(f"Discovery request failed: {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"Error in discovery: {str(e)}")
            return None

    async def handle_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        """Handle incoming A2A message"""
        try:
            # Validate message
            validation_result = await self.validate_message(message)
            if not validation_result.is_valid:
                error_message = "; ".join([e.error_message for e in validation_result.errors])
                self.logger.warning(f"Message validation failed: {error_message}")
                return {
                    "status": "error",
                    "errors": [e.dict() for e in validation_result.errors]
                }

            # Log message receipt
            self.logger.info(
                f"Received {message.message_type} message from {message.sender_role} {message.sender_id}"
            )

            # Handle different message types
            if message.message_type == MessageType.DISCOVERY:
                return await self._handle_discovery(message)
            else:
                # Subclasses should implement their own message handlers
                self.logger.warning(f"No handler implemented for message type: {message.message_type}")
                return {
                    "status": "error",
                    "message": f"Unsupported message type: {message.message_type}"
                }

        except Exception as e:
            self.logger.error(f"Error handling message: {str(e)}")
            return {
                "status": "error",
                "message": f"Internal error: {str(e)}"
            }

    async def _handle_discovery(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle discovery message"""
        try:
            request = DiscoveryRequest(**message.payload)
            # Return agent card if role matches
            if not request.required_role or request.required_role == self.role:
                if not request.required_skills or all(
                    any(s.skill_name == req_skill for s in self.skills)
                    for req_skill in request.required_skills
                ):
                    return {
                        "status": "success",
                        "agent": self.get_agent_card().dict()
                    }
            
            return {
                "status": "error",
                "message": "Agent does not match requirements"
            }

        except Exception as e:
            self.logger.error(f"Error handling discovery: {str(e)}")
            return {
                "status": "error",
                "message": f"Discovery error: {str(e)}"
            }
