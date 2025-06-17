import json
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta

@pytest.mark.asyncio
async def test_fetch_service_names(mock_coralogix_client, sample_log_results):
    """Test fetching service names from Coralogix"""
    # Mock the response
    mock_response = Mock()
    mock_response.ok = True
    mock_response.text = "\n".join([
        '{"status": "ok"}',
        json.dumps({"result": {"results": sample_log_results}})
    ])
    mock_coralogix_client._requests.post.return_value = mock_response

    # Test fetching service names
    service_names = await mock_coralogix_client.fetch_service_names()
    
    assert len(service_names) == 2
    assert "test-service-1" in service_names
    assert "test-service-2" in service_names
    
    # Verify cache is updated
    assert mock_coralogix_client._service_name_cache["data"] == service_names
    assert mock_coralogix_client._service_name_cache["timestamp"] is not None

@pytest.mark.asyncio
async def test_fetch_service_names_empty_response(mock_coralogix_client):
    """Test fetching service names with empty response"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.text = "\n".join([
        '{"status": "ok"}',
        json.dumps({"result": {"results": []}})
    ])
    mock_coralogix_client._requests.post.return_value = mock_response

    service_names = await mock_coralogix_client.fetch_service_names()
    assert service_names == []

@pytest.mark.asyncio
async def test_find_matching_coralogix_service_name_exact_match(mock_coralogix_client):
    """Test finding exact service name match"""
    mock_coralogix_client.fetch_service_names = AsyncMock(return_value=["test-service-1", "test-service-2"])
    
    result = await mock_coralogix_client.find_matching_coralogix_service_name("test-service-1")
    assert result == "test-service-1"
    assert "test-service-1" in mock_coralogix_client._service_name_matching_cache

@pytest.mark.asyncio
async def test_find_matching_coralogix_service_name_llm_match(mock_coralogix_client):
    """Test finding service name match using LLM"""
    mock_coralogix_client.fetch_service_names = AsyncMock(return_value=["test-service-1", "test-service-2"])
    mock_coralogix_client.call_llm = AsyncMock(return_value='{"service_name": "test-service-1"}')
    
    result = await mock_coralogix_client.find_matching_coralogix_service_name("test")
    assert result == "test-service-1"
    assert "test" in mock_coralogix_client._service_name_matching_cache

@pytest.mark.asyncio
async def test_find_matching_coralogix_service_name_basic_match(mock_coralogix_client):
    """Test finding service name match using basic matching"""
    mock_coralogix_client.fetch_service_names = AsyncMock(return_value=["test-service-1", "test-service-2"])
    mock_coralogix_client.call_llm = AsyncMock(return_value=None)
    
    result = await mock_coralogix_client.find_matching_coralogix_service_name("test")
    assert result == "test-service-1"  # Should match the first partial match
    assert "test" in mock_coralogix_client._service_name_matching_cache

@pytest.mark.asyncio
async def test_http_generate_query(mock_coralogix_client):
    """Test generating HTTP query"""
    mock_coralogix_client.find_matching_coralogix_service_name = AsyncMock(return_value="test-service")
    
    query = await mock_coralogix_client.http_generate_query("test-service", "4xx")
    assert "filter $l.subsystemname == 'test-service'" in query
    assert "filter ($d.status_code >= '400' && $d.status_code <= '499')" in query

@pytest.mark.asyncio
async def test_search_coralogix_logs(mock_coralogix_client, sample_http_logs):
    """Test searching Coralogix logs"""
    mock_response = Mock()
    mock_response.ok = True
    mock_response.text = "\n".join([
        '{"status": "ok"}',
        json.dumps({
            "result": {
                "results": [
                    {
                        "logRecord": {
                            "body": {
                                "log": json.dumps(sample_http_logs[0])
                            }
                        }
                    },
                    {
                        "logRecord": {
                            "body": {
                                "log": json.dumps(sample_http_logs[1])
                            }
                        }
                    }
                ]
            }
        })
    ])
    mock_coralogix_client._requests.post.return_value = mock_response
    
    results = await mock_coralogix_client.search_coralogix_logs("test query")
    assert len(results) == 2
    assert results[0]["new_path"] == "/api/v1/users"
    assert results[1]["new_path"] == "/api/v1/orders"

@pytest.mark.asyncio
async def test_analyze_logs(mock_coralogix_client, sample_http_logs):
    """Test analyzing logs"""
    analysis = await mock_coralogix_client.analyze_logs(sample_http_logs)
    
    assert analysis["total_requests"] == 150  # 100 + 50
    assert len(analysis["top_apis"]) == 2
    assert analysis["top_apis"][0]["new_path"] == "/api/v1/users"
    assert analysis["top_apis"][0]["log_count"] == 100

@pytest.mark.asyncio
async def test_get_log_context(mock_coralogix_client):
    """Test getting log context"""
    sample_logs = [
        {
            "timestamp": "2024-03-20T10:00:00Z",
            "service": "test-service",
            "logRecord": {
                "body": {
                    "log": "Line 1\nLine 2\nError in line 3\nLine 4\nLine 5"
                }
            }
        }
    ]
    
    context_results = await mock_coralogix_client.get_log_context(sample_logs, "Error", context_lines=1)
    assert len(context_results) == 1
    assert "Error in line 3" in context_results[0]["context"]
    assert "Line 2" in context_results[0]["context"]
    assert "Line 4" in context_results[0]["context"]

@pytest.mark.asyncio
async def test_search_recent_error_logs(mock_coralogix_client, sample_error_logs):
    """Test searching recent error logs"""
    # Mock the service name matching
    mock_coralogix_client.find_matching_coralogix_service_name = AsyncMock(return_value="test-service-1")
    
    # The log text must contain error-related terms for the production filter to pass
    error_log_1 = {
        "timestamp": "2024-03-20T10:00:00Z",
        "subsystemname": "test-service-1",
        "severity": "ERROR",
        "log_message": "Error processing request: Invalid input",
        "logRecord": {
            "body": {
                "log": "Error processing request: Invalid input"
            }
        }
    }
    error_log_2 = {
        "timestamp": "2024-03-20T10:01:00Z",
        "subsystemname": "test-service-2",
        "severity": "CRITICAL",
        "log_message": "Critical error: Database connection failed",
        "logRecord": {
            "body": {
                "log": "Critical error: Database connection failed"
            }
        }
    }
    mock_response = Mock()
    mock_response.ok = True
    mock_response.text = "\n".join([
        '{"status": "ok"}',
        json.dumps({
            "result": {
                "results": [
                    {
                        "logRecord": {
                            "body": {
                                "log": json.dumps(error_log_1)
                            }
                        }
                    },
                    {
                        "logRecord": {
                            "body": {
                                "log": json.dumps(error_log_2)
                            }
                        }
                    }
                ]
            }
        })
    ])
    mock_coralogix_client._requests.post.return_value = mock_response
    # Mock the query generation
    mock_coralogix_client.search_generate_query = AsyncMock(return_value="test query")
    results = await mock_coralogix_client.search_recent_error_logs("test-service-1")
    assert len(results) == 2
    assert results[0]["service"] == "test-service-1"
    assert results[1]["service"] == "test-service-2"

def test_find_best_match_basic(mock_coralogix_client):
    """Test basic matching function"""
    candidates = ["test-service-1", "test-service-2", "api-service"]
    
    # Exact match
    result = mock_coralogix_client.find_best_match_basic("test-service-1", candidates)
    assert result == "test-service-1"
    
    # Partial match
    result = mock_coralogix_client.find_best_match_basic("test", candidates)
    assert result == "test-service-1"
    
    # No match
    result = mock_coralogix_client.find_best_match_basic("unknown", candidates)
    assert result is None

@pytest.mark.asyncio
async def test_fetch_service_names_404(mock_coralogix_client):
    """Test fetch_service_names when the API returns a 404 error."""
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 404
    mock_response.text = "Not found"
    mock_coralogix_client._requests.post.return_value = mock_response
    service_names = await mock_coralogix_client.fetch_service_names()
    assert service_names == []

@pytest.mark.asyncio
async def test_call_llm(mock_coralogix_client):
    """Test call_llm (mocked) returns the expected JSON response."""
    # Mock the acompletion call
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"service_name":"test-service-1"}'))]
    
    with patch('coralogix_mcp.client.acompletion', return_value=mock_response):
        prompt = "Find the best matching service name for 'test' from [test-service-1, test-service-2]"
        result = await mock_coralogix_client.call_llm(prompt)
        assert result == '{"service_name":"test-service-1"}' 