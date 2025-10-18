# Task 5.4: Baseline Management - Frontend Implementation Plan

**Task ID**: bd-16
**Created**: 2025-10-17
**Status**: In Progress - Foundation Complete
**Remaining Effort**: 6-8 hours (components + pages + tests)

## Current Status

### ✅ Completed (2 hours)
1. **TypeScript Types** (`frontend/types/baseline.ts` - 142 lines)
   - All 11 interface types matching backend schemas
   - Baseline, BaselineDetail, TaskVariance, ComparisonSummary, etc.
   - Complete type safety across frontend-backend boundary

2. **API Client** (`frontend/lib/api/baselines.ts` - 220 lines)
   - 6 functions matching all 6 backend endpoints
   - Proper error handling with specific messages
   - Auth token interceptor configured
   - Axios instance with proper baseURL
   - Type-safe requests and responses

### 🔨 Remaining Work

**Components (4 files, ~600 lines total)**:
1. VarianceIndicator.tsx - Small reusable component
2. BaselineList.tsx - Main list view with table
3. CreateBaselineDialog.tsx - Modal form
4. BaselineComparisonView.tsx - Comparison dashboard

**Pages (2 files, ~200 lines total)**:
5. app/projects/[id]/baselines/page.tsx
6. app/projects/[id]/baselines/[baselineId]/compare/page.tsx

**Navigation Integration** (1 file):
7. Update project dashboard with baseline link

**Tests** (4 files, ~800 lines total):
8. Component tests for all 4 components

## Component Specifications

### 1. VarianceIndicator Component

**File**: `frontend/components/baselines/VarianceIndicator.tsx`

**Purpose**: Reusable badge showing task variance with color coding

**Props**:
```typescript
interface VarianceIndicatorProps {
  varianceDays: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}
```

**Rendering Logic**:
- **Ahead** (< 0 days): Green badge, down arrow, `"X days ahead"`
- **Behind** (> 0 days): Red badge, up arrow, `"X days behind"`
- **On Track** (= 0 days): Gray badge, neutral icon, `"On track"`

**Color Scheme**:
```typescript
const ahead = {
  text: 'text-green-700',
  bg: 'bg-green-50',
  border: 'border-green-200',
  icon: ArrowDown,
};

const behind = {
  text: 'text-red-700',
  bg: 'bg-red-50',
  border: 'border-red-200',
  icon: ArrowUp,
};

const onTrack = {
  text: 'text-gray-700',
  bg: 'bg-gray-50',
  border: 'border-gray-200',
  icon: Minus,
};
```

**Accessibility**:
- ARIA label describing variance
- Role="status" for screen readers
- Keyboard accessible

**Pattern**: Similar to `TrendIndicator.tsx` (existing component)

**Estimated**: 100 lines, 1 hour

---

### 2. BaselineList Component

**File**: `frontend/components/baselines/BaselineList.tsx`

**Purpose**: Display table of all baselines with actions

**Props**:
```typescript
interface BaselineListProps {
  projectId: string;
}
```

**Features**:
- Table with columns: Name, Created, Active Status, Size, Actions
- "Create Baseline" button (opens dialog)
- Per-row actions:
  - "Set Active" button (if not active)
  - "Compare" button (navigates to comparison page)
  - "Delete" button (with confirmation dialog)
- Active baseline highlighted with badge
- Pagination controls if > 50 baselines
- Loading skeleton while fetching
- Error state with retry button

**Data Fetching** (TanStack Query):
```typescript
const { data, isLoading, error, refetch } = useQuery({
  queryKey: ['baselines', projectId],
  queryFn: () => getBaselines(projectId),
  refetchInterval: 30000, // Auto-refresh every 30s
});
```

**Mutations**:
```typescript
const deleteMutation = useMutation({
  mutationFn: (baselineId: string) => deleteBaseline(projectId, baselineId),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['baselines', projectId] });
    toast.success('Baseline deleted successfully');
  },
});

const activateMutation = useMutation({
  mutationFn: (baselineId: string) => setBaselineActive(projectId, baselineId),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['baselines', projectId] });
    toast.success('Baseline activated');
  },
});
```

**UI Libraries**:
- shadcn/ui Table component
- Radix Alert Dialog for delete confirmation
- lucide-react icons (Trash2, CheckCircle, Eye)

**Pattern**: Similar to `frontend/app/projects/[id]/analytics/page.tsx`

**Estimated**: 250 lines, 2 hours

---

### 3. CreateBaselineDialog Component

**File**: `frontend/components/baselines/CreateBaselineDialog.tsx`

**Purpose**: Modal form for creating new baseline

**Props**:
```typescript
interface CreateBaselineDialogProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}
```

**Form Fields**:
```typescript
interface FormData {
  name: string;        // Required, max 255 chars
  description?: string; // Optional
}
```

**Validation** (Zod):
```typescript
const schema = z.object({
  name: z.string()
    .min(1, 'Name is required')
    .max(255, 'Name must be less than 255 characters')
    .transform(s => s.trim()),
  description: z.string().optional(),
});
```

