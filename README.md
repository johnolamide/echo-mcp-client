# Echo MCP Client

AI Agent client for the Echo MCP (Model Context Protocol) system. This client provides intelligent service management through natural language commands with advanced AI reasoning, user isolation, and real-time chat integration.

## 🚀 **New Features (Latest Update)**

### 🤖 **AI-Enhanced Agent Reasoning**
- **OpenAI Integration**: Advanced natural language understanding using GPT models
- **Intelligent Command Analysis**: AI-powered intent recognition and parameter extraction
- **Contextual Responses**: AI-generated responses based on command analysis and execution results

### 🔒 **User Isolation & Multi-Tenant Support**
- **Isolated User Agents**: Each user has their own agent instance with separate conversation history
- **Secure Service Access**: User-specific service configurations and permissions
- **Privacy Protection**: Complete data isolation between users

### 💬 **Real-Time Chat Integration**
- **WebSocket Support**: Real-time messaging capabilities
- **Agent Chat Commands**: Trigger agent actions via chat messages (e.g., `/agent pay $10`)
- **Event-Driven Architecture**: Chat listeners for incoming messages and responses

### 🧪 **Enhanced Testing Framework**
- **Comprehensive Unit Tests**: Coverage for all major components
- **Integration Tests**: End-to-end testing with mocked services
- **User Isolation Tests**: Validation of multi-user scenarios

## Features

- 🤖 **AI Agent Core**: Process natural language commands and execute service actions
- 🔗 **Service Connectors**: Modular connectors for different service types (Payment, Communication, etc.)
- 🌐 **Server Integration**: Seamless integration with echo-mcp-server
- 💬 **Command Processing**: Intelligent command parsing and execution
- 🔄 **Plug-and-Play Services**: Dynamic loading of user-configured services
- 🎯 **User Isolation**: Complete separation of user data and agent instances
- ⚡ **Real-Time Chat**: WebSocket-based messaging with agent interaction
- 🧠 **AI Reasoning**: OpenAI-powered command understanding and response generation

## Project Structure

```
echo-mcp-client/
├── src/
│   ├── agent/
│   │   ├── agent_core.py    # Main agent with AI reasoning & user isolation
│   │   └── __init__.py
│   ├── api/
│   │   ├── server_client.py # Server communication
│   │   └── __init__.py
│   ├── config/
│   │   ├── settings.py      # App settings with AI config
│   │   └── __init__.py
│   ├── main.py             # Application entry point with user isolation
│   ├── services/           # Service connectors (future expansion)
│   │   └── __init__.py
│   └── tests/              # Comprehensive test suite
│       ├── test_agent.py   # Agent, isolation, and AI tests
│       └── __init__.py
├── requirements.txt        # Dependencies including OpenAI, WebSockets
├── .env                   # Environment variables
└── README.md             # This file
```

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **AI Configuration** (Optional):
   ```bash
   # Add to .env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

### Basic Usage

```python
from src.main import client

# Initialize and login
await client.initialize()
await client.login("username", "password")

# Process commands
response = await client.process_command("pay $25.50 to merchant@example.com")
print(response)

# Get status
status = await client.get_status()
print(f"User agents: {status['active_user_agents']}")
```

### AI-Enhanced Commands

```python
# Use AI reasoning (requires OpenAI API key)
result = await agent_core.process_command_with_ai("send a payment for dinner")
print(result["ai_enhanced"])  # True if AI was used
```

### User Isolation

```python
# Each user gets their own agent instance
user_agent = await agent_manager.get_user_agent(user_id, user_data)
result = await user_agent.process_command("send message to friend@example.com")
```

### Chat Integration

```python
# Send chat messages
result = await agent_core.send_chat_message(receiver_id=2, content="Hello!")

# Add chat listeners
def on_message_received(message):
    print(f"Received: {message}")

agent_core.add_chat_listener(on_message_received)
```

## Configuration

### Environment Variables

```bash
# Server Configuration
SERVER_HOST=https://api.echo-mcp-server.qkiu.tech
JWT_TOKEN=your_jwt_token_here

# AI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Chat Configuration
WEBSOCKET_ENABLED=true

# User Isolation
USER_ISOLATION_ENABLED=true
```

### Service Connectors

The system supports extensible service connectors:

- **PaymentConnector**: Handles payment commands (`pay`, `transfer`, etc.)
- **CommunicationConnector**: Handles messaging (`send`, `call`, etc.)
- **Custom Connectors**: Extend `ServiceConnector` base class for new services

## Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest src/tests/

# Run specific test
pytest src/tests/test_agent.py::test_payment_connector
```

