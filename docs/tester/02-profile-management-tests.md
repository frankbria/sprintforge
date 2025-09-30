# Profile Management Tests - Task 2.8

## Test Overview
Visual testing for user profile management interface (Tasks 2.2, 2.5)

**Environment**: Frontend Next.js Development Server (`npm run dev`)
**URL**: http://localhost:3000/profile
**Prerequisites**: User authenticated via OAuth (complete 01-authentication-flow-tests first)

---

## Test 11: Profile Page Load and Display

### Objective
Verify profile page loads and displays user information correctly

### Steps
- [ ] Ensure you are logged in with Google or Microsoft OAuth
- [ ] Navigate to http://localhost:3000/profile
- [ ] Verify page loads without errors in browser console (F12)
- [ ] Confirm "SprintForge" logo is visible in top navigation
- [ ] Check "Profile" heading is displayed prominently
- [ ] Verify subheading "Manage your account information and preferences" is visible
- [ ] Confirm user profile card displays with avatar/placeholder
- [ ] Verify user name is displayed correctly
- [ ] Check user email is displayed correctly
- [ ] Confirm provider badge shows (e.g., "Connected via Google")
- [ ] Verify "Edit Profile" button is visible and styled properly
- [ ] Check "Account Information" section is visible
- [ ] Verify "Preferences" section is visible with toggle switches

### Expected Results
✅ Profile page loads completely
✅ All user data displayed correctly
✅ UI components render properly

### Pass Criteria
All profile elements visible with correct user data

---

## Test 12: Profile Avatar Display

### Objective
Verify user profile picture displays correctly from OAuth provider

### Steps
- [ ] On profile page, locate the profile avatar (top of profile card)
- [ ] If user has profile picture from OAuth provider:
  - [ ] Verify actual profile image is displayed (not placeholder)
  - [ ] Check image is circular and properly sized (80x80px)
  - [ ] Confirm image is not distorted or pixelated
- [ ] If user has no profile picture:
  - [ ] Verify placeholder avatar is displayed (gradient circle with user icon)
  - [ ] Check placeholder has proper gradient (blue colors)
  - [ ] Confirm SVG user icon is centered and visible

### Expected Results
✅ Profile picture displays correctly
✅ Fallback placeholder works for users without images
✅ Images are properly sized and styled

### Pass Criteria
Avatar display works for both image and placeholder states

---

## Test 13: Edit Profile - Toggle Edit Mode

### Objective
Test transitioning between view and edit modes for profile

### Steps
- [ ] From profile page, locate "Edit Profile" button (top right of profile card)
- [ ] Click "Edit Profile" button
- [ ] Verify button text changes to "Cancel"
- [ ] Confirm "Account Information" section shows input fields (not read-only text)
- [ ] Check that "Display Name" input field is populated with current name
- [ ] Verify "Email Address" input field is populated with current email
- [ ] Confirm "User ID" remains read-only with note "This cannot be changed"
- [ ] Verify "Save Changes" button appears next to "Cancel"
- [ ] Check that preference toggles become interactive (not disabled)
- [ ] Click "Cancel" button
- [ ] Verify return to view mode (input fields become read-only text)
- [ ] Confirm "Edit Profile" button reappears

### Expected Results
✅ Smooth transition between view and edit modes
✅ Form fields populate correctly
✅ Cancel button restores original state

### Pass Criteria
Edit mode toggle works without losing data or breaking UI

---

## Test 14: Edit Profile - Update Display Name

### Objective
Test updating user display name with validation

### Steps
- [ ] Click "Edit Profile" button to enter edit mode
- [ ] Click into "Display Name" input field
- [ ] Clear existing name completely
- [ ] Attempt to save without entering name
- [ ] Verify inline error message appears: "Display name is required"
- [ ] Check input field has red border indicating error
- [ ] Enter a very long name (>100 characters)
- [ ] Verify error message: "Display name must be 100 characters or less"
- [ ] Clear field and enter valid name (e.g., "Test User Updated")
- [ ] Verify error message disappears
- [ ] Check input field border returns to normal (no red border)
- [ ] Click "Save Changes" button
- [ ] Verify loading spinner appears with "Saving..." text
- [ ] Wait for save to complete (simulated 1.5 second delay)
- [ ] Confirm success: edit mode closes and new name displays
- [ ] Verify profile card shows updated name

