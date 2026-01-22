# FEAT-022: Run List Page

## Overview

Implement the Run List page as the entry point to the Windtunnel Web UI. Displays all available runs with key metrics in a sortable, filterable table.

## Dependencies

- FEAT-020 (Web UI Foundation) - Layout and shared components
- FEAT-021 (FastAPI Backend) - `/api/runs` endpoint

## Acceptance Criteria

### Page Layout
- [ ] Page title: "Runs" with run count badge
- [ ] Refresh button to reload run list
- [ ] Empty state when no runs exist

### Run Table
- [ ] Columns: Run ID, SUT Name, Scenarios, Started At, Duration, Pass Rate, Status
- [ ] Sortable by: date (default), pass rate, duration
- [ ] Clickable rows navigate to Run Detail page
- [ ] Hover state with subtle highlight

### Pass Rate Visualization
- [ ] Show as percentage with color gradient:
  - 95-100%: Green
  - 80-94%: Yellow
  - <80%: Red
- [ ] Include small progress bar under percentage

### Status Indicators
- [ ] "Running" badge for in-progress runs (animated)
- [ ] "Complete" badge for finished runs
- [ ] "Error" badge if run had fatal errors

### Loading State
- [ ] Show skeleton rows while loading
- [ ] Animate skeleton with shimmer effect

### Data Fetching
- [ ] Use TanStack Query for data fetching
- [ ] Auto-refresh every 30 seconds for active runs
- [ ] Cache run list data

## Visual Design

```
┌─────────────────────────────────────────────────────────────────────┐
│ Runs                                                    [↻ Refresh] │
│ 12 runs                                                             │
├─────────────────────────────────────────────────────────────────────┤
│ Run ID              │ SUT          │ Started    │ Duration │  Rate  │
├─────────────────────┼──────────────┼────────────┼──────────┼────────┤
│ run_20240121_143022 │ ecommerce    │ 2 min ago  │ 83s      │ ██ 98% │
│ run_20240121_141500 │ ecommerce    │ 15 min ago │ 92s      │ ██ 94% │
│ run_20240121_120000 │ payments     │ 3 hrs ago  │ 156s     │ █░ 72% │
└─────────────────────┴──────────────┴────────────┴──────────┴────────┘
```

## Technical Notes

### Component Structure
```
RunListPage/
├── index.tsx           # Page component
├── RunListHeader.tsx   # Title + refresh button
├── RunListTable.tsx    # Table with sorting
├── RunRow.tsx          # Individual row
└── PassRateCell.tsx    # Pass rate with visualization
```

### API Integration
```typescript
// hooks/useRuns.ts
export function useRuns() {
  return useQuery({
    queryKey: ['runs'],
    queryFn: () => fetch('/api/runs').then(r => r.json()),
    refetchInterval: 30000, // Auto-refresh for active runs
  });
}
```

## Estimated Complexity

Medium (2 days)

## Definition of Done

- [ ] Run list displays all available runs
- [ ] Sorting works for date, pass rate, duration
- [ ] Clicking a row navigates to `/runs/:runId`
- [ ] Loading skeleton shows during fetch
- [ ] Empty state shows when no runs exist
- [ ] Pass rate colors are correct
- [ ] Responsive on mobile (horizontal scroll)
