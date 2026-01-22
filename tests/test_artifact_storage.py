"""Tests for artifact storage and JSONL persistence."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from windtunnel.models.assertion_result import AssertionResult
from windtunnel.models.manifest import (
    AssertionRecord,
    InstanceRecord,
    RunConfig,
    RunManifest,
    RunSummary,
    StepRecord,
)
from windtunnel.models.observation import Observation
from windtunnel.storage.artifact import ArtifactStore
from windtunnel.storage.jsonl import JSONLWriter, read_jsonl, write_jsonl_record


class TestJSONLWriter:
    """Tests for JSONLWriter class."""

    def test_write_single_record(self, tmp_path: Path) -> None:
        """Test writing a single record to JSONL file."""
        jsonl_path = tmp_path / "test.jsonl"

        with JSONLWriter(jsonl_path) as writer:
            writer.write({"id": 1, "name": "test"})

        # Verify file contents
        lines = jsonl_path.read_text().strip().split("\n")
        assert len(lines) == 1
        assert json.loads(lines[0]) == {"id": 1, "name": "test"}

    def test_write_multiple_records(self, tmp_path: Path) -> None:
        """Test writing multiple records to JSONL file."""
        jsonl_path = tmp_path / "test.jsonl"

        with JSONLWriter(jsonl_path) as writer:
            writer.write({"id": 1})
            writer.write({"id": 2})
            writer.write({"id": 3})

        lines = jsonl_path.read_text().strip().split("\n")
        assert len(lines) == 3
        assert json.loads(lines[0]) == {"id": 1}
        assert json.loads(lines[1]) == {"id": 2}
        assert json.loads(lines[2]) == {"id": 3}

    def test_write_pydantic_model(self, tmp_path: Path) -> None:
        """Test writing a Pydantic model to JSONL file."""
        jsonl_path = tmp_path / "test.jsonl"

        observation = Observation(
            ok=True,
            status_code=200,
            latency_ms=100.5,
            headers={"Content-Type": "application/json"},
            body={"result": "success"},
            errors=[],
            action_name="test-action",
        )

        with JSONLWriter(jsonl_path) as writer:
            writer.write(observation)

        lines = jsonl_path.read_text().strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["ok"] is True
        assert data["status_code"] == 200
        assert data["latency_ms"] == 100.5

    def test_write_without_opening_raises_error(self, tmp_path: Path) -> None:
        """Test that writing without opening raises RuntimeError."""
        jsonl_path = tmp_path / "test.jsonl"
        writer = JSONLWriter(jsonl_path)

        with pytest.raises(RuntimeError, match="must be opened"):
            writer.write({"id": 1})

    def test_append_mode(self, tmp_path: Path) -> None:
        """Test that JSONL writer appends to existing file."""
        jsonl_path = tmp_path / "test.jsonl"

        # Write first record
        with JSONLWriter(jsonl_path) as writer:
            writer.write({"id": 1})

        # Write second record (should append)
        with JSONLWriter(jsonl_path) as writer:
            writer.write({"id": 2})

        lines = jsonl_path.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"id": 1}
        assert json.loads(lines[1]) == {"id": 2}

    def test_path_property(self, tmp_path: Path) -> None:
        """Test that path property returns the file path."""
        jsonl_path = tmp_path / "test.jsonl"
        writer = JSONLWriter(jsonl_path)

        assert writer.path == jsonl_path


class TestJSONLHelpers:
    """Tests for JSONL helper functions."""

    def test_write_jsonl_record(self, tmp_path: Path) -> None:
        """Test write_jsonl_record convenience function."""
        jsonl_path = tmp_path / "test.jsonl"

        write_jsonl_record(jsonl_path, {"id": 1})
        write_jsonl_record(jsonl_path, {"id": 2})

        lines = jsonl_path.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_read_jsonl(self, tmp_path: Path) -> None:
        """Test read_jsonl function."""
        jsonl_path = tmp_path / "test.jsonl"

        # Write some records
        with JSONLWriter(jsonl_path) as writer:
            writer.write({"id": 1, "name": "first"})
            writer.write({"id": 2, "name": "second"})
            writer.write({"id": 3, "name": "third"})

        # Read them back
        records = read_jsonl(jsonl_path)

        assert len(records) == 3
        assert records[0] == {"id": 1, "name": "first"}
        assert records[1] == {"id": 2, "name": "second"}
        assert records[2] == {"id": 3, "name": "third"}

    def test_read_jsonl_empty_lines_ignored(self, tmp_path: Path) -> None:
        """Test that empty lines are ignored when reading."""
        jsonl_path = tmp_path / "test.jsonl"

        # Write with empty lines
        with jsonl_path.open("w") as f:
            f.write('{"id": 1}\n')
            f.write("\n")
            f.write('{"id": 2}\n')
            f.write("   \n")
            f.write('{"id": 3}\n')

        records = read_jsonl(jsonl_path)
        assert len(records) == 3


class TestManifestModels:
    """Tests for manifest models."""

    def test_run_manifest_creation(self) -> None:
        """Test creating a RunManifest."""
        manifest = RunManifest(
            run_id="run_abc123",
            sut_name="ecommerce",
            scenario_ids=["checkout", "refund"],
            seed=42,
        )

        assert manifest.run_id == "run_abc123"
        assert manifest.sut_name == "ecommerce"
        assert manifest.scenario_ids == ["checkout", "refund"]
        assert manifest.seed == 42
        assert manifest.timestamp is not None

    def test_instance_record_creation(self) -> None:
        """Test creating an InstanceRecord."""
        record = InstanceRecord(
            instance_id="inst_001",
            run_id="run_abc123",
            correlation_id="corr_xyz",
            scenario_id="checkout",
            passed=True,
            duration_ms=1500.0,
            entry_data={"user_id": 123},
        )

        assert record.instance_id == "inst_001"
        assert record.run_id == "run_abc123"
        assert record.correlation_id == "corr_xyz"
        assert record.passed is True
        assert record.duration_ms == 1500.0
        assert record.entry_data == {"user_id": 123}

    def test_step_record_creation(self) -> None:
        """Test creating a StepRecord."""
        record = StepRecord(
            instance_id="inst_001",
            run_id="run_abc123",
            correlation_id="corr_xyz",
            step_index=0,
            step_name="get-user",
            step_type="http",
            observation={"ok": True, "status_code": 200},
        )

        assert record.step_index == 0
        assert record.step_name == "get-user"
        assert record.step_type == "http"
        assert record.observation["ok"] is True

    def test_assertion_record_creation(self) -> None:
        """Test creating an AssertionRecord."""
        record = AssertionRecord(
            instance_id="inst_001",
            run_id="run_abc123",
            correlation_id="corr_xyz",
            step_index=1,
            assertion_name="status_ok",
            passed=True,
            expected=200,
            actual=200,
            message="Status code matches",
        )

        assert record.assertion_name == "status_ok"
        assert record.passed is True
        assert record.expected == 200
        assert record.actual == 200

    def test_run_summary_creation(self) -> None:
        """Test creating a RunSummary."""
        summary = RunSummary(
            run_id="run_abc123",
            total_instances=100,
            pass_count=95,
            fail_count=5,
            pass_rate=95.0,
            duration_ms=30000.0,
        )

        assert summary.total_instances == 100
        assert summary.pass_count == 95
        assert summary.fail_count == 5
        assert summary.pass_rate == 95.0


class TestArtifactStore:
    """Tests for ArtifactStore class."""

    def test_create_run_directory_structure(self, tmp_path: Path) -> None:
        """Test that run directory structure is created correctly."""
        store = ArtifactStore(
            run_id="run_20240115_001",
            base_path=tmp_path,
            sut_name="ecommerce",
            scenario_ids=["checkout", "refund"],
        )
        store.initialize()

        run_dir = tmp_path / "run_20240115_001"
        assert run_dir.exists()
        assert (run_dir / "manifest.json").exists()
        assert (run_dir / "artifacts").exists()

        store.finalize()

    def test_write_manifest_json(self, tmp_path: Path) -> None:
        """Test that manifest.json contains correct metadata."""
        store = ArtifactStore(
            run_id="run_20240115_001",
            base_path=tmp_path,
            sut_name="ecommerce",
            scenario_ids=["checkout", "refund"],
            seed=42,
            config=RunConfig(concurrency=4, timeout_seconds=60.0),
        )
        store.initialize()

        manifest_path = tmp_path / "run_20240115_001" / "manifest.json"
        manifest_data = json.loads(manifest_path.read_text())

        assert manifest_data["run_id"] == "run_20240115_001"
        assert manifest_data["sut_name"] == "ecommerce"
        assert manifest_data["scenario_ids"] == ["checkout", "refund"]
        assert manifest_data["seed"] == 42
        assert manifest_data["config"]["concurrency"] == 4
        assert manifest_data["config"]["timeout_seconds"] == 60.0

        store.finalize()

    def test_stream_instance_data(self, tmp_path: Path) -> None:
        """Test streaming instance records to JSONL."""
        store = ArtifactStore(
            run_id="run_001",
            base_path=tmp_path,
            sut_name="test-sut",
        )
        store.initialize()

        # Write instance records
        store.write_instance(
            instance_id="inst_001",
            correlation_id="corr_001",
            scenario_id="checkout",
            passed=True,
            duration_ms=1000.0,
        )
        store.write_instance(
            instance_id="inst_002",
            correlation_id="corr_002",
            scenario_id="checkout",
            passed=False,
            duration_ms=1500.0,
            error="Assertion failed",
        )

        # Verify file is written immediately (before finalize)
        instances_path = tmp_path / "run_001" / "instances.jsonl"
        records = read_jsonl(instances_path)

        assert len(records) == 2
        assert records[0]["instance_id"] == "inst_001"
        assert records[0]["passed"] is True
        assert records[1]["instance_id"] == "inst_002"
        assert records[1]["passed"] is False
        assert records[1]["error"] == "Assertion failed"

        store.finalize()

    def test_stream_step_observations(self, tmp_path: Path) -> None:
        """Test streaming step observations to JSONL."""
        store = ArtifactStore(
            run_id="run_001",
            base_path=tmp_path,
        )
        store.initialize()

        # Write step with Observation model
        observation = Observation(
            ok=True,
            status_code=200,
            latency_ms=150.0,
            body={"id": 123},
        )
        store.write_step(
            instance_id="inst_001",
            correlation_id="corr_001",
            step_index=0,
            step_name="get-user",
            step_type="http",
            observation=observation,
        )

        # Write step with dict observation
        store.write_step(
            instance_id="inst_001",
            correlation_id="corr_001",
            step_index=1,
            step_name="wait-100ms",
            step_type="wait",
            observation={"duration_ms": 100},
        )

        steps_path = tmp_path / "run_001" / "steps.jsonl"
        records = read_jsonl(steps_path)

        assert len(records) == 2
        assert records[0]["instance_id"] == "inst_001"
        assert records[0]["step_name"] == "get-user"
        assert records[0]["observation"]["ok"] is True
        assert records[0]["observation"]["status_code"] == 200
        assert records[1]["step_name"] == "wait-100ms"
        assert records[1]["observation"]["duration_ms"] == 100

        store.finalize()

    def test_stream_assertions(self, tmp_path: Path) -> None:
        """Test streaming assertion results to JSONL."""
        store = ArtifactStore(
            run_id="run_001",
            base_path=tmp_path,
        )
        store.initialize()

        # Write assertion using AssertionResult model
        result = AssertionResult(
            name="status_ok",
            passed=True,
            expected=200,
            actual=200,
            message="Status code matches",
        )
        store.write_assertion(
            instance_id="inst_001",
            correlation_id="corr_001",
            step_index=0,
            assertion_result=result,
        )

        # Write assertion using individual fields
        store.write_assertion(
            instance_id="inst_001",
            correlation_id="corr_001",
            step_index=1,
            assertion_name="body_contains",
            passed=False,
            expected="success",
            actual="error",
            message="Body does not contain expected value",
        )

        assertions_path = tmp_path / "run_001" / "assertions.jsonl"
        records = read_jsonl(assertions_path)

        assert len(records) == 2
        assert records[0]["assertion_name"] == "status_ok"
        assert records[0]["passed"] is True
        assert records[1]["assertion_name"] == "body_contains"
        assert records[1]["passed"] is False

        store.finalize()

    def test_write_summary_on_completion(self, tmp_path: Path) -> None:
        """Test that summary.json is written on finalize."""
        store = ArtifactStore(
            run_id="run_001",
            base_path=tmp_path,
        )
        store.initialize()

        # Write 100 instances (95 pass, 5 fail)
        for i in range(95):
            store.write_instance(
                instance_id=f"inst_{i:03d}",
                correlation_id=f"corr_{i:03d}",
                scenario_id="test",
                passed=True,
            )
        for i in range(95, 100):
            store.write_instance(
                instance_id=f"inst_{i:03d}",
                correlation_id=f"corr_{i:03d}",
                scenario_id="test",
                passed=False,
            )

        # Write some steps and assertions
        for i in range(200):
            store.write_step(
                instance_id=f"inst_{i % 100:03d}",
                correlation_id=f"corr_{i % 100:03d}",
                step_index=i % 2,
                step_name="test-step",
                step_type="http",
                observation={"ok": True},
            )
        for i in range(150):
            store.write_assertion(
                instance_id=f"inst_{i % 100:03d}",
                correlation_id=f"corr_{i % 100:03d}",
                step_index=0,
                assertion_name="test",
                passed=i < 140,
            )

        summary = store.finalize()

        # Verify summary object
        assert summary.total_instances == 100
        assert summary.pass_count == 95
        assert summary.fail_count == 5
        assert summary.pass_rate == 95.0
        assert summary.total_steps == 200
        assert summary.total_assertions == 150
        assert summary.assertions_passed == 140
        assert summary.assertions_failed == 10

        # Verify summary.json file
        summary_path = tmp_path / "run_001" / "summary.json"
        summary_data = json.loads(summary_path.read_text())

        assert summary_data["total_instances"] == 100
        assert summary_data["pass_count"] == 95
        assert summary_data["fail_count"] == 5
        assert summary_data["pass_rate"] == 95.0
        assert summary_data["duration_ms"] >= 0

    def test_correlation_ids_in_all_records(self, tmp_path: Path) -> None:
        """Test that correlation IDs are present in all records."""
        store = ArtifactStore(
            run_id="run_001",
            base_path=tmp_path,
        )
        store.initialize()

        correlation_id = "corr_unique_123"

        store.write_instance(
            instance_id="inst_001",
            correlation_id=correlation_id,
            scenario_id="test",
        )
        store.write_step(
            instance_id="inst_001",
            correlation_id=correlation_id,
            step_index=0,
            step_name="test",
            step_type="http",
            observation={},
        )
        store.write_assertion(
            instance_id="inst_001",
            correlation_id=correlation_id,
            step_index=0,
            assertion_name="test",
            passed=True,
        )

        store.finalize()

        # Verify correlation IDs in all files
        instances = read_jsonl(tmp_path / "run_001" / "instances.jsonl")
        steps = read_jsonl(tmp_path / "run_001" / "steps.jsonl")
        assertions = read_jsonl(tmp_path / "run_001" / "assertions.jsonl")

        assert instances[0]["correlation_id"] == correlation_id
        assert steps[0]["correlation_id"] == correlation_id
        assert assertions[0]["correlation_id"] == correlation_id

    def test_context_manager_usage(self, tmp_path: Path) -> None:
        """Test using ArtifactStore as context manager."""
        with ArtifactStore(
            run_id="run_ctx",
            base_path=tmp_path,
            sut_name="test-sut",
        ) as store:
            store.write_instance(
                instance_id="inst_001",
                correlation_id="corr_001",
                scenario_id="test",
                passed=True,
            )

        # Verify files exist and are properly closed
        run_dir = tmp_path / "run_ctx"
        assert (run_dir / "manifest.json").exists()
        assert (run_dir / "instances.jsonl").exists()
        assert (run_dir / "summary.json").exists()

    def test_write_instance_artifact(self, tmp_path: Path) -> None:
        """Test writing raw artifacts for instances."""
        store = ArtifactStore(
            run_id="run_001",
            base_path=tmp_path,
        )
        store.initialize()

        # Write JSON artifact
        artifact_path = store.write_instance_artifact(
            instance_id="inst_001",
            filename="step_001_request.json",
            data={"url": "https://api.example.com", "method": "GET"},
        )

        assert artifact_path.exists()
        artifact_data = json.loads(artifact_path.read_text())
        assert artifact_data["url"] == "https://api.example.com"
        assert artifact_data["method"] == "GET"

        # Write raw text artifact
        artifact_path2 = store.write_instance_artifact(
            instance_id="inst_001",
            filename="step_001_response.txt",
            data="Raw response body",
        )

        assert artifact_path2.exists()
        assert artifact_path2.read_text() == "Raw response body"

        store.finalize()

    def test_artifact_directory_structure(self, tmp_path: Path) -> None:
        """Test that artifact directory structure matches spec."""
        store = ArtifactStore(
            run_id="run_20240115_001",
            base_path=tmp_path,
        )
        store.initialize()

        # Write artifacts for multiple instances
        store.write_instance_artifact(
            instance_id="inst_001",
            filename="step_001_request.json",
            data={"test": "data"},
        )
        store.write_instance_artifact(
            instance_id="inst_002",
            filename="step_001_request.json",
            data={"test": "data2"},
        )

        store.finalize()

        # Verify structure
        run_dir = tmp_path / "run_20240115_001"
        assert (run_dir / "artifacts" / "inst_001" / "step_001_request.json").exists()
        assert (run_dir / "artifacts" / "inst_002" / "step_001_request.json").exists()

    def test_uninitialized_store_raises_error(self, tmp_path: Path) -> None:
        """Test that writing to uninitialized store raises error."""
        store = ArtifactStore(
            run_id="run_001",
            base_path=tmp_path,
        )

        with pytest.raises(RuntimeError, match="must be initialized"):
            store.write_instance(
                instance_id="inst_001",
                correlation_id="corr_001",
                scenario_id="test",
            )

    def test_idempotent_initialization(self, tmp_path: Path) -> None:
        """Test that calling initialize() twice is idempotent."""
        store = ArtifactStore(
            run_id="run_001",
            base_path=tmp_path,
        )

        store.initialize()
        store.initialize()  # Should not raise

        store.finalize()

    def test_path_properties(self, tmp_path: Path) -> None:
        """Test that path properties return correct values."""
        store = ArtifactStore(
            run_id="run_001",
            base_path=tmp_path,
        )

        assert store.run_id == "run_001"
        assert store.run_path == tmp_path / "run_001"
        assert store.manifest_path == tmp_path / "run_001" / "manifest.json"
        assert store.instances_path == tmp_path / "run_001" / "instances.jsonl"
        assert store.steps_path == tmp_path / "run_001" / "steps.jsonl"
        assert store.assertions_path == tmp_path / "run_001" / "assertions.jsonl"
        assert store.summary_path == tmp_path / "run_001" / "summary.json"
        assert store.artifacts_path == tmp_path / "run_001" / "artifacts"

    def test_entry_data_preserved(self, tmp_path: Path) -> None:
        """Test that entry data is preserved in instance records."""
        store = ArtifactStore(
            run_id="run_001",
            base_path=tmp_path,
        )
        store.initialize()

        entry_data = {"user_id": 123, "product_ids": [1, 2, 3], "coupon": "SAVE10"}

        store.write_instance(
            instance_id="inst_001",
            correlation_id="corr_001",
            scenario_id="checkout",
            entry_data=entry_data,
        )

        store.finalize()

        instances = read_jsonl(tmp_path / "run_001" / "instances.jsonl")
        assert instances[0]["entry_data"] == entry_data

    def test_timestamps_are_serialized(self, tmp_path: Path) -> None:
        """Test that timestamps are properly serialized to JSON."""
        store = ArtifactStore(
            run_id="run_001",
            base_path=tmp_path,
        )
        store.initialize()

        now = datetime.now(timezone.utc)
        store.write_instance(
            instance_id="inst_001",
            correlation_id="corr_001",
            scenario_id="test",
            started_at=now,
            completed_at=now,
        )

        store.finalize()

        instances = read_jsonl(tmp_path / "run_001" / "instances.jsonl")
        # Timestamps should be serialized as ISO format strings
        assert "T" in instances[0]["started_at"]  # ISO format contains T
