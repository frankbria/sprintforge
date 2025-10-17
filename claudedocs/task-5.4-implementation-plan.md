# Task 5.4: Baseline Management & Comparison - Implementation Plan

**Created**: 2025-10-17
**Task**: bd-5 (P0 - Critical for MVP)
**Estimated Effort**: 10-14 hours (refined from initial 8-12)
**Dependencies**: Task 5.3 ✅ (Analytics Dashboard - Completed)

---

## Executive Summary

This document provides a comprehensive implementation plan for Baseline Management & Comparison feature, including:
- Thorough architectural analysis and design decisions
- Database schema design with constraints and indexes
- Detailed API specifications
- Component architecture
- Parallelization strategy with 4 independent sub-tasks
- Risk assessment and mitigation strategies

**Key Architectural Decisions**:
1. **No restore functionality in MVP** - Focus on comparison only, add restore later if requested
2. **SERIALIZABLE transactions** for snapshot consistency
3. **Redis caching** for comparison results (5-minute TTL)
4. **Partial unique index** for active baseline constraint
5. **JSONB storage** for snapshot data (efficient, no size issues for typical projects)

---

## 🏗️ Architecture Analysis

### Core Requirements

Users need to:
1. ✅ Create named baselines (snapshots of project state)
2. ✅ Store multiple baselines with metadata
3. ✅ Compare current state against a baseline
4. ✅ Visualize differences (ahead/behind schedule)
5. ✅ Mark one baseline as "active" for comparison
6. ❌ Restore from baseline (DEFERRED to future sprint)

### Snapshot Data Structure

**What Goes in snapshot_data JSONB**:
```json
{
  "project": {
    "id": "uuid",
    "name": "Project Alpha",
    "description": "...",
    "settings": {...}
  },
  "tasks": [
    {
      "id": "uuid",
      "name": "Task 1",
      "start_date": "2025-10-20",
      "end_date": "2025-10-25",
      "duration": 5,
      "status": "not_started",
      "dependencies": ["uuid", "uuid"],
      "assigned_to": "user@example.com",
      "priority": "HIGH"
    }
  ],
  "critical_path": ["task_id_1", "task_id_2"],
  "monte_carlo_results": {
    "p50": 125.5,
    "p90": 145.2,
    "mean_duration": 130.0
  },
  "snapshot_metadata": {
    "total_tasks": 100,
    "completion_pct": 45.5,
    "snapshot_timestamp": "2025-10-17T14:30:00Z"
  }
}
```

**Rationale**:
- **Complete snapshot**: All data needed for comparison in one place
- **Immutable**: Once created, never modified
- **Self-contained**: No external references (except project_id)
- **Size-efficient**: 1000 tasks ≈ 500KB, well within JSONB limits

### Data Consistency Strategy

**Problem**: What if tasks change during snapshot creation?

**Solution**: Use SERIALIZABLE transaction isolation

```python
async def create_baseline(project_id: UUID, name: str, db: AsyncSession):
    # Start transaction with SERIALIZABLE isolation
    async with db.begin():
        db.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))

        # Fetch all project data atomically
        project = await db.get(Project, project_id)
        tasks = await db.execute(
            select(Task).where(Task.project_id == project_id)
        )

        # Build snapshot
        snapshot_data = {
            "project": project.to_dict(),
            "tasks": [task.to_dict() for task in tasks.scalars()],
            "critical_path": await calculate_critical_path(tasks),
            "snapshot_metadata": {...}
        }

        # Create baseline
        baseline = ProjectBaseline(
            project_id=project_id,
            name=name,
            snapshot_data=snapshot_data
        )
        db.add(baseline)

    return baseline
```

**Benefits**:
- Guarantees consistent snapshot (all data from same point in time)
- Safe for single-user and future multi-user scenarios
- PostgreSQL handles serialization conflicts automatically

### Comparison Algorithm

**Variance Calculation**:

