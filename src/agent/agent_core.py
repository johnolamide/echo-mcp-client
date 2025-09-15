"""
Agent core for processing commands and managing services.
Enhanced with LangChain + Amazon Bedrock for advanced AI reasoning capabilities.
Supports dynamic service loading based on user subscriptions.
"""
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

# LangChain + Bedrock imports
from langchain_aws import ChatBedrockConverse
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferWindowMemory

from config.settings import settings
from api.server_client import api_client


logger = logging.getLogger(__name__)


class DynamicServiceRegistry:
    """Registry for dynamically creating service function tools."""

    def __init__(self):
        self.service_factories: Dict[str, Callable] = {}
        self.register_builtin_services()

    def register_builtin_services(self):
        """Register built-in service types and their tool factories."""
        self.service_factories = {
            "payment": self._create_payment_tool,
            "communication": self._create_communication_tool,
            "email": self._create_email_tool,
            "sms": self._create_sms_tool,
            "stripe": self._create_stripe_tool,
            "twilio": self._create_twilio_tool,
        }

    def register_service_factory(self, service_type: str, factory_func: Callable):
        """Register a custom service factory."""
        self.service_factories[service_type] = factory_func

    def create_tool_for_service(self, service_config: Dict[str, Any]) -> Optional[Callable]:
        """Create a function tool for a given service configuration."""
        service_type = service_config.get("type", "").lower()
        service_name = service_config.get("name", "").lower()

        # Try exact type match first
        if service_type in self.service_factories:
            return self.service_factories[service_type](service_config)

        # Try name-based matching for specific services
        for name_key in ["stripe", "twilio", "paypal", "venmo"]:
            if name_key in service_name:
                if name_key in self.service_factories:
                    return self.service_factories[name_key](service_config)

        # Fallback to generic service tool
        return self._create_generic_service_tool(service_config)

    def _create_payment_tool(self, service_config: Dict[str, Any]) -> Callable:
        """Create a payment service tool."""
        service_name = service_config.get("name", "Payment Service")

        @tool
        def payment_tool(command: str, amount: float = None, currency: str = "USD",
                        recipient: str = None, description: str = None) -> Dict[str, Any]:
            """Handle payment-related commands like pay, transfer, refund."""
            try:
                if not amount or amount <= 0:
                    return {
                        "action": "payment_failed",
                        "error": "Invalid amount",
                        "message": "Please specify a valid payment amount."
                    }

                # Simulate payment processing with service-specific logic
                return {
                    "action": "payment_processed",
                    "service": service_name,
                    "amount": amount,
                    "currency": currency,
                    "recipient": recipient,
                    "description": description,
                    "status": "success",
                    "transaction_id": f"txn_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
            except Exception as e:
                logger.error(f"{service_name} payment error: {e}")
                return {"action": "payment_failed", "error": str(e)}

        payment_tool.__name__ = f"{service_name.lower().replace(' ', '_')}_tool"
        return payment_tool

    def _create_communication_tool(self, service_config: Dict[str, Any]) -> Callable:
        """Create a communication service tool."""
        service_name = service_config.get("name", "Communication Service")

        @tool
        def communication_tool(command: str, message: str = None, recipient: str = None,
                             phone: str = None, subject: str = None) -> Dict[str, Any]:
            """Handle communication-related commands like send message, call."""
            try:
                if not message:
                    return {
                        "action": "message_failed",
                        "error": "No message content",
                        "message": "Please specify what message you want to send."
                    }

                if not (recipient or phone):
                    return {
                        "action": "message_failed",
                        "error": "No recipient",
                        "message": "Please specify who you want to send the message to."
                    }

                # Simulate message sending
                return {
                    "action": "message_sent",
                    "service": service_name,
                    "message": message,
                    "recipient": recipient or phone,
                    "subject": subject,
                    "status": "success",
                    "message_id": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
            except Exception as e:
                logger.error(f"{service_name} communication error: {e}")
                return {"action": "message_failed", "error": str(e)}

        communication_tool.__name__ = f"{service_name.lower().replace(' ', '_')}_tool"
        return communication_tool

    def _create_email_tool(self, service_config: Dict[str, Any]) -> Callable:
        """Create an email service tool."""
        service_name = service_config.get("name", "Email Service")

        @tool
        def email_tool(to: str, subject: str, body: str, cc: str = None, bcc: str = None) -> Dict[str, Any]:
            """Send an email message."""
            try:
                return {
                    "action": "email_sent",
                    "service": service_name,
                    "to": to,
                    "subject": subject,
                    "body": body,
                    "cc": cc,
                    "bcc": bcc,
                    "status": "success",
                    "message_id": f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
            except Exception as e:
                logger.error(f"{service_name} email error: {e}")
                return {"action": "email_failed", "error": str(e)}

        email_tool.__name__ = f"{service_name.lower().replace(' ', '_')}_tool"
        return email_tool

    def _create_sms_tool(self, service_config: Dict[str, Any]) -> Callable:
        """Create an SMS service tool."""
        service_name = service_config.get("name", "SMS Service")

        @tool
        def sms_tool(to: str, message: str) -> Dict[str, Any]:
            """Send an SMS message."""
            try:
                return {
                    "action": "sms_sent",
                    "service": service_name,
                    "to": to,
                    "message": message,
                    "status": "success",
                    "message_id": f"sms_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
            except Exception as e:
                logger.error(f"{service_name} SMS error: {e}")
                return {"action": "sms_failed", "error": str(e)}

        sms_tool.__name__ = f"{service_name.lower().replace(' ', '_')}_tool"
        return sms_tool

    def _create_stripe_tool(self, service_config: Dict[str, Any]) -> Callable:
        """Create a Stripe payment tool."""
        service_name = service_config.get("name", "Stripe")

        @tool
        def stripe_tool(action: str, amount: float = None, currency: str = "USD",
                       customer_id: str = None, payment_method_id: str = None) -> Dict[str, Any]:
            """Handle Stripe payment operations."""
            try:
                if action == "charge" and (not amount or amount <= 0):
                    return {
                        "action": "stripe_charge_failed",
                        "error": "Invalid amount",
                        "message": "Please specify a valid charge amount."
                    }

                return {
                    "action": f"stripe_{action}",
                    "service": service_name,
                    "amount": amount,
                    "currency": currency,
                    "customer_id": customer_id,
                    "payment_method_id": payment_method_id,
                    "status": "success",
                    "transaction_id": f"stripe_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
            except Exception as e:
                logger.error(f"{service_name} error: {e}")
                return {"action": "stripe_failed", "error": str(e)}

        stripe_tool.__name__ = "stripe_tool"
        return stripe_tool

    def _create_twilio_tool(self, service_config: Dict[str, Any]) -> Callable:
        """Create a Twilio communication tool."""
        service_name = service_config.get("name", "Twilio")

        @tool
        def twilio_tool(action: str, to: str = None, from_: str = None,
                       message: str = None, url: str = None) -> Dict[str, Any]:
            """Handle Twilio communication operations."""
            try:
                if action == "message" and not message:
                    return {
                        "action": "twilio_message_failed",
                        "error": "No message content",
                        "message": "Please specify message content."
                    }

                return {
                    "action": f"twilio_{action}",
                    "service": service_name,
                    "to": to,
                    "from": from_,
                    "message": message,
                    "url": url,
                    "status": "success",
                    "sid": f"twilio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
            except Exception as e:
                logger.error(f"{service_name} error: {e}")
                return {"action": "twilio_failed", "error": str(e)}

        twilio_tool.__name__ = "twilio_tool"
        return twilio_tool

    def _create_generic_service_tool(self, service_config: Dict[str, Any]) -> Callable:
        """Create a generic service tool for unknown service types."""
        service_name = service_config.get("name", "Generic Service")
        service_type = service_config.get("type", "generic")

        @tool
        def generic_tool(action: str, parameters: str = "{}") -> Dict[str, Any]:
            """Handle generic service operations.

            Args:
                action: The action to perform (e.g., 'send', 'receive', 'process')
                parameters: JSON string of additional parameters
            """
            try:
                # Parse parameters if provided
                parsed_params = {}
                if parameters and parameters != "{}":
                    try:
                        import json
                        parsed_params = json.loads(parameters)
                    except json.JSONDecodeError:
                        parsed_params = {"raw_parameters": parameters}

                return {
                    "action": f"{service_type}_{action}",
                    "service": service_name,
                    "parameters": parsed_params,
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"{service_name} error: {e}")
                return {"action": "generic_failed", "error": str(e)}

        generic_tool.__name__ = f"{service_name.lower().replace(' ', '_')}_tool"
        return generic_tool


# Global service registry instance
service_registry = DynamicServiceRegistry()


@tool
async def get_available_services_tool() -> Dict[str, Any]:
    """Get list of available services for the user."""
    try:
        # Get services from server
        services = await api_client.get_user_agent_services()
        return {
            "action": "services_listed",
            "services": services,
            "count": len(services)
        }
    except Exception as e:
        logger.error(f"Error getting services: {e}")
        # Fallback to mock services
        return {
            "action": "services_listed",
            "services": [
                {"id": 1, "name": "Mock Payment Service", "type": "payment"},
                {"id": 2, "name": "Mock Communication Service", "type": "communication"}
            ],
            "count": 2
        }


@tool
async def send_chat_message_tool(recipient_username: str, content: str) -> Dict[str, Any]:
    """Send a chat message to another user."""
    try:
        result = await api_client.send_message(recipient_username, content)
        return {
            "action": "message_sent",
            "recipient_username": recipient_username,
            "content": content,
            "status": "success" if result.get("status") == "success" else "failed"
        }
    except Exception as e:
        logger.error(f"Chat send error: {e}")
        return {"action": "message_failed", "error": str(e)}


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


class EchoMCPAgent:
    """LangChain + Amazon Bedrock-based agent for Echo MCP system with dynamic service loading."""

    def __init__(self, user_id: int = None, user_data: Dict[str, Any] = None):
        self.user_id = user_id
        self.user_data = user_data or {}
        self.conversation_history: List[Dict[str, Any]] = []
        self.is_initialized = False
        self.user_services: List[Dict[str, Any]] = []
        self.dynamic_tools: List[Callable] = []

        # Initialize LangChain + Bedrock agent
        self.llm = None
        self.agent_executor = None
        self.memory = None
        self._create_agent()

    async def load_user_services(self):
        """Load user services from the server and create dynamic tools."""
        try:
            logger.info(f"Loading services for user {self.user_id or 'global'}")
            self.user_services = await api_client.get_user_agent_services()

            # Create dynamic tools based on user services
            self.dynamic_tools = []
            service_capabilities = []

            for service in self.user_services:
                tool = service_registry.create_tool_for_service(service)
                if tool:
                    self.dynamic_tools.append(tool)
                    service_capabilities.append(f"- {service['name']}: {service['type']} service")

            # Add built-in tools
            self.dynamic_tools.extend([
                get_available_services_tool,
                send_chat_message_tool
            ])

            # Update agent with new tools and instructions
            self._update_agent_instructions(service_capabilities)

            logger.info(f"Loaded {len(self.user_services)} user services with {len(self.dynamic_tools)} tools")

        except Exception as e:
            logger.error(f"Failed to load user services: {e}")
            # Fallback to basic tools
            self.dynamic_tools = [
                get_available_services_tool,
                send_chat_message_tool
            ]

    def _create_agent(self):
        """Create the LangChain + Amazon Bedrock agent with initial tools."""
        instructions = self._build_base_instructions()

        # Start with basic tools, will be updated when user services are loaded
        initial_tools = [
            get_available_services_tool,
            send_chat_message_tool
        ]

        # Check if AWS credentials are available
        if not (settings.aws_access_key_id and settings.aws_secret_access_key):
            logger.warning("No AWS credentials found - operating in demo mode")
            # Create a minimal agent configuration for demo mode
            self.agent_executor = None  # Will use fallback processing
            return

        try:
            # Create Bedrock LLM using ChatBedrockConverse
            self.llm = ChatBedrockConverse(
                model="amazon.nova-pro-v1:0",
                region_name=settings.aws_region or "us-east-1",
                temperature=0.7,
                max_tokens=1000,
            )

            # Create memory for conversation history
            self.memory = ConversationBufferWindowMemory(
                memory_key="chat_history",
                return_messages=True,
                k=10  # Keep last 10 interactions
            )

            # Create the agent prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", instructions),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            # Create the agent
            agent = create_tool_calling_agent(self.llm, initial_tools, prompt)

            # Create the agent executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=initial_tools,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3,
                early_stopping_method="generate"
            )

            logger.info("LangChain + Bedrock Agent created successfully")
        except Exception as e:
            logger.error(f"Failed to create Bedrock Agent: {e}")
            logger.warning("Falling back to demo mode")
            self.agent_executor = None  # Will use fallback processing

    def _build_base_instructions(self) -> str:
        """Build the base agent instructions."""
        instructions = """
        You are Echo, an intelligent AI assistant for managing services and communications.

        Your capabilities include:
        - Managing user services and integrations
        - Providing helpful responses and guidance
        - Processing various commands through available tools

        Always be helpful, accurate, and user-friendly. If you need more information to complete a request,
        ask the user for clarification rather than making assumptions.

        Available tools:
        - get_available_services_tool: List available services
        - send_chat_message_tool: Send messages to other users
        """

        if self.user_id:
            instructions += f"\n\nYou are assisting user {self.user_id}."

        return instructions

    def _update_agent_instructions(self, service_capabilities: List[str]):
        """Update agent instructions and tools based on available services."""
        if not service_capabilities:
            return

        # Build enhanced instructions
        capabilities_text = "\n".join(service_capabilities)

        enhanced_instructions = f"""
        You are Echo, an intelligent AI assistant for managing services and communications.

        Your capabilities include:
        - Managing user services and integrations
        - Providing helpful responses and guidance
        - Processing various commands through available tools

        Available Services:
        {capabilities_text}

        Always be helpful, accurate, and user-friendly. If you need more information to complete a request,
        ask the user for clarification rather than making assumptions.

        Available tools:
        - get_available_services_tool: List available services
        - send_chat_message_tool: Send messages to other users
        """

        # Add service-specific tools to the instructions
        for service in self.user_services:
            service_name = service['name'].lower().replace(' ', '_')
            enhanced_instructions += f"- {service_name}_tool: Handle {service['type']} operations for {service['name']}\n"

        if self.user_id:
            enhanced_instructions += f"\n\nYou are assisting user {self.user_id}."

        # Update the agent's tools if available
        if self.agent_executor and self.dynamic_tools:
            # Create new prompt with updated instructions
            prompt = ChatPromptTemplate.from_messages([
                ("system", enhanced_instructions),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            # Create new agent with updated tools and prompt
            agent = create_tool_calling_agent(self.llm, self.dynamic_tools, prompt)

            # Update the agent executor
            self.agent_executor.agent = agent
            self.agent_executor.tools = self.dynamic_tools

    async def initialize(self):
        """Initialize the agent and load user services."""
        if not self.is_initialized:
            # Load user services and create dynamic tools
            await self.load_user_services()

            self.is_initialized = True
            logger.info(f"Echo MCP Agent initialized for user {self.user_id or 'global'} with {len(self.user_services)} services")

    async def process_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a command using the LangChain agent with fallback handling."""
        if not self.is_initialized:
            await self.initialize()

        # Check if we're in demo mode (no agent available)
        if self.agent_executor is None:
            logger.info("Agent executor is None, using fallback mode")
            return await self._process_command_fallback(command, context, "no_credentials")

        try:
            logger.info(f"Processing command: {command}")

            # Check if AWS credentials are available
            if not self.llm:
                logger.warning("No AWS credentials available, using fallback mode")
                return await self._process_command_fallback(command, context)

            # Add context to the command if provided
            enhanced_command = command
            if context:
                enhanced_command = f"{command}\n\nContext: {json.dumps(context)}"

            # Run the agent with the command using LangChain
            result = await self.agent_executor.ainvoke({
                "input": enhanced_command,
                "chat_history": self.memory.chat_memory.messages
            })

            # Extract the response
            response_text = result.get("output", "")
            tool_calls = []

            # Extract tool call information if available
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if len(step) > 1:
                        tool_calls.append({
                            "tool": step[0].tool,
                            "input": step[0].tool_input,
                            "output": step[1] if len(step) > 1 else None
                        })

            # Create response
            response = {
                "response": response_text,
                "action": "command_processed",
                "tool_calls": tool_calls,
                "timestamp": datetime.now().isoformat(),
                "user_id": self.user_id
            }

            # Add to conversation history
            self._add_to_history(command, response)

            return response

        except Exception as e:
            error_str = str(e).lower()

            # Check for specific AWS/Bedrock errors
            if "throttling" in error_str or "429" in error_str:
                logger.warning("AWS throttling exceeded, switching to fallback mode")
                return await self._process_command_fallback(command, context, "throttling")
            elif "unauthorized" in error_str or "access_denied" in error_str:
                logger.warning("AWS authentication error, switching to fallback mode")
                return await self._process_command_fallback(command, context, "auth_error")
            else:
                logger.error(f"Error processing command: {e}")
                return await self._process_command_fallback(command, context, "general_error")

    async def _process_command_fallback(self, command: str, context: Optional[Dict[str, Any]] = None, error_type: str = "general") -> Dict[str, Any]:
        """Fallback command processing when OpenAI is unavailable."""
        logger.info(f"Using fallback processing for command: {command}")

        # Initialize fallback response
        response = {
            "response": "",
            "action": "fallback_processed",
            "fallback_mode": True,
            "error_type": error_type,
            "timestamp": datetime.now().isoformat(),
            "user_id": self.user_id
        }

        # Simple command pattern matching for common commands
        command_lower = command.lower().strip()

        if error_type == "throttling":
            response["response"] = (
                "🤖 I'm currently operating in demo mode because the AWS service throttling limit has been reached.\n\n"
                f"I can still help you with basic commands! You said: '{command}'\n\n"
                "💡 To restore full AI capabilities:\n"
                "• Check your AWS billing and usage limits\n"
                "• Consider increasing your Bedrock service limits\n"
                "• Or wait for the throttling to reset\n\n"
                "Try commands like 'help', 'services', or 'status' to see what I can do!"
            )
        elif error_type == "auth_error":
            response["response"] = (
                "🤖 I'm operating in demo mode due to an AWS authentication issue.\n\n"
                f"I received your command: '{command}'\n\n"
                "💡 To fix the authentication:\n"
                "• Check your AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)\n"
                "• Verify your AWS region is set correctly\n"
                "• Ensure your IAM user has Bedrock permissions\n\n"
                "I can still handle basic commands while you resolve this!"
            )
        else:
            response["response"] = (
                f"🤖 I'm operating in demo mode. I received your command: '{command}'\n\n"
                "I can help you with basic information and service management!"
            )

        # Handle specific commands even in fallback mode
        if "help" in command_lower or command_lower in ["h", "?"]:
            response["response"] += (
                "\n\n📋 Available Commands:\n"
                "• 'services' - List available services\n"
                "• 'status' - Show system status\n"
                "• 'help' - Show this help message\n"
                "• Payment commands: 'pay $10 to user@example.com'\n"
                "• Message commands: 'send message hello to user@example.com'"
            )
            response["action"] = "help"

        elif "services" in command_lower:
            try:
                services = await self.get_available_services()
                service_list = "\n".join([f"• {s.get('name', 'Unknown')} ({s.get('type', 'generic')})" for s in services])
                response["response"] = f"📋 Available Services:\n{service_list}"
                response["action"] = "services_list"
                response["services"] = services
            except Exception as e:
                logger.warning(f"Failed to get services in fallback mode: {e}")
                response["response"] = "📋 Available Services:\n• Payment Service\n• Communication Service\n• Email Service"
                response["action"] = "services_list"

        elif "status" in command_lower:
            response["response"] = (
                "📊 System Status:\n"
                "• Mode: Demo/Fallback\n"
                "• AI Service: Unavailable\n"
                "• Services: Basic functionality available\n"
                "• User ID: " + str(self.user_id or "Not set")
            )
            response["action"] = "status"

        elif "pay" in command_lower and ("to" in command_lower or "@" in command):
            # Extract payment amount and recipient
            response["response"] = (
                f"💰 Payment Command Detected: '{command}'\n\n"
                "In demo mode, I can simulate payment processing but cannot execute real transactions.\n"
                "This would normally:\n"
                "• Validate payment amount and recipient\n"
                "• Process payment through your configured payment service\n"
                "• Send confirmation to both parties"
            )
            response["action"] = "payment_simulated"

        elif ("send" in command_lower or "message" in command_lower) and ("to" in command_lower or "@" in command):
            response["response"] = (
                f"📤 Message Command Detected: '{command}'\n\n"
                "In demo mode, I can simulate message sending but cannot send real messages.\n"
                "This would normally:\n"
                "• Validate recipient and message content\n"
                "• Send through your configured communication service\n"
                "• Confirm delivery status"
            )
            response["action"] = "message_simulated"

        # Add to conversation history
        self._add_to_history(command, response)

        return response

    def _add_to_history(self, command: str, response: Dict[str, Any]):
        """Add interaction to conversation history."""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "response": response
        })

        # Keep only last 50 interactions
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]

    async def get_available_services(self) -> List[Dict[str, Any]]:
        """Get available services for this user."""
        try:
            # Try to get from server first
            services = await api_client.get_user_agent_services()
            return services
        except Exception as e:
            logger.warning(f"Failed to get services from server: {e}")
            # Return mock services
            return [
                {"id": 1, "name": "Mock Payment Service", "type": "payment"},
                {"id": 2, "name": "Mock Communication Service", "type": "communication"}
            ]

    async def send_chat_message(self, receiver_username: str, content: str) -> Dict[str, Any]:
        """Send a chat message through the agent."""
        try:
            result = await api_client.send_message(receiver_username, content)

            if result.get("status") == "success":
                return {
                    "action": "message_sent",
                    "receiver_username": receiver_username,
                    "content": content,
                    "status": "success"
                }
            else:
                return {
                    "action": "message_failed",
                    "receiver_username": receiver_username,
                    "error": "Failed to send message"
                }
        except Exception as e:
            logger.error(f"Chat send error: {e}")
            return {"action": "message_failed", "error": str(e)}

    def add_chat_listener(self, listener: callable):
        """Add a listener for incoming chat messages (placeholder)."""
        # This would be implemented for real-time chat integration
        pass


class AgentCore:
    """Core agent logic for command processing and service management."""

    def __init__(self):
        # Use the new EchoMCPAgent as the core
        self.sdk_agent = EchoMCPAgent()
        self.is_initialized = False
        self.conversation_history: List[Dict[str, Any]] = []
        self.chat_listeners: List[callable] = []

        # Legacy attributes for backward compatibility
        self.connectors: List[ServiceConnector] = []
        self.user_services: List[Dict[str, Any]] = []
        self.ai_enabled = bool(settings.openai_api_key)
        self.websocket_connection = None

    async def initialize(self):
        """Initialize the agent."""
        await self.sdk_agent.initialize()
        self.is_initialized = True
        logger.info("AgentCore initialized with OpenAI Agents SDK")

        # Load user services for backward compatibility
        try:
            services = await api_client.get_user_agent_services()
            self.user_services = services
        except Exception as api_error:
            logger.warning(f"Failed to load services from server: {api_error}")
            self.user_services = [
                {"id": 1, "name": "Mock Payment Service", "type": "payment"},
                {"id": 2, "name": "Mock Communication Service", "type": "communication"}
            ]

        # Initialize connectors
        self._initialize_connectors()

    def _initialize_connectors(self):
        """Initialize service connectors based on user services using dynamic registry."""
        self.connectors = []

        for service in self.user_services:
            service_type = service.get("type", "").lower()

            # Use dynamic service registry to create appropriate connectors
            if service_type == "payment":
                connector = PaymentConnector(service)
            elif service_type == "communication":
                connector = CommunicationConnector(service)
            else:
                # Generic connector for unknown service types
                connector = ServiceConnector(service)

            self.connectors.append(connector)

        logger.info(f"Initialized {len(self.connectors)} service connectors from {len(self.user_services)} user services")

    async def process_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process command using the OpenAI Agents SDK."""
        return await self.sdk_agent.process_command(command, context)

    async def process_command_with_ai(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process command with AI reasoning (same as process_command in new implementation)."""
        return await self.process_command(command, context)

    async def _analyze_command_with_ai(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Use AI to analyze and understand the command intent."""
        if not self.ai_enabled or not self.llm:
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

            # Use LangChain for analysis
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            result = await self.llm.ainvoke(messages)
            analysis_text = result.content.strip()

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
        if not self.ai_enabled or not self.llm:
            return self._generate_response(result, connector)

        try:
            system_prompt = """Generate a helpful, natural response for the user based on the service execution result.
Be concise but informative. Include relevant details from the result."""

            user_prompt = f"""Service: {connector.name}
Action: {result.get('action', 'unknown')}
Result: {json.dumps(result)}
Analysis: {json.dumps(ai_analysis)}"""

            # Use LangChain for response generation
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response_result = await self.llm.ainvoke(messages)
            return response_result.content.strip()

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

    async def send_chat_message(self, receiver_username: str, content: str) -> Dict[str, Any]:
        """Send a chat message through the agent."""
        try:
            result = await api_client.send_message(receiver_username, content)

            if result.get("status") == "success":
                # Notify listeners
                for listener in self.chat_listeners:
                    try:
                        await listener({
                            "type": "message_sent",
                            "receiver_username": receiver_username,
                            "content": content,
                            "result": result
                        })
                    except Exception as e:
                        logger.error(f"Chat listener error: {e}")

                return {
                    "action": "message_sent",
                    "receiver_username": receiver_username,
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

        # Extract phone numbers - improved pattern
        phone_match = re.search(r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}|\+1-[0-9]{3}-[0-9]{3}-[0-9]{4})', command)
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
        
        # Use the new EchoMCPAgent as the core
        self.sdk_agent = EchoMCPAgent(user_id=user_id, user_data=user_data)
        
        # Legacy attributes for backward compatibility
        self.connectors: List[ServiceConnector] = []
        self.user_services: List[Dict[str, Any]] = []
        self.conversation_history: List[Dict[str, Any]] = []
        self.chat_listeners: List[callable] = []
        self.is_initialized = False

        # AI capabilities
        self.ai_enabled = bool(settings.openai_api_key)

    async def initialize(self):
        """Initialize user-specific agent."""
        await self.sdk_agent.initialize()
        self.is_initialized = True
        logger.info(f"UserAgent {self.user_id} initialized with OpenAI Agents SDK")

        # Load user services for backward compatibility
        try:
            services = await api_client.get_user_agent_services()
            self.user_services = services
        except Exception as api_error:
            logger.warning(f"Failed to load services for user {self.user_id}: {api_error}")
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
        """Initialize service connectors for this user using dynamic registry."""
        self.connectors = []

        for service in self.user_services:
            service_type = service.get("type", "").lower()

            # Use dynamic service registry to create appropriate connectors
            if service_type == "payment":
                connector = PaymentConnector(service)
            elif service_type == "communication":
                connector = CommunicationConnector(service)
            else:
                # Generic connector for unknown service types
                connector = ServiceConnector(service)

            self.connectors.append(connector)

        logger.info(f"UserAgent {self.user_id} initialized with {len(self.connectors)} connectors from {len(self.user_services)} services")

    async def process_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process command for this specific user using OpenAI Agents SDK."""
        return await self.sdk_agent.process_command(command, context)

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

    async def send_chat_message(self, receiver_username: str, content: str) -> Dict[str, Any]:
        """Send chat message as this user."""
        try:
            result = await api_client.send_message(receiver_username, content)
            return {
                "action": "message_sent",
                "receiver_username": receiver_username,
                "content": content,
                "status": "success" if result.get("status") == "success" else "failed"
            }
        except Exception as e:
            logger.error(f"Chat send error for user {self.user_id}: {e}")
            return {"action": "message_failed", "error": str(e)}

    async def get_available_services(self) -> List[Dict[str, Any]]:
        """Get list of available services for this user."""
        try:
            # Try to get services from the SDK agent first
            if hasattr(self.sdk_agent, 'user_services') and self.sdk_agent.user_services:
                services = self.sdk_agent.user_services
            else:
                # Fallback to API call
                services = await api_client.get_user_agent_services()

            # Format services for response
            formatted_services = []
            for service in services:
                formatted_services.append({
                    "id": service.get("id"),
                    "name": service.get("name", "Unknown Service"),
                    "type": service.get("type", "generic"),
                    "description": f"{service.get('type', 'generic').title()} service: {service.get('name', 'Unknown')}",
                    "status": "available"
                })

            return formatted_services

        except Exception as e:
            logger.warning(f"Failed to get services for user {self.user_id}: {e}")
            # Return mock services as fallback
            return [
                {
                    "id": 1,
                    "name": "Mock Payment Service",
                    "type": "payment",
                    "description": "Payment service for transactions",
                    "status": "available"
                },
                {
                    "id": 2,
                    "name": "Mock Communication Service",
                    "type": "communication",
                    "description": "Communication service for messaging",
                    "status": "available"
                }
            ]


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
