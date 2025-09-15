"""
Echo MCP Client - Main Application with WebSocket Support
"""
import asyncio
import logging
import sys
import json
from typing import Optional, Dict, Any
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
# Authentication removed for hackathon demo
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.api.server_client import api_client
from src.agent.agent_core import agent_core, agent_manager


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.log_file) if settings.log_file else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

# FastAPI application for WebSocket endpoints
app = FastAPI(title="Echo MCP Client Agent API", description="Real-time agent communication via WebSocket")

# CORS Configuration - Temporarily disabled for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                # WebSocket connection is likely closed, remove it
                logger.warning(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)
                raise

manager = ConnectionManager()

# Authentication removed for hackathon demo
# Authentication dependency
# security = HTTPBearer()

# async def get_current_user_ws(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     """Authenticate WebSocket connection."""
#     token = credentials.credentials

#     # Verify token with server
#     api_client.set_auth_token(token)
#     try:
#         user_info = await api_client.get_current_user()
#         if user_info.get("status") == "success":
#             return user_info["data"]
#         else:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid authentication token"
#             )
#     except Exception as e:
#         logger.error(f"Authentication error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authentication failed"
#         )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Echo MCP Client Agent API",
        "status": "running",
        "websocket_endpoint": "/ws/agent/{user_id}"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancer."""
    # Get basic status information
    status_info = await client.get_status()

    return {
        "status": "healthy",
        "service": "echo-mcp-client",
        "timestamp": asyncio.get_event_loop().time(),
        "version": "1.0.0",
        "authenticated": status_info.get("authenticated", False),
        "server_connection": status_info.get("server_host", "unknown"),
        "websocket_endpoint": "/ws/agent/{user_id}",
        "active_user_agents": status_info.get("active_user_agents", 0)
    }

@app.websocket("/ws/agent/{user_id}")
async def websocket_agent(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time agent communication."""
    logger.info(f"WebSocket connection attempt for user {user_id}")

    try:
        # Accept connection
        await manager.connect(websocket, user_id)
        logger.info(f"✅ WebSocket connection established for user {user_id}")

        # Get user data (simplified - in production you'd validate the token)
        user_data = {"id": int(user_id), "username": f"user_{user_id}"}

        # Get or create user agent
        user_agent = await agent_manager.get_user_agent(int(user_id), user_data)

        # Send welcome message
        welcome_msg = {
            "type": "welcome",
            "message": f"🤖 Connected to Echo Agent for user {user_id}",
            "timestamp": asyncio.get_event_loop().time(),
            "available_commands": [
                "Type your commands naturally (e.g., 'pay $10 to merchant@example.com')",
                "Use 'services' to see available services",
                "Use 'help' for more information"
            ]
        }
        await manager.send_personal_message(json.dumps(welcome_msg), user_id)

        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                logger.info(f"📨 Received from user {user_id}: {data}")

                message_data = json.loads(data)
                message_type = message_data.get("type", "command")
                content = message_data.get("content", "").strip()

                if message_type == "command":
                    if not content:
                        response = {
                            "type": "error",
                            "message": "Empty command received",
                            "timestamp": asyncio.get_event_loop().time()
                        }
                    elif content.lower() in ["help", "h", "?"]:
                        response = {
                            "type": "help",
                            "message": "🤖 Echo Agent Help",
                            "commands": [
                                "• Send payments: 'pay $25.50 to merchant@example.com'",
                                "• Send messages: 'send message hello to user@example.com'",
                                "• Check services: 'services'",
                                "• Get status: 'status'"
                            ],
                            "timestamp": asyncio.get_event_loop().time()
                        }
                    elif content.lower() == "services":
                        services = await user_agent.get_available_services()
                        response = {
                            "type": "services",
                            "message": f"Available services ({len(services)}):",
                            "services": services,
                            "timestamp": asyncio.get_event_loop().time()
                        }
                    elif content.lower() == "status":
                        status_info = {
                            "user_id": user_id,
                            "agent_initialized": user_agent.is_initialized,
                            "services_count": len(user_agent.connectors),
                            "conversation_length": len(user_agent.conversation_history)
                        }
                        response = {
                            "type": "status",
                            "message": "Agent Status",
                            "status": status_info,
                            "timestamp": asyncio.get_event_loop().time()
                        }
                    else:
                        # Process command with user agent
                        result = await user_agent.process_command(content)

                        response = {
                            "type": "response",
                            "message": result.get("response", "Command processed"),
                            "action": result.get("action", "unknown"),
                            "service": result.get("service", "unknown"),
                            "timestamp": asyncio.get_event_loop().time()
                        }

                elif message_type == "ping":
                    response = {
                        "type": "pong",
                        "timestamp": asyncio.get_event_loop().time()
                    }
                else:
                    response = {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                        "timestamp": asyncio.get_event_loop().time()
                    }

                # Send response back to client
                await manager.send_personal_message(json.dumps(response), user_id)
                logger.info(f"📤 Sent response to user {user_id}: {response['type']}")

            except WebSocketDisconnect:
                # Handle WebSocket disconnect gracefully
                logger.info(f"WebSocket disconnected for user {user_id} during message processing")
                break

            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": asyncio.get_event_loop().time()
                }
                try:
                    await manager.send_personal_message(json.dumps(error_response), user_id)
                except:
                    # Connection might be closed, break the loop
                    logger.warning(f"Failed to send error response to user {user_id}, connection likely closed")
                    break

            except Exception as e:
                # Check if this is a WebSocket connection error
                error_str = str(e).lower()
                if "disconnect" in error_str or "connection" in error_str or "websocket" in error_str:
                    logger.info(f"WebSocket connection error for user {user_id}: {e}")
                    break
                
                logger.error(f"Error processing message for user {user_id}: {e}")
                error_response = {
                    "type": "error",
                    "message": f"Internal error: {str(e)}",
                    "timestamp": asyncio.get_event_loop().time()
                }
                try:
                    await manager.send_personal_message(json.dumps(error_response), user_id)
                except:
                    # Connection might be closed, break the loop
                    logger.warning(f"Failed to send error response to user {user_id}, connection likely closed")
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
        manager.disconnect(user_id)

    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)


