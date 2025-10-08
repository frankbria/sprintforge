# Onboarding Flow Tests - Task 2.8

## Test Overview
Visual testing for new user onboarding experience (Task 2.7)

**Environment**: Frontend Next.js Development Server (`npm run dev`)
**URL**: http://localhost:3000/onboarding
**Prerequisites**: Fresh OAuth authentication (use new test account or clear onboarding state)

---

## Test 41: Onboarding - Initial Page Load

### Objective
Verify onboarding page loads correctly for new users

### Steps
- [ ] Create new test account or clear localStorage onboarding flags
- [ ] Complete OAuth authentication (Google or Microsoft)
- [ ] Verify automatic redirect to /onboarding (for first-time users)
- [ ] Check page loads without errors in browser console (F12)
- [ ] Verify header displays "SprintForge" logo/branding
- [ ] Confirm "Skip Setup" button visible in top right
- [ ] Check progress indicator displays "Getting Started"
- [ ] Verify progress shows "1 of 3" (three total steps)
- [ ] Confirm progress bar shows 33% completion (first step)
- [ ] Check progress bar has blue color scheme
- [ ] Verify main content area displays welcome message
- [ ] Confirm step title: "Welcome to SprintForge!"
- [ ] Check step description: "Let's get you started with the basics"

### Expected Results
✅ Onboarding page loads automatically for new users
✅ All UI elements render correctly
✅ Progress tracking visible from start

### Pass Criteria
Onboarding experience begins smoothly after first authentication

---

## Test 42: Onboarding Step 1 - Welcome Screen

### Objective
Verify welcome step content and layout

### Steps
- [ ] On first step of onboarding, verify heading: "Welcome to SprintForge!"
- [ ] Check personalized greeting: "Hello, [User Name]!" (uses actual OAuth name)
- [ ] If no name from OAuth, verify fallback: "Hello, there!"
- [ ] Verify icon/illustration displayed (lightning bolt icon in blue circle)
- [ ] Check icon has proper styling (h-24 w-24, centered)
- [ ] Read welcome description text
- [ ] Verify text mentions: "Excel-based Gantt charts and sprint planning"
- [ ] Confirm navigation buttons at bottom:
  - [ ] "← Previous" button (disabled/grayed out on first step)
  - [ ] Progress dots (3 dots, first one highlighted blue)
  - [ ] "Next →" button (enabled, blue primary color)
- [ ] Check content is centered and readable
- [ ] Verify responsive layout (content adapts to window size)

### Expected Results
✅ Welcome message displays with user personalization
✅ Clear introduction to SprintForge features
✅ Navigation controls visible and functional

### Pass Criteria
Welcome step provides friendly introduction and clear path forward

---

## Test 43: Onboarding Step 2 - Key Features

### Objective
Verify features step displays product capabilities clearly

### Steps
- [ ] From Step 1, click "Next →" button
- [ ] Verify smooth transition to Step 2 (no page reload)
- [ ] Check progress bar updates to 66% (second step)
- [ ] Verify progress indicator shows "2 of 3"
- [ ] Confirm step title: "Key Features"
- [ ] Check step description: "Discover what SprintForge can do for you"
- [ ] Verify four feature cards are displayed in grid layout
- [ ] Check Feature 1: "Excel-Based Gantt Charts"
  - [ ] Green icon with checkmark
  - [ ] Description: "Generate sophisticated project timelines without macros"
- [ ] Check Feature 2: "Sprint Planning"
  - [ ] Blue icon with graph
  - [ ] Description: "Plan and track your agile development cycles"
- [ ] Check Feature 3: "Probabilistic Timelines"
  - [ ] Purple icon with bar chart
  - [ ] Description: "Monte Carlo simulations for realistic project estimates"
- [ ] Check Feature 4: "Team Collaboration"
  - [ ] Orange icon with people
  - [ ] Description: "Share projects and coordinate with your team"
- [ ] Verify grid layout (2x2 on desktop, stacked on mobile)
- [ ] Check navigation buttons:
  - [ ] "← Previous" now enabled
  - [ ] Middle dot highlighted
  - [ ] "Next →" button enabled

### Expected Results
✅ Feature overview clearly presented
✅ Icons and descriptions readable
✅ Grid layout responsive

### Pass Criteria
Users understand core product features from this step

---

## Test 44: Onboarding Step 3 - Project Creation Guide

### Objective
Verify final step explains project creation process

