"""Tests for agent/llm.py parse_llm_json."""

import pytest
from agent.llm import parse_llm_json


def test_parse_llm_json_clean_json():
    s = '{"root_cause": "OOM", "confidence_score": 85}'
    assert parse_llm_json(s) == {"root_cause": "OOM", "confidence_score": 85}


def test_parse_llm_json_wrapped_in_backticks():
    s = '```json\n{"resolved": true}\n```'
    assert parse_llm_json(s) == {"resolved": True}


def test_parse_llm_json_with_extra_text():
    s = 'Here is the result: {"key": "value"} Thanks.'
    assert parse_llm_json(s) == {"key": "value"}


def test_parse_llm_json_invalid_returns_empty_dict():
    assert parse_llm_json("not json at all") == {}
    assert parse_llm_json("") == {}
    assert parse_llm_json("{invalid}") == {}
