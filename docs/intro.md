---
sidebar_position: 1
---

# Windtunnel Docs

Windtunnel is a workflow simulation and testing framework for distributed
systems. You model user journeys in YAML, run them concurrently with the async
engine, and get JSONL artifacts plus a rich HTML report for analysis.

Use the **User Guide** to get running quickly and author scenarios. The
**Developer Guide** covers internals, local development, and testing.

## Core Workflow

1. Define a System Under Test (SUT) in YAML.
2. Create one or more scenario YAML files describing the workflow steps.
3. Run `windtunnel run` to execute instances and store artifacts under `runs/`.
4. Generate reports with `windtunnel report` or replay a single instance with
   `windtunnel replay`.

If you are new, start with **User Guide → Getting Started**.