### Steps
- [ ] From Step 2, click "Next →" button
- [ ] Verify transition to Step 3 (final step)
- [ ] Check progress bar updates to 100% completion
- [ ] Verify progress indicator shows "3 of 3"
- [ ] Confirm step title: "Creating Your First Project"
- [ ] Check step description: "Learn how to set up a new project"
- [ ] Verify numbered process steps displayed in gray box:
  1. [ ] "Define project scope and timeline" (with blue numbered badge)
  2. [ ] "Add tasks and dependencies" (with blue numbered badge)
  3. [ ] "Configure team members and roles" (with blue numbered badge)
  4. [ ] "Generate Excel files and track progress" (with blue numbered badge)
- [ ] Check "Pro Tip" callout box is visible (blue background)
- [ ] Verify Pro Tip icon and content:
  - [ ] Info icon displayed
  - [ ] Text: "Start with a simple project to familiarize yourself..."
- [ ] Verify navigation buttons:
  - [ ] "← Previous" enabled
  - [ ] Last progress dot highlighted
  - [ ] "Get Started →" button (changed from "Next")

### Expected Results
✅ Project creation process clearly outlined
✅ Helpful tip provided
✅ Final CTA button indicates completion

### Pass Criteria
Users understand how to create their first project

---

## Test 45: Onboarding Navigation - Previous Button

### Objective
Test backward navigation through onboarding steps

### Steps
- [ ] Navigate to Step 3 (final step) of onboarding
- [ ] Click "← Previous" button
- [ ] Verify return to Step 2 (Key Features)
- [ ] Check progress bar updates back to 66%
- [ ] Confirm progress indicator shows "2 of 3"
- [ ] Verify Step 2 content displays correctly
- [ ] Click "← Previous" again
- [ ] Verify return to Step 1 (Welcome)
- [ ] Check progress bar returns to 33%
- [ ] Verify progress indicator shows "1 of 3"
- [ ] Confirm "← Previous" button is now disabled
- [ ] Check button styling shows disabled state (grayed out)
- [ ] Verify clicking disabled button does nothing

### Expected Results
✅ Backward navigation works correctly
✅ Progress tracking updates properly
✅ Previous button disabled on first step

### Pass Criteria
Users can navigate backward through onboarding freely

---

## Test 46: Onboarding Navigation - Progress Dots

### Objective
Verify progress indicator dots reflect current step

### Steps
- [ ] Start onboarding from Step 1
- [ ] Locate three progress dots between navigation buttons
- [ ] Verify first dot is highlighted blue
- [ ] Check second and third dots are gray
- [ ] Click "Next →" to move to Step 2
- [ ] Verify second dot now highlighted blue
- [ ] Check first dot changes to lighter blue (completed state)
- [ ] Verify third dot remains gray
- [ ] Click "Next →" to move to Step 3
- [ ] Verify third dot highlighted blue
- [ ] Check first two dots show completed state (lighter blue)
- [ ] Navigate backward and verify dots update correctly

### Expected Results
✅ Progress dots accurately show current step
✅ Completed steps visually distinguished
✅ Future steps clearly marked as incomplete

### Pass Criteria
Visual progress indicator helps users track position in flow

---

## Test 47: Onboarding - Skip Setup Flow

### Objective
Test ability to skip onboarding and go directly to dashboard

### Steps
- [ ] Start fresh onboarding (Step 1)
- [ ] Locate "Skip Setup" button in top right of header
- [ ] Verify button is visible and styled as ghost/secondary button
- [ ] Click "Skip Setup" button
- [ ] Verify immediate redirect to /dashboard
- [ ] Check onboarding is marked as completed (not shown again)
- [ ] Verify user preferences are NOT initialized (default state)
- [ ] Open browser DevTools → Application → Local Storage
- [ ] Check for onboarding completion flag: `onboarding-completed-[userId]`
- [ ] Verify flag value is 'true'
- [ ] Log out and log back in with same account
- [ ] Confirm no redirect to /onboarding (skip was permanent)

### Expected Results
✅ Skip button immediately exits onboarding
✅ Onboarding marked complete
✅ User not shown onboarding again

### Pass Criteria
Experienced users can bypass onboarding efficiently

---

## Test 48: Onboarding Completion - Get Started

### Objective
Test completing onboarding and preference initialization

### Steps
- [ ] Start fresh onboarding flow
- [ ] Navigate through all three steps using "Next →" buttons
- [ ] On Step 3 (final step), click "Get Started →" button
- [ ] Verify button shows loading state:
  - [ ] Loading spinner appears
  - [ ] Button text changes to "Setting up..."
