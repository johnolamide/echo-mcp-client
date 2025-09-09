#!/usr/bin/env python3
"""
WebSocket client example for connecting to Echo MCP Client Agent.
"""
import asyncio
import json
import websockets
import sys

async def agent_client():
    """Connect to the agent WebSocket endpoint."""
    user_id = input("Enter your user ID: ").strip()
    jwt_token = input("Enter your JWT token: ").strip()

    uri = f"ws://localhost:8000/ws/agent/{user_id}"

    try:
        async with websockets.connect(
            uri,
            extra_headers={"Authorization": f"Bearer {jwt_token}"}
        ) as websocket:
            print("🤖 Connected to Echo Agent!")
            print("Type your commands (or 'quit' to exit):")
            print()

            # Handle incoming messages
            async def receive_messages():
                try:
                    async for message in websocket:
                        data = json.loads(message)
                        msg_type = data.get("type", "unknown")

                        if msg_type == "welcome":
                            print(f"🤖 {data['message']}")
                            for cmd in data.get("available_commands", []):
                                print(f"   {cmd}")
                        elif msg_type == "response":
                            print(f"🤖 {data['message']}")
                        elif msg_type == "error":
                            print(f"❌ {data['message']}")
                        elif msg_type == "help":
                            print(f"🤖 {data['message']}")
                            for cmd in data.get("commands", []):
                                print(f"   {cmd}")
                        elif msg_type == "services":
                            print(f"🤖 {data['message']}")
                            for service in data.get("services", []):
                                print(f"   • {service['name']} ({service['type']})")
                        elif msg_type == "status":
                            print(f"🤖 {data['message']}")
                            status = data.get("status", {})
                            print(f"   User ID: {status.get('user_id')}")
                            print(f"   Agent Initialized: {status.get('agent_initialized')}")
                            print(f"   Services: {status.get('services_count')}")
                            print(f"   Conversation Length: {status.get('conversation_length')}")
                        elif msg_type == "pong":
                            print("🏓 Pong!")
                        else:
                            print(f"📨 {message}")
                        print()
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 Connection closed")

            # Send messages
            async def send_messages():
                try:
                    while True:
                        command = input("You: ").strip()

                        if command.lower() in ['quit', 'exit', 'q']:
                            await websocket.close()
                            break

                        if command.lower() == 'ping':
                            message = {"type": "ping"}
                        else:
                            message = {
                                "type": "command",
                                "content": command
                            }

                        await websocket.send(json.dumps(message))

                except KeyboardInterrupt:
                    await websocket.close()

            # Run both tasks concurrently
            await asyncio.gather(receive_messages(), send_messages())

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nMake sure:")
        print("1. The Echo MCP Client server is running: python -m src.main --server")
        print("2. You have a valid JWT token")
        print("3. The server is accessible at ws://localhost:8000")

if __name__ == "__main__":
    print("🔌 Echo MCP Client - WebSocket Agent Connector")
    print("=" * 50)
    asyncio.run(agent_client())
