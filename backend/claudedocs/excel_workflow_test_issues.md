# Excel Workflow Test Issues

## Summary
The tests in `tests/api/endpoints/test_excel_workflow.py` have fundamental architectural mismatches with the actual implementation in `app/api/endpoints/excel_workflow.py` and the service layer.

## Issues Identified

### 1. URL Path Mismatches (7 tests affected)
**Tests expect**: `/api/v1/projects/{project_id}/excel/simulate`
**Actual endpoint**: `/api/v1/excel/projects/{project_id}/simulate`

The excel_workflow router has prefix `/excel` and the route is `/projects/{project_id}/simulate`, resulting in the full path `/api/v1/excel/projects/{project_id}/simulate`.

**Affected tests**:
- test_upload_valid_excel_and_simulate_success
- test_upload_excel_file_too_large
- test_upload_invalid_file_type
- test_upload_excel_unauthorized
- test_upload_excel_invalid_iterations
- test_download_simulation_excel_unauthorized
- test_download_template_unauthorized

**Error**: 404 Not Found

### 2. Service Method Name Mismatches (Mock AttributeError)

#### ExcelParserService
**Tests mock**: `ExcelParserService.parse_excel`
**Actual method**: `ExcelParserService.parse_excel_file`

The service uses `parse_excel_file(file_bytes: bytes, filename: str)` but tests try to mock `parse_excel`.

**Affected tests**:
- test_upload_valid_excel_and_simulate_success
- test_upload_excel_with_parsing_errors
- test_upload_excel_with_circular_dependencies

#### ExcelGenerationService
**Tests mock**:
- `ExcelGenerationService.generate_simulation_excel`
- `ExcelGenerationService.generate_blank_template`
- `ExcelGenerationService.generate_sample_template`

**Actual methods**:
- `create_template_workbook()`
- `add_monte_carlo_results_sheet()`
- `save_workbook_to_bytes()`
- Other lower-level methods

The service has a different architecture - it provides building blocks rather than high-level wrapper methods. The endpoint orchestrates these methods directly.

**Affected tests**:
- test_download_simulation_excel_success
- test_download_blank_template
- test_download_template_with_sample_data

### 3. Test Architecture Issues

The tests were written assuming:
1. A different URL structure
2. High-level service wrapper methods that don't exist
3. A service layer API that wasn't implemented

This suggests the tests were written from a specification/design document before implementation, and the implementation diverged from the spec.

## Current Test Status (After SF-24 Fixes)

### Passing Tests
- **test_main.py**: 6/6 passing ✅
- **test_models.py**: 8/8 passing ✅
- **test_excel_workflow.py**: 1/14 passing ⚠️
  - Only `test_download_simulation_excel_not_found` passes (doesn't use mocks or authentication)

### Failing Tests
- **test_excel_workflow.py**: 13/14 failing ❌
  - 7 failures: 404 errors (URL mismatches)
  - 6 failures: AttributeError (mock method mismatches)

## Recommendations

### Option 1: Fix Tests to Match Implementation (Recommended)
Update tests to:
1. Use correct URL paths: `/api/v1/excel/projects/{project_id}/simulate`
2. Mock correct service methods: `parse_excel_file` instead of `parse_excel`
3. Adjust mocks for ExcelGenerationService's actual architecture

**Pros**: Tests will validate actual implementation
**Cons**: Significant test rewrite required (estimated 2-3 hours)

### Option 2: Add Service Wrapper Methods
Add convenience methods to services that tests expect:
- `ExcelParserService.parse_excel()` → wrapper for `parse_excel_file()`
- `ExcelGenerationService.generate_simulation_excel()` → wrapper combining multiple methods
- `ExcelGenerationService.generate_blank_template()` → wrapper
- `ExcelGenerationService.generate_sample_template()` → wrapper

**Pros**: Tests work as-is, provides cleaner service API
**Cons**: Adds abstraction layer that may not be needed

### Option 3: Integration Tests Instead
Replace unit tests with end-to-end integration tests that:
- Don't mock services
- Test actual request/response behavior
- Validate full workflow

**Pros**: More reliable, tests real behavior
**Cons**: Slower, requires test database setup

## Impact Assessment

**Test Coverage Impact**: The Excel workflow endpoints are currently undertested. While fixtures and basic tests pass, the core Excel workflow functionality lacks proper test coverage.

**Development Impact**: Without working tests:
- Regression risk when modifying Excel workflow code
- Harder to validate new features
- Reduced confidence in deployments

**Priority**: Medium-High - These are core features (Excel upload/download, Monte Carlo simulation)

## Next Steps

1. ✅ Document issues (this file)
2. ⏳ Update beads issue sf-24 with findings
3. ⏳ Decide on fix strategy (Options 1-3)
4. ⏳ Implement chosen fix
5. ⏳ Achieve 85%+ coverage requirement

## Related Files

- **Implementation**: `app/api/endpoints/excel_workflow.py`
- **Tests**: `tests/api/endpoints/test_excel_workflow.py`
- **Services**:
  - `app/services/excel_parser_service.py`
  - `app/services/excel_generation_service.py`
  - `app/services/simulation_service.py`

## Session Context

**Fixed in Session**:
- ✅ All 30 fixture/setup errors (test_db_session, conftest.py issues)
- ✅ test_main.py CORS header test
- ✅ test_models.py async relationship and timestamp tests
- ⏳ test_excel_workflow.py architectural mismatches (documented here)

**Commits**:
- 7935d94: fix(tests): Resolve all 30 integration test fixture/setup errors
- 6772437: fix(tests): Fix test_main.py CORS and test_models.py async issues
