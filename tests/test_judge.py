"""Tests for judge error handling with mocked Anthropic client."""

from unittest import mock

import pytest

from bootcamp_cli.judge import judge, JudgeError


class TestJudgeErrors:
    """Test error handling in judge."""

    def test_judge_raises_error_if_api_key_missing(self, monkeypatch) -> None:
        """Test that judge raises JudgeError if ANTHROPIC_API_KEY is unset."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(JudgeError) as exc_info:
            judge("C1", "rubric", "artifact")

        assert "ANTHROPIC_API_KEY" in str(exc_info.value)

    def test_judge_raises_error_if_no_tool_use_block(self, monkeypatch) -> None:
        """Test that judge raises JudgeError if no render_verdict tool_use."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("anthropic.Anthropic") as mock_client:
            mock_response = mock.Mock()
            mock_response.content = [mock.Mock(type="text", text="Just text")]

            mock_client_instance = mock.Mock()
            mock_client_instance.messages.create.return_value = mock_response
            mock_client.return_value = mock_client_instance

            with pytest.raises(JudgeError) as exc_info:
                judge("C1", "rubric", "artifact")

            assert "render_verdict" in str(exc_info.value).lower()

    def test_judge_raises_error_if_wrong_tool_name(self, monkeypatch) -> None:
        """Test that judge raises JudgeError if tool_use has wrong name."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("anthropic.Anthropic") as mock_client:
            mock_tool_use = mock.Mock()
            mock_tool_use.type = "tool_use"
            mock_tool_use.name = "wrong_tool"
            mock_tool_use.input = {"criterion": "C1", "pass": True}

            mock_response = mock.Mock()
            mock_response.content = [mock_tool_use]

            mock_client_instance = mock.Mock()
            mock_client_instance.messages.create.return_value = mock_response
            mock_client.return_value = mock_client_instance

            with pytest.raises(JudgeError):
                judge("C1", "rubric", "artifact")

    def test_judge_raises_error_on_api_exception(self, monkeypatch) -> None:
        """Test that judge raises JudgeError on API errors."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("anthropic.Anthropic") as mock_client:
            mock_client_instance = mock.Mock()
            mock_client_instance.messages.create.side_effect = Exception("API error")
            mock_client.return_value = mock_client_instance

            with pytest.raises(JudgeError):
                judge("C1", "rubric", "artifact")

    def test_judge_raises_error_on_client_construction_failure(
        self, monkeypatch
    ) -> None:
        """Test that judge raises JudgeError if client construction fails."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("anthropic.Anthropic") as mock_client:
            mock_client.side_effect = Exception("Client error")

            with pytest.raises(JudgeError) as exc_info:
                judge("C1", "rubric", "artifact")

            assert "client" in str(exc_info.value).lower()

    def test_judge_preserves_exception_message(self, monkeypatch) -> None:
        """Test that JudgeError includes original exception details."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("anthropic.Anthropic") as mock_client:
            mock_client_instance = mock.Mock()
            mock_client_instance.messages.create.side_effect = ValueError(
                "Specific error"
            )
            mock_client.return_value = mock_client_instance

            with pytest.raises(JudgeError) as exc_info:
                judge("C1", "rubric", "artifact")

            error_str = str(exc_info.value).lower()
            assert "error" in error_str or "specific" in error_str