```python
def compare_to_baseline(baseline_id: UUID, project_id: UUID):
    baseline = get_baseline(baseline_id)
    current_project = get_project(project_id)

    # Build lookup dictionaries
    baseline_tasks = {t['id']: t for t in baseline.snapshot_data['tasks']}
    current_tasks = {t.id: t for t in current_project.tasks}

    # Calculate variances
    task_variances = []
    for task_id, baseline_task in baseline_tasks.items():
        if task_id in current_tasks:
            current = current_tasks[task_id]
            variance = {
                'task_id': task_id,
                'task_name': current.name,
                'start_date_variance': (current.start_date - parse_date(baseline_task['start_date'])).days,
                'end_date_variance': (current.end_date - parse_date(baseline_task['end_date'])).days,
                'duration_variance': current.duration - baseline_task['duration'],
                'variance_days': (current.end_date - parse_date(baseline_task['end_date'])).days,
                'is_ahead': current.end_date < parse_date(baseline_task['end_date']),
                'is_behind': current.end_date > parse_date(baseline_task['end_date']),
                'status_changed': baseline_task['status'] != current.status,
                'dependencies_changed': set(baseline_task['dependencies']) != set(current.dependency_ids)
            }
            task_variances.append(variance)

    # Find new/deleted tasks
    new_tasks = [t for t in current_tasks.values() if t.id not in baseline_tasks]
    deleted_tasks = [t for t in baseline_tasks.values() if t['id'] not in current_tasks]

    # Calculate summary
    summary = {
        'total_tasks': len(current_tasks),
        'tasks_ahead': sum(1 for v in task_variances if v['is_ahead']),
        'tasks_behind': sum(1 for v in task_variances if v['is_behind']),
        'tasks_on_track': sum(1 for v in task_variances if v['variance_days'] == 0),
        'avg_variance_days': mean([v['variance_days'] for v in task_variances]),
        'critical_path_variance_days': sum([
            v['variance_days']
            for v in task_variances
            if v['task_id'] in current_project.critical_path
        ])
    }

    return {
        'baseline': baseline.to_summary_dict(),
        'summary': summary,
        'task_variances': task_variances,
        'new_tasks': new_tasks,
        'deleted_tasks': deleted_tasks
    }
```

**Performance**: O(n) where n = number of tasks. Cached in Redis for 5 minutes.

### Active Baseline Constraint

**Requirement**: Only one baseline per project can be "active"

**Implementation**: PostgreSQL partial unique index

```sql
CREATE UNIQUE INDEX unique_active_baseline_per_project
ON project_baselines (project_id)
WHERE is_active = true;
```

**Activation Logic**:
```python
async def set_baseline_active(baseline_id: UUID, project_id: UUID, db: AsyncSession):
    async with db.begin():
        # Deactivate all baselines for this project
        await db.execute(
            update(ProjectBaseline)
            .where(ProjectBaseline.project_id == project_id)
            .values(is_active=False)
        )

        # Activate the selected baseline
        await db.execute(
            update(ProjectBaseline)
            .where(ProjectBaseline.id == baseline_id)
            .values(is_active=True)
        )
```

**Benefits**:
- Database-enforced constraint (cannot be violated)
- Atomic operation (both updates in same transaction)
- No race conditions

### Caching Strategy

**Cache Key**: `baseline_comparison:{baseline_id}:{project_updated_at_timestamp}`

**Invalidation**: Automatic via timestamp in key
- Project changes → updated_at changes → new cache key
- Old cache entries expire after 5 minutes (TTL)
- No manual invalidation needed

**Implementation**:
```python
async def get_cached_comparison(baseline_id: UUID, project: Project, redis: Redis):
    cache_key = f"baseline_comparison:{baseline_id}:{project.updated_at.timestamp()}"

    # Try cache
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Calculate comparison
    comparison = await compare_to_baseline(baseline_id, project.id)

    # Cache result (5 min TTL)
    await redis.setex(cache_key, 300, json.dumps(comparison))

    return comparison
```

---

## 📊 Database Schema

### Table Definition

```sql
CREATE TABLE project_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    snapshot_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT false,
    snapshot_size_bytes INTEGER,

    -- Constraints
    CONSTRAINT baseline_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT snapshot_size_limit CHECK (snapshot_size_bytes < 10485760)  -- 10MB limit
);
```

### Indexes

```sql
-- Fast baseline lookups by project
CREATE INDEX idx_baselines_project_id ON project_baselines(project_id);

-- Order baselines by creation date
CREATE INDEX idx_baselines_created_at ON project_baselines(created_at DESC);

-- Enforce single active baseline per project
CREATE UNIQUE INDEX unique_active_baseline_per_project
    ON project_baselines(project_id)
    WHERE is_active = true;

-- Enable JSONB queries (if needed)
CREATE INDEX idx_baselines_snapshot_data_gin
    ON project_baselines USING GIN(snapshot_data);
```

