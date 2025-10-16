# Task 4.7: E2E Testing Suite - Implementation Plan

**Status**: Planned
**Priority**: P0 (Sprint 4 Enhancement)
**Estimated Hours**: 5-6
**Created**: October 15, 2025

## Overview

Comprehensive E2E testing suite to validate complete user workflows and system integration. This addresses the testing gap identified in Task 4.6, where only unit tests (86.48% coverage) were implemented, leaving E2E, integration, and visual regression testing at 0%.

## Current Testing Gap Analysis

### What We Have ✅
- **Unit Tests**: 54 tests across 4 dashboard components
- **Coverage**: 86.48% component-level coverage
- **Speed**: Fast (<5 seconds)
- **Scope**: Component behavior, props, state management

### What We're Missing ❌
- **E2E Tests**: 0 browser-based workflow tests
- **Integration Tests**: 0 frontend-backend integration tests
- **Visual Tests**: 0 screenshot/regression tests
- **Performance Tests**: 0 load/stress tests
- **Cross-browser Tests**: 0 multi-browser validation

### Impact of Gap
- ⚠️ No validation that features work in real browsers
- ⚠️ No testing of complete user journeys
- ⚠️ No verification of API integration (all mocked)
- ⚠️ No cross-browser compatibility assurance
- ⚠️ No performance baseline or regression detection

## Implementation Plan

### Phase 1: Infrastructure Setup (1 hour)

**Playwright Configuration**
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

**Dependencies**
```bash
npm install -D @playwright/test
npx playwright install
```

**Test Utilities**
```typescript
// tests/e2e/utils/auth.ts
export async function login(page: Page, email: string, password: string) {
  await page.goto('/auth/signin')
  await page.fill('[name="email"]', email)
  await page.fill('[name="password"]', password)
  await page.click('button[type="submit"]')
  await page.waitForURL('/dashboard')
}

// tests/e2e/utils/fixtures.ts
export const testUser = {
  email: 'test@sprintforge.com',
  password: 'Test123!',
  name: 'Test User'
}

export const testProject = {
  name: 'E2E Test Project',
  description: 'Project for E2E testing',
  template_id: 'agile-basic'
}
```

### Phase 2: Critical User Workflows (2-3 hours)

**Test 1: Authentication Flow**
```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test('complete signup and login flow', async ({ page }) => {
    // Signup
    await page.goto('/auth/signup')
    await page.fill('[name="name"]', 'New User')
    await page.fill('[name="email"]', 'newuser@test.com')
    await page.fill('[name="password"]', 'Password123!')
    await page.click('button[type="submit"]')

    // Verify email verification prompt
    await expect(page.locator('text=Check your email')).toBeVisible()

    // Login
    await page.goto('/auth/signin')
    await page.fill('[name="email"]', 'newuser@test.com')
    await page.fill('[name="password"]', 'Password123!')
    await page.click('button[type="submit"]')

    // Verify dashboard redirect
    await expect(page).toHaveURL('/dashboard')
    await expect(page.locator('text=Welcome, New User')).toBeVisible()
  })

  test('handles login errors correctly', async ({ page }) => {
    await page.goto('/auth/signin')
    await page.fill('[name="email"]', 'invalid@test.com')
    await page.fill('[name="password"]', 'wrongpassword')
    await page.click('button[type="submit"]')

    await expect(page.locator('text=Invalid credentials')).toBeVisible()
  })

  test('logout redirects to home', async ({ page }) => {
    await login(page, testUser.email, testUser.password)
    await page.click('text=Sign Out')
    await expect(page).toHaveURL('/')
  })
})
```