### Expected Results
✅ Form validation works correctly
✅ Error messages clear as user types valid input
✅ Save operation completes successfully
✅ UI updates with new data

### Pass Criteria
Name update workflow functional with proper validation

---

## Test 15: Edit Profile - Update Email Address

### Objective
Test updating user email with email format validation

### Steps
- [ ] Click "Edit Profile" button to enter edit mode
- [ ] Click into "Email Address" input field
- [ ] Clear existing email completely
- [ ] Attempt to save without entering email
- [ ] Verify inline error message: "Email address is required"
- [ ] Enter invalid email format: "notanemail"
- [ ] Verify error message: "Please enter a valid email address"
- [ ] Enter invalid email format: "test@"
- [ ] Verify same error message persists
- [ ] Enter invalid email format: "@example.com"
- [ ] Verify same error message persists
- [ ] Clear field and enter valid email: "test.updated@example.com"
- [ ] Verify error message disappears
- [ ] Check input field border returns to normal
- [ ] Click "Save Changes" button
- [ ] Verify loading state with spinner
- [ ] Wait for save to complete
- [ ] Confirm email displays updated value in view mode

### Expected Results
✅ Email validation enforces proper format
✅ Multiple invalid formats caught
✅ Valid email saves successfully

### Pass Criteria
Email update workflow with comprehensive validation

---

## Test 16: Edit Profile - Form Field Character Limits

### Objective
Test input field character limits and max-length enforcement

### Steps
- [ ] Click "Edit Profile" button
- [ ] Click into "Display Name" input field
- [ ] Type or paste a string exactly 100 characters long
- [ ] Verify field accepts all 100 characters
- [ ] Try to type additional characters beyond 100
- [ ] Verify no additional characters can be entered (hard limit)
- [ ] Check no error message appears at exactly 100 characters
- [ ] Clear field and paste string with 150 characters
- [ ] Verify only first 100 characters are accepted
- [ ] Test email field has reasonable max length (no specific limit mentioned)
- [ ] Cancel out of edit mode

### Expected Results
✅ Character limits enforced at input level
✅ Users cannot exceed max length
✅ No JS errors when reaching limits

### Pass Criteria
Input length restrictions work correctly

---

## Test 17: Preferences - Email Notifications Toggle

### Objective
Test email notifications preference toggle functionality

### Steps
- [ ] Locate "Preferences" section on profile page (right side)
- [ ] Find "Email notifications" toggle switch
- [ ] Note description: "Receive email updates about your projects"
- [ ] Verify toggle is in view-only mode (disabled appearance)
- [ ] Click "Edit Profile" button to enter edit mode
- [ ] Verify toggle becomes interactive (no longer disabled appearance)
- [ ] Note current state of toggle (on/blue or off/gray)
- [ ] Click toggle to change state
- [ ] Verify toggle animates smoothly between states
- [ ] Confirm toggle color changes (blue when on, gray when off)
- [ ] Toggle back and forth multiple times to test interaction
- [ ] Click "Save Changes" button
- [ ] Verify toggle state persists after save
- [ ] Enter edit mode again and confirm state was saved

### Expected Results
✅ Toggle interactive in edit mode only
✅ Smooth animation between states
✅ State persists after save

### Pass Criteria
Email notifications toggle functional and state management works

---

## Test 18: Preferences - Project Reminders Toggle

### Objective
Test project reminders preference toggle functionality

### Steps
- [ ] In "Preferences" section, find "Project reminders" toggle
- [ ] Note description: "Get reminded about upcoming deadlines"
- [ ] Verify toggle is disabled in view mode
- [ ] Enter edit mode via "Edit Profile" button
- [ ] Verify toggle becomes interactive
- [ ] Note current state of toggle
- [ ] Click toggle to change state
- [ ] Verify toggle animates and changes color appropriately
- [ ] Toggle multiple times to test repeated interaction
- [ ] Test both toggles together (email notifications + project reminders)
- [ ] Set them to different states (one on, one off)
- [ ] Click "Save Changes"
- [ ] Verify both toggle states persist correctly after save