### Triggers

```sql
-- Automatically calculate snapshot size
CREATE OR REPLACE FUNCTION update_snapshot_size()
RETURNS TRIGGER AS $$
BEGIN
    NEW.snapshot_size_bytes := length(NEW.snapshot_data::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER baseline_snapshot_size_trigger
    BEFORE INSERT OR UPDATE ON project_baselines
    FOR EACH ROW
    EXECUTE FUNCTION update_snapshot_size();
```

### SQLAlchemy Model

```python
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class ProjectBaseline(BaseModel):
    __tablename__ = "project_baselines"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    snapshot_data = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=False)
    snapshot_size_bytes = Column(Integer)

    # Relationships
    project = relationship("Project", back_populates="baselines")

    # Constraints
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="baseline_name_not_empty"),
        CheckConstraint("snapshot_size_bytes < 10485760", name="snapshot_size_limit"),
    )

    def to_summary_dict(self):
        """Lightweight dict without snapshot data"""
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "snapshot_size_bytes": self.snapshot_size_bytes
        }

    def to_full_dict(self):
        """Full dict with snapshot data"""
        return {
            **self.to_summary_dict(),
            "snapshot_data": self.snapshot_data
        }
```

---

## 🔌 API Specification

### Endpoints Overview

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/projects/{id}/baselines` | Create new baseline |
| GET | `/api/v1/projects/{id}/baselines` | List all baselines |
| GET | `/api/v1/projects/{id}/baselines/{baseline_id}` | Get baseline details |
| DELETE | `/api/v1/projects/{id}/baselines/{baseline_id}` | Delete baseline |
| PATCH | `/api/v1/projects/{id}/baselines/{baseline_id}/activate` | Set as active |
| GET | `/api/v1/projects/{id}/baselines/{baseline_id}/compare` | Compare to current |

### Detailed Specifications

#### 1. Create Baseline

**POST** `/api/v1/projects/{project_id}/baselines`

**Request Body**:
```json
{
  "name": "Initial Plan Q4 2025",
  "description": "Baseline created before Sprint 5 starts"
}
```

**Response**: 201 Created
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "name": "Initial Plan Q4 2025",
  "description": "Baseline created before Sprint 5 starts",
  "created_at": "2025-10-17T14:30:00Z",
  "is_active": false,
  "snapshot_size_bytes": 458392
}
```

**Errors**:
- 400: Name is empty or invalid
- 404: Project not found
- 413: Snapshot size exceeds 10MB limit
- 500: Snapshot creation failed

#### 2. List Baselines

**GET** `/api/v1/projects/{project_id}/baselines`

**Query Parameters**:
- `page` (int, default=1): Page number
- `limit` (int, default=50): Items per page
- `sort` (string, default="created_at_desc"): Sort order

**Response**: 200 OK
```json
{
  "baselines": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Initial Plan Q4 2025",
      "created_at": "2025-10-17T14:30:00Z",
      "is_active": true,
      "snapshot_size_bytes": 458392
    },
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "name": "Mid-Sprint Checkpoint",
      "created_at": "2025-10-20T10:15:00Z",
      "is_active": false,
      "snapshot_size_bytes": 492103
    }
  ],
  "total": 2,
  "page": 1,
  "limit": 50
}
```

**Note**: Does NOT include `snapshot_data` in list (too large)

#### 3. Get Baseline Details

**GET** `/api/v1/projects/{project_id}/baselines/{baseline_id}`

**Response**: 200 OK
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "name": "Initial Plan Q4 2025",
  "description": "Baseline created before Sprint 5 starts",
  "created_at": "2025-10-17T14:30:00Z",
  "is_active": true,
  "snapshot_size_bytes": 458392,
  "snapshot_data": {
    "project": {...},
    "tasks": [...],
    "critical_path": [...],
    "snapshot_metadata": {...}
  }
}
```

**Errors**:
- 404: Baseline not found

#### 4. Delete Baseline

**DELETE** `/api/v1/projects/{project_id}/baselines/{baseline_id}`

**Response**: 204 No Content

**Errors**:
- 404: Baseline not found

#### 5. Set Baseline Active

**PATCH** `/api/v1/projects/{project_id}/baselines/{baseline_id}/activate`

**Request Body**: (empty)

**Response**: 200 OK
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "is_active": true,
  "message": "Baseline activated successfully"
}
```

