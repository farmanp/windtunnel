"""HTML report generator for Turbulence runs."""

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape


def calculate_percentile(data: list[float], percentile: int) -> float:
    """Calculate the Nth percentile of a list of values."""
    if not data:
        return 0.0
    data.sort()
    k = (len(data) - 1) * (percentile / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return data[int(k)]
    d0 = data[int(f)]
    d1 = data[int(c)]
    return d0 + (d1 - d0) * (k - f)


@dataclass
class ActionStats:
    """Statistics for a single action type within a scenario."""

    name: str
    count: int = 0
    latencies: list[float] = field(default_factory=list)
    fail_count: int = 0

    @property
    def p50(self) -> float:
        return calculate_percentile(self.latencies, 50)

    @property
    def p95(self) -> float:
        return calculate_percentile(self.latencies, 95)

    @property
    def p99(self) -> float:
        return calculate_percentile(self.latencies, 99)

    @property
    def avg_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0


@dataclass
class ServiceStats:
    """Statistics for a service across all scenarios."""

    name: str
    request_count: int = 0
    fail_count: int = 0
    latencies: list[float] = field(default_factory=list)

    @property
    def p50(self) -> float:
        return calculate_percentile(self.latencies, 50)

    @property
    def p95(self) -> float:
        return calculate_percentile(self.latencies, 95)

    @property
    def p99(self) -> float:
        return calculate_percentile(self.latencies, 99)


@dataclass
class ScenarioStats:
    """Statistics for a single scenario."""

    name: str
    pass_count: int = 0
    fail_count: int = 0
    actions: dict[str, ActionStats] = field(default_factory=dict)

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
    
    @property
    def actions_list(self) -> list[ActionStats]:
        """Return actions sorted by name? Or just list."""
        # Maybe sorted by order of appearance would be better but we don't track order here.
        # Sorted by name for consistency.
        return sorted(self.actions.values(), key=lambda a: a.name)


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
    services: dict[str, ServiceStats] = field(default_factory=dict)
    error_categories: Counter[str] = field(default_factory=Counter)

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
    
    @property
    def services_stats_list(self) -> list[ServiceStats]:
        """Return service stats sorted by request count."""
        return sorted(self.services.values(), key=lambda s: s.request_count, reverse=True)

    @property
    def error_categories_list(self) -> list[tuple[str, int]]:
        """Return error categories sorted by count."""
        return self.error_categories.most_common()


class HTMLReportGenerator:
    """Generates self-contained HTML reports from Turbulence run artifacts."""

    def __init__(self, run_path: Path) -> None:
        """Initialize the report generator.

        Args:
            run_path: Path to the run directory containing artifacts.
        """
        self.run_path = run_path
        self.env = Environment(
            loader=PackageLoader("turbulence.report", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def _load_manifest(self) -> dict[str, Any]:
        """Load the run manifest.json file."""
        manifest_path = self.run_path / "manifest.json"
        if not manifest_path.exists():
            return {}
        with manifest_path.open() as f:
            result: dict[str, Any] = json.load(f)
            return result

    def _load_summary(self) -> dict[str, Any]:
        """Load the run summary.json file."""
        summary_path = self.run_path / "summary.json"
        if not summary_path.exists():
            return {}
        with summary_path.open() as f:
            result: dict[str, Any] = json.load(f)
            return result

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
        steps = self._load_jsonl("steps.jsonl")
        assertions = self._load_jsonl("assertions.jsonl")

        # Initialize report data
        report_data = ReportData(
            run_id=manifest.get("run_id", self.run_path.name),
            timestamp=manifest.get("timestamp", ""),
            sut_name=manifest.get("sut_name", ""),
            duration_ms=summary.get("duration_ms", 0.0),
        )

        # Map instance_id to scenario_id for step aggregation
        instance_scenario_map: dict[str, str] = {}

        # Process instances for overall and per-scenario stats
        for instance in instances:
            report_data.total_instances += 1
            passed = instance.get("passed", False)
            scenario = instance.get("scenario_id", "unknown")
            instance_id = instance.get("instance_id")
            if instance_id:
                instance_scenario_map[instance_id] = scenario

            if scenario not in report_data.scenarios:
                report_data.scenarios[scenario] = ScenarioStats(name=scenario)

            if passed:
                report_data.pass_count += 1
                report_data.scenarios[scenario].pass_count += 1
            else:
                report_data.fail_count += 1
                report_data.scenarios[scenario].fail_count += 1
            
            # Error categorization from instance-level errors
            if not passed and instance.get("error"):
                error_msg = instance["error"]
                # Simplify error message for categorization (e.g. "HTTP 500..." -> "HTTP 500")
                category = self._categorize_error(error_msg)
                report_data.error_categories[category] += 1

        # Process steps for latency and action stats
        for step in steps:
            instance_id = step.get("instance_id")
            scenario = instance_scenario_map.get(instance_id, "unknown")
            if scenario not in report_data.scenarios:
                report_data.scenarios[scenario] = ScenarioStats(name=scenario)
            
            step_name = step.get("step_name", "unknown")
            obs = step.get("observation", {})
            latency = obs.get("latency_ms", 0.0)
            service = obs.get("service")
            
            # Update ActionStats
            scenario_stats = report_data.scenarios[scenario]
            if step_name not in scenario_stats.actions:
                scenario_stats.actions[step_name] = ActionStats(name=step_name)
            
            action_stats = scenario_stats.actions[step_name]
            action_stats.count += 1
            action_stats.latencies.append(latency)
            if not obs.get("ok", False):
                action_stats.fail_count += 1
                # Collect errors from observations
                for err in obs.get("errors", []):
                    category = self._categorize_error(err)
                    report_data.error_categories[category] += 1

            # Update ServiceStats
            if service:
                if service not in report_data.services:
                    report_data.services[service] = ServiceStats(name=service)
                
                service_stats = report_data.services[service]
                service_stats.request_count += 1
                service_stats.latencies.append(latency)
                if not obs.get("ok", False):
                    service_stats.fail_count += 1

        # Process assertions for failure analysis
        for assertion in assertions:
            if not assertion.get("passed", True):
                name = assertion.get("assertion_name", "unknown")
                # assertions.jsonl doesn't have 'service', it relies on implicit knowledge or manual mapping?
                # The existing code tried to get 'service' from assertion dict.
                # If we want service failures from assertions, we need 'service' in assertion record.
                # Since we can't easily add it now without changing AssertAction execution, 
                # we'll stick to what we have or just use step failures for service stats.
                # report_data.failures_by_service[service] += 1  <-- Removing this as it's unreliable from assertions
                
                report_data.failing_assertions[name] += 1

        # Fill failures_by_service from ServiceStats instead
        for service_name, stats in report_data.services.items():
            if stats.fail_count > 0:
                report_data.failures_by_service[service_name] = stats.fail_count

        # Use summary data if instances.jsonl is empty but summary exists
        if report_data.total_instances == 0 and summary:
            report_data.pass_count = summary.get("pass_count", 0)
            report_data.fail_count = summary.get("fail_count", 0)
            report_data.total_instances = (
                report_data.pass_count + report_data.fail_count
            )

        return report_data

    def _categorize_error(self, error_msg: str) -> str:
        """Categorize an error message into a high-level bucket."""
        if "HTTP 5" in error_msg:
            return "5xx Server Error"
        if "HTTP 4" in error_msg:
            return "4xx Client Error"
        if "timeout" in error_msg.lower():
            return "Timeout"
        if "connection" in error_msg.lower():
            return "Connection Error"
        if "validation" in error_msg.lower() or "schema" in error_msg.lower():
            return "Validation Error"
        if "jsonpath" in error_msg.lower():
            return "Extraction Error"
        return "Other Error"

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
            services=report_data.services_stats_list,
            error_categories=report_data.error_categories_list,
        )

        output_path.write_text(html_content)
        return output_path