**Test 2: Project Creation Workflow**
```typescript
// tests/e2e/project-wizard.spec.ts
import { test, expect } from '@playwright/test'
import { login, testUser, testProject } from './utils/fixtures'

test.describe('Project Wizard', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUser.email, testUser.password)
  })

  test('complete project creation via wizard', async ({ page }) => {
    // Navigate to wizard
    await page.click('text=New Project')
    await expect(page).toHaveURL('/projects/new')

    // Step 1: Template Selection
    await page.click('[data-template="agile-basic"]')
    await page.click('text=Next')

    // Step 2: Project Basics
    await page.fill('[name="name"]', testProject.name)
    await page.fill('[name="description"]', testProject.description)
    await page.click('text=Next')

    // Step 3: Sprint Configuration
    await page.selectOption('[name="sprint_pattern"]', 'Sprint {n}')
    await page.fill('[name="sprint_duration_weeks"]', '2')
    await page.click('text=Next')

    // Step 4: Working Days
    await page.check('[name="working_days"][value="1"]') // Monday
    await page.check('[name="working_days"][value="5"]') // Friday
    await page.click('text=Next')

    // Step 5: Features
    await page.check('[name="features.monte_carlo"]')
    await page.check('[name="features.gantt_chart"]')
    await page.click('text=Next')

    // Step 6: Review and Create
    await expect(page.locator(`text=${testProject.name}`)).toBeVisible()
    await page.click('text=Create Project')

    // Verify success and redirect
    await expect(page).toHaveURL(/\/projects\/[a-f0-9-]+/)
    await expect(page.locator('text=Project created successfully')).toBeVisible()
  })

  test('validates required fields', async ({ page }) => {
    await page.click('text=New Project')
    await page.click('[data-template="agile-basic"]')
    await page.click('text=Next')

    // Try to proceed without filling required fields
    await page.click('text=Next')

    await expect(page.locator('text=Project name is required')).toBeVisible()
  })
})
```

**Test 3: Dashboard Workflow**
```typescript
// tests/e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test'
import { login, testUser } from './utils/fixtures'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUser.email, testUser.password)
  })

  test('displays statistics correctly', async ({ page }) => {
    await expect(page.locator('text=Total Projects')).toBeVisible()
    await expect(page.locator('text=Active Projects')).toBeVisible()
    await expect(page.locator('text=Excel Reports Generated')).toBeVisible()
    await expect(page.locator('text=Recent Activity')).toBeVisible()
  })

  test('search filters project list', async ({ page }) => {
    // Type in search
    await page.fill('[placeholder="Search projects..."]', 'Test Project')

    // Wait for filtered results
    await page.waitForTimeout(500) // Debounce delay

    // Verify filtered results
    await expect(page.locator('text=Test Project')).toBeVisible()
  })

  test('sort changes project order', async ({ page }) => {
    // Get initial first project
    const firstProject = await page.locator('.project-list li:first-child').textContent()

    // Click sort by name
    await page.click('button:has-text("Name")')

    // Verify order changed
    const newFirstProject = await page.locator('.project-list li:first-child').textContent()
    expect(newFirstProject).not.toBe(firstProject)
  })

  test('quick actions are functional', async ({ page }) => {
    await page.click('text=New Project')
    await expect(page).toHaveURL('/projects/new')

    await page.goBack()
    await page.click('text=Documentation')
    await expect(page).toHaveURL('/docs')
  })
})
```

**Test 4: Excel Generation Workflow**
```typescript
// tests/e2e/excel-generation.spec.ts
import { test, expect } from '@playwright/test'
import { login, testUser } from './utils/fixtures'

test.describe('Excel Generation', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUser.email, testUser.password)
  })

  test('generates and downloads Excel file', async ({ page }) => {
    // Open project action menu
    await page.click('.project-list li:first-child button[aria-label="Actions"]')

    // Start download
    const downloadPromise = page.waitForEvent('download')
    await page.click('text=Generate Excel')

    // Wait for download
    const download = await downloadPromise

    // Verify file properties
    expect(download.suggestedFilename()).toMatch(/project-.+\.xlsx/)

    // Verify activity feed updated
    await expect(page.locator('text=generated Excel report')).toBeVisible()
  })

  test('shows generation progress', async ({ page }) => {
    await page.click('.project-list li:first-child button[aria-label="Actions"]')
    await page.click('text=Generate Excel')

    // Verify loading state (brief)
    await expect(page.locator('.loading-spinner')).toBeVisible({ timeout: 1000 })
  })
})
```