**Behavior**: Automatically deactivates all other baselines for this project

**Errors**:
- 404: Baseline not found

#### 6. Compare to Current State

**GET** `/api/v1/projects/{project_id}/baselines/{baseline_id}/compare`

**Query Parameters**:
- `include_unchanged` (bool, default=false): Include tasks with no variance

**Response**: 200 OK
```json
{
  "baseline": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Initial Plan Q4 2025",
    "created_at": "2025-10-17T14:30:00Z"
  },
  "comparison_date": "2025-10-20T16:45:00Z",
  "summary": {
    "total_tasks": 100,
    "tasks_ahead": 15,
    "tasks_behind": 10,
    "tasks_on_track": 75,
    "avg_variance_days": -0.5,
    "critical_path_variance_days": 3.0
  },
  "task_variances": [
    {
      "task_id": "abc-123",
      "task_name": "Setup Infrastructure",
      "variance_days": -2,
      "is_ahead": true,
      "is_behind": false,
      "start_date_variance": -1,
      "end_date_variance": -2,
      "duration_variance": 0,
      "status_changed": true,
      "dependencies_changed": false
    }
  ],
  "new_tasks": [
    {
      "task_id": "xyz-789",
      "task_name": "Emergency Security Patch",
      "added_after_baseline": true
    }
  ],
  "deleted_tasks": [
    {
      "task_id": "old-456",
      "task_name": "Deprecated Feature",
      "existed_in_baseline": true
    }
  ]
}
```

**Caching**: Results cached for 5 minutes in Redis

**Errors**:
- 404: Baseline or project not found

---

## 🎨 Frontend Architecture

### Component Structure

```
frontend/
├── app/
│   └── projects/
│       └── [id]/
│           └── baselines/
│               ├── page.tsx                    # Main baselines list page
│               └── [baselineId]/
│                   └── compare/
│                       └── page.tsx            # Comparison view page
├── components/
│   └── baselines/
│       ├── BaselineList.tsx                    # List of all baselines
│       ├── CreateBaselineDialog.tsx            # Create baseline modal
│       ├── BaselineComparisonView.tsx          # Main comparison UI
│       ├── VarianceIndicators.tsx              # Reusable variance badges
│       └── index.ts                            # Barrel exports
├── lib/
│   └── api/
│       └── baselines.ts                        # API client functions
└── types/
    └── baseline.ts                             # TypeScript type definitions
```

### Component Specifications

#### 1. BaselineList.tsx

**Purpose**: Display all baselines for a project

**Props**:
```typescript
interface BaselineListProps {
  projectId: string;
}
```

**Features**:
- Table display with columns: Name, Created Date, Active Status, Actions
- "Create Baseline" button (opens CreateBaselineDialog)
- "Set Active" button (per baseline)
- "Delete" button (per baseline, with confirmation)
- "View Comparison" button (navigates to comparison view)
- Active baseline highlighted with badge
- Pagination if > 50 baselines

