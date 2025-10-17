# Task 5.3 Implementation Breakdown: Project Analytics Dashboard

**Created**: 2025-10-17
**Beads Issue**: bd-4
**Status**: In Progress
**Estimated Effort**: 12-16 hours

---

## 🎯 Implementation Strategy

This task will be implemented using **parallel subagent execution** with the following strategy:

1. **Backend Analytics Service** (Subagent A) - Core calculation logic
2. **Backend API Endpoints** (Subagent B) - REST API layer
3. **Frontend Dashboard Page** (Subagent C) - Main analytics view
4. **Frontend Chart Components** (Subagent D) - Visualization components

Each subagent will work independently and then integration will bring everything together.

---

## 📦 Subagent A: Backend Analytics Service

**File**: `app/services/analytics_service.py`
**Dependencies**: Existing models (Project, SimulationResult), scheduler services
**Estimated Effort**: 4-6 hours

### Responsibilities

Implement core analytics calculation logic that aggregates and analyzes project data.

### Functions to Implement

```python
class AnalyticsService:
    """Service for calculating project analytics and metrics."""

    async def calculate_project_health_score(
        self,
        project_id: UUID,
        db: AsyncSession
    ) -> float:
        """
        Calculate overall project health score (0-100).

        Factors:
        - Schedule adherence (30%): Are we on track vs baseline?
        - Critical path stability (25%): How often does critical path change?
        - Resource utilization (20%): Are resources properly allocated?
        - Risk level (15%): Monte Carlo P90 vs P50 spread
        - Completion rate (10%): Sprint velocity trend

        Returns:
            float: Health score 0-100 (100 = excellent health)
        """
        pass

    async def get_critical_path_metrics(
        self,
        project_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get critical path analysis metrics.

        Returns:
            {
                "critical_tasks": List[task_ids],
                "total_duration": int,  # days
                "float_time": Dict[task_id, float_days],
                "risk_tasks": List[task_ids],  # high risk items
                "path_stability_score": float  # 0-100
            }
        """
        pass

    async def get_resource_utilization(
        self,
        project_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Calculate resource allocation and utilization metrics.

        Returns:
            {
                "total_resources": int,
                "allocated_resources": int,
                "utilization_pct": float,
                "over_allocated": List[resource_info],
                "under_utilized": List[resource_info],
                "resource_timeline": Dict[date, utilization_pct]
            }
        """
        pass

    async def get_simulation_summary(
        self,
        project_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Aggregate Monte Carlo simulation results.

        Returns:
            {
                "percentiles": {
                    "p10": float,
                    "p50": float,
                    "p75": float,
                    "p90": float,
                    "p95": float
                },
                "mean_duration": float,
                "std_deviation": float,
                "risk_level": str,  # "low", "medium", "high"
                "confidence_80pct_range": [min, max],
                "histogram_data": List[{bucket: count}]
            }
        """
        pass

    async def get_progress_metrics(
        self,
        project_id: UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Calculate progress tracking metrics.

        Returns:
            {
                "completion_pct": float,
                "tasks_completed": int,
                "tasks_total": int,
                "on_time_pct": float,
                "delayed_tasks": int,
                "burn_rate": float,  # tasks per day
                "estimated_completion_date": date,
                "variance_from_plan": int  # days ahead/behind
            }
        """
        pass
```

### Testing Requirements

- Unit tests for each calculation function
- Mock data with known outcomes
- Edge cases: empty projects, single-task projects, complex dependencies
- Performance tests with large projects (1000+ tasks)
- Test Redis caching integration

### Acceptance Criteria

- [ ] All 5 functions implemented with type hints
- [ ] Docstrings for all public methods
- [ ] Unit tests with 85%+ coverage
- [ ] Performance: calculations complete in <500ms for 1000 tasks
- [ ] Redis caching implemented (5-minute TTL)

---

## 📦 Subagent B: Backend API Endpoints

**File**: `app/api/endpoints/analytics.py`
**Dependencies**: AnalyticsService, authentication
**Estimated Effort**: 2-3 hours

### Responsibilities

Create REST API endpoints that expose analytics data to the frontend.

