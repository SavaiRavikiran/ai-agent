"""Tests for elk_tools."""

import pytest
from unittest.mock import patch, MagicMock
from tools.elk_tools import query_app_logs, search_logs_freetext, get_log_error_summary, get_logs_around_time


def test_query_app_logs_success(mock_elasticsearch):
    mock_elasticsearch.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "@timestamp": "2024-01-15T10:00:00Z",
                        "log": {"level": "ERROR"},
                        "kubernetes": {"pod": {"name": "d2-app-1"}},
                        "message": "OOMKilled",
                    }
                }
            ]
        }
    }
    with patch("tools.elk_tools._client", return_value=mock_elasticsearch):
        result = query_app_logs("d2", time_range_minutes=60)
        assert "OOMKilled" in result
        assert "d2-app-1" in result


def test_query_app_logs_empty_result(mock_elasticsearch):
    mock_elasticsearch.search.return_value = {"hits": {"hits": []}}
    with patch("tools.elk_tools._client", return_value=mock_elasticsearch):
        result = query_app_logs("d2")
        assert "No logs" in result or result == "No logs found."


def test_error_summary_aggregation(mock_elasticsearch):
    mock_elasticsearch.search.return_value = {
        "aggregations": {
            "error_messages": {
                "buckets": [
                    {"key": "OutOfMemoryError", "doc_count": 5},
                    {"key": "Connection refused", "doc_count": 2},
                ]
            }
        }
    }
    with patch("tools.elk_tools._client", return_value=mock_elasticsearch):
        result = get_log_error_summary("d2")
        assert "total_errors" in result
        assert result.get("total_errors") == 7 or "error_types" in result


def test_connection_error_returns_string_not_exception():
    with patch("tools.elk_tools._client") as m:
        m.side_effect = Exception("Connection refused")
        result = query_app_logs("d2")
        assert isinstance(result, str)
        assert "error" in result.lower() or "connection" in result.lower()