class EchoMCPClient:
    """Main client application class."""

    def __init__(self):
        self.is_authenticated = False
        self.current_user = None

    async def initialize(self):
        """Initialize the client application."""
        logger.info("Initializing Echo MCP Client...")

        try:
            # Test server connection (optional)
            try:
                await self._test_server_connection()
            except Exception as e:
                logger.warning(f"Server connection test failed: {e}. Continuing without server connection.")

            # Authenticate if token is available
            if settings.jwt_token:
                try:
                    await self._authenticate_with_token()
                except Exception as e:
                    logger.warning(f"Authentication failed: {e}. Continuing without authentication.")
            else:
                logger.info("No JWT token provided. Running in anonymous mode.")

            # Initialize agent (should work even without authentication)
            try:
                await agent_core.initialize()
            except Exception as e:
                logger.warning(f"Agent initialization failed: {e}. Using mock services.")
                # Continue anyway - agent should work with mock services

            logger.info("Echo MCP Client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize client: {e}")
            # Don't raise - allow the application to start even with initialization issues
            logger.warning("Continuing with limited functionality due to initialization errors")

    async def _test_server_connection(self):
        """Test connection to the server."""
        try:
            # Try to access a public endpoint or health check
            response = await api_client._make_request("GET", "/health")
            logger.info("✅ Server connection successful")
        except Exception as e:
            # Try alternative endpoint if health check doesn't exist
            try:
                response = await api_client._make_request("GET", "/")
                logger.info("✅ Server connection successful (via root endpoint)")
            except Exception as e2:
                logger.warning(f"Server connection test failed: {e2}")
                raise Exception(f"Cannot connect to server at {settings.server_host}")

    async def _authenticate_with_token(self):
        """Authenticate using existing JWT token."""
        try:
            api_client.set_auth_token(settings.jwt_token)
            user_info = await api_client.get_current_user()

            if user_info.get("status") == "success":
                self.current_user = user_info["data"]
                self.is_authenticated = True
                logger.info(f"✅ Authenticated as user: {self.current_user.get('username')}")
            else:
                logger.error("❌ Authentication failed")
                raise ValueError("Invalid JWT token")

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise

    async def login(self, username: str, password: str):
        """Login with username and password."""
        try:
            response = await api_client.login(username, password)

            if response.get("status") == "success":
                self.is_authenticated = True
                self.current_user = response["data"]["user"]
                logger.info(f"✅ Logged in as: {self.current_user.get('username')}")
                return True
            else:
                logger.error("❌ Login failed")
                return False

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    async def process_command(self, command: str) -> str:
        """Process a user command and return response."""
        if not self.is_authenticated or not self.current_user:
            return "Please login first to use the agent."

        try:
            # Use isolated user agent
            user_id = self.current_user.get("id")
            result = await agent_manager.process_command_for_user(user_id, self.current_user, command)
            return result.get("response", "Command processed successfully")

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return "Sorry, I encountered an error processing your command."

    async def get_status(self) -> Dict[str, Any]:
        """Get client status information."""
        user_agent_info = {}
        if self.current_user:
            user_id = self.current_user.get("id")
            if user_id in agent_manager.user_agents:
                user_agent = agent_manager.user_agents[user_id]
                user_agent_info = {
                    "user_services_count": len(user_agent.user_services),
                    "user_connectors_count": len(user_agent.connectors),
                    "conversation_history_count": len(user_agent.conversation_history)
                }

        return {
            "authenticated": self.is_authenticated,
            "user": self.current_user.get("username") if self.current_user else None,
            "user_isolation": True,
            "active_user_agents": len(agent_manager.user_agents),
            "global_agent_initialized": agent_core.is_initialized,
            "user_agent_info": user_agent_info,
            "server_host": settings.server_host
        }

    async def close(self):
        """Clean up resources."""
        await api_client.close()
        logger.info("Echo MCP Client shut down")


