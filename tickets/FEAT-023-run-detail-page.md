# FEAT-023: Run Detail Page with Instance Grid

## Overview

Implement the Run Detail page showing aggregated stats and a filterable grid of all instances within a run. This is the primary drill-down view for understanding run results.

## Dependencies

- FEAT-020 (Web UI Foundation) - Layout and shared components
- FEAT-021 (FastAPI Backend) - `/api/runs/:runId` and `/api/runs/:runId/instances` endpoints

## Acceptance Criteria

### Page Header
- [ ] Breadcrumb: Runs > Run ID
- [ ] Run ID as title
- [ ] SUT name and scenario list as subtitle
- [ ] Timestamp (started at / completed at)

### Summary Cards Row
- [ ] **Pass Rate Card**: Large percentage with color, trend indicator
- [ ] **Duration Card**: Total run time in human-readable format
- [ ] **Instance Count Card**: Total / Passed / Failed breakdown
- [ ] **Error Count Card**: Count of instances with errors

### Filter Bar
- [ ] Quick filters: All | Passed | Failed | Errors
- [ ] Click filter shows count and applies instantly
- [ ] Active filter highlighted

### Instance Grid
- [ ] Columns: Instance ID, Correlation ID, Scenario, Duration, Status
- [ ] Status shows as colored badge (Pass/Fail/Error)
- [ ] Sortable by duration, status
- [ ] Pagination for large runs (50 per page)
- [ ] Clickable rows navigate to Instance Timeline

### Performance
- [ ] Virtual scrolling for 1000+ instances
- [ ] Debounced filtering
- [ ] Pagination controls at bottom

## Visual Design

```
┌─────────────────────────────────────────────────────────────────────┐
│ Runs > run_20240121_143022                                          │
│                                                                     │
│ ecommerce-checkout                              Started: 2 min ago  │
│ checkout-flow, payment-flow                     Duration: 83s       │
├─────────────────────────────────────────────────────────────────────┤
│ ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│ │   98.2%  │  │   83s    │  │  1000    │  │    3     │              │
│ │ Pass Rate│  │ Duration │  │Instances │  │  Errors  │              │
│ └──────────┘  └──────────┘  └──────────┘  └──────────┘              │
├─────────────────────────────────────────────────────────────────────┤
│ [All: 1000] [Passed: 982] [Failed: 15] [Errors: 3]                  │
├─────────────────────────────────────────────────────────────────────┤
│ Instance ID  │ Correlation ID │ Scenario      │ Duration │ Status  │
├──────────────┼────────────────┼───────────────┼──────────┼─────────┤
│ inst_001     │ corr_abc123    │ checkout-flow │ 245ms    │ ✓ Pass  │
│ inst_002     │ corr_def456    │ payment-flow  │ 892ms    │ ✗ Fail  │
│ inst_003     │ corr_ghi789    │ checkout-flow │ 156ms    │ ✓ Pass  │
├──────────────────────────────────────────────────────────────────────┤
│                        Page 1 of 20  [< Prev] [Next >]              │
└─────────────────────────────────────────────────────────────────────┘
```

## Technical Notes

### Component Structure
```
RunDetailPage/
├── index.tsx              # Page component
├── RunHeader.tsx          # Breadcrumb, title, metadata
├── SummaryCards.tsx       # Row of metric cards
│   ├── PassRateCard.tsx
│   ├── DurationCard.tsx
│   ├── InstanceCountCard.tsx
│   └── ErrorCountCard.tsx
├── FilterBar.tsx          # Quick filter buttons
├── InstanceGrid.tsx       # Table with pagination
│   └── InstanceRow.tsx
└── Pagination.tsx         # Page controls
```

### State Management
```typescript
// stores/runDetailStore.ts
interface RunDetailState {
  filter: 'all' | 'passed' | 'failed' | 'errors';
  page: number;
  sort: { field: string; direction: 'asc' | 'desc' };
  setFilter: (filter: string) => void;
  setPage: (page: number) => void;
  setSort: (field: string) => void;
}
```

## Estimated Complexity

High (2-3 days)

## Definition of Done

- [ ] Summary cards display correct aggregated stats
- [ ] Filter buttons work and show filtered counts
- [ ] Instance grid is sortable and paginated
- [ ] Clicking instance row navigates to timeline
- [ ] Page handles 10,000+ instances without lag
- [ ] Loading states for all async operations
- [ ] Breadcrumb navigation works correctly
