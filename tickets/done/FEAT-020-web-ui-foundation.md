# FEAT-020: Web UI Foundation (Vite, React, Tailwind)

## Overview

Set up the foundational React application with Vite, TypeScript, and Tailwind CSS. This establishes the development environment and shared components for the Windtunnel Web UI.

## Dependencies

- FEAT-008 (Artifact Storage) - Must be able to read JSONL artifacts

## Acceptance Criteria

### Project Setup
- [ ] Initialize Vite project with React 18 + TypeScript template
- [ ] Configure Tailwind CSS with custom design tokens (colors, fonts)
- [ ] Set up path aliases for clean imports (`@/components`, `@/pages`, etc.)
- [ ] Configure ESLint and Prettier for consistent code style
- [ ] Create `npm run dev` and `npm run build` scripts

### Design System
- [ ] Create CSS custom properties for color palette (dark mode default)
- [ ] Configure Inter font family for UI text
- [ ] Configure JetBrains Mono for monospace/code display
- [ ] Define spacing and sizing scale in Tailwind config

### Layout Components
- [ ] Create `Layout` component with sidebar + main content structure
- [ ] Create `Sidebar` component with logo and navigation items
- [ ] Create `NavItem` component with active state styling
- [ ] Implement responsive behavior (collapsible sidebar on mobile)

### Shared Components
- [ ] `StatusBadge` - Pass/Fail/Error status indicator
- [ ] `MetricCard` - Display key metrics with label and value
- [ ] `SkeletonLoader` - Loading placeholder component
- [ ] `EmptyState` - "No data" display with icon and message
- [ ] `ErrorBoundary` - Graceful error handling wrapper

### Routing
- [ ] Set up React Router with routes:
  - `/` → Run List Page
  - `/runs/:runId` → Run Detail Page
  - `/runs/:runId/instances/:instanceId` → Instance Timeline Page
- [ ] Implement route-based code splitting

## Technical Notes

### Tailwind Configuration
```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        success: 'hsl(142, 71%, 45%)',
        failure: 'hsl(0, 84%, 60%)',
        warning: 'hsl(38, 92%, 50%)',
        bg: {
          primary: 'hsl(222, 47%, 11%)',
          secondary: 'hsl(222, 47%, 15%)',
          elevated: 'hsl(222, 47%, 18%)',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    }
  }
}
```

### Project Structure
```
ui/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── router.tsx
│   ├── components/
│   │   ├── Layout/
│   │   ├── StatusBadge/
│   │   ├── MetricCard/
│   │   └── ...
│   ├── pages/
│   │   ├── RunListPage/
│   │   ├── RunDetailPage/
│   │   └── InstanceTimelinePage/
│   └── styles/
│       └── globals.css
└── package.json
```

## Estimated Complexity

Medium (2-3 days)

## Definition of Done

- [ ] `npm run dev` starts development server on localhost:5173
- [ ] Dark mode UI renders correctly
- [ ] Navigation between routes works
- [ ] All shared components render with Storybook-style demo
- [ ] No TypeScript or ESLint errors