- [ ] Wait for completion (simulated 1 second delay)
- [ ] Verify redirect to /dashboard
- [ ] Open browser DevTools → Application → Local Storage
- [ ] Check onboarding completion flag exists: `onboarding-completed-[userId]`
- [ ] Check user preferences initialized: `user-preferences-[userId]`
- [ ] Verify default preferences JSON contains:
  - [ ] `theme: 'light'`
  - [ ] `emailNotifications: true`
  - [ ] `projectReminders: true`
  - [ ] `weeklyDigest: false`
  - [ ] `completedAt: [ISO timestamp]`
- [ ] Log out and log in again
- [ ] Confirm no redirect to /onboarding

### Expected Results
✅ Completion initializes user preferences
✅ Loading state provides feedback
✅ Successful redirect to dashboard
✅ Onboarding not shown again

### Pass Criteria
Completing onboarding properly sets up user account

---

## Test 49: Onboarding - Authentication Check

### Objective
Verify unauthenticated users cannot access onboarding

### Steps
- [ ] Log out completely (clear all cookies and sessions)
- [ ] Navigate directly to http://localhost:3000/onboarding
- [ ] Verify automatic redirect to /auth/signin
- [ ] Check no onboarding content is briefly visible (no flash)
- [ ] Authenticate via OAuth
- [ ] If using fresh account, verify redirect back to /onboarding
- [ ] If using existing account with completed onboarding:
  - [ ] Verify redirect to /dashboard instead

### Expected Results
✅ Onboarding requires authentication
✅ Proper redirect for unauthenticated users
✅ No content leakage before redirect

### Pass Criteria
Onboarding properly protected behind authentication

---

## Test 50: Onboarding - Returning User Behavior

### Objective
Verify users who completed onboarding don't see it again

### Steps
- [ ] Complete onboarding flow fully (Test 48)
- [ ] Log out after completion
- [ ] Log in again with same OAuth account
- [ ] Verify automatic redirect to /dashboard (NOT /onboarding)
- [ ] Manually navigate to http://localhost:3000/onboarding
- [ ] Verify automatic redirect to /dashboard (onboarding bypassed)
- [ ] Check browser DevTools → Application → Local Storage
- [ ] Confirm onboarding flag still exists and is 'true'
- [ ] Test with different browser (to verify server-side tracking if implemented)

### Expected Results
✅ Completed onboarding not shown again
✅ Direct navigation redirects to dashboard
✅ Onboarding state persists across sessions

### Pass Criteria
Onboarding is one-time experience for each user

---

## Test 51: Onboarding - Mobile Responsive Design

### Objective
Test onboarding experience on mobile devices

### Steps
- [ ] Open browser DevTools (F12)
- [ ] Toggle device toolbar (Ctrl+Shift+M)
- [ ] Select "iPhone 12 Pro" or similar mobile preset
- [ ] Start fresh onboarding flow
- [ ] Verify header adapts to mobile (logo and "Skip Setup" both visible)
- [ ] Check progress bar displays full-width
- [ ] Verify progress indicator "1 of 3" is readable
- [ ] On Step 1:
  - [ ] Check icon/illustration displays at appropriate size
  - [ ] Verify text is readable without zooming
  - [ ] Confirm navigation buttons are tappable (adequate touch targets)
- [ ] Navigate to Step 2:
  - [ ] Verify feature cards stack vertically on mobile
  - [ ] Check all four features visible (no hidden cards)
  - [ ] Confirm icons and text are readable
- [ ] Navigate to Step 3:
  - [ ] Verify numbered steps display clearly
  - [ ] Check Pro Tip box fits within viewport
- [ ] Test all navigation throughout mobile flow
- [ ] Complete onboarding on mobile and verify redirect works

### Expected Results
✅ Responsive layout adapts to mobile
✅ All content readable and accessible
✅ Touch-friendly navigation

### Pass Criteria
Full onboarding experience functional on mobile devices

---

## Test 52: Onboarding - Keyboard Navigation

### Objective
Test keyboard accessibility throughout onboarding

### Steps
- [ ] Start fresh onboarding flow
- [ ] Use Tab key to navigate through interactive elements
- [ ] Verify focus moves in logical order:
  1. [ ] "Skip Setup" button
  2. [ ] "← Previous" button (disabled on Step 1)
  3. [ ] "Next →" button
- [ ] Check visible focus indicators on all buttons (outline or highlight)
- [ ] Press Enter or Space on "Next →" button
- [ ] Verify advancement to next step
- [ ] Continue keyboard navigation through all steps
- [ ] Test Enter/Space on "Get Started →" button on final step
- [ ] Verify completion and redirect work with keyboard
- [ ] Test Tab + Shift (backward tab navigation)
- [ ] Verify no keyboard traps (can always navigate forward/backward)

### Expected Results
✅ Full keyboard navigation support
✅ Clear focus indicators
✅ Logical tab order
✅ All actions triggerable via keyboard

