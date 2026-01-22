# FEAT-024: Instance Timeline Page

## Overview

Implement the Instance Timeline page showing step-by-step execution details for a single workflow instance. This is the deepest drill-down level for debugging failures.

## Dependencies

- FEAT-020 (Web UI Foundation) - Layout and shared components
- FEAT-021 (FastAPI Backend) - `/api/runs/:runId/instances/:instanceId` endpoint

## Acceptance Criteria

### Page Header
- [ ] Breadcrumb: Runs > Run ID > Instance ID
- [ ] Instance ID as title
- [ ] Correlation ID (copyable)
- [ ] Scenario name and overall status

### Instance Summary
- [ ] Total steps count
- [ ] Total duration
- [ ] Pass/Fail status with color
- [ ] Entry context data (collapsible)

### Step Timeline
- [ ] Vertical timeline with connected steps
- [ ] Each step shows:
  - Step number and name
  - Action type icon (HTTP, Wait, Assert)
  - Latency
  - Status (pass/fail)
- [ ] Failed steps highlighted in red
- [ ] Turbulence indicators if injected

### Step Detail (Expandable)
- [ ] Expand/collapse individual steps
- [ ] For HTTP actions:
  - Request method, URL, headers, body
  - Response status, headers, body
  - Extracted values
- [ ] For Wait actions:
  - Poll attempts with timestamps
  - Final condition result
- [ ] For Assert actions:
  - Expectation details
  - Actual vs expected values
  - Error message if failed

### JSON Viewer
- [ ] Syntax-highlighted JSON display
- [ ] Collapsible nested objects
- [ ] Copy-to-clipboard button
- [ ] Search within JSON

### Replay Button
- [ ] "Replay Instance" button in header
- [ ] Shows confirmation dialog
- [ ] Navigates to replay results when complete

## Visual Design

```
┌─────────────────────────────────────────────────────────────────────┐
│ Runs > run_20240121_143022 > inst_042                               │
│                                                                     │
│ Instance inst_042                                   [Replay ↻]      │
│ Correlation: corr_abc123 [📋]    Scenario: checkout-flow            │
│ Status: ✗ Failed    Duration: 892ms    Steps: 5                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ●─── Step 1: create_cart ─────────────────────────────── ✓ 45ms   │
│  │    [HTTP] POST /api/cart                                         │
│  │    ▸ Show Details                                                │
│  │                                                                  │
│  ●─── Step 2: add_item ────────────────────────────────── ✓ 67ms   │
│  │    [HTTP] POST /api/cart/items                                   │
│  │    ▸ Show Details                                                │
│  │                                                                  │
│  ●─── Step 3: wait_for_inventory ──────────────────────── ✓ 320ms  │
│  │    [WAIT] GET /api/inventory/check                               │
│  │    ▸ Show Details                                                │
│  │                                                                  │
│  ●─── Step 4: checkout ────────────────────────────────── ✗ 450ms  │
│  │    [HTTP] POST /api/checkout          ⚠️ TURBULENCE: 200ms delay │
│  │    ▼ Show Details                                                │
│  │    ┌─────────────────────────────────────────────────────────┐  │
│  │    │ Request                                                 │  │
│  │    │ POST https://api.example.com/api/checkout               │  │
│  │    │ Headers: { "Content-Type": "application/json" }         │  │
│  │    │ Body: { "cartId": "cart_xyz", "paymentMethod": "card" } │  │
│  │    ├─────────────────────────────────────────────────────────┤  │
│  │    │ Response                                                │  │
│  │    │ Status: 500 Internal Server Error                       │  │
│  │    │ Body: { "error": "Payment service unavailable" }        │  │
│  │    └─────────────────────────────────────────────────────────┘  │
│  │                                                                  │
│  ●─── Step 5: assert_order_created ────────────────────── ✗ 10ms   │
│       [ASSERT] $.order.status equals "confirmed"                    │
│       Expected: "confirmed", Actual: null                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Technical Notes

### Component Structure
```
InstanceTimelinePage/
├── index.tsx              # Page component
├── InstanceHeader.tsx     # Title, metadata, replay button
├── InstanceSummary.tsx    # Stats cards row
├── StepTimeline.tsx       # Vertical timeline container
│   └── StepCard.tsx       # Individual step
│       ├── StepIcon.tsx   # Action type icon
│       ├── StepSummary.tsx  # One-line summary
│       └── StepDetail.tsx   # Expandable detail panel
│           ├── RequestViewer.tsx
│           ├── ResponseViewer.tsx
│           └── AssertionViewer.tsx
├── JsonViewer.tsx         # Reusable JSON display
└── ReplayDialog.tsx       # Confirmation modal
```

### State for Expanded Steps
```typescript
// Local state for which steps are expanded
const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

const toggleStep = (index: number) => {
  setExpandedSteps(prev => {
    const next = new Set(prev);
    if (next.has(index)) {
      next.delete(index);
    } else {
      next.add(index);
    }
    return next;
  });
};
```

## Estimated Complexity

High (2-3 days)

## Definition of Done

- [ ] Timeline displays all steps in order
- [ ] Steps are expandable/collapsible
- [ ] HTTP requests show full request/response details
- [ ] JSON viewer has syntax highlighting and copy button
- [ ] Failed steps are visually highlighted
- [ ] Turbulence injection shown when applicable
- [ ] Replay button triggers replay command
- [ ] Breadcrumb navigation works correctly
