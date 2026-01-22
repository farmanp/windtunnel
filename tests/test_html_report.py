"""Tests for HTML report generation."""

import json
from pathlib import Path

import pytest

from turbulence.report import HTMLReportGenerator
from turbulence.report.html import ActionStats, ReportData, ScenarioStats, calculate_percentile


class TestPercentiles:
    """Tests for percentile calculation."""

    def test_calculate_percentile_empty(self) -> None:
        assert calculate_percentile([], 50) == 0.0

    def test_calculate_percentile_exact(self) -> None:
        # [1, 2, 3, 4, 5], 50th percentile is 3
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert calculate_percentile(data, 50) == 3.0

    def test_calculate_percentile_interpolated(self) -> None:
        # [1, 2, 3, 4], 50th percentile is 2.5
        data = [1.0, 2.0, 3.0, 4.0]
        assert calculate_percentile(data, 50) == 2.5

    def test_calculate_percentile_edges(self) -> None:
        data = [1.0, 10.0]
        assert calculate_percentile(data, 0) == 1.0
        assert calculate_percentile(data, 100) == 10.0


class TestScenarioStats:
    """Tests for ScenarioStats dataclass."""

    def test_total_calculation(self) -> None:
        """Total should be sum of pass and fail counts."""
        stats = ScenarioStats(name="checkout", pass_count=95, fail_count=5)
        assert stats.total == 100

    def test_pass_rate_calculation(self) -> None:
        """Pass rate should be calculated correctly."""
        stats = ScenarioStats(name="checkout", pass_count=95, fail_count=5)
        assert stats.pass_rate == 95.0

    def test_pass_rate_zero_total(self) -> None:
        """Pass rate should be 0 when no instances."""
        stats = ScenarioStats(name="empty")
        assert stats.pass_rate == 0.0

    def test_pass_rate_all_passed(self) -> None:
        """Pass rate should be 100 when all passed."""
        stats = ScenarioStats(name="perfect", pass_count=100, fail_count=0)
        assert stats.pass_rate == 100.0

    def test_pass_rate_all_failed(self) -> None:
        """Pass rate should be 0 when all failed."""
        stats = ScenarioStats(name="broken", pass_count=0, fail_count=100)
        assert stats.pass_rate == 0.0


class TestReportData:
    """Tests for ReportData dataclass."""

    def test_pass_rate_calculation(self) -> None:
        """Overall pass rate should be calculated correctly."""
        data = ReportData(
            run_id="test_run",
            total_instances=1000,
            pass_count=950,
            fail_count=50,
        )
        assert data.pass_rate == 95.0

    def test_pass_rate_zero_instances(self) -> None:
        """Pass rate should be 0 when no instances."""
        data = ReportData(run_id="empty_run")
        assert data.pass_rate == 0.0

    def test_scenarios_sorted_by_failure(self) -> None:
        """Scenarios should be sorted by failure rate (worst first)."""
        data = ReportData(run_id="test_run")
        data.scenarios["checkout"] = ScenarioStats(
            name="checkout", pass_count=98, fail_count=2
        )
        data.scenarios["refund"] = ScenarioStats(
            name="refund", pass_count=85, fail_count=15
        )
        data.scenarios["login"] = ScenarioStats(
            name="login", pass_count=100, fail_count=0
        )

        sorted_scenarios = data.scenarios_sorted_by_failure
        assert sorted_scenarios[0].name == "refund"  # Worst: 85% pass rate
        assert sorted_scenarios[1].name == "checkout"  # Middle: 98% pass rate
        assert sorted_scenarios[2].name == "login"  # Best: 100% pass rate

    def test_top_failing_assertions(self) -> None:
        """Failing assertions should be sorted by count."""
        data = ReportData(run_id="test_run")
        data.failing_assertions["payment_captured"] = 30
        data.failing_assertions["order_confirmed"] = 10
        data.failing_assertions["email_sent"] = 5

        top_failures = data.top_failing_assertions
        assert top_failures[0] == ("payment_captured", 30)
        assert top_failures[1] == ("order_confirmed", 10)
        assert top_failures[2] == ("email_sent", 5)

    def test_services_by_failure_count(self) -> None:
        """Services should be sorted by failure count."""
        data = ReportData(run_id="test_run")
        data.failures_by_service["api"] = 20
        data.failures_by_service["payments"] = 15
        data.failures_by_service["notifications"] = 5

        services = data.services_by_failure_count
        assert services[0] == ("api", 20)
        assert services[1] == ("payments", 15)
        assert services[2] == ("notifications", 5)


