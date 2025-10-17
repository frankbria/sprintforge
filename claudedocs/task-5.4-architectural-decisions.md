# Task 5.4: Architectural Decisions & Risk Analysis

**Date**: 2025-10-17
**Task**: bd-5 (Baseline Management & Comparison)
**Document Type**: Architecture Decision Record (ADR)

---

## Summary of Decisions

| # | Decision | Rationale | Alternatives Considered |
|---|----------|-----------|------------------------|
| 1 | No restore functionality in MVP | Reduces scope and risk; comparison-only sufficient for MVP | Full restore, selective restore |
| 2 | SERIALIZABLE transactions for snapshots | Guarantees data consistency; safe for multi-user future | Application locks, optimistic locking |
| 3 | JSONB storage for snapshot data | Efficient, flexible, handles large data well | External storage (S3), normalized tables |
| 4 | Redis caching with timestamp-based keys | Auto-invalidation, simple, effective | Manual invalidation, no caching |
| 5 | Partial unique index for active baseline | Database-enforced constraint, reliable | Application-level checks, triggers |

---

## Decision 1: No Restore Functionality in MVP

### Context

The planning document mentions `restore_from_baseline()` as an optional feature. We need to decide whether to include restore functionality in the MVP.

### Decision

**DEFER restore functionality to future sprint**. Implement **comparison-only** in MVP.

### Rationale

**Arguments Against Restore**:
1. **Data Loss Risk**: Restoring overwrites current work, potentially losing important updates
2. **UX Complexity**: Users may not understand implications of restore
3. **Audit Trail**: Difficult to track who restored what and when
4. **Feature Conflict**: May break analytics, notifications, other features that depend on current state
5. **Scope Creep**: Adds significant complexity for unclear user value

**Arguments For Comparison-Only**:
1. **Core Value**: Users primarily need to *track* variance, not undo changes
2. **Safer**: Read-only operation has no data loss risk
3. **Simpler**: Less code, fewer edge cases, faster implementation
4. **Sufficient**: Users can manually adjust tasks if they want to "restore"
5. **Iterative**: Can add restore later if users request it

### Consequences

**Positive**:
- Reduced implementation time (save ~2-3 hours)
- Lower risk of data loss bugs
- Simpler user mental model
- Focus on making comparison really good

**Negative**:
- Some users might expect restore functionality
- If restore is added later, requires additional planning

### Mitigation

- Document clearly that baselines are for comparison only
- Add "Restore" to future roadmap if users request it
- Can implement "Create project from baseline" instead (safer alternative)

---

## Decision 2: SERIALIZABLE Transactions for Snapshots

### Context

When creating a baseline snapshot, we need to ensure all project data is captured from the same point in time. What if tasks change during snapshot creation?

### Decision

Use **SERIALIZABLE transaction isolation** for baseline snapshot creation.

### Rationale

**Options Considered**:

**Option A: SERIALIZABLE Isolation** (CHOSEN)
```python
async with db.begin():
    db.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
    # Fetch project data
    # Create snapshot
```
- ✅ Guarantees data consistency
- ✅ PostgreSQL handles conflicts automatically
- ✅ Safe for current and future multi-user scenarios
- ⚠️ Can cause serialization errors under high contention

**Option B: Application-Level Lock**
```python
async with acquire_project_lock(project_id):
    # Fetch project data
    # Create snapshot
```
- ✅ Simple to understand
- ❌ Blocks ALL project operations during snapshot
- ❌ Requires lock management infrastructure
- ❌ Deadlock potential

**Option C: Optimistic Locking**
```python
# Snapshot, then check if data changed
if project.updated_at != original_timestamp:
    retry()
```
- ✅ No blocking
- ❌ Complex retry logic
- ❌ May require multiple attempts
- ❌ Not fully reliable

### Implementation

```python
async def create_baseline(
    project_id: UUID,
    name: str,
    description: Optional[str],
    db: AsyncSession
) -> ProjectBaseline:
    async with db.begin():
        # Set isolation level
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))

        try:
            # Fetch all data atomically
            project = await db.get(Project, project_id)
            tasks = await db.execute(
                select(Task).where(Task.project_id == project_id)
            )

            # Build snapshot
            snapshot_data = await _build_snapshot_data(project, tasks, db)

            # Create baseline
            baseline = ProjectBaseline(
                project_id=project_id,
                name=name,
                description=description,
                snapshot_data=snapshot_data
            )
            db.add(baseline)
            await db.flush()

            return baseline

        except SerializationFailure:
            # Rare: concurrent update during snapshot
            # Let transaction retry automatically
            raise
```

