"""Tests for Ollama client (unit tests, no live Ollama required)."""

import pytest
from unittest.mock import patch, MagicMock
import json

from drift_cli.core.ollama import OllamaClient
from drift_cli.models import RiskLevel


class TestOllamaClientInit:
    """Test client initialization."""

    def test_default_config(self):
        client = OllamaClient()
        assert client.base_url == "http://localhost:11434"
        assert client.model == "qwen2.5-coder:1.5b"

    def test_custom_config(self):
        client = OllamaClient(base_url="http://myhost:1234", model="llama3:8b")
        assert client.base_url == "http://myhost:1234"
        assert client.model == "llama3:8b"


class TestInputSanitization:
    """Test input sanitization / prompt injection prevention."""

    def test_removes_null_bytes(self):
        client = OllamaClient()
        result = client._sanitize_input("hello\x00world")
        assert "\x00" not in result

    def test_truncates_long_input(self):
        client = OllamaClient()
        long_input = "a" * 2000
        result = client._sanitize_input(long_input)
        assert len(result) <= 1000

    def test_strips_whitespace(self):
        client = OllamaClient()
        result = client._sanitize_input("  hello  ")
        assert result == "hello"

    def test_replaces_excessive_newlines(self):
        client = OllamaClient()
        result = client._sanitize_input("hello\n\n\nworld")
        assert "\n\n\n" not in result

    def test_normal_input_passes_through(self):
        client = OllamaClient()
        result = client._sanitize_input("list all python files")
        assert result == "list all python files"


class TestPromptBuilding:
    """Test prompt construction."""

    def test_system_prompt_contains_json_schema(self):
        client = OllamaClient()
        prompt = client._build_system_prompt()
        assert "JSON" in prompt
        assert "summary" in prompt
        assert "commands" in prompt
        assert "risk" in prompt

    def test_system_prompt_includes_safety_rules(self):
        client = OllamaClient()
        prompt = client._build_system_prompt()
        assert "rm -rf /" in prompt
        assert "destructive" in prompt.lower()

    def test_user_prompt_includes_query(self):
        client = OllamaClient()
        prompt = client._build_user_prompt("find large files")
        assert "find large files" in prompt

    def test_user_prompt_includes_context(self):
        client = OllamaClient()
        prompt = client._build_user_prompt("list files", context="cwd: /home/user")
        assert "cwd: /home/user" in prompt

    def test_user_prompt_no_context(self):
        client = OllamaClient()
        prompt = client._build_user_prompt("list files", context=None)
        assert "Context" not in prompt


class TestOllamaAvailability:
    """Test availability checking (mocked)."""

    def test_is_available_when_running(self):
        client = OllamaClient()
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(client.client, "get", return_value=mock_response):
            assert client.is_available() is True

    def test_is_not_available_when_down(self):
        client = OllamaClient()
        with patch.object(client.client, "get", side_effect=Exception("Connection refused")):
            assert client.is_available() is False

    def test_is_not_available_bad_status(self):
        client = OllamaClient()
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(client.client, "get", return_value=mock_response):
            assert client.is_available() is False


class TestGetPlan:
    """Test plan generation (mocked LLM responses)."""

    def _mock_ollama_response(self, plan_dict):
        """Create a mock httpx response with a plan JSON."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": json.dumps(plan_dict)
        }
        mock_response.raise_for_status = MagicMock()
        return mock_response

    def test_valid_plan_response(self):
        client = OllamaClient()
        plan_data = {
            "summary": "List files",
            "risk": "low",
            "commands": [{"command": "ls -la", "description": "List all files"}],
            "explanation": "Lists directory contents",
        }

        with patch.object(client.client, "post", return_value=self._mock_ollama_response(plan_data)):
            plan = client.get_plan("list files", use_memory=False)
            assert plan.summary == "List files"
            assert plan.risk == RiskLevel.LOW
            assert len(plan.commands) == 1

    def test_invalid_json_raises(self):
        client = OllamaClient()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "NOT JSON AT ALL"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, "post", return_value=mock_response):
            with pytest.raises(ValueError, match="Invalid JSON"):
                client.get_plan("test", use_memory=False)

    def test_timeout_raises(self):
        import httpx
        client = OllamaClient()

        with patch.object(client.client, "post", side_effect=httpx.TimeoutException("timeout")):
            with pytest.raises(ValueError, match="timed out"):
                client.get_plan("test", use_memory=False)

    def test_http_error_raises(self):
        import httpx
        client = OllamaClient()

        with patch.object(client.client, "post", side_effect=httpx.HTTPError("500 error")):
            with pytest.raises(ValueError, match="Failed to communicate"):
                client.get_plan("test", use_memory=False)
