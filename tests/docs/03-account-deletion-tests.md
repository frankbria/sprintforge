# Account Deletion Tests - Task 2.8

## Test Overview
Visual testing for account deletion flow with safety confirmations (Task 2.5)

**Environment**: Frontend Next.js Development Server (`npm run dev`)
**URL**: http://localhost:3000/profile
**Prerequisites**: User authenticated via OAuth

⚠️ **Warning**: These tests involve account deletion workflows. Use test accounts only.

---

## Test 26: Danger Zone - Initial Display

### Objective
Verify Danger Zone section displays correctly with proper warnings

### Steps
- [ ] Navigate to http://localhost:3000/profile while authenticated
- [ ] Scroll down to bottom of profile page
- [ ] Locate "Danger Zone" section (red-bordered area)
- [ ] Verify section has red/warning color scheme (red border, red background)
- [ ] Check warning icon (triangle with exclamation) is visible
- [ ] Confirm heading reads "Danger Zone"
- [ ] Verify warning text: "Once you delete your account, there is no going back"
- [ ] Check all warning bullet points are visible:
  - [ ] "Permanently delete all your projects and data"
  - [ ] "Remove your account from all shared projects"
  - [ ] "Cancel any active subscriptions"
  - [ ] "Cannot be undone or recovered"
- [ ] Verify "Delete Account" button is visible
- [ ] Check button has danger styling (red color scheme)

### Expected Results
✅ Danger Zone clearly distinguished from other content
✅ Comprehensive warnings visible
✅ Delete button prominently displayed with danger styling

### Pass Criteria
All warning elements visible and properly styled to indicate risk

---

## Test 27: Delete Account Button - State Management

### Objective
Test Delete Account button state based on profile edit mode

### Steps
- [ ] From profile page, locate "Delete Account" button in Danger Zone
- [ ] Verify button is enabled and clickable (normal state)
- [ ] Hover over button to verify hover effect (darker red)
- [ ] Click "Edit Profile" button to enter edit mode
- [ ] Return to Danger Zone section
- [ ] Verify "Delete Account" button is now disabled (grayed out)
- [ ] Attempt to click disabled button
- [ ] Confirm no action occurs (button not clickable)
- [ ] Verify disabled state styling (opacity reduced, cursor not pointer)
- [ ] Click "Cancel" to exit edit mode
- [ ] Verify "Delete Account" button becomes enabled again

### Expected Results
✅ Button disabled during profile edit mode
✅ Button enabled in view mode
✅ Clear visual distinction between enabled/disabled states

### Pass Criteria
Button state management prevents accidental deletion during editing

---

## Test 28: Delete Account - Confirmation Modal Trigger

### Objective
Test opening of confirmation modal when Delete Account is clicked

### Steps
- [ ] Ensure profile is in view mode (not editing)
- [ ] Scroll to Danger Zone section
- [ ] Click "Delete Account" button
- [ ] Verify confirmation modal appears (overlaying page)
- [ ] Check modal has semi-transparent backdrop (page dimmed behind modal)
- [ ] Confirm modal centers on screen
- [ ] Verify modal heading reads "Delete Account"
- [ ] Check detailed warning message is displayed:
  - "Are you absolutely sure you want to delete your account?"
  - "This action cannot be undone and will permanently delete all your data, projects, and account information."
- [ ] Verify two action buttons are present:
  - [ ] "Cancel" button (gray/neutral styling)
  - [ ] "Yes, Delete My Account" button (red/danger styling)
- [ ] Check modal is styled consistently with application theme

### Expected Results
✅ Modal appears correctly on button click
✅ Clear confirmation message displayed
✅ Both action options available

### Pass Criteria
Confirmation modal displays with proper warnings and options

---

## Test 29: Confirmation Modal - Cancel Action

### Objective
Test canceling account deletion from confirmation modal

### Steps
- [ ] Open confirmation modal (click "Delete Account" button)
- [ ] Verify modal is displayed
- [ ] Locate "Cancel" button in modal
- [ ] Click "Cancel" button
- [ ] Verify modal closes immediately
- [ ] Confirm return to normal profile page view
- [ ] Check page backdrop returns to normal (no longer dimmed)
- [ ] Verify account is NOT deleted (page still accessible)
- [ ] Confirm user remains authenticated (avatar/name still visible)
- [ ] Try opening modal again and click outside modal area (on backdrop)
- [ ] Verify modal closes on backdrop click (if implemented)

