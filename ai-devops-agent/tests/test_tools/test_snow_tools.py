"""Tests for snow_tools."""

import pytest
from unittest.mock import patch, MagicMock
from tools.snow_tools import (
    get_incident,
    update_work_notes,
    resolve_incident,
    close_incident,
    get_open_incidents,
    SnowAPIError,
)


def test_get_incident_success(mock_snow_client, sample_incident):
    with patch("tools.snow_tools._get_sys_id", return_value="abc123"):
        with patch("tools.snow_tools._request") as req:
            req.return_value = {"result": sample_incident}
            result = get_incident("INC0010001")
            assert result["number"] == "INC0010001"
            assert result["priority"] == "2"


def test_get_incident_not_found():
    with patch("tools.snow_tools._get_sys_id") as m:
        m.side_effect = SnowAPIError("Incident not found: INC9999999")
        with pytest.raises(SnowAPIError):
            get_incident("INC9999999")


def test_get_incident_network_error():
    with patch("tools.snow_tools._request") as m:
        m.side_effect = SnowAPIError("Connection refused")
        with pytest.raises(SnowAPIError):
            get_incident("INC0010001")


def test_update_work_notes(mock_snow_client):
    with patch("tools.snow_tools._get_sys_id", return_value="abc"):
        with patch("tools.snow_tools._request") as m:
            m.return_value = {}
            assert update_work_notes("INC001", "test note") is True
            call = m.call_args
            assert "[AI Agent]" in call.kwargs.get("json", {}).get("work_notes", "")


def test_resolve_incident(mock_snow_client):
    with patch("tools.snow_tools._get_sys_id", return_value="abc"):
        with patch("tools.snow_tools._request") as m:
            m.return_value = {}
            assert resolve_incident("INC001", "Fixed.") is True


def test_close_incident(mock_snow_client):
    with patch("tools.snow_tools._get_sys_id", return_value="abc"):
        with patch("tools.snow_tools._request") as m:
            m.return_value = {}
            assert close_incident("INC001", "Closed.") is True


def test_get_open_incidents_filtered_by_priority(mock_snow_client):
    with patch("tools.snow_tools._request") as m:
        m.return_value = {"result": [{"number": "INC001"}]}
        result = get_open_incidents(priority_filter=["2", "3"])
        assert len(result) == 1


def test_get_open_incidents_empty(mock_snow_client):
    with patch("tools.snow_tools._request") as m:
        m.return_value = {"result": []}
        assert get_open_incidents() == []


def test_retry_logic_on_failure():
    with patch("tools.snow_tools._get_sys_id") as m:
        m.side_effect = SnowAPIError("failed after retries")
        with pytest.raises(SnowAPIError):
            get_incident("INC001")