## API Reference

### AgentCore

- `process_command(command, context)`: Process natural language commands
- `process_command_with_ai(command, context)`: AI-enhanced command processing
- `send_chat_message(receiver_id, content)`: Send chat messages
- `add_chat_listener(listener)`: Add chat event listeners

### AgentManager

- `get_user_agent(user_id, user_data)`: Get isolated user agent
- `process_command_for_user(user_id, user_data, command)`: Process command for specific user

### EchoMCPClient

- `initialize()`: Initialize client and connect to server
- `login(username, password)`: Authenticate user
- `process_command(command)`: Process commands with user isolation
- `get_status()`: Get client status including user agent info

## Architecture

### User Isolation Strategy

```
User A (ID: 1)           User B (ID: 2)
├── Agent Instance A     ├── Agent Instance B
├── Services: [Pay]      ├── Services: [Pay, Comm]
├── History: [...]       ├── History: [...]
└── Connectors: [...]    └── Connectors: [...]
```

### AI Integration Flow

```
User Command → AI Analysis → Parameter Extraction → Service Matching → Execution → AI Response
```

### Chat Integration Flow

```
Chat Message → Agent Processing → Service Execution → Chat Response
```

## Contributing

1. Follow the existing code structure with user isolation in mind
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure AI features are optional (graceful degradation without API keys)

## License

This project is part of the Echo MCP system.

## Configuration

Create a `.env` file with the following variables:

```env
# Server Configuration
SERVER_HOST=https://api.echo-mcp-server.qkiu.tech
MCP_SERVER_URL=https://api.echo-mcp-server.qkiu.tech/mcp

# Authentication
JWT_TOKEN=your_jwt_token_here

# AI Configuration
OPENAI_API_KEY=your_openai_api_key

# Agent Configuration
AGENT_NAME=Echo Assistant
AGENT_DESCRIPTION=Your personal AI assistant

# Logging
LOG_LEVEL=INFO
```

## Usage

### Command Line Interface

```bash
# Run the interactive CLI
python src/main.py
```

### Programmatic Usage

```python
from src.main import client
from src.agent.agent_core import agent_core

# Initialize
await client.initialize()

# Process commands
response = await client.process_command("pay $10 to merchant")
print(response)
```

## Available Commands

The agent can handle various commands based on your configured services:

### Payment Commands
- "pay $50 to Starbucks"
- "process payment of $25.99"
- "refund transaction txn_123"

### Communication Commands
- "send message to +123-456-7890"
- "call 555-123-4567"
- "text John: Hello there!"

### General Commands
- "status" - Show client status
- "services" - List available services
- "quit" - Exit the application

## Service Connectors

### Built-in Connectors

1. **PaymentConnector**: Handles payment processing
   - Stripe integration
   - Transaction management
   - Refund processing

2. **CommunicationConnector**: Handles messaging
   - SMS sending
   - Phone calls
   - Message templates

### Adding Custom Connectors

```python
from src.agent.agent_core import ServiceConnector

class CustomConnector(ServiceConnector):
    def __init__(self, service_config: dict):
        super().__init__(service_config)

    def can_handle(self, command: str) -> bool:
        return "custom" in command.lower()

    async def execute(self, command: str, parameters: dict) -> dict:
        # Your custom logic here
        return {"action": "custom_executed", "result": "success"}
```

## Testing

Run the test suite:

```bash
python test_client.py
```

## Integration with Server

The client automatically connects to the echo-mcp-server for:

- User authentication
- Service registry access
- Agent configuration
- Real-time messaging

Ensure the server is running before starting the client.

## Development

### Adding New Features

1. **New Service Types**: Add connectors in `src/agent/`
2. **API Endpoints**: Extend `src/api/server_client.py`
3. **Configuration**: Update `src/config/settings.py`

### Code Style

- Use Black for code formatting
- Use isort for import sorting
- Follow PEP 8 guidelines

## Troubleshooting

### Common Issues

1. **Server Connection Failed**
   - Ensure echo-mcp-server is running
   - Check SERVER_HOST in .env
   - Verify network connectivity

2. **Authentication Failed**
   - Check JWT_TOKEN in .env
   - Ensure token is not expired
   - Verify user credentials

3. **Service Not Available**
   - Check if service is added to your agent
   - Verify service configuration
   - Check server logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is part of the Echo MCP system.
- `tests/`: Unit tests