**TanStack Query**:
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['baselines', projectId],
  queryFn: () => getBaselines(projectId)
});
```

#### 2. CreateBaselineDialog.tsx

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
- Name (required, text input, max 255 chars)
- Description (optional, textarea)

**Validation**:
- Name cannot be empty
- Name trimmed of whitespace

**Submit Flow**:
1. Validate form
2. POST to `/api/v1/projects/{id}/baselines`
3. Show loading spinner
4. On success: Close dialog, refresh baseline list, show toast
5. On error: Display error message

**Technologies**:
- Radix Dialog for modal
- React Hook Form for form management
- Zod for validation schema

#### 3. BaselineComparisonView.tsx

**Purpose**: Main comparison UI showing variance analysis

**Props**:
```typescript
interface BaselineComparisonViewProps {
  projectId: string;
  baselineId: string;
}
```

**Layout**:
```
┌─────────────────────────────────────────┐
│  Baseline: Initial Plan Q4 2025        │
│  Created: Oct 17, 2025                  │
│  Comparing to: Current State            │
├─────────────────────────────────────────┤
│  Summary Metrics                        │
│  ┌──────┬──────┬────────┬──────────┐   │
│  │ 100  │  15  │   10   │   75     │   │
│  │Total │Ahead │Behind  │On Track  │   │
│  └──────┴──────┴────────┴──────────┘   │
├─────────────────────────────────────────┤
│  Task Variance Table                    │
│  ┌─────────────┬──────────┬─────────┐  │
│  │ Task Name   │ Variance │ Status  │  │
│  ├─────────────┼──────────┼─────────┤  │
│  │ Setup Infra │  -2 days │  ✅     │  │
│  │ Build API   │  +3 days │  ⚠️     │  │
│  └─────────────┴──────────┴─────────┘  │
└─────────────────────────────────────────┘
```

**Features**:
- Summary cards at top (total, ahead, behind, on track)
- Filter toggle: "Show only changed tasks"
- Sortable table (by variance, task name, etc.)
- Color-coded variance indicators
- Expandable rows for detailed variance breakdown

**TanStack Query**:
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['baseline-comparison', baselineId, projectId],
  queryFn: () => compareBaseline(projectId, baselineId),
  refetchInterval: 30000  // Auto-refresh every 30s
});
```

#### 4. VarianceIndicators.tsx

**Purpose**: Reusable component for displaying variance

**Props**:
```typescript
interface VarianceIndicatorProps {
  varianceDays: number;
  size?: 'sm' | 'md' | 'lg';
}
```

**Rendering Logic**:
```typescript
function VarianceIndicator({ varianceDays, size = 'md' }: VarianceIndicatorProps) {
  const isAhead = varianceDays < 0;
  const isBehind = varianceDays > 0;
  const isOnTrack = varianceDays === 0;

  const colorClass = isAhead ? 'bg-green-100 text-green-800' :
                     isBehind ? 'bg-red-100 text-red-800' :
                     'bg-gray-100 text-gray-800';

  const icon = isAhead ? '↓' : isBehind ? '↑' : '→';

  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 ${colorClass}`}>
      <span>{icon}</span>
      <span>{Math.abs(varianceDays)} days</span>
    </span>
  );
}
```

### TypeScript Types

```typescript
// types/baseline.ts

export interface Baseline {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  created_at: string;
  is_active: boolean;
  snapshot_size_bytes: number;
}

export interface BaselineDetail extends Baseline {
  snapshot_data: {
    project: object;
    tasks: Task[];
    critical_path: string[];
    snapshot_metadata: object;
  };
}

export interface TaskVariance {
  task_id: string;
  task_name: string;
  variance_days: number;
  is_ahead: boolean;
  is_behind: boolean;
  start_date_variance: number;
  end_date_variance: number;
  duration_variance: number;
  status_changed: boolean;
  dependencies_changed: boolean;
}

export interface ComparisonSummary {
  total_tasks: number;
  tasks_ahead: number;
  tasks_behind: number;
  tasks_on_track: number;
  avg_variance_days: number;
  critical_path_variance_days: number;
}

export interface BaselineComparison {
  baseline: {
    id: string;
    name: string;
    created_at: string;
  };
  comparison_date: string;
  summary: ComparisonSummary;
  task_variances: TaskVariance[];
  new_tasks: any[];
  deleted_tasks: any[];
}
```

### API Client

```typescript
// lib/api/baselines.ts

import { apiClient } from './client';
import type { Baseline, BaselineDetail, BaselineComparison } from '@/types/baseline';

export async function getBaselines(projectId: string): Promise<Baseline[]> {
  const response = await apiClient.get(`/projects/${projectId}/baselines`);
  return response.data.baselines;
}

export async function getBaseline(projectId: string, baselineId: string): Promise<BaselineDetail> {
  const response = await apiClient.get(`/projects/${projectId}/baselines/${baselineId}`);
  return response.data;
}

export async function createBaseline(
  projectId: string,
  data: { name: string; description?: string }
): Promise<Baseline> {
  const response = await apiClient.post(`/projects/${projectId}/baselines`, data);
  return response.data;
}

export async function deleteBaseline(projectId: string, baselineId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}/baselines/${baselineId}`);
}

export async function setBaselineActive(projectId: string, baselineId: string): Promise<void> {
  await apiClient.patch(`/projects/${projectId}/baselines/${baselineId}/activate`);
}

export async function compareBaseline(
  projectId: string,
  baselineId: string
): Promise<BaselineComparison> {
  const response = await apiClient.get(`/projects/${projectId}/baselines/${baselineId}/compare`);
  return response.data;
}
```