**Form Management** (React Hook Form):
```typescript
const { register, handleSubmit, formState: { errors }, reset } = useForm<FormData>({
  resolver: zodResolver(schema),
});
```

**Submit Flow**:
1. Validate form
2. Show loading spinner
3. Call `createBaseline(projectId, data)`
4. On success:
   - Close dialog
   - Reset form
   - Call `onSuccess()` callback
   - Show success toast
5. On error:
   - Show error message in dialog
   - Keep dialog open

**Error Handling**:
- 413 error → "Snapshot too large" message
- Other errors → Display server error message
- Network errors → "Connection failed" message

**UI Libraries**:
- Radix Dialog
- React Hook Form
- Zod validation
- shadcn/ui Input and Textarea

**Pattern**: Similar to existing form dialogs in project

**Estimated**: 150 lines, 1.5 hours

---

### 4. BaselineComparisonView Component

**File**: `frontend/components/baselines/BaselineComparisonView.tsx`

**Purpose**: Main comparison dashboard with variance analysis

**Props**:
```typescript
interface BaselineComparisonViewProps {
  projectId: string;
  baselineId: string;
}
```

**Layout Structure**:
```
┌─────────────────────────────────────────────────────────┐
│  Header                                                  │
│  ├─ Baseline: "Initial Plan Q4 2025"                    │
│  ├─ Created: Oct 17, 2025                               │
│  └─ Comparing to: Current State                         │
├─────────────────────────────────────────────────────────┤
│  Summary Metrics (4 cards)                              │
│  ┌──────────┬──────────┬──────────┬───────────┐         │
│  │   100    │    15    │    10    │    75     │         │
│  │  Total   │  Ahead   │  Behind  │ On Track  │         │
│  └──────────┴──────────┴──────────┴───────────┘         │
├─────────────────────────────────────────────────────────┤
│  Filters & Controls                                      │
│  [x] Show only changed tasks                            │
│  Sort by: [ Variance ▼ ]                                │
├─────────────────────────────────────────────────────────┤
│  Task Variance Table                                     │
│  ┌──────────────────┬───────────┬─────────────┐         │
│  │ Task Name        │ Variance  │ Status      │         │
│  ├──────────────────┼───────────┼─────────────┤         │
│  │ Setup Infra      │  -2 days  │ 🟢 Ahead   │         │
│  │ Build API        │  +3 days  │ 🔴 Behind  │         │
│  │ Write Tests      │   0 days  │ ⚪ Track   │         │
│  └──────────────────┴───────────┴─────────────┘         │
└─────────────────────────────────────────────────────────┘
```

**Sub-components**:
1. **Summary Cards** - 4 metric cards at top
2. **Filters** - Toggle for "show changed only", sort dropdown
3. **Variance Table** - Sortable table with task variances
4. **New/Deleted Tasks** - Separate sections below main table

