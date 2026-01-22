# FEAT-025: Real-Time Run Streaming

## Overview

Implement WebSocket-based real-time updates for in-progress runs. As instances complete during an active run, the UI updates live without manual refresh.

## Dependencies

- FEAT-021 (FastAPI Backend) - Backend infrastructure
- FEAT-022 (Run List Page) - Shows running status
- FEAT-023 (Run Detail Page) - Shows instance updates

## Acceptance Criteria

### Backend WebSocket
- [ ] `WS /api/runs/:runId/stream` endpoint
- [ ] Streams instance completion events
- [ ] Streams step completion events (optional granularity)
- [ ] Sends heartbeat every 5 seconds
- [ ] Gracefully closes when run completes

### Run List Updates
- [ ] "Running" badge shows animated spinner
- [ ] Pass rate updates in real-time
- [ ] Instance count increments as instances complete
- [ ] Duration updates every second for active runs

### Run Detail Updates
- [ ] Summary cards update as instances complete
- [ ] Instance grid receives new rows in real-time
- [ ] Filter counts update dynamically
- [ ] Smooth animation for new data

### Connection Management
- [ ] Auto-reconnect on connection drop
- [ ] Exponential backoff for retries
- [ ] Visual indicator when disconnected
- [ ] Manual reconnect button

### Performance
- [ ] Batch updates to avoid UI thrashing
- [ ] Throttle to max 10 updates/second
- [ ] Smooth animations, no jank

## Technical Notes

### WebSocket Message Format
```json
// Instance completed
{
  "type": "instance_complete",
  "data": {
    "instanceId": "inst_042",
    "correlationId": "corr_abc123",
    "scenarioId": "checkout-flow",
    "passed": true,
    "durationMs": 245
  }
}

// Run stats update
{
  "type": "stats_update",
  "data": {
    "total": 500,
    "passed": 490,
    "failed": 10,
    "passRate": 98.0
  }
}

// Run completed
{
  "type": "run_complete",
  "data": {
    "completedAt": "2024-01-21T14:31:45Z",
    "finalStats": { ... }
  }
}
```

### Frontend Hook
```typescript
// hooks/useRunStream.ts
export function useRunStream(runId: string) {
  const queryClient = useQueryClient();
  
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/api/runs/${runId}/stream`);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'instance_complete') {
        // Optimistically update the instances list
        queryClient.setQueryData(['runs', runId, 'instances'], (old) => {
          return [...old, message.data];
        });
      }
      
      if (message.type === 'stats_update') {
        queryClient.setQueryData(['runs', runId], (old) => ({
          ...old,
          stats: message.data
        }));
      }
    };
    
    return () => ws.close();
  }, [runId, queryClient]);
}
```

### Backend Implementation
```python
# api/routes/stream.py
from fastapi import WebSocket
from windtunnel.storage.artifact import ArtifactStore

@router.websocket("/api/runs/{run_id}/stream")
async def stream_run(websocket: WebSocket, run_id: str):
    await websocket.accept()
    
    # Watch for new JSONL entries
    store = ArtifactStore.open_readonly(run_id)
    last_position = 0
    
    try:
        while not store.is_finalized:
            new_entries = store.read_since(last_position)
            for entry in new_entries:
                await websocket.send_json({
                    "type": "instance_complete",
                    "data": entry
                })
            last_position = store.position
            await asyncio.sleep(0.1)
        
        await websocket.send_json({"type": "run_complete"})
    finally:
        await websocket.close()
```

## Estimated Complexity

Medium (2 days)

## Definition of Done

- [ ] WebSocket connection established for active runs
- [ ] Run List shows real-time pass rate updates
- [ ] Run Detail receives new instances live
- [ ] Summary cards update without refresh
- [ ] Connection indicator shows in UI
- [ ] Auto-reconnect works on disconnect
- [ ] No memory leaks from WebSocket listeners
- [ ] Smooth animations for incoming data