---

## 🔄 Parallelization Strategy

### Task Breakdown (4 Sub-Issues)

#### Sub-task A: Database & Models (bd-13)

**Assignee**: Backend specialist (or subagent)
**Estimated**: 2-3 hours
**Dependencies**: None

**Deliverables**:
1. Alembic migration for `project_baselines` table
2. SQLAlchemy `ProjectBaseline` model
3. Pydantic schemas:
   - `CreateBaselineRequest`
   - `BaselineResponse`
   - `BaselineDetailResponse`
   - `ComparisonResponse`
   - `TaskVarianceSchema`
4. Unit tests for model validation
5. Database constraints and indexes

**Acceptance Criteria**:
- [ ] Migration applies cleanly
- [ ] Model has all required fields and relationships
- [ ] Schemas validate correctly
- [ ] Unique index on active baseline works
- [ ] Size constraint enforced
- [ ] 85%+ test coverage

**Files to Create**:
- `backend/alembic/versions/XXXX_add_project_baselines.py`
- `backend/app/models/baseline.py`
- `backend/app/schemas/baseline.py`
- `backend/tests/models/test_baseline.py`
- `backend/tests/schemas/test_baseline.py`

---

#### Sub-task B: Baseline Service (bd-14)

**Assignee**: Backend specialist (or subagent)
**Estimated**: 3-4 hours
**Dependencies**: Sub-task A (can use stubs initially)

**Deliverables**:
1. `BaselineService` class
2. Methods:
   - `create_baseline(project_id, name, description, db)`
   - `compare_to_baseline(baseline_id, project_id, db, redis)`
   - `get_variance_analysis(baseline_snapshot, current_project)`
   - `_calculate_task_variance(baseline_task, current_task)`
   - `_build_snapshot_data(project, tasks, db)`
3. Redis caching integration
4. SERIALIZABLE transaction handling
5. Comprehensive unit tests
6. Error handling (snapshot too large, project not found, etc.)

**Acceptance Criteria**:
- [ ] Snapshot creates consistent data
- [ ] Comparison algorithm accurate
- [ ] Variance calculations correct
- [ ] Redis caching works (5 min TTL)
- [ ] Handles edge cases (empty project, deleted tasks)
- [ ] 85%+ test coverage
- [ ] All service methods have docstrings

**Files to Create**:
- `backend/app/services/baseline_service.py`
- `backend/tests/services/test_baseline_service.py`

**Test Cases**:
- Create baseline with 0 tasks
- Create baseline with 1000 tasks
- Compare baseline where all tasks unchanged
- Compare baseline with new tasks added
- Compare baseline with tasks deleted
- Compare baseline with variances
- Cache hit scenario
- Cache miss scenario

---

#### Sub-task C: API Endpoints (bd-15)

**Assignee**: Backend specialist (or subagent)
**Estimated**: 2-3 hours
**Dependencies**: Sub-tasks A & B (can mock initially)

**Deliverables**:
1. `baselines.py` router with 6 endpoints
2. Request validation (Pydantic)
3. Error handling:
   - 404: Baseline/project not found
   - 400: Invalid request body
   - 409: Conflict (e.g., constraint violation)
   - 413: Snapshot too large
4. OpenAPI documentation (docstrings)
5. Integration tests for all endpoints
6. Authentication & authorization checks

**Acceptance Criteria**:
- [ ] All 6 endpoints functional
- [ ] Request/response schemas validated
- [ ] Proper HTTP status codes
- [ ] Error messages clear and actionable
- [ ] OpenAPI docs complete
- [ ] 85%+ test coverage
- [ ] Only project owner can manage baselines

**Files to Create**:
- `backend/app/api/endpoints/baselines.py`
- `backend/tests/api/endpoints/test_baselines.py`

**Test Cases**:
- Create baseline successfully
- Create baseline with empty name (400)
- Create baseline for non-existent project (404)
- List baselines (pagination)
- Get baseline detail
- Delete baseline
- Delete non-existent baseline (404)
- Activate baseline
- Activate baseline deactivates others
- Compare to baseline
- Compare non-existent baseline (404)