### Consequences

**Positive**:
- Data consistency guaranteed
- Works for single-user (no contention)
- Ready for multi-user future
- No manual lock management

**Negative**:
- Rare serialization errors possible (retry handled by application)
- Slightly more complex than READ COMMITTED

### Monitoring

- Log serialization errors
- Track snapshot creation time
- Alert if errors increase (indicates contention)

---

## Decision 3: JSONB Storage for Snapshot Data

### Context

Baseline snapshots need to store complete project state. How should we store this data?

### Decision

Use **JSONB column** for `snapshot_data` in `project_baselines` table.

### Rationale

**Options Considered**:

**Option A: JSONB Column** (CHOSEN)
```sql
snapshot_data JSONB NOT NULL
```
- ✅ Flexible schema (can evolve over time)
- ✅ Efficient storage (PostgreSQL compresses automatically)
- ✅ Can query nested data with JSONB operators
- ✅ Well-tested at scale (100MB+ per field)
- ✅ Atomic updates (though we don't need for immutable data)

**Option B: External Storage (S3/File)**
```python
snapshot_url = "s3://bucket/snapshots/uuid.json"
```
- ❌ Additional complexity (S3 client, credentials)
- ❌ Network latency for retrieval
- ❌ Additional cost
- ❌ Sync issues (database vs S3)
- ✅ Could handle arbitrarily large data

**Option C: Normalized Tables**
```sql
CREATE TABLE baseline_tasks (
    baseline_id UUID,
    task_id UUID,
    task_data JSONB
)
```
- ❌ More complex queries
- ❌ No benefit for immutable data
- ❌ Harder to ensure consistency
- ✅ Slightly better for partial queries

### Size Analysis

Estimated size for typical projects:
```
Project with 100 tasks:
- Each task: ~500 bytes (all fields JSON serialized)
- 100 tasks = 50 KB
- Project metadata: ~5 KB
- Total: ~55 KB

Project with 1,000 tasks:
- 1,000 tasks = 500 KB
- Project metadata: ~5 KB
- Total: ~505 KB

Project with 10,000 tasks:
- 10,000 tasks = 5 MB
- Project metadata: ~5 KB
- Total: ~5 MB
```

PostgreSQL JSONB handles these sizes easily. Set safety limit at 10MB.

### Implementation

```sql
CREATE TABLE project_baselines (
    ...
    snapshot_data JSONB NOT NULL,
    snapshot_size_bytes INTEGER,
    ...
    CONSTRAINT snapshot_size_limit CHECK (snapshot_size_bytes < 10485760)  -- 10MB
);

-- GIN index for JSONB queries (optional, if needed)
CREATE INDEX idx_baselines_snapshot_data_gin
    ON project_baselines USING GIN(snapshot_data);
```

### Consequences

**Positive**:
- Simple implementation
- Fast retrieval (single query)
- No external dependencies
- Flexible schema evolution

**Negative**:
- Size limit (10MB) might be hit by very large projects
- Full snapshot returned (can't select subset)

### Migration Path

If JSONB becomes limiting factor:
1. Keep JSONB for projects <10MB
2. Add external storage for >10MB projects
3. `snapshot_storage_type` field ('jsonb' | 's3')
4. Abstract storage layer in service

---

## Decision 4: Redis Caching with Timestamp-Based Keys

### Context

Baseline comparison calculations are expensive (O(n) where n = tasks). How should we cache results?

### Decision

Use **Redis caching with automatic invalidation via timestamp-based cache keys**.

### Rationale

**Cache Key Design**:
```python
cache_key = f"baseline_comparison:{baseline_id}:{project.updated_at.timestamp()}"
```

**Why this works**:
1. **Automatic Invalidation**: When project changes, `updated_at` changes, new cache key generated
2. **No Manual Invalidation**: Don't need to track which cache keys to delete
3. **TTL Cleanup**: Old keys expire after 5 minutes
4. **Deterministic**: Same inputs → same cache key

**Alternatives Considered**:

**Option A: Timestamp-Based Keys** (CHOSEN)
- ✅ Automatic invalidation
- ✅ Simple logic
- ✅ No race conditions
- ⚠️ Orphaned keys (cleaned by TTL)

**Option B: Manual Invalidation**
```python
# On project update:
redis.delete(f"baseline_comparison:{baseline_id}:*")
```
- ❌ Need to track all cache keys
- ❌ Race condition: delete might miss in-flight updates
- ❌ More complex code

**Option C: No Caching**
- ❌ Slow for repeated comparisons
- ❌ Wasteful recomputation
- ✅ Simpler code

### Implementation

```python
async def compare_to_baseline(
    baseline_id: UUID,
    project_id: UUID,
    db: AsyncSession,
    redis: Redis
) -> BaselineComparison:
    # Get current project
    project = await db.get(Project, project_id)

    # Build cache key with timestamp
    cache_key = f"baseline_comparison:{baseline_id}:{project.updated_at.timestamp()}"

    # Try cache
    cached = await redis.get(cache_key)
    if cached:
        logger.info(f"Cache HIT for {cache_key}")
        return json.loads(cached)

    # Cache miss - calculate
    logger.info(f"Cache MISS for {cache_key}")
    comparison = await _calculate_comparison(baseline_id, project, db)

    # Store with TTL
    await redis.setex(cache_key, 300, json.dumps(comparison))  # 5 min

    return comparison
```

### Consequences

**Positive**:
- Fast repeated comparisons (cache hit)
- Simple invalidation logic
- No stale data issues
- Automatic cleanup

**Negative**:
- Orphaned keys for 5 minutes (minimal)
- Cache miss on every project update

### Performance Impact

- Cache HIT: <10ms (Redis read)
- Cache MISS: 100-500ms (calculation + Redis write)
- For unchanged projects: >95% cache hit rate expected

---

## Decision 5: Partial Unique Index for Active Baseline

### Context

Requirement: "Only one baseline can be 'active' for comparison per project"

How to enforce this constraint?

### Decision

Use **PostgreSQL partial unique index** to enforce at database level.

### Rationale

**Options Considered**:

**Option A: Partial Unique Index** (CHOSEN)
```sql
CREATE UNIQUE INDEX unique_active_baseline_per_project
    ON project_baselines (project_id)
    WHERE is_active = true;
```
- ✅ Database-enforced (cannot be violated)
- ✅ Elegant and declarative
- ✅ No race conditions
- ✅ `NULL` and `false` values don't conflict
- ✅ Automatic enforcement

**Option B: Application-Level Check**
```python
existing_active = await db.execute(
    select(Baseline)
    .where(Baseline.project_id == project_id)
    .where(Baseline.is_active == true)
)
if existing_active:
    raise ConflictError("Active baseline already exists")
```
- ❌ Race condition: Two requests could both pass check
- ❌ Not reliable in concurrent scenarios
- ❌ More code to maintain

**Option C: Database Trigger**
```sql
CREATE TRIGGER enforce_single_active_baseline
    BEFORE INSERT OR UPDATE ON project_baselines
    FOR EACH ROW
    EXECUTE FUNCTION check_active_baseline();
```
- ✅ Database-enforced
- ❌ More complex than index
- ❌ Harder to debug
- ❌ Performance overhead

### Implementation

**Database Schema**:
```sql
-- Partial unique index
CREATE UNIQUE INDEX unique_active_baseline_per_project
    ON project_baselines (project_id)
    WHERE is_active = true;
```

**Activation Logic** (atomic):
```python
async def set_baseline_active(
    baseline_id: UUID,
    project_id: UUID,
    db: AsyncSession
) -> ProjectBaseline:
    async with db.begin():
        # Deactivate all baselines for this project
        await db.execute(
            update(ProjectBaseline)
            .where(ProjectBaseline.project_id == project_id)
            .where(ProjectBaseline.is_active == true)
            .values(is_active=False)
        )

        # Activate selected baseline
        await db.execute(
            update(ProjectBaseline)
            .where(ProjectBaseline.id == baseline_id)
            .values(is_active=True)
        )

    # Fetch updated baseline
    return await db.get(ProjectBaseline, baseline_id)
```

### Consequences

**Positive**:
- Constraint cannot be violated
- Simple, declarative
- Works in all concurrent scenarios
- No additional code complexity

**Negative**:
- None (this is the ideal solution)

### Error Handling

If constraint violated (shouldn't happen with proper activation logic):
```python
try:
    await db.commit()
except IntegrityError as e:
    if "unique_active_baseline_per_project" in str(e):
        raise ConflictError("Another baseline is already active")
    raise
```

---

## Risk Assessment Summary

### High-Priority Risks

| Risk | Likelihood | Impact | Mitigation | Status |
|------|-----------|--------|-----------|--------|
| JSONB size exceeds limits | Low | Medium | 10MB constraint + monitoring | ✅ Mitigated |
| Comparison performance slow | Medium | Low | Redis caching + pagination | ✅ Mitigated |
| Baseline immutability violated | Low | High | No UPDATE endpoint + tests | ✅ Mitigated |

### Medium-Priority Risks

| Risk | Likelihood | Impact | Mitigation | Status |
|------|-----------|--------|-----------|--------|
| Concurrent baseline creation | Very Low | Low | SERIALIZABLE transactions | ✅ Mitigated |
| Frontend state complexity | Medium | Low | TanStack Query + patterns | ✅ Mitigated |
| Serialization errors | Low | Low | Automatic retry + monitoring | ✅ Mitigated |

### Risk Monitoring

**Metrics to Track**:
1. `snapshot_size_bytes` distribution (alert if approaching 10MB)
2. Comparison calculation time (p50, p95, p99)
3. Cache hit rate (should be >90% for unchanged projects)
4. Serialization error rate (should be near 0%)
5. API endpoint latency (all <2s at p95)

**Alerts**:
- Alert if snapshot size >8MB (approaching limit)
- Alert if comparison time >3s (performance degradation)
- Alert if cache hit rate <70% (caching not working)
- Alert if serialization errors >0.1% (contention issues)

---

## Security Considerations

### Authentication & Authorization

All baseline endpoints require:
1. **Authentication**: Valid JWT token
2. **Authorization**: User must own the project

```python
@router.post("/projects/{project_id}/baselines")
async def create_baseline(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify project ownership
    project = await db.get(Project, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    # Proceed with baseline creation
    ...
```

### Data Privacy

- Baseline snapshots contain project data
- Should inherit project's access controls
- Delete baselines when project is deleted (CASCADE)

### Rate Limiting

Apply rate limits to prevent abuse:
- Create baseline: 10 per hour per user
- Comparison: 100 per hour per user
- List: 1000 per hour per user

---

## Performance Benchmarks

### Target Performance

| Operation | Target | Measured |
|-----------|--------|----------|
| Create baseline (100 tasks) | <1s | TBD |
| Create baseline (1000 tasks) | <3s | TBD |
| Comparison (100 tasks, cache miss) | <500ms | TBD |
| Comparison (1000 tasks, cache miss) | <2s | TBD |
| Comparison (cache hit) | <10ms | TBD |
| List baselines (50 items) | <200ms | TBD |

### Load Testing Plan

Test scenarios:
1. **Baseline Creation Load**:
   - 10 concurrent users creating baselines
   - Projects with 100, 500, 1000 tasks
   - Measure: Latency, throughput, error rate

2. **Comparison Load**:
   - 50 concurrent users comparing baselines
   - Mix of cache hits (70%) and misses (30%)
   - Measure: Cache hit rate, latency distribution

3. **Stress Test**:
   - 100 users creating baselines simultaneously
   - Verify: No serialization errors, no deadlocks

---

## Future Enhancements

Potential features for future sprints:

1. **Baseline Restore** (if users request)
   - Restore entire project from baseline
   - Selective restore (choose specific tasks)
   - Restore as new project (safer)

2. **Baseline Templates**
   - Save baseline as reusable template
   - Apply template to new projects
   - Template marketplace

3. **Comparison Visualization**
   - Gantt chart overlay (baseline vs current)
   - Timeline diff view
   - Interactive variance explorer

4. **Scheduled Baselines**
   - Auto-create baseline daily/weekly
   - Keep last N baselines automatically
   - Retention policy

5. **Baseline Comments**
   - Add notes to specific baselines
   - Tag team members
   - Baseline changelog

6. **External Storage**
   - For projects >10MB
   - S3/cloud storage integration
   - Transparent to user

---

## Conclusion

These architectural decisions provide a **solid foundation** for baseline management:

✅ **Simple**: JSONB storage, Redis caching, partial index
✅ **Reliable**: SERIALIZABLE transactions, database constraints
✅ **Scalable**: Handles typical projects, path to large projects
✅ **Safe**: Immutable snapshots, authorization checks
✅ **Performant**: Caching, efficient algorithms

**Total Risk Level**: **LOW**
- All high-priority risks mitigated
- Proven technologies (PostgreSQL JSONB, Redis)
- Clear implementation path
- Well-defined scope

**Ready for Implementation**: ✅ **YES**

---

**Document Status**: Complete
**Next Action**: Begin implementation with Sub-task A (bd-13)
**Estimated Total Time**: 10-14 hours across 4 parallelizable sub-tasks