### Expected Results
✅ Cancel button closes modal without deletion
✅ User remains on profile page
✅ No changes to account or session

### Pass Criteria
Cancel action safely exits deletion flow without making changes

---

## Test 30: Confirmation Modal - Keyboard Navigation

### Objective
Test keyboard accessibility and Escape key functionality

### Steps
- [ ] Click "Delete Account" button to open modal
- [ ] Verify modal is displayed
- [ ] Press "Escape" key on keyboard
- [ ] Verify modal closes (same as clicking Cancel)
- [ ] Open modal again
- [ ] Press "Tab" key repeatedly
- [ ] Verify focus cycles through modal buttons (Cancel → Delete → back to Cancel)
- [ ] Check focus indicator is visible (outline or highlight on focused button)
- [ ] Use "Tab" to focus "Cancel" button
- [ ] Press "Enter" or "Space" key
- [ ] Verify modal closes (keyboard activation works)
- [ ] Open modal again
- [ ] Tab to "Yes, Delete My Account" button
- [ ] Verify focus styling on danger button

### Expected Results
✅ Escape key closes modal
✅ Tab navigation works correctly
✅ Keyboard activation (Enter/Space) triggers buttons

### Pass Criteria
Full keyboard accessibility for modal interactions

---

## Test 31: Account Deletion - Loading State

### Objective
Test loading state during account deletion process

### Steps
- [ ] Click "Delete Account" button to open modal
- [ ] Click "Yes, Delete My Account" button to confirm
- [ ] Immediately observe modal state changes
- [ ] Verify loading indicator appears on "Delete" button
- [ ] Check button shows loading spinner
- [ ] Confirm button text may change or disappear during loading
- [ ] Verify both buttons become disabled during loading (cannot click Cancel)
- [ ] Check modal cannot be closed during deletion process (Escape key disabled)
- [ ] Wait for deletion to complete (simulated 2 second delay)
- [ ] Verify proper transition after loading completes

### Expected Results
✅ Clear loading state with spinner
✅ Buttons disabled during operation
✅ Modal locked during deletion process
✅ No way to interrupt deletion once started

### Pass Criteria
Loading state prevents user interference during critical operation

---

## Test 32: Account Deletion - Successful Completion

### Objective
Test complete account deletion workflow from start to finish

### Steps
- [ ] Note: Use a test account for this test
- [ ] From profile page, scroll to Danger Zone
- [ ] Click "Delete Account" button
- [ ] Verify confirmation modal appears
- [ ] Read all warnings carefully
- [ ] Click "Yes, Delete My Account" button
- [ ] Observe loading state (Test 31 steps)
- [ ] Wait for deletion to complete
- [ ] Verify automatic logout occurs
- [ ] Confirm redirect to homepage (/) or sign-in page (/auth/signin)
- [ ] Check user is no longer authenticated (no avatar/name in navigation)
- [ ] Try to navigate to /profile
- [ ] Verify redirect to sign-in page (account deleted, cannot access)
- [ ] Check browser console for any errors during process

### Expected Results
✅ Account deletion completes successfully
✅ Automatic logout and redirect
✅ Session cleared completely
✅ Account no longer accessible

### Pass Criteria
Complete deletion workflow functional from start to finish

---

## Test 33: Account Deletion - Session Cleanup

### Objective
Verify all session data and cookies are cleared after deletion

### Steps
- [ ] Before deletion, open browser DevTools (F12)
- [ ] Navigate to Application tab → Cookies
- [ ] Note existing NextAuth session cookies
- [ ] Navigate to Application tab → Local Storage
- [ ] Note any stored user data or preferences
- [ ] Perform account deletion (Test 32 steps)
- [ ] After redirect to public page, return to DevTools
- [ ] Check Application tab → Cookies
- [ ] Verify all NextAuth session cookies are removed
- [ ] Check Application tab → Local Storage
- [ ] Verify user preferences and onboarding flags are cleared
- [ ] Try to manually navigate to /dashboard
- [ ] Confirm redirect to sign-in (no cached authentication)

### Expected Results
✅ All authentication cookies removed
✅ Local storage cleaned up
✅ No residual session data

### Pass Criteria
Complete session and storage cleanup after deletion

---

## Test 34: Danger Zone - Mobile Responsive View