---

#### Sub-task D: Frontend Components (bd-16)

**Assignee**: Frontend specialist (or subagent)
**Estimated**: 3-4 hours
**Dependencies**: Sub-task C (can use MSW mocks initially)

**Deliverables**:
1. Components:
   - `BaselineList.tsx`
   - `CreateBaselineDialog.tsx`
   - `BaselineComparisonView.tsx`
   - `VarianceIndicators.tsx`
2. Pages:
   - `app/projects/[id]/baselines/page.tsx`
   - `app/projects/[id]/baselines/[baselineId]/compare/page.tsx`
3. API client (`lib/api/baselines.ts`)
4. TypeScript types (`types/baseline.ts`)
5. Component tests (React Testing Library)
6. Navigation integration (add link from project dashboard)

**Acceptance Criteria**:
- [ ] All components render correctly
- [ ] Forms validate input
- [ ] API integration works
- [ ] Loading states shown
- [ ] Error states handled
- [ ] Responsive design (mobile + desktop)
- [ ] 85%+ test coverage
- [ ] Accessible (ARIA labels, keyboard nav)

**Files to Create**:
- `frontend/components/baselines/BaselineList.tsx`
- `frontend/components/baselines/CreateBaselineDialog.tsx`
- `frontend/components/baselines/BaselineComparisonView.tsx`
- `frontend/components/baselines/VarianceIndicators.tsx`
- `frontend/components/baselines/index.ts`
- `frontend/app/projects/[id]/baselines/page.tsx`
- `frontend/app/projects/[id]/baselines/[baselineId]/compare/page.tsx`
- `frontend/lib/api/baselines.ts`
- `frontend/types/baseline.ts`
- `frontend/__tests__/components/baselines/*.test.tsx`

**Test Cases**:
- BaselineList renders baselines
- CreateBaselineDialog validates form
- CreateBaselineDialog submits successfully
- BaselineComparisonView displays variances
- VarianceIndicators show correct colors
- Loading states work
- Error states work

---

### Execution Order

**Recommended Sequence**:
```
Day 1:
  Hour 0-3:  Sub-task A (Database & Models) - SEQUENTIAL
  Hour 3-7:  Sub-task B (Service) - SEQUENTIAL (depends on A)

Day 2:
  Hour 0-3:  Sub-task C (API Endpoints) - Can start in parallel with D using mocks
  Hour 0-4:  Sub-task D (Frontend) - Can start in parallel with C using MSW

  Hour 7-10: Integration & Testing - All components together
  Hour 10:   Final verification, documentation
```

**Parallel Opportunities**:
- Sub-tasks C and D can run in parallel if using mocks/stubs
- Backend tests and frontend tests can run in parallel
- Documentation can be written concurrently with implementation

**Integration Points**:
1. After A completes: B can use real models
2. After B completes: C can use real service
3. After C completes: D can use real API (remove MSW mocks)
4. Final integration: Run full E2E tests

---

## ⚠️ Risk Assessment & Mitigation

### Risk 1: JSONB Size Limits

**Risk**: Very large projects (10,000+ tasks) might exceed reasonable JSONB size

**Likelihood**: Low (most projects < 1000 tasks)

**Impact**: Medium (snapshot creation fails)

**Mitigation**:
- Database constraint: MAX 10MB per snapshot
- Validation before snapshot creation
- If needed: Implement compression or external storage (S3) in future

**Monitoring**: Track `snapshot_size_bytes` in database

---

### Risk 2: Comparison Performance

**Risk**: Comparison calculation slow for large projects

**Likelihood**: Medium (depends on project size)

**Impact**: Low (caching mitigates)

**Mitigation**:
- Redis caching (5 min TTL)
- Async comparison calculation
- Pagination for task variance list
- Consider background job for very large projects (future)

**Monitoring**: Add timing metrics to comparison endpoint

---

### Risk 3: Concurrent Baseline Creation

**Risk**: Two users create baseline simultaneously for same project

**Likelihood**: Very Low (single-user MVP)

**Impact**: Low (both baselines created, no data loss)

**Mitigation**:
- SERIALIZABLE transaction prevents inconsistent snapshots
- Unique constraint on active baseline prevents conflicts
- No additional mitigation needed for MVP

**Future**: Add optimistic locking or advisory locks for multi-user

---