### Endpoints to Implement

```python
@router.get("/projects/{project_id}/analytics/overview")
async def get_analytics_overview(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    analytics_service: AnalyticsService = Depends()
) -> AnalyticsOverviewResponse:
    """
    Get comprehensive analytics overview.

    Returns all key metrics in a single response:
    - Health score
    - Critical path summary
    - Resource utilization summary
    - Latest simulation results
    - Progress metrics
    """
    pass

@router.get("/projects/{project_id}/analytics/critical-path")
async def get_critical_path_analytics(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    analytics_service: AnalyticsService = Depends()
) -> CriticalPathResponse:
    """Get detailed critical path analysis."""
    pass

@router.get("/projects/{project_id}/analytics/resources")
async def get_resource_analytics(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    analytics_service: AnalyticsService = Depends()
) -> ResourceUtilizationResponse:
    """Get resource utilization metrics."""
    pass

@router.get("/projects/{project_id}/analytics/simulation")
async def get_simulation_analytics(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    analytics_service: AnalyticsService = Depends()
) -> SimulationSummaryResponse:
    """Get Monte Carlo simulation summary."""
    pass

@router.get("/projects/{project_id}/analytics/progress")
async def get_progress_analytics(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    analytics_service: AnalyticsService = Depends()
) -> ProgressMetricsResponse:
    """Get progress tracking metrics."""
    pass
```

### Pydantic Response Models

```python
class AnalyticsOverviewResponse(BaseModel):
    health_score: float
    critical_path_summary: Dict[str, Any]
    resource_summary: Dict[str, Any]
    simulation_summary: Dict[str, Any]
    progress_summary: Dict[str, Any]
    generated_at: datetime

class CriticalPathResponse(BaseModel):
    critical_tasks: List[UUID]
    total_duration: int
    float_time: Dict[str, float]
    risk_tasks: List[UUID]
    path_stability_score: float

class ResourceUtilizationResponse(BaseModel):
    total_resources: int
    allocated_resources: int
    utilization_pct: float
    over_allocated: List[Dict]
    under_utilized: List[Dict]
    resource_timeline: Dict[str, float]

class SimulationSummaryResponse(BaseModel):
    percentiles: Dict[str, float]
    mean_duration: float
    std_deviation: float
    risk_level: str
    confidence_80pct_range: List[float]
    histogram_data: List[Dict]

class ProgressMetricsResponse(BaseModel):
    completion_pct: float
    tasks_completed: int
    tasks_total: int
    on_time_pct: float
    delayed_tasks: int
    burn_rate: float
    estimated_completion_date: date
    variance_from_plan: int
```

### Testing Requirements

- API endpoint tests with mock analytics service
- Authentication/authorization tests
- Error handling tests (project not found, permission denied)
- Response validation tests
- Performance tests (response time <100ms excluding calculations)

### Acceptance Criteria

- [ ] All 5 endpoints implemented
- [ ] Pydantic models for all responses
- [ ] OpenAPI documentation auto-generated
- [ ] Integration tests with 85%+ coverage
- [ ] Proper error handling and status codes

---

## 📦 Subagent C: Frontend Dashboard Page

**File**: `frontend/app/projects/[id]/analytics/page.tsx`
**Dependencies**: TanStack Query, API client, chart library
**Estimated Effort**: 3-4 hours

### Responsibilities

Create the main analytics dashboard page with tab navigation and real-time data refresh.

### Component Structure