class TestHTMLReportGenerator:
    """Tests for HTMLReportGenerator class."""

    @pytest.fixture
    def run_dir(self, tmp_path: Path) -> Path:
        """Create a temporary run directory with artifacts."""
        run_path = tmp_path / "run_20240115_001"
        run_path.mkdir()
        return run_path

    @pytest.fixture
    def populated_run_dir(self, run_dir: Path) -> Path:
        """Create a run directory with populated artifacts."""
        # Create manifest.json
        manifest = {
            "run_id": "run_20240115_001",
            "timestamp": "2024-01-15T10:30:00Z",
            "sut_name": "ecommerce",
            "scenario_ids": ["checkout", "refund"],
            "seed": 12345,
        }
        (run_dir / "manifest.json").write_text(json.dumps(manifest))

        # Create instances.jsonl
        instances = [
            {"instance_id": "inst_001", "scenario_id": "checkout", "passed": True},
            {"instance_id": "inst_002", "scenario_id": "checkout", "passed": True},
            {"instance_id": "inst_003", "scenario_id": "checkout", "passed": False},
            {"instance_id": "inst_004", "scenario_id": "refund", "passed": True},
            {"instance_id": "inst_005", "scenario_id": "refund", "passed": False},
        ]
        with (run_dir / "instances.jsonl").open("w") as f:
            for instance in instances:
                f.write(json.dumps(instance) + "\n")

        # Create steps.jsonl
        steps = [
            {
                "instance_id": "inst_001", 
                "step_name": "login", 
                "observation": {"ok": True, "latency_ms": 100, "service": "auth"}
            },
            {
                "instance_id": "inst_001", 
                "step_name": "get_cart", 
                "observation": {"ok": True, "latency_ms": 50, "service": "cart"}
            },
            {
                "instance_id": "inst_003", 
                "step_name": "login", 
                "observation": {"ok": False, "latency_ms": 5000, "errors": ["Timeout"], "service": "auth"}
            },
        ]
        with (run_dir / "steps.jsonl").open("w") as f:
            for step in steps:
                f.write(json.dumps(step) + "\n")

        # Create assertions.jsonl
        assertions = [
            {
                "assertion_name": "payment_captured",
                "passed": False,
                "instance_id": "inst_003",
            },
            {
                "assertion_name": "payment_captured",
                "passed": False,
                "instance_id": "inst_005",
            },
            {
                "assertion_name": "refund_processed",
                "passed": False,
                "instance_id": "inst_005",
            },
            {
                "assertion_name": "order_confirmed",
                "passed": True,
                "instance_id": "inst_001",
            },
        ]
        with (run_dir / "assertions.jsonl").open("w") as f:
            for assertion in assertions:
                f.write(json.dumps(assertion) + "\n")

        # Create summary.json
        summary = {
            "pass_count": 3,
            "fail_count": 2,
            "pass_rate": 60.0,
            "duration_ms": 5000.0,
        }
        (run_dir / "summary.json").write_text(json.dumps(summary))

        return run_dir

    def test_generate_creates_report_file(self, populated_run_dir: Path) -> None:
        """Report file should be created in run directory."""
        generator = HTMLReportGenerator(populated_run_dir)
        result_path = generator.generate()

        assert result_path.exists()
        assert result_path.name == "report.html"
        assert result_path.parent == populated_run_dir

    def test_generate_custom_output_path(
        self,
        populated_run_dir: Path,
        tmp_path: Path,
    ) -> None:
        """Report should be written to custom output path."""
        custom_path = tmp_path / "custom_report.html"
        generator = HTMLReportGenerator(populated_run_dir)
        result_path = generator.generate(custom_path)

        assert result_path == custom_path
        assert result_path.exists()

    def test_report_contains_run_id(self, populated_run_dir: Path) -> None:
        """Report should contain the run ID."""
        generator = HTMLReportGenerator(populated_run_dir)
        result_path = generator.generate()

        content = result_path.read_text()
        assert "run_20240115_001" in content

    def test_report_contains_overall_pass_rate(self, populated_run_dir: Path) -> None:
        """Report should display overall pass rate."""
        generator = HTMLReportGenerator(populated_run_dir)
        result_path = generator.generate()

        content = result_path.read_text()
        # 3 passed out of 5 = 60%
        assert "60.0%" in content

    def test_report_contains_pass_fail_counts(self, populated_run_dir: Path) -> None:
        """Report should display pass and fail counts."""
        generator = HTMLReportGenerator(populated_run_dir)
        result_path = generator.generate()

        content = result_path.read_text()
        assert "3" in content  # Pass count
        assert "2" in content  # Fail count

    def test_report_contains_scenario_breakdown(self, populated_run_dir: Path) -> None:
        """Report should show per-scenario breakdown."""
        generator = HTMLReportGenerator(populated_run_dir)
        result_path = generator.generate()

        content = result_path.read_text()
        assert "checkout" in content
        assert "refund" in content

    def test_report_contains_failing_assertions(self, populated_run_dir: Path) -> None:
        """Report should list failing assertions."""
        generator = HTMLReportGenerator(populated_run_dir)
        result_path = generator.generate()

        content = result_path.read_text()
        assert "payment_captured" in content
        assert "refund_processed" in content

    def test_report_contains_service_failures(self, populated_run_dir: Path) -> None:
        """Report should group failures by service."""
        generator = HTMLReportGenerator(populated_run_dir)
        result_path = generator.generate()

        content = result_path.read_text()
        # "auth" service failed in steps.jsonl
        assert "auth" in content
        # "cart" service passed
        assert "cart" in content

    def test_report_is_self_contained(self, populated_run_dir: Path) -> None:
        """Report HTML should not reference external resources."""
        generator = HTMLReportGenerator(populated_run_dir)
        result_path = generator.generate()

        content = result_path.read_text()
        # Check for inline styles
        assert "<style>" in content
        # Check no external CSS links
        assert 'rel="stylesheet"' not in content
        assert "http://" not in content
        assert "https://" not in content

    def test_report_is_valid_html(self, populated_run_dir: Path) -> None:
        """Report should be valid HTML."""
        generator = HTMLReportGenerator(populated_run_dir)
        result_path = generator.generate()

        content = result_path.read_text()
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "</html>" in content
        assert "<head>" in content
        assert "</head>" in content
        assert "<body>" in content
        assert "</body>" in content

    def test_generate_with_empty_run_dir(self, run_dir: Path) -> None:
        """Report should handle empty run directory gracefully."""
        generator = HTMLReportGenerator(run_dir)
        result_path = generator.generate()

        assert result_path.exists()
        content = result_path.read_text()
        assert "0.0%" in content  # Zero pass rate

    def test_generate_with_only_manifest(self, run_dir: Path) -> None:
        """Report should work with only manifest file."""
        manifest = {
            "run_id": "test_run",
            "timestamp": "2024-01-15T10:30:00Z",
            "sut_name": "test_sut",
        }
        (run_dir / "manifest.json").write_text(json.dumps(manifest))

        generator = HTMLReportGenerator(run_dir)
        result_path = generator.generate()

        assert result_path.exists()
        content = result_path.read_text()
        assert "test_run" in content
        assert "test_sut" in content

    def test_generate_uses_summary_when_instances_empty(self, run_dir: Path) -> None:
        """Report should use summary data when instances.jsonl is empty."""
        manifest = {"run_id": "summary_test", "sut_name": "test"}
        (run_dir / "manifest.json").write_text(json.dumps(manifest))

        summary = {"pass_count": 90, "fail_count": 10, "duration_ms": 3000.0}
        (run_dir / "summary.json").write_text(json.dumps(summary))

        generator = HTMLReportGenerator(run_dir)
        result_path = generator.generate()

        content = result_path.read_text()
        assert "90.0%" in content  # 90/(90+10) = 90%

    def test_scenarios_sorted_worst_first(self, run_dir: Path) -> None:
        """Scenarios in report should be sorted by failure rate (worst first)."""
        manifest = {"run_id": "sort_test"}
        (run_dir / "manifest.json").write_text(json.dumps(manifest))

        # Create instances with different pass rates
        instances = [
            # checkout: 2/2 = 100% pass
            {"scenario_id": "checkout", "passed": True},
            {"scenario_id": "checkout", "passed": True},
            # refund: 1/2 = 50% pass (worst)
            {"scenario_id": "refund", "passed": True},
            {"scenario_id": "refund", "passed": False},
            # login: 3/4 = 75% pass
            {"scenario_id": "login", "passed": True},
            {"scenario_id": "login", "passed": True},
            {"scenario_id": "login", "passed": True},
            {"scenario_id": "login", "passed": False},
        ]
        with (run_dir / "instances.jsonl").open("w") as f:
            for instance in instances:
                f.write(json.dumps(instance) + "\n")

        generator = HTMLReportGenerator(run_dir)
        result_path = generator.generate()

        content = result_path.read_text()
        # Verify order: refund (worst) should appear before login and checkout
        refund_pos = content.find("refund")
        login_pos = content.find("login")
        checkout_pos = content.find("checkout")

        # In the scenarios table, refund should come first
        assert refund_pos < login_pos
        assert login_pos < checkout_pos

    def test_assertion_failure_count_displayed(self, run_dir: Path) -> None:
        """Report should show failure count for each assertion."""
        manifest = {"run_id": "assertion_count_test"}
        (run_dir / "manifest.json").write_text(json.dumps(manifest))

        assertions = [
            {"assertion_name": "payment_captured", "passed": False},
            {"assertion_name": "payment_captured", "passed": False},
            {"assertion_name": "payment_captured", "passed": False},
        ]
        with (run_dir / "assertions.jsonl").open("w") as f:
            for assertion in assertions:
                f.write(json.dumps(assertion) + "\n")

        generator = HTMLReportGenerator(run_dir)
        result_path = generator.generate()

        content = result_path.read_text()
        assert "payment_captured" in content
        # The count 3 should appear near payment_captured in the table
        assert ">3<" in content

    def test_report_contains_timestamp(self, populated_run_dir: Path) -> None:
        """Report should display run timestamp."""
        generator = HTMLReportGenerator(populated_run_dir)
        result_path = generator.generate()

        content = result_path.read_text()
        assert "2024-01-15T10:30:00Z" in content

    def test_report_contains_sut_name(self, populated_run_dir: Path) -> None:
        """Report should display SUT name."""
        generator = HTMLReportGenerator(populated_run_dir)
        result_path = generator.generate()

        content = result_path.read_text()
        assert "ecommerce" in content