### Objective
Verify Danger Zone and deletion flow work on mobile devices

### Steps
- [ ] Open browser DevTools (F12)
- [ ] Toggle device toolbar (Ctrl+Shift+M)
- [ ] Select "iPhone 12 Pro" or similar mobile preset
- [ ] Navigate to /profile
- [ ] Scroll to Danger Zone section
- [ ] Verify section displays properly on mobile (no horizontal scroll)
- [ ] Check warning text is readable without zooming
- [ ] Confirm "Delete Account" button is full-width or appropriately sized
- [ ] Verify button is easily tappable (adequate touch target size)
- [ ] Tap "Delete Account" button
- [ ] Verify confirmation modal displays correctly on mobile
- [ ] Check modal fits within viewport (no content cut off)
- [ ] Confirm buttons are easily tappable
- [ ] Test tapping outside modal closes it (if implemented)
- [ ] Verify all text in modal is readable on mobile

### Expected Results
✅ Danger Zone layout adapts to mobile
✅ Deletion flow fully functional on mobile
✅ Touch-friendly UI elements

### Pass Criteria
Account deletion accessible and functional on mobile devices

---

## Test 35: Danger Zone - Accessibility Features

### Objective
Test accessibility features for account deletion flow

### Steps
- [ ] Navigate to /profile
- [ ] Use keyboard only (no mouse) to navigate to Danger Zone
- [ ] Press Tab key until "Delete Account" button receives focus
- [ ] Verify button has visible focus indicator (outline or highlight)
- [ ] Press Enter or Space to activate button
- [ ] Verify modal opens
- [ ] Use Tab to navigate through modal buttons
- [ ] Verify focus indicators on all modal interactive elements
- [ ] Press Escape to close modal
- [ ] Enable screen reader (if available: NVDA, JAWS, or browser extension)
- [ ] Navigate to Danger Zone with screen reader
- [ ] Verify warning text is read aloud
- [ ] Check button has descriptive label read by screen reader
- [ ] Open modal and verify modal content is announced
- [ ] Verify button roles and states are properly announced

### Expected Results
✅ Full keyboard navigation support
✅ Clear focus indicators
✅ Screen reader compatibility
✅ Proper ARIA labels and roles

### Pass Criteria
Account deletion flow meets accessibility standards

---

## Test 36: Danger Zone - Warning Visibility

### Objective
Verify all warning messages are clear, visible, and comprehensive

### Steps
- [ ] Navigate to /profile and locate Danger Zone
- [ ] Read through all warning text carefully
- [ ] Verify main warning: "Once you delete your account, there is no going back"
- [ ] Check all four bullet points are present and complete:
  1. [ ] "Permanently delete all your projects and data"
  2. [ ] "Remove your account from all shared projects"
  3. [ ] "Cancel any active subscriptions"
  4. [ ] "Cannot be undone or recovered"
- [ ] Open confirmation modal
- [ ] Verify modal warning is more detailed than Danger Zone warning
- [ ] Check modal emphasizes permanence: "cannot be undone"
- [ ] Confirm modal mentions: "all your data, projects, and account information"
- [ ] Verify warnings are in plain language (no technical jargon)
- [ ] Check contrast/readability of warning text (red text on red background)

### Expected Results
✅ Comprehensive warnings at multiple stages
✅ Clear consequences outlined
✅ Readable and understandable language
✅ Progressive disclosure (brief warning → detailed warning)

### Pass Criteria
Users fully informed of deletion consequences before proceeding

---

## Test 37: Account Deletion - Error Handling

### Objective
Test error handling if account deletion fails

### Steps
- [ ] Note: This test requires simulating a backend failure
- [ ] If backend is running, stop it temporarily (Ctrl+C in backend terminal)
- [ ] From profile page, click "Delete Account"
- [ ] Confirm deletion in modal
- [ ] Observe loading state begins
- [ ] Wait for operation to fail (network error or timeout)
- [ ] Verify error handling occurs (check console for errors)
- [ ] Verify modal does not close on error (user not logged out)
- [ ] Check if error message is displayed to user
- [ ] If error message shown, verify it's user-friendly
- [ ] Restart backend server
- [ ] Close modal and try deletion again
- [ ] Verify successful deletion with backend running

### Expected Results
✅ Graceful error handling
✅ User remains authenticated on error
✅ Clear error communication
✅ Ability to retry after fixing issue