**Test 5: Project Sharing Workflow**
```typescript
// tests/e2e/project-sharing.spec.ts
import { test, expect } from '@playwright/test'
import { login, testUser } from './utils/fixtures'

test.describe('Project Sharing', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUser.email, testUser.password)
  })

  test('generates public share link', async ({ page, context }) => {
    // Navigate to project
    await page.click('.project-list li:first-child a')

    // Click share button
    await page.click('button:has-text("Share")')

    // Generate public link
    await page.check('text=Make publicly accessible')
    await page.click('text=Generate Link')

    // Copy share link
    const shareLink = await page.locator('[data-share-link]').textContent()

    // Verify public badge appears
    await page.goto('/dashboard')
    await expect(page.locator('.project-list li:first-child text=Public')).toBeVisible()

    // Test public access (new incognito context)
    const incognitoPage = await context.newPage()
    await incognitoPage.goto(shareLink!)

    // Verify public view loads without auth
    await expect(incognitoPage.locator('text=Public Project View')).toBeVisible()
  })

  test('revokes public access', async ({ page }) => {
    await page.click('.project-list li:first-child a')
    await page.click('button:has-text("Share")')
    await page.uncheck('text=Make publicly accessible')
    await page.click('text=Save')

    await page.goto('/dashboard')
    await expect(page.locator('.project-list li:first-child text=Public')).not.toBeVisible()
  })
})
```

### Phase 3: Integration Tests (1 hour)

**API Integration Tests**
```typescript
// tests/integration/api.spec.ts
import { test, expect } from '@playwright/test'
import { login, testUser, testProject } from '../e2e/utils/fixtures'

test.describe('API Integration', () => {
  let authToken: string

  test.beforeAll(async ({ request }) => {
    // Get auth token
    const response = await request.post('/api/v1/auth/login', {
      data: { email: testUser.email, password: testUser.password }
    })
    const data = await response.json()
    authToken = data.token
  })

  test('CRUD operations work end-to-end', async ({ request }) => {
    // Create
    const createResponse = await request.post('/api/v1/projects', {
      headers: { Authorization: `Bearer ${authToken}` },
      data: testProject
    })
    expect(createResponse.ok()).toBeTruthy()
    const project = await createResponse.json()
    expect(project.id).toBeDefined()

    // Read
    const getResponse = await request.get(`/api/v1/projects/${project.id}`, {
      headers: { Authorization: `Bearer ${authToken}` }
    })
    expect(getResponse.ok()).toBeTruthy()

    // Update
    const updateResponse = await request.patch(`/api/v1/projects/${project.id}`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: { name: 'Updated Name' }
    })
    expect(updateResponse.ok()).toBeTruthy()

    // Delete
    const deleteResponse = await request.delete(`/api/v1/projects/${project.id}`, {
      headers: { Authorization: `Bearer ${authToken}` }
    })
    expect(deleteResponse.ok()).toBeTruthy()
  })

  test('rate limiting prevents abuse', async ({ request }) => {
    const requests = []

    // Attempt 101 requests (limit is 100/min)
    for (let i = 0; i < 101; i++) {
      requests.push(
        request.get('/api/v1/projects', {
          headers: { Authorization: `Bearer ${authToken}` }
        })
      )
    }

    const responses = await Promise.all(requests)
    const rateLimited = responses.filter(r => r.status() === 429)

    expect(rateLimited.length).toBeGreaterThan(0)
  })
})
```

### Phase 4: Visual Regression Tests (1 hour)