```typescript
// frontend/app/projects/[id]/analytics/page.tsx

'use client'

import { useParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'

// Chart components (from Subagent D)
import ProjectHealthCard from '@/components/analytics/ProjectHealthCard'
import CriticalPathVisualization from '@/components/analytics/CriticalPathVisualization'
import ResourceUtilizationChart from '@/components/analytics/ResourceUtilizationChart'
import SimulationResultsChart from '@/components/analytics/SimulationResultsChart'
import ProgressTracking from '@/components/analytics/ProgressTracking'
import MetricsGrid from '@/components/analytics/MetricsGrid'

export default function AnalyticsPage() {
  const params = useParams()
  const projectId = params.id as string

  // Fetch analytics data with auto-refresh every 30 seconds
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['analytics', projectId],
    queryFn: () => fetchAnalytics(projectId),
    refetchInterval: 30000, // 30 seconds
    staleTime: 10000, // Consider stale after 10 seconds
  })

  if (isLoading) {
    return <AnalyticsLoadingSkeleton />
  }

  if (error) {
    return <AnalyticsErrorState error={error} onRetry={refetch} />
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Project Analytics</h1>
          <p className="text-muted-foreground">
            Comprehensive insights into project health and performance
          </p>
        </div>
        <Button onClick={() => refetch()} variant="outline">
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Health Score Overview */}
      <ProjectHealthCard healthScore={data.health_score} />

      {/* Key Metrics Grid */}
      <MetricsGrid metrics={data} />

      {/* Tabbed Analytics Views */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="critical-path">Critical Path</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
          <TabsTrigger value="simulation">Simulation</TabsTrigger>
          <TabsTrigger value="progress">Progress</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Summary of all analytics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Critical Path</CardTitle>
              </CardHeader>
              <CardContent>
                <CriticalPathSummary data={data.critical_path_summary} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Resources</CardTitle>
              </CardHeader>
              <CardContent>
                <ResourceSummary data={data.resource_summary} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Risk Level</CardTitle>
              </CardHeader>
              <CardContent>
                <RiskIndicator data={data.simulation_summary} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="critical-path">
          <CriticalPathVisualization projectId={projectId} />
        </TabsContent>

        <TabsContent value="resources">
          <ResourceUtilizationChart projectId={projectId} />
        </TabsContent>

        <TabsContent value="simulation">
          <SimulationResultsChart projectId={projectId} />
        </TabsContent>

        <TabsContent value="progress">
          <ProgressTracking projectId={projectId} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
```

### Testing Requirements

- Component rendering tests
- Data fetching tests with mocked API
- Tab navigation tests
- Auto-refresh functionality tests
- Error state handling tests
- Loading skeleton tests

### Acceptance Criteria

- [ ] Dashboard page implemented with TypeScript
- [ ] Tab navigation functional
- [ ] Auto-refresh every 30 seconds
- [ ] Loading and error states handled
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Component tests with 85%+ coverage

---

## 📦 Subagent D: Frontend Chart Components

**Directory**: `frontend/components/analytics/`
**Dependencies**: Chart library (Recharts), UI components
**Estimated Effort**: 4-5 hours

### Responsibilities

Create reusable chart components for visualizing analytics data.

### Components to Implement

#### 1. ProjectHealthCard.tsx
```typescript
interface ProjectHealthCardProps {
  healthScore: number // 0-100
}

export default function ProjectHealthCard({ healthScore }: ProjectHealthCardProps) {
  // Gauge chart showing health score
  // Color coding: 0-40 red, 40-70 yellow, 70-100 green
  // Include health score interpretation text
}
```

#### 2. CriticalPathVisualization.tsx
```typescript
interface CriticalPathVisualizationProps {
  projectId: string
}

export default function CriticalPathVisualization({ projectId }: CriticalPathVisualizationProps) {
  // Network diagram or horizontal Gantt chart
  // Highlight critical path in red
  // Show float time for non-critical tasks
  // Interactive: hover for task details
}
```

#### 3. ResourceUtilizationChart.tsx
```typescript
interface ResourceUtilizationChartProps {
  projectId: string
}

export default function ResourceUtilizationChart({ projectId }: ResourceUtilizationChartProps) {
  // Stacked bar chart showing resource allocation over time
  // Color coding by resource type or allocation percentage
  // Show over-allocated resources prominently
}
```

#### 4. SimulationResultsChart.tsx
```typescript
interface SimulationResultsChartProps {
  projectId: string
}

export default function SimulationResultsChart({ projectId }: SimulationResultsChartProps) {
  // Histogram of Monte Carlo simulation outcomes
  // Vertical lines for P10, P50, P90, P95
  // Shaded area for 80% confidence interval
  // Risk level indicator
}
```