### Expected Results
✅ Project reminders toggle works independently
✅ Multiple toggles can be changed in same edit session
✅ States save correctly for all toggles

### Pass Criteria
Project reminders toggle functional with proper state management

---

## Test 19: Profile Save - Error Handling

### Objective
Test error handling when profile save operation fails

### Steps
- [ ] Enter edit mode by clicking "Edit Profile"
- [ ] Make changes to display name or email
- [ ] Note: Simulated API failure cannot be easily triggered in UI
- [ ] Check browser console (F12) for any save errors
- [ ] If save fails (network issue or backend down):
  - [ ] Verify error message appears at top of page
  - [ ] Confirm error message is user-friendly (not raw error)
  - [ ] Check that "Retry" button is available in error message
  - [ ] Verify form remains in edit mode with user's changes
  - [ ] Click "Retry" button
  - [ ] Verify save operation attempts again
- [ ] If save succeeds, manually test by stopping backend server:
  - [ ] Stop backend server (Ctrl+C in backend terminal)
  - [ ] Make profile changes and try to save
  - [ ] Verify appropriate error handling occurs

### Expected Results
✅ Save errors handled gracefully
✅ User-friendly error messages
✅ Retry mechanism available
✅ User changes not lost on error

### Pass Criteria
Error handling provides good user experience

---

## Test 20: Profile Navigation and Breadcrumbs

### Objective
Verify navigation between profile and other pages works correctly

### Steps
- [ ] From profile page, locate navigation bar at top
- [ ] Click "SprintForge" logo/link in top left
- [ ] Verify redirect to homepage (/)
- [ ] Navigate back to /profile
- [ ] Click "Dashboard" link in navigation
- [ ] Verify redirect to /dashboard
- [ ] Navigate back to /profile
- [ ] In profile section, locate "Sign Out" button
- [ ] Verify button is visible and accessible
- [ ] Test browser back button functionality
- [ ] Navigate: /profile → /dashboard → browser back button
- [ ] Verify return to /profile works correctly

### Expected Results
✅ All navigation links functional
✅ Browser history works correctly
✅ No broken links or dead ends

### Pass Criteria
Navigation between profile and other pages seamless

---

## Test 21: Responsive Design - Mobile Profile View

### Objective
Verify profile page is responsive on mobile devices

### Steps
- [ ] Open browser DevTools (F12)
- [ ] Toggle device toolbar (Ctrl+Shift+M)
- [ ] Select "iPhone 12 Pro" or similar mobile preset
- [ ] Navigate to /profile
- [ ] Verify page layout adapts to mobile (no horizontal scroll)
- [ ] Check navigation bar collapses appropriately (hamburger menu or stacked)
- [ ] Confirm profile card displays full-width on mobile
- [ ] Verify avatar, name, and email are readable
- [ ] Check "Edit Profile" button is easily tappable (adequate touch target)
- [ ] Test "Account Information" and "Preferences" sections stack vertically
- [ ] Enter edit mode and verify form fields are usable on mobile
- [ ] Test toggling preferences on mobile (easy to tap)
- [ ] Verify "Save Changes" and "Cancel" buttons are accessible
- [ ] Check "Danger Zone" section displays properly on mobile

### Expected Results
✅ Responsive layout on mobile
✅ All interactive elements accessible
✅ No content overflow or hidden elements

### Pass Criteria
Profile management fully functional on mobile devices

---

## Test 22: Profile Display - User ID Read-Only

### Objective
Verify User ID is displayed as read-only and cannot be edited

### Steps
- [ ] On profile page in view mode, locate "Account Information" section
- [ ] Verify "User ID" is displayed with actual user ID value
- [ ] Note ID format (should be unique identifier from OAuth provider)
- [ ] Enter edit mode by clicking "Edit Profile"
- [ ] Verify "User ID" remains in read-only format (not editable input field)
- [ ] Check that descriptive text appears: "This cannot be changed"
- [ ] Confirm User ID displays with monospace font in gray box
- [ ] Verify User ID cannot be selected for editing (no input cursor)
- [ ] Attempt to click on User ID field
- [ ] Confirm no edit functionality triggers

