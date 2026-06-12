"""Tests for judge verdict extraction with mocked Anthropic client."""

from unittest import mock

import pytest

from bootcamp_cli.judge import judge, Verdict, JudgeError


class TestJudgeVerdictExtraction:
    """Test verdict extraction from tool_use blocks."""

    def test_judge_extracts_verdict_from_tool_use(self, monkeypatch):
        """Test that judge extracts verdict from render_verdict tool."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("anthropic.Anthropic") as mock_client:
            mock_tool_use = mock.Mock()
            mock_tool_use.type = "tool_use"
            mock_tool_use.name = "render_verdict"
            mock_tool_use.input = {
                "criterion": "C1-test",
                "pass": True,
                "reasoning": "Test reasoning",
            }

            mock_response = mock.Mock()
            mock_response.content = [mock_tool_use]

            mock_client_instance = mock.Mock()
            mock_client_instance.messages.create.return_value = mock_response
            mock_client.return_value = mock_client_instance

            verdict = judge("C1-test", "Test rubric", "Test artifact")

            assert isinstance(verdict, Verdict)
            assert verdict.criterion == "C1-test"
            assert verdict.passed is True
            assert verdict.reasoning == "Test reasoning"

    def test_judge_returns_false_verdict(self, monkeypatch):
        """Test that judge can return false verdicts."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("anthropic.Anthropic") as mock_client:
            mock_tool_use = mock.Mock()
            mock_tool_use.type = "tool_use"
            mock_tool_use.name = "render_verdict"
            mock_tool_use.input = {
                "criterion": "C2-fail",
                "pass": False,
                "reasoning": "Did not meet criterion",
            }

            mock_response = mock.Mock()
            mock_response.content = [mock_tool_use]

            mock_client_instance = mock.Mock()
            mock_client_instance.messages.create.return_value = mock_response
            mock_client.return_value = mock_client_instance

            verdict = judge("C2-fail", "Test rubric", "Test artifact")

            assert verdict.passed is False

    def test_judge_uses_correct_model(self, monkeypatch):
        """Test that judge uses JUDGE_MODEL env var."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("JUDGE_MODEL", "claude-opus-4")

        with mock.patch("anthropic.Anthropic") as mock_client:
            mock_tool_use = mock.Mock()
            mock_tool_use.type = "tool_use"
            mock_tool_use.name = "render_verdict"
            mock_tool_use.input = {"criterion": "C1", "pass": True, "reasoning": "ok"}

            mock_response = mock.Mock()
            mock_response.content = [mock_tool_use]

            mock_client_instance = mock.Mock()
            mock_client_instance.messages.create.return_value = mock_response
            mock_client.return_value = mock_client_instance

            judge("C1", "rubric", "artifact")

            call_args = mock_client_instance.messages.create.call_args
            assert call_args[1]["model"] == "claude-opus-4"

    def test_judge_uses_default_model_if_not_set(self, monkeypatch):
        """Test that judge defaults to claude-haiku-4-5."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.delenv("JUDGE_MODEL", raising=False)

        with mock.patch("anthropic.Anthropic") as mock_client:
            mock_tool_use = mock.Mock()
            mock_tool_use.type = "tool_use"
            mock_tool_use.name = "render_verdict"
            mock_tool_use.input = {"criterion": "C1", "pass": True, "reasoning": "ok"}

            mock_response = mock.Mock()
            mock_response.content = [mock_tool_use]

            mock_client_instance = mock.Mock()
            mock_client_instance.messages.create.return_value = mock_response
            mock_client.return_value = mock_client_instance

            judge("C1", "rubric", "artifact")

            call_args = mock_client_instance.messages.create.call_args
            assert call_args[1]["model"] == "claude-haiku-4-5"

    def test_judge_sets_temperature_zero(self, monkeypatch):
        """Test that judge uses temperature=0."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("anthropic.Anthropic") as mock_client:
            mock_tool_use = mock.Mock()
            mock_tool_use.type = "tool_use"
            mock_tool_use.name = "render_verdict"
            mock_tool_use.input = {"criterion": "C1", "pass": True, "reasoning": "ok"}

            mock_response = mock.Mock()
            mock_response.content = [mock_tool_use]

            mock_client_instance = mock.Mock()
            mock_client_instance.messages.create.return_value = mock_response
            mock_client.return_value = mock_client_instance

            judge("C1", "rubric", "artifact")

            call_args = mock_client_instance.messages.create.call_args
            assert call_args[1]["temperature"] == 0

    def test_judge_sets_tool_choice_forced(self, monkeypatch):
        """Test that judge forces tool_choice to render_verdict."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("anthropic.Anthropic") as mock_client:
            mock_tool_use = mock.Mock()
            mock_tool_use.type = "tool_use"
            mock_tool_use.name = "render_verdict"
            mock_tool_use.input = {"criterion": "C1", "pass": True, "reasoning": "ok"}

            mock_response = mock.Mock()
            mock_response.content = [mock_tool_use]

            mock_client_instance = mock.Mock()
            mock_client_instance.messages.create.return_value = mock_response
            mock_client.return_value = mock_client_instance

            judge("C1", "rubric", "artifact")

            call_args = mock_client_instance.messages.create.call_args
            tool_choice = call_args[1]["tool_choice"]
            assert tool_choice["type"] == "tool"
            assert tool_choice["name"] == "render_verdict"

    def test_judge_tool_has_correct_schema(self, monkeypatch):
        """Test that render_verdict tool has correct input_schema."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("anthropic.Anthropic") as mock_client:
            mock_tool_use = mock.Mock()
            mock_tool_use.type = "tool_use"
            mock_tool_use.name = "render_verdict"
            mock_tool_use.input = {"criterion": "C1", "pass": True, "reasoning": "ok"}

            mock_response = mock.Mock()
            mock_response.content = [mock_tool_use]

            mock_client_instance = mock.Mock()
            mock_client_instance.messages.create.return_value = mock_response
            mock_client.return_value = mock_client_instance

            judge("C1", "rubric", "artifact")

            call_args = mock_client_instance.messages.create.call_args
            tools = call_args[1]["tools"]

            render_verdict_tool = next(
                (t for t in tools if t["name"] == "render_verdict"), None
            )
            assert render_verdict_tool is not None

            schema = render_verdict_tool["input_schema"]
            props = schema["properties"]
            assert "criterion" in props
            assert "pass" in props
            assert "reasoning" in props
            assert schema["required"] == ["criterion", "pass", "reasoning"]