### Pass Criteria
Onboarding meets keyboard accessibility standards

---

## Test 53: Onboarding - Animation and Transitions

### Objective
Verify smooth transitions between onboarding steps

### Steps
- [ ] Start onboarding flow
- [ ] Observe initial page load animation
- [ ] Click "Next →" button to move from Step 1 to Step 2
- [ ] Watch for transition animation (fade, slide, or crossfade)
- [ ] Verify transition is smooth (no jarring jumps)
- [ ] Check progress bar animates smoothly (33% → 66%)
- [ ] Click "Next →" again (Step 2 → Step 3)
- [ ] Observe transition and progress bar animation (66% → 100%)
- [ ] Click "← Previous" to go backward
- [ ] Verify reverse transition is equally smooth
- [ ] Check progress dots animate when changing states
- [ ] On final step, observe "Get Started →" button loading animation
- [ ] Verify no visual glitches during any transitions

### Expected Results
✅ Smooth transitions between steps
✅ Progress animations provide feedback
✅ No jarring visual changes
✅ Professional, polished feel

### Pass Criteria
Transitions enhance user experience without distraction

---

## Test 54: Onboarding - Content Accuracy

### Objective
Verify all onboarding content is accurate and helpful

### Steps
- [ ] Read through all onboarding content carefully
- [ ] Step 1 - Welcome:
  - [ ] Verify user name displays correctly from OAuth
  - [ ] Check description accurately represents SprintForge purpose
- [ ] Step 2 - Key Features:
  - [ ] Verify all four features are actual product capabilities
  - [ ] Check descriptions are accurate and clear
  - [ ] Confirm icons match feature descriptions
- [ ] Step 3 - Project Creation:
  - [ ] Verify four-step process matches actual project creation flow
  - [ ] Check Pro Tip is genuinely helpful advice
  - [ ] Confirm no outdated or incorrect information
- [ ] Check for typos, grammatical errors, or formatting issues
- [ ] Verify all text uses consistent tone and voice

### Expected Results
✅ All content accurate and up-to-date
✅ Clear, helpful information
✅ Professional writing quality

### Pass Criteria
Onboarding content provides real value to new users

---

## Test 55: Onboarding - Browser Compatibility

### Objective
Test onboarding across different browsers

### Steps

**Chrome:**
- [ ] Complete full onboarding flow in Chrome
- [ ] Verify animations work correctly
- [ ] Check localStorage persistence
- [ ] Verify no console errors

**Firefox:**
- [ ] Complete full onboarding flow in Firefox
- [ ] Verify animations work correctly
- [ ] Check localStorage persistence
- [ ] Verify no console errors

**Safari (if available):**
- [ ] Complete full onboarding flow in Safari
- [ ] Verify animations work correctly
- [ ] Check localStorage persistence works (Safari can restrict)
- [ ] Verify no console errors

### Expected Results
✅ Consistent experience across browsers
✅ No browser-specific issues
✅ All features functional

### Pass Criteria
Onboarding works in all major browsers

---

## Test Summary Checklist

Complete all tests and mark overall status:

- [ ] Test 41: Onboarding - Initial Page Load - PASSED
- [ ] Test 42: Onboarding Step 1 - Welcome Screen - PASSED
- [ ] Test 43: Onboarding Step 2 - Key Features - PASSED
- [ ] Test 44: Onboarding Step 3 - Project Creation Guide - PASSED
- [ ] Test 45: Onboarding Navigation - Previous Button - PASSED
- [ ] Test 46: Onboarding Navigation - Progress Dots - PASSED
- [ ] Test 47: Onboarding - Skip Setup Flow - PASSED
- [ ] Test 48: Onboarding Completion - Get Started - PASSED
- [ ] Test 49: Onboarding - Authentication Check - PASSED
- [ ] Test 50: Onboarding - Returning User Behavior - PASSED
- [ ] Test 51: Onboarding - Mobile Responsive Design - PASSED
- [ ] Test 52: Onboarding - Keyboard Navigation - PASSED
- [ ] Test 53: Onboarding - Animation and Transitions - PASSED
- [ ] Test 54: Onboarding - Content Accuracy - PASSED
- [ ] Test 55: Onboarding - Browser Compatibility - PASSED

---

## Notes and Issues

**Issue Log:**
```
Issue #: [Number]
Test: [Test Name]
Description: [What went wrong]
Severity: [Critical/High/Medium/Low]
Screenshot: [Path or description]
Status: [Open/Fixed/Won't Fix]
```

**Testing Environment:**
- Browser: __________________
- OS: __________________
- Date Tested: __________________
- Tester Name: __________________