### Risk 4: Baseline Immutability Violation

**Risk**: Bug allows modifying snapshot_data after creation

**Likelihood**: Low (code review + tests)

**Impact**: High (comparison integrity broken)

**Mitigation**:
- No UPDATE endpoint for snapshot_data
- Database trigger to block updates (optional)
- Comprehensive integration tests
- Code review focuses on immutability

**Monitoring**: Audit log for any baseline updates

---

### Risk 5: Frontend State Management Complexity

**Risk**: Managing baseline list, active state, comparison view becomes complex

**Likelihood**: Medium (typical React state management)

**Impact**: Low (user experience degraded)

**Mitigation**:
- Use TanStack Query for server state
- Clear component boundaries
- Comprehensive component tests
- Follow established patterns from Task 5.3

**Monitoring**: User feedback on UI responsiveness

---

## ✅ Testing Strategy

### Backend Tests

**Unit Tests** (Target: 90%+ coverage):
- Model validation
- Service methods (snapshot, comparison, variance calculation)
- Cache key generation
- Error handling

**Integration Tests** (Target: 85%+ coverage):
- API endpoints (all 6 endpoints)
- Database transactions (SERIALIZABLE)
- Redis caching
- Constraint enforcement (active baseline, size limit)

**Performance Tests**:
- Snapshot creation with 1000 tasks
- Comparison calculation with 1000 tasks
- Concurrent baseline creation (stress test)

### Frontend Tests

**Component Tests** (Target: 85%+ coverage):
- BaselineList rendering
- CreateBaselineDialog form validation
- BaselineComparisonView variance display
- VarianceIndicators color logic

**Integration Tests**:
- API client functions
- TanStack Query integration
- Navigation flows

**E2E Tests** (Optional):
- Create baseline → View list → Compare → Delete
- Set active baseline → UI updates

---

## 📚 Documentation Requirements

### Technical Documentation

1. **API Documentation** (OpenAPI)
   - All endpoints documented
   - Request/response schemas
   - Error codes and meanings

2. **Database Documentation**
   - Schema diagram
   - Index explanations
   - Migration guide

3. **Component Documentation**
   - Component props and usage
   - Storybook entries (optional)

### User Documentation

1. **Feature Guide**
   - How to create a baseline
   - How to compare baselines
   - Understanding variance indicators

2. **Use Cases**
   - Track progress vs original plan
   - Identify schedule slippage
   - Analyze project evolution

---

## 🎯 Acceptance Criteria (Final)

### Functional Requirements

- [ ] Users can create named baselines
- [ ] Users can view list of all baselines for a project
- [ ] Users can delete baselines
- [ ] Only one baseline per project can be "active"
- [ ] Comparison shows clear variance indicators (green=ahead, red=behind)
- [ ] New tasks and deleted tasks identified in comparison
- [ ] Summary metrics calculated correctly
- [ ] Baseline data is immutable once created

### Non-Functional Requirements

- [ ] Snapshot creation completes in <3 seconds (1000 tasks)
- [ ] Comparison calculation completes in <2 seconds (1000 tasks)
- [ ] Comparison results cached for 5 minutes
- [ ] 85%+ test coverage (backend and frontend)
- [ ] 100% test pass rate
- [ ] All code follows project style guidelines
- [ ] API documentation complete

### Documentation Requirements

- [ ] Implementation plan documented (this file)
- [ ] API endpoints documented in OpenAPI
- [ ] Database schema documented
- [ ] User guide created
- [ ] CLAUDE.md updated if needed

---

## 📝 Next Steps

1. **Review this plan** with team/stakeholders
2. **Create beads sub-issues** (bd-13, bd-14, bd-15, bd-16)
3. **Assign sub-tasks** to team members or subagents
4. **Set up branch** (`feature/baseline-management`)
5. **Begin implementation** starting with Sub-task A
6. **Daily integration** as sub-tasks complete
7. **Final testing** and documentation
8. **Create PR** for review
9. **Merge to main** after approval

---

**Document Status**: ✅ Complete and Ready for Implementation
**Total Estimated Hours**: 10-14 hours
**Parallelization Potential**: High (4 independent sub-tasks)
**Risk Level**: Low (well-understood domain, proven patterns)
**Dependencies**: Task 5.3 ✅ (Analytics Dashboard - Completed)
