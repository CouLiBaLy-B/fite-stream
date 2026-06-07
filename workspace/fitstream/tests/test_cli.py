"""Tests for FitStream CLI argument parsing and command structure."""

import pytest
from click.testing import CliRunner
from fitstream.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestCLIHelp:
    """CLI help output tests."""

    def test_main_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "FitStream" in result.output

    def test_animate_help(self, runner):
        result = runner.invoke(main, ["animate", "--help"])
        assert result.exit_code == 0
        assert "--image" in result.output
        assert "--prompt" in result.output

    def test_story_help(self, runner):
        result = runner.invoke(main, ["story", "--help"])
        assert result.exit_code == 0
        assert "--story" in result.output

    def test_status_help(self, runner):
        result = runner.invoke(main, ["status", "--help"])
        assert result.exit_code == 0

    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "FitStream" in result.output


class TestCLIValidation:
    """CLI input validation."""

    def test_animate_missing_image(self, runner):
        result = runner.invoke(main, ["animate", "--prompt", "test"])
        assert result.exit_code != 0

    def test_animate_missing_prompt(self, runner, sample_image_path):
        result = runner.invoke(main, ["animate", "--image", sample_image_path])
        assert result.exit_code != 0

    def test_story_missing_image(self, runner):
        result = runner.invoke(main, ["story", "--story", "test story"])
        assert result.exit_code != 0


class TestCLICommandsExist:
    """All commands are registered."""

    def test_all_commands_registered(self, runner):
        result = runner.invoke(main, ["--help"])
        assert "animate" in result.output
        assert "story" in result.output
        assert "tryon" in result.output
        assert "compose" in result.output
        assert "status" in result.output


class TestCLIOptions:
    """Option parsing for key commands."""

    def test_animate_with_preset(self, runner, sample_image_path):
        result = runner.invoke(main, [
            "animate",
            "--image", sample_image_path,
            "--prompt", "Walking",
            "--preset", "draft",
            "--style", "ghibli",
        ])
        # Will fail at GPU generation, but should parse options fine
        assert result.exit_code in (0, 1)

    def test_animate_with_seed(self, runner, sample_image_path):
        result = runner.invoke(main, [
            "animate",
            "--image", sample_image_path,
            "--prompt", "Walking",
            "--seed", "42",
        ])
        assert result.exit_code in (0, 1)