### Expected Results
✅ User ID displayed prominently
✅ Always read-only, never editable
✅ Clear indication it cannot be changed

### Pass Criteria
User ID display correct and properly restricted from editing

---

## Test 23: Profile Provider Badge Display

### Objective
Verify OAuth provider badge displays correctly

### Steps
- [ ] On profile page, locate provider badge below user email
- [ ] Verify badge shows green dot indicator
- [ ] Check badge text format: "Connected via [Provider Name]"
- [ ] If logged in with Google:
  - [ ] Verify text reads "Connected via Google"
- [ ] If logged in with Microsoft:
  - [ ] Verify text reads "Connected via Microsoft"
- [ ] Confirm badge styling is consistent and readable
- [ ] Check green dot is visible and properly colored
- [ ] Log out and log in with different provider
- [ ] Verify badge updates to reflect new provider

### Expected Results
✅ Provider badge displays correctly
✅ Badge reflects actual OAuth provider used
✅ Consistent styling and formatting

### Pass Criteria
Provider information accurately displayed

---

## Test 24: Profile - Cancel Edit Without Saving

### Objective
Verify canceling edit mode discards unsaved changes

### Steps
- [ ] Note current profile name and email values
- [ ] Click "Edit Profile" button
- [ ] Change display name to "Temporary Test Name"
- [ ] Change email to "temp@test.com"
- [ ] Toggle email notifications switch
- [ ] WITHOUT clicking "Save Changes", click "Cancel" button
- [ ] Verify return to view mode
- [ ] Confirm display name shows original value (not "Temporary Test Name")
- [ ] Confirm email shows original value (not "temp@test.com")
- [ ] Verify email notifications toggle returns to original state
- [ ] Enter edit mode again
- [ ] Confirm form fields show original values (changes were discarded)

### Expected Results
✅ Cancel button discards all unsaved changes
✅ Original values restored
✅ No partial saves or data corruption

### Pass Criteria
Cancel functionality properly resets form state

---

## Test 25: Profile - Multiple Edit Sessions

### Objective
Test saving profile changes multiple times in succession

### Steps
- [ ] Click "Edit Profile" and change name to "First Update"
- [ ] Click "Save Changes" and wait for completion
- [ ] Verify name updated to "First Update"
- [ ] Immediately click "Edit Profile" again
- [ ] Change name to "Second Update"
- [ ] Toggle both preference switches
- [ ] Click "Save Changes"
- [ ] Verify all changes saved correctly
- [ ] Edit profile a third time
- [ ] Change email to different value
- [ ] Click "Save Changes"
- [ ] Verify email updated successfully
- [ ] Check that all previous changes persist (name still "Second Update")

### Expected Results
✅ Multiple edit sessions work consecutively
✅ No conflicts between saves
✅ All changes persist correctly

### Pass Criteria
Profile can be edited multiple times without issues

---

## Test Summary Checklist

Complete all tests and mark overall status:

- [ ] Test 11: Profile Page Load and Display - PASSED
- [ ] Test 12: Profile Avatar Display - PASSED
- [ ] Test 13: Edit Profile - Toggle Edit Mode - PASSED
- [ ] Test 14: Edit Profile - Update Display Name - PASSED
- [ ] Test 15: Edit Profile - Update Email Address - PASSED
- [ ] Test 16: Edit Profile - Form Field Character Limits - PASSED
- [ ] Test 17: Preferences - Email Notifications Toggle - PASSED
- [ ] Test 18: Preferences - Project Reminders Toggle - PASSED
- [ ] Test 19: Profile Save - Error Handling - PASSED
- [ ] Test 20: Profile Navigation and Breadcrumbs - PASSED
- [ ] Test 21: Responsive Design - Mobile Profile View - PASSED
- [ ] Test 22: Profile Display - User ID Read-Only - PASSED
- [ ] Test 23: Profile Provider Badge Display - PASSED
- [ ] Test 24: Profile - Cancel Edit Without Saving - PASSED
- [ ] Test 25: Profile - Multiple Edit Sessions - PASSED

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