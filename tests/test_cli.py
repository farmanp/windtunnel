"""Tests for CLI commands (FEAT-001)."""

from typer.testing import CliRunner

from windtunnel import __version__
from windtunnel.cli import app

runner = CliRunner()


class TestVersionDisplay:
    """Test version display functionality."""

    def test_version_flag_shows_version(self) -> None:
        """--version shows the current version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_version_short_flag(self) -> None:
        """-V shows the current version."""
        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert __version__ in result.stdout


class TestRunCommand:
    """Test the run command options."""

    def test_run_help_shows_options(self) -> None:
        """Run --help shows all required options."""
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--sut" in result.stdout
        assert "--scenarios" in result.stdout
        assert "--n" in result.stdout
        assert "--parallel" in result.stdout
        assert "--seed" in result.stdout

    def test_run_requires_sut_option(self) -> None:
        """Run command requires --sut option."""
        result = runner.invoke(app, ["run", "--scenarios", "."])
        assert result.exit_code != 0
        # Just verify it fails - error message format varies by typer version

    def test_run_requires_scenarios_option(self) -> None:
        """Run command requires --scenarios option."""
        result = runner.invoke(app, ["run", "--sut", "sut.yaml"])
        assert result.exit_code != 0


class TestReportCommand:
    """Test the report command options."""

    def test_report_help_shows_options(self) -> None:
        """Report --help shows --run-id option."""
        result = runner.invoke(app, ["report", "--help"])
        assert result.exit_code == 0
        assert "--run-id" in result.stdout

    def test_report_requires_run_id(self) -> None:
        """Report command requires --run-id option."""
        result = runner.invoke(app, ["report"])
        assert result.exit_code != 0


class TestReplayCommand:
    """Test the replay command options."""

    def test_replay_help_shows_options(self) -> None:
        """Replay --help shows --run-id and --instance-id options."""
        result = runner.invoke(app, ["replay", "--help"])
        assert result.exit_code == 0
        assert "--run-id" in result.stdout
        assert "--instance-id" in result.stdout

    def test_replay_requires_both_ids(self) -> None:
        """Replay command requires both --run-id and --instance-id."""
        result = runner.invoke(app, ["replay", "--run-id", "test"])
        assert result.exit_code != 0

        result = runner.invoke(app, ["replay", "--instance-id", "test"])
        assert result.exit_code != 0


class TestMainHelp:
    """Test main CLI help."""

    def test_no_args_shows_help(self) -> None:
        """Running without arguments shows help (exit code 2 for no_args_is_help)."""
        result = runner.invoke(app, [])
        # no_args_is_help=True causes exit code 2
        assert result.exit_code in (0, 2)
        assert "run" in result.stdout
        assert "report" in result.stdout
        assert "replay" in result.stdout

    def test_help_flag_shows_help(self) -> None:
        """--help shows all commands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "run" in result.stdout
        assert "report" in result.stdout
        assert "replay" in result.stdout
