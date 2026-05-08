"""Tests for agent nodes and routing."""

import pytest
from unittest.mock import patch, MagicMock
from agent.state import AgentState
from agent.nodes import node_fetch_incident, node_diagnose
from agent.edges import route_after_diagnosis


@pytest.fixture
def base_state(sample_incident):
    return {
        "incident_id": "INC0010001",
        "run_id": "run-1",
        "started_at": "2024-01-15T10:00:00Z",
        "fix_attempts": 0,
        "actions_taken": [],
        "action_results": [],
        "issue_resolved": False,
        "confidence_score": 0,
        "can_auto_fix": False,
    }


def test_node_fetch_incident_populates_state(base_state, sample_incident):
    with patch("agent.nodes.get_incident", return_value=sample_incident):
        with patch("agent.nodes.update_work_notes", return_value=True):
            with patch("agent.nodes.get_settings") as gs:
                gs.return_value = MagicMock(APP_NAME_MAP={"d2": "d2-app"}, K8S_NAMESPACE_PROD="production")
                out = node_fetch_incident(base_state)
                assert out.get("incident_data") == sample_incident
                assert out.get("app_name") in ("d2", "d2-app") or out.get("app_name")


def test_node_diagnose_sets_confidence(base_state, sample_incident):
    base_state["incident_data"] = sample_incident
    base_state["rag_context"] = "runbook"
    base_state["logs"] = "OOMKilled"
    base_state["metrics"] = {}
    base_state["k8s_events"] = ""
    base_state["firing_alerts"] = []
    with patch("agent.nodes.get_json_llm") as mock_llm:
        with patch("agent.nodes.invoke_with_retry") as inv:
            inv.return_value = '{"root_cause":"OOM","confidence_score":85,"can_auto_fix":true,"suggested_actions":["restart"],"escalation_reason":null}'
            out = node_diagnose(base_state)
            assert out.get("confidence_score") == 85
            assert out.get("can_auto_fix") is True


def test_node_diagnose_sets_can_auto_fix_false_for_p1(base_state, sample_incident):
    sample_incident["priority"] = "1"
    base_state["incident_data"] = sample_incident
    base_state["rag_context"] = ""
    base_state["logs"] = ""
    base_state["metrics"] = {}
    base_state["k8s_events"] = ""
    base_state["firing_alerts"] = []
    with patch("agent.nodes.get_json_llm"):
        with patch("agent.nodes.invoke_with_retry") as inv:
            inv.return_value = '{"root_cause":"P1","confidence_score":90,"can_auto_fix":true,"suggested_actions":[],"escalation_reason":null}'
            out = node_diagnose(base_state)
            assert out.get("can_auto_fix") is False


def test_route_after_diagnosis_escalates_low_confidence(base_state):
    base_state["confidence_score"] = 50
    base_state["can_auto_fix"] = True
    base_state["incident_data"] = {"priority": "2"}
    with patch("config.settings.get_settings") as gs:
        gs.return_value = MagicMock(AUTO_FIX_CONFIDENCE_THRESHOLD=80)
        assert route_after_diagnosis(base_state) == "escalate"


def test_route_after_diagnosis_escalates_p1(base_state):
    base_state["confidence_score"] = 90
    base_state["can_auto_fix"] = True
    base_state["incident_data"] = {"priority": "1"}
    assert route_after_diagnosis(base_state) == "escalate"


def test_route_after_diagnosis_executes_high_confidence(base_state):
    base_state["confidence_score"] = 85
    base_state["can_auto_fix"] = True
    base_state["incident_data"] = {"priority": "2"}
    base_state["error_trace"] = None
    with patch("config.settings.get_settings") as gs:
        gs.return_value = MagicMock(AUTO_FIX_CONFIDENCE_THRESHOLD=80)
        assert route_after_diagnosis(base_state) == "execute_fix"