**Visual Tests**
```typescript
// tests/visual/dashboard.spec.ts
import { test, expect } from '@playwright/test'
import { login, testUser } from '../e2e/utils/fixtures'

test.describe('Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, testUser.email, testUser.password)
  })

  test('dashboard matches baseline', async ({ page }) => {
    await expect(page).toHaveScreenshot('dashboard-full.png', {
      fullPage: true,
      maxDiffPixels: 100
    })
  })

  test('empty state matches baseline', async ({ page, request }) => {
    // Delete all projects first
    const response = await request.get('/api/v1/projects')
    const { projects } = await response.json()

    for (const project of projects) {
      await request.delete(`/api/v1/projects/${project.id}`)
    }

    await page.reload()
    await expect(page.locator('text=No projects yet')).toBeVisible()
    await expect(page).toHaveScreenshot('dashboard-empty.png')
  })

  test('project wizard matches baseline', async ({ page }) => {
    await page.click('text=New Project')
    await expect(page).toHaveScreenshot('wizard-step-1.png')

    await page.click('[data-template="agile-basic"]')
    await page.click('text=Next')
    await expect(page).toHaveScreenshot('wizard-step-2.png')
  })

  test('responsive design at mobile width', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await expect(page).toHaveScreenshot('dashboard-mobile.png')
  })

  test('responsive design at tablet width', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    await expect(page).toHaveScreenshot('dashboard-tablet.png')
  })
})
```

### Phase 5: Documentation & CI Integration (30 minutes)

**E2E Testing Guide**
```markdown
# E2E Testing Guide

## Running Tests

### All Tests
npm run test:e2e

### Specific Browser
npm run test:e2e -- --project=chromium

### Specific Test File
npm run test:e2e -- tests/e2e/dashboard.spec.ts

### Debug Mode
npm run test:e2e -- --debug

### UI Mode (Interactive)
npm run test:e2e -- --ui

## Writing Tests

### Best Practices
1. Use data-testid attributes for stable selectors
2. Avoid brittle CSS selectors
3. Test user behavior, not implementation
4. Use Page Object Model for reusability
5. Keep tests independent and isolated

### Test Structure
- tests/e2e/ - Browser-based E2E tests
- tests/integration/ - API integration tests
- tests/visual/ - Screenshot regression tests
- tests/e2e/utils/ - Shared fixtures and helpers
```

**CI Configuration**
```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npm run test:e2e
        env:
          CI: true

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

## Test Coverage Goals

### Before (Current State)
- Unit Tests: 54 tests (86.48% coverage)
- Integration Tests: 0
- E2E Tests: 0
- Visual Tests: 0
- **Total Coverage**: ~30% of comprehensive testing

### After (Target State)
- Unit Tests: 54 tests (86.48% coverage)
- Integration Tests: 5 tests
- E2E Tests: 10 tests
- Visual Tests: 5 tests
- **Total Coverage**: ~95% of comprehensive testing

## Success Criteria

- [ ] Playwright configured and running
- [ ] 10 E2E tests covering critical user workflows
- [ ] 5 API integration tests
- [ ] 5 visual regression tests
- [ ] All tests passing in CI/CD
- [ ] Documentation complete
- [ ] Cross-browser testing enabled (Chrome, Firefox, Safari)
- [ ] Mobile/tablet responsive tests
- [ ] Test execution time <5 minutes

## Estimated Timeline

- Phase 1 (Infrastructure): 1 hour
- Phase 2 (E2E Tests): 2-3 hours
- Phase 3 (Integration): 1 hour
- Phase 4 (Visual): 1 hour
- Phase 5 (Docs/CI): 30 minutes

**Total: 5.5-6.5 hours**

## Dependencies

- Task 4.1: Project CRUD API (for API tests)
- Task 4.2: Excel Generation API (for generation tests)
- Task 4.4: Public Sharing (for sharing tests)
- Task 4.5: Project Wizard (for wizard tests)
- Task 4.6: Dashboard (for dashboard tests)

## Next Steps

1. Install Playwright and configure
2. Set up test infrastructure and utilities
3. Implement critical path E2E tests
4. Add integration and visual tests
5. Configure CI/CD pipeline
6. Document testing procedures
7. Train team on E2E test practices

## Notes

This E2E testing suite complements the existing unit tests to provide comprehensive test coverage. While unit tests validate component behavior in isolation, E2E tests validate that the entire system works together correctly from the user's perspective. This is essential for production confidence.