# Global client instance
client = EchoMCPClient()


async def run_server():
    """Run the FastAPI server with WebSocket support."""
    print("🚀 Starting Echo MCP Client Agent Server")
    print("=" * 50)
    print("WebSocket endpoint: ws://localhost:8000/ws/agent/{user_id}")
    print("REST API: http://localhost:8000")
    print("Press Ctrl+C to stop")
    print()

    # Initialize the client
    await client.initialize()

    # Start server
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=settings.agent_port,
        log_level=settings.log_level.lower()
    )
    server = uvicorn.Server(config)

    try:
        await server.serve()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    finally:
        await client.close()


async def main():
    """Main entry point - supports both CLI and server modes."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        # Run as WebSocket server
        await run_server()
    else:
        # Run as CLI application
        await run_cli()


async def run_cli():
    """CLI application mode."""
    print("🤖 Echo MCP Client - CLI Mode")
    print("=" * 50)
    print("💡 For WebSocket server mode, run: python -m src.main --server")
    print()

    try:
        # Initialize client
        await client.initialize()

        # CLI loop
        while True:
            if not client.is_authenticated:
                print("\nPlease login to continue:")
                username = input("Username: ").strip()
                password = input("Password: ").strip()

                if await client.login(username, password):
                    print("Login successful!")
                else:
                    print("Login failed. Please try again.")
                    continue

            # Main command loop
            print("\n🤖 Agent ready! Type your commands (or 'quit' to exit):")
            while True:
                try:
                    command = input("\nYou: ").strip()

                    if command.lower() in ['quit', 'exit', 'q']:
                        break

                    if command.lower() == 'status':
                        status = await client.get_status()
                        print(f"Status: {status}")
                        continue

                    if command.lower() == 'services':
                        services = await agent_core.get_available_services()
                        print("Available services:")
                        for service in services:
                            print(f"  - {service['name']} ({service['type']})")
                        continue

                    # Process command
                    response = await client.process_command(command)
                    print(f"🤖 Agent: {response}")

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")

            if input("\nSwitch user? (y/n): ").lower() != 'y':
                break

    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Error: {e}")

    finally:
        await client.close()
        print("\n👋 Goodbye!")


async def main():
    """Main entry point - supports both CLI and server modes."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        # Run as WebSocket server
        await run_server()
    else:
        # Run as CLI application
        await run_cli()


if __name__ == "__main__":
    asyncio.run(main())