### Pass Criteria
Errors handled gracefully without leaving user in bad state

---

## Test 38: Account Deletion - Visual Confirmation

### Objective
Verify visual feedback throughout deletion process

### Steps
- [ ] Navigate to /profile
- [ ] Observe Danger Zone section styling (red theme)
- [ ] Note icon, colors, and border treatment
- [ ] Click "Delete Account" button
- [ ] Verify smooth modal transition (fade in or slide in animation)
- [ ] Observe modal styling (danger colors, clear hierarchy)
- [ ] Click "Yes, Delete My Account"
- [ ] Watch for loading animations (spinner, opacity changes)
- [ ] After deletion, verify smooth redirect transition
- [ ] Check for any visual glitches or flashing during process
- [ ] Test on different browsers to ensure consistent visual feedback

### Expected Results
✅ Consistent danger theming throughout flow
✅ Smooth animations and transitions
✅ Clear visual hierarchy
✅ No visual glitches or jarring transitions

### Pass Criteria
Visual design enhances user understanding of deletion severity

---

## Test 39: Delete Account - Accidental Click Prevention

### Objective
Verify safeguards prevent accidental account deletion

### Steps
- [ ] Count the number of clicks required to delete account:
  1. [ ] Click "Delete Account" button (first barrier)
  2. [ ] Click "Yes, Delete My Account" in modal (second barrier)
- [ ] Verify two-step confirmation process exists
- [ ] Check that buttons are not positioned dangerously close to other actions
- [ ] Verify no keyboard shortcuts trigger deletion without confirmation
- [ ] Test rapid clicking: quickly click "Delete Account" twice
- [ ] Confirm modal only opens once (no double modal)
- [ ] In modal, verify accidental click on backdrop doesn't delete (only closes modal)
- [ ] Test that Escape key closes modal safely (doesn't proceed with deletion)

### Expected Results
✅ Multi-step confirmation required
✅ No accidental trigger mechanisms
✅ Safe cancellation options at each step

### Pass Criteria
Strong safeguards against accidental deletion

---

## Test 40: Post-Deletion Verification

### Objective
Verify account is truly deleted and cannot be accessed

### Steps
- [ ] After completing account deletion (Test 32)
- [ ] From logged-out state, go to /auth/signin
- [ ] Attempt to sign in with the same OAuth provider used previously
- [ ] If deletion is properly implemented:
  - [ ] Account should not exist anymore
  - [ ] OAuth may allow sign-in but create NEW account
  - [ ] Previous data should not be accessible
- [ ] If account re-creation occurs, check:
  - [ ] User ID is different from deleted account
  - [ ] No previous projects or data visible
  - [ ] Profile starts fresh (no previous preferences)
- [ ] Verify no residual data from deleted account

### Expected Results
✅ Deleted account not restorable
✅ Fresh start if OAuth sign-in occurs again
✅ No data carryover from deleted account

### Pass Criteria
Account deletion is permanent and complete

---

## Test Summary Checklist

Complete all tests and mark overall status:

- [ ] Test 26: Danger Zone - Initial Display - PASSED
- [ ] Test 27: Delete Account Button - State Management - PASSED
- [ ] Test 28: Delete Account - Confirmation Modal Trigger - PASSED
- [ ] Test 29: Confirmation Modal - Cancel Action - PASSED
- [ ] Test 30: Confirmation Modal - Keyboard Navigation - PASSED
- [ ] Test 31: Account Deletion - Loading State - PASSED
- [ ] Test 32: Account Deletion - Successful Completion - PASSED
- [ ] Test 33: Account Deletion - Session Cleanup - PASSED
- [ ] Test 34: Danger Zone - Mobile Responsive View - PASSED
- [ ] Test 35: Danger Zone - Accessibility Features - PASSED
- [ ] Test 36: Danger Zone - Warning Visibility - PASSED
- [ ] Test 37: Account Deletion - Error Handling - PASSED
- [ ] Test 38: Account Deletion - Visual Confirmation - PASSED
- [ ] Test 39: Delete Account - Accidental Click Prevention - PASSED
- [ ] Test 40: Post-Deletion Verification - PASSED

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

**Important Notes:**
- Always use test accounts for deletion tests
- Document any unexpected behavior during deletion
- Verify backend properly handles account deletion API calls