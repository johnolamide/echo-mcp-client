"""
Agent core for processing commands and managing services.
Enhanced with AI reasoning capabilities.
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import websockets
import openai

from config.settings import settings
from api.server_client import api_client


logger = logging.getLogger(__name__)


class ServiceConnector:
    """Base class for service connectors."""

    def __init__(self, service_config: Dict[str, Any]):
        self.service_config = service_config
        self.name = service_config.get("name", "Unknown Service")
        self.type = service_config.get("type", "unknown")

    async def execute(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command on this service."""
        raise NotImplementedError("Subclasses must implement execute method")

    def can_handle(self, command: str) -> bool:
        """Check if this connector can handle the given command."""
        return False


class PaymentConnector(ServiceConnector):
    """Connector for payment services like Stripe."""

    def can_handle(self, command: str) -> bool:
        payment_keywords = ["pay", "payment", "charge", "refund", "stripe"]
        return any(keyword in command.lower() for keyword in payment_keywords)

    async def execute(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute payment-related commands."""
        if "pay" in command.lower():
            return await self._process_payment(parameters)
        elif "refund" in command.lower():
            return await self._process_refund(parameters)
        else:
            return {"error": f"Unsupported payment command: {command}"}

    async def _process_payment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment."""
        amount = parameters.get("amount", 0)

        # Validate required parameters
        if amount <= 0:
            return {
                "action": "payment_failed",
                "error": "Invalid amount",
                "message": "Please specify a valid payment amount."
            }

        currency = parameters.get("currency", "USD")

        return {
            "action": "payment_processed",
            "amount": amount,
            "currency": currency,
            "status": "success",
            "transaction_id": f"txn_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }

    async def _process_refund(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process a refund."""
        transaction_id = parameters.get("transaction_id")
        amount = parameters.get("amount", 0)

        return {
            "action": "refund_processed",
            "transaction_id": transaction_id,
            "amount": amount,
            "status": "success"
        }


class CommunicationConnector(ServiceConnector):
    """Connector for communication services like Twilio."""

    def can_handle(self, command: str) -> bool:
        comm_keywords = ["send", "message", "sms", "call", "twilio", "text"]
        return any(keyword in command.lower() for keyword in comm_keywords)

    async def execute(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute communication-related commands."""
        if "send" in command.lower() and "message" in command.lower():
            return await self._send_message(parameters)
        elif "call" in command.lower():
            return await self._make_call(parameters)
        else:
            return {"error": f"Unsupported communication command: {command}"}

    async def _send_message(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message."""
        to = parameters.get("to")
        message = parameters.get("message", "")

        # Validate required parameters
        if not to:
            return {
                "action": "message_failed",
                "error": "No recipient specified",
                "message": "Please specify who you want to send the message to (phone number, email, or name)."
            }

        if not message:
            return {
                "action": "message_failed",
                "error": "No message content",
                "message": "Please specify what message you want to send."
            }

        return {
            "action": "message_sent",
            "to": to,
            "message": message,
            "status": "success",
            "message_id": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }

    async def _make_call(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Make a phone call."""
        to = parameters.get("to")

        return {
            "action": "call_initiated",
            "to": to,
            "status": "success",
            "call_id": f"call_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }


class AgentCore:
    """Core agent logic for command processing and service management."""

    def __init__(self):
        self.connectors: List[ServiceConnector] = []
        self.user_services: List[Dict[str, Any]] = []
        self.is_initialized = False
        self.conversation_history: List[Dict[str, Any]] = []
        self.ai_enabled = bool(settings.openai_api_key)
        self.websocket_connection = None
        self.chat_listeners: List[callable] = []

        # Initialize OpenAI client if API key is available
        if self.ai_enabled:
            try:
                self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
                logger.info("AI reasoning capabilities enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.ai_enabled = False

    async def initialize(self):
        """Initialize the agent by loading user services."""
        try:
            logger.info("Initializing agent...")

            # Try to load user services from server
            try:
                services = await api_client.get_user_agent_services()
                self.user_services = services
                logger.info(f"Loaded {len(services)} user services from server")
            except Exception as api_error:
                logger.warning(f"Failed to load services from server: {api_error}")
                logger.info("Continuing with mock services for testing...")
                # Use mock services for testing when API is not available
                self.user_services = [
                    {"id": 1, "name": "Mock Payment Service", "type": "payment"},
                    {"id": 2, "name": "Mock Communication Service", "type": "communication"}
                ]

            # Initialize connectors for each service
            self._initialize_connectors()

            self.is_initialized = True
            logger.info(f"Agent initialized with {len(self.connectors)} service connectors")

        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            # Initialize with empty connectors if everything fails
            self.connectors = []
            self.is_initialized = True
            raise

        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise

    def _initialize_connectors(self):
        """Initialize service connectors based on user services."""
        self.connectors = []

        for service in self.user_services:
            service_type = service.get("type", "").lower()

            if service_type == "payment":
                connector = PaymentConnector(service)
            elif service_type == "communication":
                connector = CommunicationConnector(service)
            else:
                # Generic connector for unknown service types
                connector = ServiceConnector(service)

            self.connectors.append(connector)

        logger.info(f"Initialized {len(self.connectors)} service connectors")

    async def process_command_with_ai(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process command with AI reasoning for better understanding."""
        if not self.ai_enabled:
            return await self.process_command(command, context)

        try:
            # Use AI to understand and enhance the command
            ai_analysis = await self._analyze_command_with_ai(command, context)

            # Extract enhanced parameters
            parameters = self._extract_parameters_enhanced(command, ai_analysis)

            # Find best connector with AI help
            connector = await self._find_connector_with_ai(command, ai_analysis)

            if not connector:
                return {
                    "response": "I'm sorry, I don't have a service that can handle that request.",
                    "action": "no_service_found",
                    "available_services": [c.name for c in self.connectors]
                }

            # Execute with enhanced parameters
            result = await connector.execute(command, parameters)

            # Generate AI-enhanced response
            response = await self._generate_response_with_ai(result, connector, ai_analysis)

            # Store in conversation history
            self._add_to_history(command, response, result)

            return {
                "response": response,
                "action": result.get("action", "command_executed"),
                "service": connector.name,
                "ai_enhanced": True,
                "result": result
            }

        except Exception as e:
            logger.error(f"AI processing error: {e}")
            # Fallback to regular processing
            return await self.process_command(command, context)

    async def _analyze_command_with_ai(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Use AI to analyze and understand the command intent."""
        if not self.ai_enabled:
            return {}

        try:
            system_prompt = f"""You are an AI assistant analyzing user commands for service execution.
Available services: {', '.join([c.name for c in self.connectors])}

Analyze the command and extract:
- intent: What the user wants to do
- service_type: Which service category (payment, communication, etc.)
- parameters: Key information needed
- confidence: How confident you are (0-1)

Return JSON format."""

            user_prompt = f"Command: {command}"
            if context:
                user_prompt += f"\nContext: {json.dumps(context)}"

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=200,
                    temperature=0.3
                )
            )

            analysis_text = response.choices[0].message.content.strip()
            return json.loads(analysis_text) if analysis_text.startswith('{') else {}

        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")
            return {}

    async def _find_connector_with_ai(self, command: str, ai_analysis: Dict[str, Any]) -> Optional[ServiceConnector]:
        """Find connector using AI analysis."""
        if ai_analysis.get("confidence", 0) > 0.7:
            service_type = ai_analysis.get("service_type", "").lower()

            for connector in self.connectors:
                if service_type in connector.type.lower() or service_type in connector.name.lower():
                    return connector

        # Fallback to regular connector finding
        return self._find_connector(command)

    async def _generate_response_with_ai(self, result: Dict[str, Any], connector: ServiceConnector, ai_analysis: Dict[str, Any]) -> str:
        """Generate AI-enhanced response."""
        if not self.ai_enabled:
            return self._generate_response(result, connector)

        try:
            system_prompt = """Generate a helpful, natural response for the user based on the service execution result.
Be concise but informative. Include relevant details from the result."""

            user_prompt = f"""Service: {connector.name}
Action: {result.get('action', 'unknown')}
Result: {json.dumps(result)}
Analysis: {json.dumps(ai_analysis)}"""

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=100,
                    temperature=0.7
                )
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.warning(f"AI response generation failed: {e}")
            return self._generate_response(result, connector)

    def _add_to_history(self, command: str, response: str, result: Dict[str, Any]):
        """Add interaction to conversation history."""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "response": response,
            "result": result
        })

        # Keep only last 50 interactions
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]

    async def connect_to_chat(self):
        """Connect to WebSocket chat system for real-time messaging."""
        if not settings.jwt_token:
            logger.warning("No JWT token available for WebSocket connection")
            return

        try:
            # WebSocket URL for chat
            ws_url = f"wss://{settings.server_host.replace('https://', '')}/chat/ws"
            headers = {"Authorization": f"Bearer {settings.jwt_token}"}

            # Note: This is a simplified WebSocket connection
            # In production, you'd want proper connection management
            logger.info(f"WebSocket chat integration ready (URL: {ws_url})")

        except Exception as e:
            logger.error(f"Failed to setup WebSocket chat connection: {e}")

    def add_chat_listener(self, listener: callable):
        """Add a listener for incoming chat messages."""
        self.chat_listeners.append(listener)

    async def send_chat_message(self, receiver_id: int, content: str) -> Dict[str, Any]:
        """Send a chat message through the agent."""
        try:
            result = await api_client.send_message(receiver_id, content)

            if result.get("status") == "success":
                # Notify listeners
                for listener in self.chat_listeners:
                    try:
                        await listener({
                            "type": "message_sent",
                            "receiver_id": receiver_id,
                            "content": content,
                            "result": result
                        })
                    except Exception as e:
                        logger.error(f"Chat listener error: {e}")

                return {
                    "action": "message_sent",
                    "receiver_id": receiver_id,
                    "content": content,
                    "status": "success"
                }
            else:
                return {
                    "action": "message_failed",
                    "error": result.get("message", "Failed to send message")
                }

        except Exception as e:
            logger.error(f"Chat message send error: {e}")
            return {
                "action": "message_failed",
                "error": str(e)
            }

    async def process_incoming_message(self, message_data: Dict[str, Any]):
        """Process incoming chat messages and potentially respond."""
        try:
            sender_id = message_data.get("sender_id")
            content = message_data.get("content", "")

            logger.info(f"Processing incoming message from {sender_id}: {content}")

            # Check if message is a command for the agent
            if content.startswith("/agent") or content.startswith("!"):
                # Extract command
                command = content.replace("/agent", "").replace("!", "").strip()

                # Process command
                result = await self.process_command(command)

                # Send response back
                if sender_id and result.get("response"):
                    await self.send_chat_message(sender_id, f"🤖 {result['response']}")

            # Notify listeners
            for listener in self.chat_listeners:
                try:
                    await listener({
                        "type": "message_received",
                        "sender_id": sender_id,
                        "content": content,
                        "processed": True
                    })
                except Exception as e:
                    logger.error(f"Chat listener error: {e}")

        except Exception as e:
            logger.error(f"Error processing incoming message: {e}")

    def _find_connector(self, command: str) -> Optional[ServiceConnector]:
        """Find the appropriate connector for a command."""
        for connector in self.connectors:
            if connector.can_handle(command):
                return connector
        return None

    def _extract_parameters(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters from command text (improved implementation)."""
        import re
        parameters = {}

        # Extract amounts (for payments) - more specific pattern
        amount_match = re.search(r'\$?(\d+(?:\.\d{2})?)\s*(?:USD|dollars?|bucks?)?\b', command, re.IGNORECASE)
        if amount_match:
            try:
                amount = float(amount_match.group(1))
                # Don't treat phone numbers as amounts (phone numbers are usually > 10M when treated as floats)
                if amount < 1000000:
                    parameters["amount"] = amount
            except ValueError:
                pass

        # Extract phone numbers
        phone_match = re.search(r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})', command)
        if phone_match:
            parameters["to"] = phone_match.group(1)

        # Extract email addresses
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', command)
        if email_match:
            parameters["to"] = email_match.group(0)

        # Extract recipient names (basic - looks for "to [name]" patterns)
        to_match = re.search(r'\bto\s+([A-Za-z\s]+?)(?:\s|$)', command, re.IGNORECASE)
        if to_match and not parameters.get("to"):
            parameters["recipient_name"] = to_match.group(1).strip()

        # Extract message content (everything after "saying" or in quotes)
        message_match = re.search(r'(?:saying|message|text)\s+(.+?)(?:\s+to\s|$)', command, re.IGNORECASE)
        if message_match:
            parameters["message"] = message_match.group(1).strip()
        else:
            # Look for quoted message
            quote_match = re.search(r'["\']([^"\']+)["\']', command)
            if quote_match:
                parameters["message"] = quote_match.group(1)

        # Add context parameters
        parameters.update(context)

        return parameters

    def _generate_response(self, result: Dict[str, Any], connector: ServiceConnector) -> str:
        """Generate a natural language response from the result."""
        action = result.get("action", "")

        if action == "payment_processed":
            amount = result.get("amount", 0)
            currency = result.get("currency", "USD")
            return f"✅ Payment of ${amount} {currency} has been processed successfully."

        elif action == "refund_processed":
            amount = result.get("amount", 0)
            return f"✅ Refund of ${amount} has been processed successfully."

        elif action == "message_sent":
            to = result.get("to", "recipient")
            return f"✅ Your message has been sent successfully to {to}."

        elif action == "message_failed":
            error_msg = result.get("message", "Message could not be sent.")
            return f"❌ {error_msg}"

        elif action == "call_initiated":
            return "✅ Call has been initiated successfully."

        else:
            return f"✅ {connector.name} has completed the requested action."

    async def get_available_services(self) -> List[Dict[str, Any]]:
        """Get list of available services."""
        return [
            {
                "name": connector.name,
                "type": connector.type,
                "capabilities": self._get_connector_capabilities(connector)
            }
            for connector in self.connectors
        ]

    def _get_connector_capabilities(self, connector: ServiceConnector) -> List[str]:
        """Get capabilities of a connector."""
        if isinstance(connector, PaymentConnector):
            return ["Process payments", "Handle refunds", "Manage transactions"]
        elif isinstance(connector, CommunicationConnector):
            return ["Send messages", "Make calls", "Handle communications"]
        else:
            return ["Execute service commands"]


class UserAgent:
    """Isolated agent instance for a specific user."""

    def __init__(self, user_id: int, user_data: Dict[str, Any]):
        self.user_id = user_id
        self.user_data = user_data
        self.connectors: List[ServiceConnector] = []
        self.user_services: List[Dict[str, Any]] = []
        self.conversation_history: List[Dict[str, Any]] = []
        self.chat_listeners: List[callable] = []
        self.is_initialized = False

        # AI capabilities (shared across users for now)
        self.ai_enabled = bool(settings.openai_api_key)
        if self.ai_enabled:
            try:
                self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.ai_enabled = False

    async def initialize(self):
        """Initialize user-specific agent."""
        try:
            logger.info(f"Initializing agent for user {self.user_id}")

            # Load user-specific services
            try:
                services = await api_client.get_user_agent_services()
                self.user_services = services
                logger.info(f"Loaded {len(services)} services for user {self.user_id}")
            except Exception as api_error:
                logger.warning(f"Failed to load services for user {self.user_id}: {api_error}")
                # Use mock services
                self.user_services = [
                    {"id": 1, "name": "Mock Payment Service", "type": "payment"},
                    {"id": 2, "name": "Mock Communication Service", "type": "communication"}
                ]

            # Initialize connectors for this user
            self._initialize_connectors()
            self.is_initialized = True

            logger.info(f"User agent {self.user_id} initialized with {len(self.connectors)} connectors")

        except Exception as e:
            logger.error(f"Failed to initialize user agent {self.user_id}: {e}")
            raise

    def _initialize_connectors(self):
        """Initialize service connectors for this user."""
        self.connectors = []

        for service in self.user_services:
            service_type = service.get("type", "").lower()

            if service_type == "payment":
                connector = PaymentConnector(service)
            elif service_type == "communication":
                connector = CommunicationConnector(service)
            else:
                connector = ServiceConnector(service)

            self.connectors.append(connector)

    async def process_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process command for this specific user."""
        if not self.is_initialized:
            await self.initialize()

        try:
            logger.info(f"User {self.user_id} processing command: {command}")

            # Find appropriate connector
            connector = self._find_connector(command)

            if not connector:
                return {
                    "response": "I'm sorry, I don't have a service that can handle that request.",
                    "action": "no_service_found",
                    "available_services": [c.name for c in self.connectors]
                }

            # Extract parameters
            parameters = self._extract_parameters(command, context or {})

            # Execute command
            result = await connector.execute(command, parameters)

            # Generate response
            response = self._generate_response(result, connector)

            # Add to user-specific history
            self._add_to_history(command, response, result)

            return {
                "response": response,
                "action": result.get("action", "command_executed"),
                "service": connector.name,
                "user_id": self.user_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error processing command for user {self.user_id}: {e}")
            return {
                "response": "I encountered an error while processing your request. Please try again.",
                "error": str(e),
                "action": "error"
            }

    def _find_connector(self, command: str) -> Optional[ServiceConnector]:
        """Find appropriate connector for command."""
        for connector in self.connectors:
            if connector.can_handle(command):
                return connector
        return None

    def _extract_parameters(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters from command (same as global agent)."""
        # Use the same parameter extraction logic
        return AgentCore()._extract_parameters(command, context)

    def _generate_response(self, result: Dict[str, Any], connector: ServiceConnector) -> str:
        """Generate response (same as global agent)."""
        return AgentCore()._generate_response(result, connector)

    def _add_to_history(self, command: str, response: str, result: Dict[str, Any]):
        """Add to user-specific conversation history."""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "response": response,
            "result": result
        })

        # Keep only last 50 interactions per user
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]

    async def send_chat_message(self, receiver_id: int, content: str) -> Dict[str, Any]:
        """Send chat message as this user."""
        try:
            result = await api_client.send_message(receiver_id, content)
            return {
                "action": "message_sent",
                "receiver_id": receiver_id,
                "content": content,
                "status": "success" if result.get("status") == "success" else "failed"
            }
        except Exception as e:
            logger.error(f"Chat send error for user {self.user_id}: {e}")
            return {"action": "message_failed", "error": str(e)}


class AgentManager:
    """Manages isolated agent instances for multiple users."""

    def __init__(self):
        self.user_agents: Dict[int, UserAgent] = {}
        self.global_agent = AgentCore()  # Fallback global agent

    async def get_user_agent(self, user_id: int, user_data: Dict[str, Any]) -> UserAgent:
        """Get or create isolated agent for user."""
        if user_id not in self.user_agents:
            self.user_agents[user_id] = UserAgent(user_id, user_data)
            await self.user_agents[user_id].initialize()

        return self.user_agents[user_id]

    async def process_command_for_user(self, user_id: int, user_data: Dict[str, Any], command: str) -> Dict[str, Any]:
        """Process command for specific user with isolation."""
        try:
            user_agent = await self.get_user_agent(user_id, user_data)
            return await user_agent.process_command(command)
        except Exception as e:
            logger.error(f"Failed to process command for user {user_id}: {e}")
            # Fallback to global agent
            return await self.global_agent.process_command(command)


# Global instances
agent_core = AgentCore()
agent_manager = AgentManager()
