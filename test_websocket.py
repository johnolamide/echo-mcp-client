#!/usr/bin/env python3
"""
Simple WebSocket test for Echo MCP Client Agent.
"""
import asyncio
import json
import websockets

async def test_websocket():
    """Test WebSocket connection to the agent."""
    user_id = "test_user"
    jwt_token = "mock_jwt_token_for_testing"

    uri = f"ws://localhost:8000/ws/agent/{user_id}"

    try:
        async with websockets.connect(
            uri,
            extra_headers={"Authorization": f"Bearer {jwt_token}"}
        ) as websocket:
            print("✅ Connected to Echo Agent WebSocket!")

            # Send a test command
            test_command = {
                "type": "command",
                "content": "help"
            }

            await websocket.send(json.dumps(test_command))
            print("📤 Sent test command: help")

            # Receive response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 Received: {data}")

            # Send ping
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            print("📤 Sent ping")

            # Receive pong
            pong_response = await websocket.recv()
            pong_data = json.loads(pong_response)
            print(f"📨 Received: {pong_data}")

            print("✅ WebSocket test completed successfully!")

    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    print("🔌 Testing Echo MCP Client WebSocket Connection")
    print("=" * 50)
    asyncio.run(test_websocket())