#### 5. ProgressTracking.tsx
```typescript
interface ProgressTrackingProps {
  projectId: string
}

export default function ProgressTracking({ projectId }: ProgressTrackingProps) {
  // Burndown or burnup chart
  // Actual vs planned progress line
  // Completion percentage
  // Estimated completion date
}
```

#### 6. MetricsGrid.tsx
```typescript
interface MetricsGridProps {
  metrics: AnalyticsOverviewData
}

export default function MetricsGrid({ metrics }: MetricsGridProps) {
  // Grid of key metric cards
  // Each card: label, value, trend indicator
  // Responsive grid layout
}
```

#### 7. TrendIndicator.tsx
```typescript
interface TrendIndicatorProps {
  value: number
  previousValue?: number
  format?: 'number' | 'percent' | 'currency'
}

export default function TrendIndicator({ value, previousValue, format }: TrendIndicatorProps) {
  // Up/down arrow with percentage change
  // Color coded: green for improvement, red for degradation
}
```

#### 8. RiskIndicator.tsx
```typescript
interface RiskIndicatorProps {
  riskLevel: 'low' | 'medium' | 'high'
  riskScore?: number
}

export default function RiskIndicator({ riskLevel, riskScore }: RiskIndicatorProps) {
  // Color-coded badge or indicator
  // Tooltip with explanation
}
```

### Testing Requirements

- Component rendering tests for each chart
- Data transformation tests
- Interactive behavior tests (hover, click)
- Responsive design tests
- Accessibility tests (ARIA labels, keyboard navigation)

### Acceptance Criteria

- [ ] All 8 components implemented
- [ ] TypeScript interfaces defined
- [ ] Recharts integration for all charts
- [ ] Responsive design
- [ ] Accessible (WCAG AA)
- [ ] Component tests with 85%+ coverage

---

## 🔗 Integration Phase

After all subagents complete their work:

### Integration Tasks

1. **API Registration**: Register analytics router in main FastAPI app
2. **Frontend API Client**: Add analytics API calls to frontend API client
3. **Navigation Integration**: Add analytics link to project navigation
4. **Permission Checks**: Ensure proper authentication/authorization
5. **End-to-End Testing**: Test complete flow from frontend to backend

### Integration Testing

- Test data flow: Frontend → API → Service → Database
- Test caching behavior
- Test error propagation
- Performance testing (<2 second load time)
- Cross-browser testing

---

## 📊 Quality Checklist

Before marking bd-4 complete:

### Backend
- [ ] `analytics_service.py` implements all 5 functions
- [ ] Unit tests with 85%+ coverage
- [ ] Redis caching implemented
- [ ] Performance benchmarks met (<500ms calculations)
- [ ] Type hints and docstrings complete

### API
- [ ] All 5 endpoints implemented
- [ ] Pydantic response models defined
- [ ] OpenAPI docs generated
- [ ] Integration tests with 85%+ coverage
- [ ] Proper error handling

### Frontend Page
- [ ] Dashboard page complete
- [ ] Tab navigation functional
- [ ] Auto-refresh working
- [ ] Loading/error states
- [ ] Responsive design
- [ ] Component tests with 85%+ coverage

### Frontend Components
- [ ] All 8 chart components implemented
- [ ] Recharts integration working
- [ ] Interactive features functional
- [ ] Accessible (WCAG AA)
- [ ] Component tests with 85%+ coverage

### Documentation
- [ ] API documented in OpenAPI
- [ ] Component usage documented
- [ ] README updated
- [ ] This breakdown document updated with results

### Git
- [ ] All changes committed
- [ ] Conventional commit messages
- [ ] Feature branch created
- [ ] Changes pushed to remote

---

## 📝 Subagent Instructions

Each subagent will receive this document plus specific instructions for their component. They should:

1. Read this breakdown document
2. Implement their assigned component
3. Write comprehensive tests
4. Update this document with implementation notes
5. Commit their changes with clear messages
6. Report completion with coverage metrics

---

**Document Status**: ✅ Ready for Subagent Dispatch
**Next Action**: Dispatch 4 subagents in parallel
