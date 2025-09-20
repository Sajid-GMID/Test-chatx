"""
Unit tests for app.py.

Tests the main application module including web server setup,
message handling, bot framework integration, and error handling.
"""
import json
import pytest
from unittest.mock import Mock, AsyncMock, patch
from aiohttp import web
from botbuilder.core.invoke_response import InvokeResponse

from chatx.app import messages


class TestMessagesEndpoint:
    """Test the messages endpoint functionality."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock aiohttp Request."""
        request = Mock(spec=web.Request)
        request.headers = {"Content-Type": "application/json", "Authorization": "Bearer test-token"}
        request.json = AsyncMock()
        return request

    @pytest.fixture
    def mock_activity_data(self):
        """Create mock activity data."""
        return {
            "type": "message",
            "id": "test-activity-id",
            "from": {"id": "user-id", "name": "Test User"},
            "recipient": {"id": "bot-id", "name": "Test Bot"},
            "text": "Hello, bot!",
            "channelId": "test-channel"
        }

    @pytest.mark.asyncio
    async def test_messages_valid_json_request(self, mock_request, mock_activity_data):
        """Test messages endpoint with valid JSON request."""
        mock_request.json.return_value = mock_activity_data
        
        with patch('chatx.app.ADAPTER.process_activity') as mock_process:
            mock_process.return_value = None  # No response body
            
            response = await messages(mock_request)
            
            assert response.status == 201
            mock_request.json.assert_called_once()
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_messages_with_response_body(self, mock_request, mock_activity_data):
        """Test messages endpoint when adapter returns a response with body."""
        mock_request.json.return_value = mock_activity_data
        
        mock_invoke_response = Mock(spec=InvokeResponse)
        mock_invoke_response.status = 200
        mock_invoke_response.body = {"message": "Hello from bot"}
        
        with patch('chatx.app.ADAPTER.process_activity') as mock_process:
            mock_process.return_value = mock_invoke_response
            
            response = await messages(mock_request)
            
            assert response.status == 200
            # Verify response is a JSON response
            assert isinstance(response, web.Response)

    @pytest.mark.asyncio
    async def test_messages_with_response_no_body(self, mock_request, mock_activity_data):
        """Test messages endpoint when adapter returns a response without body."""
        mock_request.json.return_value = mock_activity_data
        
        mock_invoke_response = Mock(spec=InvokeResponse)
        mock_invoke_response.status = 202
        mock_invoke_response.body = None
        
        with patch('chatx.app.ADAPTER.process_activity') as mock_process:
            mock_process.return_value = mock_invoke_response
            
            response = await messages(mock_request)
            
            assert response.status == 202

    @pytest.mark.asyncio
    async def test_messages_adapter_exception_handling(self, mock_request, mock_activity_data):
        """Test exception handling in messages endpoint."""
        mock_request.json.return_value = mock_activity_data
        
        with patch('chatx.app.ADAPTER.process_activity') as mock_process:
            mock_process.side_effect = Exception("Adapter processing error")
            
            with patch('chatx.app.logger.error') as mock_logger:
                response = await messages(mock_request)
                
                assert response.status == 500
                mock_logger.assert_called_once()

