import os
import pytest
from unittest.mock import Mock, patch
from coralogix_mcp.client import CoralogixClient

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing"""
    monkeypatch.setenv("CORALOGIX_API_KEY", "test_coralogix_key")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("MODEL", "gpt-3.5-turbo")
    monkeypatch.setenv("APPLICATION_NAME", "test-app")

@pytest.fixture
def mock_coralogix_client(mock_env_vars):
    """Create a CoralogixClient instance with mocked dependencies"""
    with patch('coralogix_mcp.client.requests') as mock_requests:
        client = CoralogixClient(
            model="gpt-3.5-turbo",
            openai_api_key="test_openai_key",
            coralogix_api_key="test_coralogix_key",
            application_name="test-app"
        )
        client.llm = Mock()
        client._requests = mock_requests  # Assign the mocked requests module
        yield client

@pytest.fixture
def sample_log_results():
    """Sample log results for testing"""
    return [
        {
            "metadata": [],
            "labels": [],
            "userData": "{\"subsystemname\":\"test-service-1\"}"
        },
        {
            "metadata": [],
            "labels": [],
            "userData": "{\"subsystemname\":\"test-service-2\"}"
        }
    ]

@pytest.fixture
def sample_http_logs():
    """Sample HTTP log data for testing"""
    return [
        {
            "new_path": "/api/v1/users",
            "http_method": "GET",
            "status_code": "200",
            "log_count": 100
        },
        {
            "new_path": "/api/v1/orders",
            "http_method": "POST",
            "status_code": "400",
            "log_count": 50
        }
    ]

@pytest.fixture
def sample_error_logs():
    """Sample error log data for testing"""
    return [
        {
            "timestamp": "2024-03-20T10:00:00Z",
            "service": "test-service-1",
            "severity": "ERROR",
            "log_message": "Error processing request: Invalid input"
        },
        {
            "timestamp": "2024-03-20T10:01:00Z",
            "service": "test-service-2",
            "severity": "CRITICAL",
            "log_message": "Critical error: Database connection failed"
        }
    ] 