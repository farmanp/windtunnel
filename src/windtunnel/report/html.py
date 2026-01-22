"""HTML report generator for Windtunnel runs."""

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape


@dataclass
class ScenarioStats:
    """Statistics for a single scenario."""

    name: str
    pass_count: int = 0
    fail_count: int = 0

    @property
    def total(self) -> int:
        """Total number of instances in this scenario."""
        return self.pass_count + self.fail_count

    @property
    def pass_rate(self) -> float:
        """Pass rate as a percentage."""
        if self.total == 0:
            return 0.0
        return (self.pass_count / self.total) * 100


@dataclass
class ReportData:
    """Aggregated data for the HTML report."""

    run_id: str
    timestamp: str = ""
    sut_name: str = ""
    total_instances: int = 0
    pass_count: int = 0
    fail_count: int = 0
    duration_ms: float = 0.0
    scenarios: dict[str, ScenarioStats] = field(default_factory=dict)
    failing_assertions: Counter[str] = field(default_factory=Counter)
    failures_by_service: Counter[str] = field(default_factory=Counter)

    @property
    def pass_rate(self) -> float:
        """Overall pass rate as a percentage."""
        if self.total_instances == 0:
            return 0.0
        return (self.pass_count / self.total_instances) * 100

    @property
    def scenarios_sorted_by_failure(self) -> list[ScenarioStats]:
        """Return scenarios sorted by failure rate (worst first)."""
        return sorted(
            self.scenarios.values(),
            key=lambda s: (100 - s.pass_rate, s.fail_count),
            reverse=True,
        )

    @property
    def top_failing_assertions(self) -> list[tuple[str, int]]:
        """Return failing assertions sorted by count (most failures first)."""
        return self.failing_assertions.most_common()

    @property
    def services_by_failure_count(self) -> list[tuple[str, int]]:
        """Return services sorted by failure count (most failures first)."""
        return self.failures_by_service.most_common()


class HTMLReportGenerator:
    """Generates self-contained HTML reports from Windtunnel run artifacts."""

    def __init__(self, run_path: Path) -> None:
        """Initialize the report generator.

        Args:
            run_path: Path to the run directory containing artifacts.
        """
        self.run_path = run_path
        self.env = Environment(
            loader=PackageLoader("windtunnel.report", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def _load_manifest(self) -> dict[str, Any]:
        """Load the run manifest.json file."""
        manifest_path = self.run_path / "manifest.json"
        if not manifest_path.exists():
            return {}
        with manifest_path.open() as f:
            return json.load(f)

    def _load_summary(self) -> dict[str, Any]:
        """Load the run summary.json file."""
        summary_path = self.run_path / "summary.json"
        if not summary_path.exists():
            return {}
        with summary_path.open() as f:
            return json.load(f)

    def _load_jsonl(self, filename: str) -> list[dict[str, Any]]:
        """Load a JSONL file and return all records.

        Args:
            filename: Name of the JSONL file to load.

        Returns:
            List of parsed JSON records.
        """
        file_path = self.run_path / filename
        if not file_path.exists():
            return []

        records = []
        with file_path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def _collect_report_data(self) -> ReportData:
        """Collect and aggregate all data needed for the report.

        Returns:
            ReportData containing all aggregated statistics.
        """
        manifest = self._load_manifest()
        summary = self._load_summary()
        instances = self._load_jsonl("instances.jsonl")
        assertions = self._load_jsonl("assertions.jsonl")

        # Initialize report data
        report_data = ReportData(
            run_id=manifest.get("run_id", self.run_path.name),
            timestamp=manifest.get("timestamp", ""),
            sut_name=manifest.get("sut_name", ""),
            duration_ms=summary.get("duration_ms", 0.0),
        )

        # Process instances for overall and per-scenario stats
        for instance in instances:
            report_data.total_instances += 1
            passed = instance.get("passed", False)
            scenario = instance.get("scenario", "unknown")

            if scenario not in report_data.scenarios:
                report_data.scenarios[scenario] = ScenarioStats(name=scenario)

            if passed:
                report_data.pass_count += 1
                report_data.scenarios[scenario].pass_count += 1
            else:
                report_data.fail_count += 1
                report_data.scenarios[scenario].fail_count += 1

        # Process assertions for failure analysis
        for assertion in assertions:
            if not assertion.get("passed", True):
                name = assertion.get("name", "unknown")
                service = assertion.get("service", "unknown")

                report_data.failing_assertions[name] += 1
                report_data.failures_by_service[service] += 1

        # Use summary data if instances.jsonl is empty but summary exists
        if report_data.total_instances == 0 and summary:
            report_data.pass_count = summary.get("pass_count", 0)
            report_data.fail_count = summary.get("fail_count", 0)
            report_data.total_instances = (
                report_data.pass_count + report_data.fail_count
            )

        return report_data

    def generate(self, output_path: Path | None = None) -> Path:
        """Generate the HTML report.

        Args:
            output_path: Optional custom output path. Defaults to report.html
                        in the run directory.

        Returns:
            Path to the generated report file.
        """
        if output_path is None:
            output_path = self.run_path / "report.html"

        report_data = self._collect_report_data()
        template = self.env.get_template("report.html.j2")

        html_content = template.render(
            run_id=report_data.run_id,
            timestamp=report_data.timestamp,
            sut_name=report_data.sut_name,
            total_instances=report_data.total_instances,
            pass_count=report_data.pass_count,
            fail_count=report_data.fail_count,
            pass_rate=report_data.pass_rate,
            duration_ms=report_data.duration_ms,
            scenarios=report_data.scenarios_sorted_by_failure,
            failing_assertions=report_data.top_failing_assertions,
            failures_by_service=report_data.services_by_failure_count,
        )

        output_path.write_text(html_content)
        return output_path