**Data Fetching**:
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['baseline-comparison', baselineId, projectId],
  queryFn: () => compareBaseline(projectId, baselineId, includeUnchanged),
  refetchInterval: 30000, // Auto-refresh
});
```

**Table Features**:
- Sortable columns (by variance, task name, etc.)
- Color-coded variance cells using VarianceIndicator
- Expandable rows for detailed variance breakdown
- Filter to show only changed tasks
- Pagination if > 100 tasks

**Charts** (Optional for MVP):
- Variance distribution histogram
- Timeline comparison chart

**UI Libraries**:
- shadcn/ui Table, Card components
- Chart.js or Recharts (if charts included)
- VarianceIndicator component
- lucide-react icons

**Pattern**: Similar to `frontend/components/analytics/*` components

**Estimated**: 300 lines, 3 hours

---

## Pages

### 5. Baselines List Page

**File**: `frontend/app/projects/[id]/baselines/page.tsx`

**Purpose**: Main baselines page showing list and create button

**Structure**:
```typescript
export default function BaselinesPage({ params }: { params: { id: string } }) {
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Project Baselines</h1>
        <Button onClick={() => setDialogOpen(true)}>
          Create Baseline
        </Button>
      </div>

      <BaselineList projectId={params.id} />

      <CreateBaselineDialog
        projectId={params.id}
        isOpen={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSuccess={() => setDialogOpen(false)}
      />
    </div>
  );
}
```

**Metadata**:
```typescript
export const metadata: Metadata = {
  title: 'Baselines - SprintForge',
  description: 'Manage project baselines and track variance',
};
```

**Estimated**: 80 lines, 0.5 hours

---

### 6. Baseline Comparison Page

**File**: `frontend/app/projects/[id]/baselines/[baselineId]/compare/page.tsx`

**Purpose**: Comparison view page

**Structure**:
```typescript
export default function BaselineComparisonPage({
  params,
}: {
  params: { id: string; baselineId: string };
}) {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-6">
        <Link href={`/projects/${params.id}/baselines`}>
          ← Back to Baselines
        </Link>
      </div>

      <BaselineComparisonView
        projectId={params.id}
        baselineId={params.baselineId}
      />
    </div>
  );
}
```

**Metadata**:
```typescript
export const metadata: Metadata = {
  title: 'Baseline Comparison - SprintForge',
  description: 'Compare project baseline to current state',
};
```

**Estimated**: 60 lines, 0.5 hours

---

## Testing Strategy

### Component Tests

**Pattern**: React Testing Library + Jest

**Test Files**:
1. `__tests__/components/baselines/VarianceIndicator.test.tsx`
2. `__tests__/components/baselines/BaselineList.test.tsx`
3. `__tests__/components/baselines/CreateBaselineDialog.test.tsx`
4. `__tests__/components/baselines/BaselineComparisonView.test.tsx`

**Test Cases for VarianceIndicator**:
```typescript
describe('VarianceIndicator', () => {
  it('renders ahead status with green color', () => {
    render(<VarianceIndicator varianceDays={-2} />);
    expect(screen.getByText('2 days ahead')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveClass('bg-green-50');
  });

  it('renders behind status with red color', () => {
    render(<VarianceIndicator varianceDays={3} />);
    expect(screen.getByText('3 days behind')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveClass('bg-red-50');
  });

  it('renders on-track status with gray color', () => {
    render(<VarianceIndicator varianceDays={0} />);
    expect(screen.getByText('On track')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveClass('bg-gray-50');
  });
});
```

**Test Cases for BaselineList**:
- Renders loading state
- Renders empty state
- Renders baselines table
- Handles delete with confirmation
- Handles activate baseline
- Handles navigation to comparison

**Test Cases for CreateBaselineDialog**:
- Validates required name field
- Validates max length
- Submits successfully
- Handles errors (413, network, etc.)
- Resets form on close

**Test Cases for BaselineComparisonView**:
- Renders summary metrics
- Renders variance table
- Handles sorting
- Handles filtering
- Shows new/deleted tasks

**Coverage Target**: 85%+ per component

**Estimated**: 800 lines total, 3 hours

---

## Navigation Integration

**File to Update**: `frontend/app/projects/[id]/layout.tsx` or dashboard component

**Add Link**:
```typescript
<NavigationItem
  href={`/projects/${projectId}/baselines`}
  icon={Layers}
  label="Baselines"
/>
```

**Estimated**: 10 lines, 0.25 hours

---

## Implementation Sequence

### Day 1 (4 hours)
**Hour 0-1**: VarianceIndicator component + tests
**Hour 1-3**: BaselineList component + tests
**Hour 3-4**: CreateBaselineDialog component + tests

### Day 2 (4 hours)
**Hour 0-3**: BaselineComparisonView component + tests
**Hour 3-3.5**: Pages (list + comparison)
**Hour 3.5-4**: Navigation integration
**Hour 4**: Final testing, coverage verification

---

## Dependencies & Tools

### UI Libraries (Already in Project)
- shadcn/ui components (Table, Card, Dialog, Input, Button)
- Radix UI primitives
- Tailwind CSS for styling
- lucide-react for icons

### State Management
- TanStack Query (React Query) for server state
- React Hook Form for forms
- Zod for validation

### Testing
- Jest
- React Testing Library
- @testing-library/user-event

---

## Acceptance Criteria

### Functional
- [ ] Can create baselines from project
- [ ] Can view list of baselines
- [ ] Can set active baseline
- [ ] Can delete baselines (with confirmation)
- [ ] Can view comparison dashboard
- [ ] Variance indicators color-coded correctly
- [ ] Summary metrics calculated correctly
- [ ] New/deleted tasks identified

### Non-Functional
- [ ] All components render without errors
- [ ] Loading states displayed
- [ ] Error states handled gracefully
- [ ] Responsive design (mobile + desktop)
- [ ] 85%+ test coverage
- [ ] Accessible (ARIA, keyboard nav)
- [ ] Type-safe (no TypeScript errors)

### Documentation
- [ ] Component props documented
- [ ] API client functions documented
- [ ] README updated with baseline features
- [ ] User guide created (optional)

---

## Risks & Mitigation

### Risk 1: shadcn/ui Components Missing
**Mitigation**: Check for missing components before starting, install if needed:
```bash
npx shadcn-ui@latest add table dialog input textarea button card
```

### Risk 2: TanStack Query Not Configured
**Mitigation**: Verify QueryClientProvider in app layout, add if missing

### Risk 3: Test Coverage Below 85%
**Mitigation**: Write tests alongside components (TDD approach), not after

### Risk 4: Time Overrun on BaselineComparisonView
**Mitigation**: Start with MVP table view, add charts later if time permits

---

## Next Steps

1. **Verify Dependencies**
   ```bash
   cd frontend
   npm list @tanstack/react-query react-hook-form zod
   npx shadcn-ui@latest list
   ```

2. **Start with TDD**
   - Write VarianceIndicator test first
   - Implement component to pass test
   - Repeat for each component

3. **Incremental Integration**
   - Test each component in isolation
   - Integrate into pages
   - Test full flow end-to-end

4. **Final Verification**
   ```bash
   npm test -- --coverage
   npm run type-check
   npm run lint
   ```

---

**Status**: Ready to Begin Component Implementation
**Estimated Total**: 8 hours remaining
**Priority**: P0 - Critical for MVP
**Blocking**: None (backend complete)
