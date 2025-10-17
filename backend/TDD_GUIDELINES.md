# Test-Driven Development (TDD) Guidelines - SprintForge

## Overview

**ALL code in SprintForge MUST be developed using Test-Driven Development (TDD).**

This is not optional. TDD is a core development practice that ensures:
- ✅ Code correctness from the start
- ✅ Comprehensive test coverage (85%+ target)
- ✅ Better design through testability
- ✅ Living documentation through tests
- ✅ Regression prevention

## Table of Contents
- [The RED-GREEN-REFACTOR Cycle](#the-red-green-refactor-cycle)
- [TDD Workflow](#tdd-workflow)
- [Writing Tests First](#writing-tests-first)
- [Backend TDD Examples](#backend-tdd-examples)
- [Frontend TDD Examples](#frontend-tdd-examples)
- [TDD Anti-Patterns](#tdd-anti-patterns)
- [Test Coverage Requirements](#test-coverage-requirements)
- [Code Review Checklist](#code-review-checklist)

---

## The RED-GREEN-REFACTOR Cycle

TDD follows a strict three-phase cycle:

### 🔴 **RED** - Write a Failing Test
```python
def test_create_baseline_validates_name():
    """Test that create_baseline rejects empty names."""
    service = BaselineService()

    with pytest.raises(ValueError, match="name cannot be empty"):
        await service.create_baseline(
            project_id=UUID("..."),
            name="",  # Invalid!
            description=None,
            db=mock_db
        )
```

**Rules:**
- Write the test BEFORE any implementation code
- Test MUST fail initially (if it passes, you're testing existing code)
- Verify the test fails for the RIGHT reason
- Keep tests simple and focused on one behavior

---

### 🟢 **GREEN** - Write Minimal Code to Pass
```python
async def create_baseline(self, project_id, name, description, db):
    """Create a baseline snapshot."""
    if not name or not name.strip():
        raise ValueError("name cannot be empty")

    # Minimal implementation to pass the test
    # Don't add features not covered by tests!
```

**Rules:**
- Write ONLY enough code to make the test pass
- Don't add extra features "just in case"
- Resist the urge to "improve" things beyond test requirements
- Accept ugly code at this stage - refactoring comes next

---

### 🔵 **REFACTOR** - Improve Code Quality
```python
async def create_baseline(self, project_id, name, description, db):
    """Create a baseline snapshot for a project."""
    self._validate_baseline_name(name)  # Extracted for clarity

    async with db.begin_nested():
        snapshot_data = await self._build_snapshot_data(project_id, db)
        baseline = ProjectBaseline(
            project_id=project_id,
            name=name.strip(),
            description=description,
            snapshot_data=snapshot_data,
        )
        db.add(baseline)

    await db.commit()
    return baseline

def _validate_baseline_name(self, name: str) -> None:
    """Validate baseline name is not empty."""
    if not name or not name.strip():
        raise ValueError("name cannot be empty")
```

**Rules:**
- Improve code structure WITHOUT changing behavior
- All tests must still pass
- Extract methods, rename variables, remove duplication
- Commit frequently during refactoring

---

## TDD Workflow

### Step-by-Step Process

#### 1. **Understand the Requirement**
```
Feature: Users need to create named baselines to track project progress
```

#### 2. **Write Test for Simplest Case**
```python
@pytest.mark.asyncio
async def test_create_baseline_with_valid_name(mock_db):
    """Test creating baseline with valid name succeeds."""
    service = BaselineService()
    project_id = UUID("12345678-1234-5678-1234-567812345678")

    baseline = await service.create_baseline(
        project_id=project_id,
        name="Q4 2025 Baseline",
        description="Initial project plan",
        db=mock_db
    )

    assert baseline is not None
    assert baseline.name == "Q4 2025 Baseline"
    assert baseline.project_id == project_id
```

#### 3. **Run Test - Verify It FAILS**
```bash
uv run pytest tests/services/test_baseline_service.py::test_create_baseline_with_valid_name -v

# Expected: AttributeError or NameError because create_baseline doesn't exist yet
```

#### 4. **Write Minimum Code**
```python
class BaselineService:
    async def create_baseline(self, project_id, name, description, db):
        baseline = ProjectBaseline(
            project_id=project_id,
            name=name,
            description=description,
            snapshot_data={}  # Minimal implementation
        )
        db.add(baseline)
        await db.commit()
        return baseline
```

#### 5. **Run Test - Verify It PASSES**
```bash
uv run pytest tests/services/test_baseline_service.py::test_create_baseline_with_valid_name -v

# Expected: PASSED
```

#### 6. **Add Next Test (Edge Case)**
```python
@pytest.mark.asyncio
async def test_create_baseline_rejects_empty_name(mock_db):
    """Test that empty name is rejected."""
    service = BaselineService()

    with pytest.raises(ValueError, match="name cannot be empty"):
        await service.create_baseline(
            project_id=UUID("..."),
            name="",
            description=None,
            db=mock_db
        )
```

#### 7. **Repeat RED-GREEN-REFACTOR**
- Run new test → FAILS (no validation yet)
- Add validation → PASSES
- Refactor if needed
- Repeat for each new behavior

---

## Writing Tests First

### ✅ DO: Write Test Before Implementation

```python
# STEP 1: Write test
def test_baseline_activation_deactivates_others(mock_db):
    """Test that activating a baseline deactivates all others."""
    # Arrange
    service = BaselineService()
    project_id = UUID("...")
    baseline1_id = UUID("...")
    baseline2_id = UUID("...")

    # Pre-populate with two baselines
    await mock_db.add_baseline(project_id, baseline1_id, is_active=True)
    await mock_db.add_baseline(project_id, baseline2_id, is_active=False)

    # Act
    await service.set_baseline_active(baseline2_id, project_id, mock_db)

    # Assert
    baseline1 = await mock_db.get_baseline(baseline1_id)
    baseline2 = await mock_db.get_baseline(baseline2_id)

    assert baseline1.is_active is False  # Deactivated
    assert baseline2.is_active is True   # Activated

# STEP 2: Run test → FAILS (method doesn't exist)

# STEP 3: Implement
async def set_baseline_active(self, baseline_id, project_id, db):
    async with db.begin_nested():
        # Deactivate all
        await db.execute(
            update(ProjectBaseline)
            .where(ProjectBaseline.project_id == project_id)
            .values(is_active=False)
        )

        # Activate selected
        await db.execute(
            update(ProjectBaseline)
            .where(ProjectBaseline.id == baseline_id)
            .values(is_active=True)
        )
    await db.commit()

# STEP 4: Run test → PASSES

# STEP 5: Refactor if needed
```

### ❌ DON'T: Write Implementation First

```python
# ❌ WRONG - Implementation without test
async def set_baseline_active(self, baseline_id, project_id, db):
    # How do you know this works?
    # What if there's a bug?
    # What if requirements change?
    async with db.begin_nested():
        await db.execute(...)
    await db.commit()

# NOW trying to write test after the fact
def test_baseline_activation():  # Test might pass even if code is broken!
    ...
```

---

## Backend TDD Examples

### Example 1: Database Model Validation

**Requirement**: Baseline name must not be empty

```python
# tests/models/test_baseline.py

@pytest.mark.asyncio
async def test_baseline_name_cannot_be_empty(async_session):
    """Test that baseline name must not be empty."""
    # RED: Write failing test
    baseline = ProjectBaseline(
        project_id=UUID("..."),
        name="",  # Empty name
        snapshot_data={}
    )

    async_session.add(baseline)

    with pytest.raises(IntegrityError):  # Expect database constraint violation
        await async_session.commit()

# Run test → FAILS (no constraint exists)

# GREEN: Add constraint in migration
# migrations/003_project_baselines.sql
CONSTRAINT baseline_name_not_empty CHECK (length(trim(name)) > 0)

# Run test → PASSES

# REFACTOR: Add Pydantic validation for early catch
class CreateBaselineRequest(BaseModel):
    name: str = Field(..., min_length=1)

    @field_validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()
```

### Example 2: Service Layer Business Logic

**Requirement**: Only one active baseline per project

```python
# tests/services/test_baseline_service.py

@pytest.mark.asyncio
async def test_activating_baseline_deactivates_previous(mock_db):
    """Test that only one baseline can be active per project."""
    # RED: Write test first
    service = BaselineService()
    project_id = UUID("...")

    # Create two baselines
    baseline1 = await service.create_baseline(project_id, "B1", None, mock_db)
    baseline2 = await service.create_baseline(project_id, "B2", None, mock_db)

    # Activate first
    await service.set_baseline_active(baseline1.id, project_id, mock_db)

    # Activate second
    await service.set_baseline_active(baseline2.id, project_id, mock_db)

    # Assert: Only baseline2 is active
    result = await mock_db.execute(
        select(ProjectBaseline).where(ProjectBaseline.project_id == project_id)
    )
    baselines = result.scalars().all()

    active_count = sum(1 for b in baselines if b.is_active)
    assert active_count == 1
    assert baseline2.is_active is True
    assert baseline1.is_active is False

# Run → FAILS (no deactivation logic)

# GREEN: Implement
async def set_baseline_active(self, baseline_id, project_id, db):
    async with db.begin_nested():
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
    await db.commit()

# Run → PASSES
```

### Example 3: API Endpoint Testing

**Requirement**: POST /baselines returns 201 with baseline data

```python
# tests/api/endpoints/test_baselines.py

@pytest.mark.asyncio
async def test_create_baseline_returns_201(async_client, auth_headers):
    """Test creating baseline returns 201 Created with baseline data."""
    # RED: Write test
    project_id = "12345678-1234-5678-1234-567812345678"

    response = await async_client.post(
        f"/api/v1/projects/{project_id}/baselines",
        headers=auth_headers,
        json={
            "name": "Q4 2025 Baseline",
            "description": "Initial project plan"
        }
    )

    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Q4 2025 Baseline"
    assert data["project_id"] == project_id
    assert "id" in data
    assert "created_at" in data

# Run → FAILS (endpoint doesn't exist)

# GREEN: Implement endpoint
@router.post("/{project_id}/baselines", status_code=201)
async def create_baseline(
    project_id: UUID,
    request: CreateBaselineRequest,
    db: AsyncSession = Depends(get_db)
):
    service = BaselineService()
    baseline = await service.create_baseline(
        project_id, request.name, request.description, db
    )
    return BaselineResponse.model_validate(baseline)

# Run → PASSES
```

---

## Frontend TDD Examples

### Example 1: React Component Testing

**Requirement**: BaselineList component displays baselines

```typescript
// __tests__/components/BaselineList.test.tsx

describe('BaselineList', () => {
  // RED: Write test
  it('displays baselines when data is loaded', async () => {
    const mockBaselines = [
      { id: '1', name: 'Q4 Baseline', created_at: '2025-10-17T10:00:00Z', is_active: true },
      { id: '2', name: 'Q3 Baseline', created_at: '2025-07-01T10:00:00Z', is_active: false },
    ];

    render(<BaselineList projectId="123" baselines={mockBaselines} />);

    expect(screen.getByText('Q4 Baseline')).toBeInTheDocument();
    expect(screen.getByText('Q3 Baseline')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument(); // Active badge
  });

  // Run → FAILS (component doesn't exist)

  // GREEN: Implement minimal component
  export function BaselineList({ projectId, baselines }) {
    return (
      <div>
        {baselines.map(b => (
          <div key={b.id}>
            <span>{b.name}</span>
            {b.is_active && <span>Active</span>}
          </div>
        ))}
      </div>
    );
  }

  // Run → PASSES

  // REFACTOR: Improve UI
  export function BaselineList({ projectId, baselines }) {
    return (
      <Table>
        {baselines.map(baseline => (
          <TableRow key={baseline.id}>
            <TableCell>{baseline.name}</TableCell>
            <TableCell>{formatDate(baseline.created_at)}</TableCell>
            <TableCell>
              {baseline.is_active && <Badge variant="success">Active</Badge>}
            </TableCell>
          </TableRow>
        ))}
      </Table>
    );
  }
});
```

### Example 2: API Client Testing

```typescript
// __tests__/lib/api/baselines.test.ts

describe('baselines API client', () => {
  // RED
  it('fetches baselines for a project', async () => {
    const projectId = '123';
    const mockResponse = {
      baselines: [{ id: '1', name: 'Test' }],
      total: 1,
      page: 1,
      limit: 50
    };

    // Mock fetch
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })
    );

    const result = await getBaselines(projectId);

    expect(result.baselines).toHaveLength(1);
    expect(result.baselines[0].name).toBe('Test');
  });

  // Run → FAILS

  // GREEN
  export async function getBaselines(projectId: string) {
    const response = await fetch(`/api/v1/projects/${projectId}/baselines`);
    return response.json();
  }

  // Run → PASSES
});
```

---

## TDD Anti-Patterns

### ❌ **Anti-Pattern 1: Writing Tests After Implementation**

```python
# WRONG ORDER:

# 1. Write implementation first
def calculate_variance(baseline, current):
    return current.end_date - baseline.end_date

# 2. Then write test
def test_calculate_variance():
    result = calculate_variance(baseline, current)
    assert result == expected  # Test might pass even if logic is wrong!
```

**Problem**: Test validates existing code, not requirements. Bugs slip through.

**Fix**: Always write test BEFORE implementation.

---

### ❌ **Anti-Pattern 2: Testing Implementation Details**

```python
# BAD: Testing internal method names
def test_baseline_service_calls_build_snapshot():
    service = BaselineService()
    service._build_snapshot_data = Mock()

    await service.create_baseline(...)

    service._build_snapshot_data.assert_called_once()  # Testing HOW, not WHAT
```

**Problem**: Tests break when refactoring, even if behavior is correct.

**Fix**: Test behavior and outcomes, not implementation.

```python
# GOOD: Testing behavior
def test_baseline_service_creates_snapshot_with_project_data():
    service = BaselineService()

    baseline = await service.create_baseline(project_id, name, desc, db)

    assert baseline.snapshot_data["project"]["id"] == str(project_id)
    assert baseline.snapshot_data["project"]["name"] == "Test Project"
```

---

### ❌ **Anti-Pattern 3: Not Watching Tests Fail**

```python
# Test that accidentally passes without implementation
def test_baseline_name_validation():
    service = BaselineService()

    # BUG: Wrong exception type!
    with pytest.raises(Exception):  # Too generic - always passes
        await service.create_baseline(project_id, "", None, db)
```

**Problem**: Test gives false confidence. Never saw it fail, so don't know it works.

**Fix**: ALWAYS run test and verify it fails for the right reason before implementing.

```python
# GOOD: Specific exception
def test_baseline_name_validation():
    service = BaselineService()

    with pytest.raises(ValueError, match="name cannot be empty"):
        await service.create_baseline(project_id, "", None, db)

# Run → Should fail with "method doesn't exist" or "no validation"
# Implement → Should pass
```

---

### ❌ **Anti-Pattern 4: One Giant Test**

```python
# BAD: Testing multiple behaviors in one test
def test_baseline_service():
    service = BaselineService()

    # Test creation
    baseline = await service.create_baseline(...)
    assert baseline is not None

    # Test activation
    await service.set_baseline_active(...)
    assert baseline.is_active

    # Test comparison
    comparison = await service.compare_to_baseline(...)
    assert len(comparison["variances"]) > 0

    # Test deletion
    await service.delete_baseline(...)
    # ... and so on
```

**Problem**: Hard to debug, unclear what failed, violates Single Responsibility.

**Fix**: One test per behavior.

```python
# GOOD: Separate focused tests
def test_create_baseline_returns_baseline_instance():
    ...

def test_set_baseline_active_marks_baseline_as_active():
    ...

def test_compare_to_baseline_calculates_task_variances():
    ...
```

---

## Test Coverage Requirements

### Minimum Coverage Targets

- **Overall**: 85% minimum
- **Critical Paths**: 95%+ (authentication, data mutations, financial calculations)
- **Services**: 90%+ (business logic must be thoroughly tested)
- **Models**: 85%+ (validation and constraints)
- **API Endpoints**: 85%+ (all status codes and error paths)

### Running Coverage

```bash
# Full coverage report
uv run pytest --cov=app tests/ --cov-report=term-missing

# Coverage for specific module
uv run pytest --cov=app.services.baseline_service tests/services/test_baseline_service.py

# Fail build if coverage below threshold
uv run pytest --cov=app tests/ --cov-fail-under=85
```

### What to Cover

✅ **Must Cover:**
- Happy path (normal execution)
- Error cases (validation failures, not found, etc.)
- Edge cases (empty lists, None values, boundary conditions)
- Security (authentication, authorization)
- Database constraints (unique, foreign keys, checks)

❌ **Don't Need to Cover:**
- Third-party library internals
- Generated code (Pydantic models without custom logic)
- Simple getters/setters without logic
- Configuration constants

---

## Code Review Checklist

Before approving ANY pull request, verify:

### TDD Process

- [ ] Tests were written BEFORE implementation (check git history)
- [ ] All tests were seen failing before implementation
- [ ] Tests follow RED-GREEN-REFACTOR cycle
- [ ] No implementation code without corresponding tests

### Test Quality

- [ ] Tests are isolated (no shared state between tests)
- [ ] Tests are focused (one behavior per test)
- [ ] Test names clearly describe what is being tested
- [ ] Tests use meaningful assertions (not just `assert result`)
- [ ] Edge cases are covered

### Coverage

- [ ] Overall coverage ≥ 85%
- [ ] New code coverage ≥ 90%
- [ ] Critical paths coverage ≥ 95%
- [ ] All public methods have tests

### Code Quality

- [ ] Implementation is minimal (only what tests require)
- [ ] Code has been refactored for clarity
- [ ] No premature optimization
- [ ] No speculative features ("might need later")

---

## Enforcement

### Pre-Commit Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "Running tests..."
uv run pytest

if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Commit aborted."
    exit 1
fi

echo "Checking coverage..."
uv run pytest --cov=app tests/ --cov-fail-under=85 -q

if [ $? -ne 0 ]; then
    echo "❌ Coverage below 85%. Commit aborted."
    exit 1
fi

echo "✅ All checks passed!"
```

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: TDD Enforcement

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Tests
        run: |
          cd backend
          uv run pytest --cov=app tests/ --cov-fail-under=85

      - name: Verify Test Coverage
        run: |
          if [ $(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//') -lt 85 ]; then
            echo "Coverage below 85%"
            exit 1
          fi
```

---

## Resources

- **Kent Beck's TDD Book**: *Test-Driven Development: By Example*
- **Martin Fowler on TDD**: https://martinfowler.com/bliki/TestDrivenDevelopment.html
- **pytest Documentation**: https://docs.pytest.org/
- **Testing Guide**: [TESTING.md](TESTING.md)

---

## Summary

### The Golden Rules of TDD

1. **NEVER write production code without a failing test first**
2. **Write only enough test code to fail**
3. **Write only enough production code to pass the test**
4. **Refactor only after tests pass**
5. **Run tests frequently (every few minutes)**

### Benefits You'll See

- ✅ Fewer bugs in production
- ✅ Faster debugging (tests pinpoint failures)
- ✅ Confidence to refactor
- ✅ Better design (testable = decoupled)
- ✅ Living documentation
- ✅ Regression prevention

### Remember

> "Code without tests is broken by design." - Jacob Kaplan-Moss

TDD isn't extra work - it's how professional software gets built. The time spent writing tests is saved many times over in debugging, bug fixes, and maintenance.

---

**Questions?** See [TESTING.md](TESTING.md) for practical testing guidance or reach out to the team.

**Follow TDD. Ship quality code. Sleep well at night.** 😴✅
