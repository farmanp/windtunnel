"""WebSocket routes for real-time run streaming."""

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

router = APIRouter(tags=["streaming"])


async def tail_jsonl(file_path: Path, last_position: int = 0) -> tuple[list[dict], int]:
    """Read new lines from a JSONL file since last position.

    Args:
        file_path: Path to the JSONL file.
        last_position: Last read position in bytes.

    Returns:
        Tuple of (new entries, new position).
    """
    entries = []
    if not file_path.exists():
        return entries, last_position

    with file_path.open() as f:
        f.seek(last_position)
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        new_position = f.tell()

    return entries, new_position


def compute_stats(entries: list[dict]) -> dict:
    """Compute run statistics from instance entries.

    Args:
        entries: List of instance entries.

    Returns:
        Statistics dictionary.
    """
    total = len(entries)
    passed = sum(1 for e in entries if e.get("passed", False))
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0.0

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "passRate": round(pass_rate, 1),
    }


@router.websocket("/runs/{run_id}/stream")
async def stream_run(websocket: WebSocket, run_id: str) -> None:
    """Stream real-time updates for a run.

    Sends:
        - instance_complete: When a new instance finishes
        - stats_update: Aggregated statistics
        - heartbeat: Every 5 seconds to keep connection alive
        - run_complete: When the run finishes

    Args:
        websocket: WebSocket connection.
        run_id: The run ID to stream.
    """
    await websocket.accept()

    # Get runs directory from app state
    runs_dir: Path = websocket.app.state.runs_dir
    run_dir = runs_dir / run_id
    instances_file = run_dir / "instances.jsonl"

    if not run_dir.exists():
        await websocket.send_json(
            {"type": "error", "data": {"message": f"Run '{run_id}' not found"}}
        )
        await websocket.close()
        return

    last_position = 0
    all_entries: list[dict] = []
    heartbeat_interval = 5.0
    poll_interval = 0.5
    last_heartbeat = asyncio.get_event_loop().time()

    try:
        while websocket.client_state == WebSocketState.CONNECTED:
            # Check for new entries
            new_entries, last_position = await asyncio.to_thread(
                tail_jsonl, instances_file, last_position
            )

            # Send new instance events
            for entry in new_entries:
                all_entries.append(entry)
                await websocket.send_json(
                    {
                        "type": "instance_complete",
                        "data": {
                            "instanceId": entry.get("instance_id", ""),
                            "correlationId": entry.get("correlation_id", ""),
                            "scenarioId": entry.get("scenario_id", ""),
                            "passed": entry.get("passed", False),
                            "durationMs": entry.get("duration_ms", 0),
                        },
                    }
                )

            # Send stats update if we got new data
            if new_entries:
                stats = compute_stats(all_entries)
                await websocket.send_json({"type": "stats_update", "data": stats})

            # Check for run completion (presence of summary.json)
            summary_file = run_dir / "summary.json"
            if summary_file.exists():
                await websocket.send_json(
                    {"type": "run_complete", "data": {"message": "Run completed"}}
                )
                break

            # Send heartbeat
            now = asyncio.get_event_loop().time()
            if now - last_heartbeat >= heartbeat_interval:
                await websocket.send_json({"type": "heartbeat"})
                last_heartbeat = now

            await asyncio.sleep(poll_interval)

    except WebSocketDisconnect:
        pass
    finally:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()
