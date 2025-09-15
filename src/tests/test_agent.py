"""
Unit tests for the agent and tools.
Enhanced with AI and user isolation tests.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.agent.agent_core import AgentCore, UserAgent, AgentManager, PaymentConnector, CommunicationConnector


@pytest.mark.asyncio
async def test_payment_connector():
    """Test payment connector functionality."""
    config = {"name": "Test Payment", "type": "payment"}
    connector = PaymentConnector(config)

    assert connector.can_handle("pay $10")
    assert connector.can_handle("send payment")
    assert not connector.can_handle("send message")

    # Test parameter extraction and execution
    result = await connector.execute("pay $25.50", {"amount": 25.50})
    assert result["action"] == "payment_processed"
    assert result["amount"] == 25.50


@pytest.mark.asyncio
async def test_communication_connector():
    """Test communication connector functionality."""
    config = {"name": "Test Communication", "type": "communication"}
    connector = CommunicationConnector(config)

    assert connector.can_handle("send message")
    assert connector.can_handle("text someone")
    assert not connector.can_handle("pay bill")

    # Test message sending
    result = await connector.execute("send message", {
        "to": "test@example.com",
        "message": "Hello"
    })
    assert result["action"] == "message_sent"


@pytest.mark.asyncio
async def test_agent_core_initialization():
    """Test agent core initialization."""
    agent = AgentCore()

    # Mock the API client to avoid network calls
    with patch('src.agent.agent_core.api_client') as mock_api:
        mock_api.get_user_agent_services = AsyncMock(return_value=[
            {"id": 1, "name": "Mock Payment", "type": "payment"}
        ])

        await agent.initialize()

        assert agent.is_initialized
        assert len(agent.connectors) > 0
        assert any(isinstance(c, PaymentConnector) for c in agent.connectors)


@pytest.mark.asyncio
async def test_user_agent_isolation():
    """Test user agent isolation."""
    user_data = {"id": 1, "username": "testuser"}

    # Mock API client
    with patch('src.agent.agent_core.api_client') as mock_api:
        mock_api.get_user_agent_services = AsyncMock(return_value=[
            {"id": 1, "name": "User Payment", "type": "payment"}
        ])

        user_agent = UserAgent(1, user_data)
        await user_agent.initialize()

        assert user_agent.user_id == 1
        assert user_agent.is_initialized
        assert len(user_agent.connectors) > 0


@pytest.mark.asyncio
async def test_agent_manager():
    """Test agent manager for multiple users."""
    manager = AgentManager()
    user_data = {"id": 1, "username": "testuser"}

    # Mock API client
    with patch('src.agent.agent_core.api_client') as mock_api:
        mock_api.get_user_agent_services = AsyncMock(return_value=[
            {"id": 1, "name": "User Payment", "type": "payment"}
        ])

        # Get agent for user
        agent = await manager.get_user_agent(1, user_data)
        assert agent.user_id == 1

        # Process command for user
        result = await manager.process_command_for_user(1, user_data, "pay $10")
        assert "response" in result
        assert result["user_id"] == 1


@pytest.mark.asyncio
async def test_parameter_extraction():
    """Test enhanced parameter extraction."""
    agent = AgentCore()

    # Test email extraction
    params = agent._extract_parameters("send message to user@example.com", {})
    assert params.get("to") == "user@example.com"

    # Test amount extraction
    params = agent._extract_parameters("pay $25.50", {})
    assert params.get("amount") == 25.50

    # Test phone extraction
    params = agent._extract_parameters("call +1-555-0123", {})
    assert params.get("to") == "+1-555-0123"


@pytest.mark.asyncio
async def test_chat_integration():
    """Test chat message sending."""
    agent = AgentCore()

    # Mock API client
    with patch('src.agent.agent_core.api_client') as mock_api:
        mock_api.send_message = AsyncMock(return_value={
            "status": "success",
            "data": {"id": 123}
        })

        result = await agent.send_chat_message("testuser", "Hello from agent")
        assert result["action"] == "message_sent"
        assert result["receiver_username"] == "testuser"


@pytest.mark.asyncio
async def test_ai_enhancement():
    """Test AI enhancement capabilities."""
    # Use UserAgent instead of AgentCore for process_command
    agent = UserAgent(user_id=1, user_data={})

    # Test without AI (should work normally)
    result = await agent.process_command("pay $10")
    assert "response" in result

    # Test AI analysis (mocked)
    with patch.object(agent, '_analyze_command_with_ai', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "intent": "payment",
            "service_type": "payment",
            "confidence": 0.9
        }

        # This would test AI path if OpenAI was available
        # result = await agent.process_command_with_ai("pay $10")
        # assert result.get("ai_enhanced") is True


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling capabilities."""
    # Use UserAgent instead of AgentCore for process_command
    agent = UserAgent(user_id=1, user_data={})

    # Test unknown command
    result = await agent.process_command("unknown command")
    assert "response" in result
    assert "no_service_found" in result.get("action", "")


@pytest.mark.asyncio
async def test_conversation_history():
    """Test conversation history management."""
    user_agent = UserAgent(1, {"id": 1, "username": "test"})

    # Add some history
    user_agent._add_to_history("test command", "test response", {"action": "test"})

    assert len(user_agent.conversation_history) == 1
    assert user_agent.conversation_history[0]["command"] == "test command"

    # Test history limit
    for i in range(55):  # More than 50
        user_agent._add_to_history(f"cmd{i}", f"resp{i}", {"action": "test"})

    assert len(user_agent.conversation_history) == 50  # Should be capped at 50
