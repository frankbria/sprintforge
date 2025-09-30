# Authentication Flow Tests - Task 2.8

## Test Overview
Visual testing for Google/Microsoft OAuth authentication flows (Tasks 2.1-2.3)

**Environment**: Frontend Next.js Development Server (`npm run dev`)
**URL**: http://localhost:3000
**Prerequisites**: Backend running on http://localhost:8000

---

## Test 1: Sign-In Page Load and Display

### Objective
Verify sign-in page loads correctly with all authentication providers

### Steps
- [ ] Navigate to http://localhost:3000/auth/signin
- [ ] Verify page loads without errors in browser console (F12)
- [ ] Confirm SprintForge logo is displayed in header
- [ ] Verify "Welcome to SprintForge" heading is visible
- [ ] Check that description text is readable and properly formatted
- [ ] Confirm authentication provider buttons are displayed
- [ ] Verify Google provider button shows Google icon and text
- [ ] Verify Microsoft provider button shows Microsoft icon and text
- [ ] Check "Secure Authentication" section shows OAuth 2.0 and Encrypted badges
- [ ] Verify footer shows Terms of Service and Privacy Policy links
- [ ] Check keyboard navigation hint is displayed at bottom

### Expected Results
✅ Page loads completely without errors
✅ All UI elements render correctly
✅ Provider buttons are interactive and styled properly
✅ Security badges are visible

### Pass Criteria
All checkboxes completed with no visual or functional issues

---

## Test 2: Google OAuth Authentication Flow

### Objective
Complete full Google OAuth authentication workflow

### Steps
- [ ] From sign-in page, click "Continue with Google" button
- [ ] Verify button shows loading spinner and "Signing in with Google..." text
- [ ] Confirm redirect to Google OAuth consent screen (accounts.google.com)
- [ ] Select a Google account from the list
- [ ] On consent screen, verify SprintForge app name and permissions
- [ ] Click "Allow" or "Continue" to grant permissions
- [ ] Wait for redirect back to SprintForge application
- [ ] Verify redirect lands on homepage (/) or dashboard (/dashboard)
- [ ] Confirm user is authenticated (check for user avatar/name in navigation)
- [ ] Verify no error messages are displayed
- [ ] Check browser console for any authentication errors

### Expected Results
✅ Smooth redirect to Google OAuth
✅ Successful authentication and callback
✅ User session established
✅ No console errors

### Pass Criteria
User successfully authenticated via Google OAuth without errors

---

## Test 3: Microsoft OAuth Authentication Flow

### Objective
Complete full Microsoft OAuth authentication workflow

### Steps
- [ ] Clear browser cookies and session data (to test fresh login)
- [ ] Navigate to http://localhost:3000/auth/signin
- [ ] Click "Continue with Microsoft" button
- [ ] Verify button shows loading spinner and "Signing in with Microsoft..." text
- [ ] Confirm redirect to Microsoft login page (login.microsoftonline.com)
- [ ] Enter Microsoft account credentials and sign in
- [ ] On consent screen, verify SprintForge app name and permissions
- [ ] Click "Accept" to grant permissions
- [ ] Wait for redirect back to SprintForge application
- [ ] Verify redirect lands on homepage (/) or dashboard (/dashboard)
- [ ] Confirm user is authenticated (check for user avatar/name in navigation)
- [ ] Verify no error messages are displayed
- [ ] Check browser console for any authentication errors

### Expected Results
✅ Smooth redirect to Microsoft OAuth
✅ Successful authentication and callback
✅ User session established
✅ No console errors

### Pass Criteria
User successfully authenticated via Microsoft OAuth without errors

---

## Test 4: Session Persistence Across Page Refresh

### Objective
Verify authentication session persists after browser refresh

### Steps
- [ ] Ensure you are logged in (use Test 2 or Test 3)
- [ ] Note current page URL (e.g., /dashboard)
- [ ] Press F5 or click browser refresh button
- [ ] Wait for page to reload completely
- [ ] Verify user remains authenticated (user avatar/name still visible)
- [ ] Confirm no redirect to sign-in page occurred
- [ ] Check that user data is displayed correctly
- [ ] Verify no "Loading authentication..." spinner appears indefinitely
- [ ] Open browser DevTools → Application → Cookies
- [ ] Verify NextAuth session cookies are present

### Expected Results
✅ User session persists after refresh
✅ No re-authentication required
✅ Session cookies present

### Pass Criteria
Authentication state maintained across page reload

---

## Test 5: Protected Route Access (Unauthenticated)

### Objective
Verify unauthenticated users cannot access protected routes

### Steps
- [ ] Clear browser cookies and session data completely
- [ ] Navigate directly to http://localhost:3000/dashboard
- [ ] Verify automatic redirect to /auth/signin occurs
- [ ] Confirm sign-in page loads
- [ ] Note URL changes from /dashboard to /auth/signin
- [ ] Try navigating to http://localhost:3000/profile
- [ ] Verify redirect to /auth/signin occurs again
- [ ] Try navigating to http://localhost:3000/onboarding
- [ ] Verify redirect to /auth/signin occurs

### Expected Results
✅ Unauthenticated users redirected to sign-in
✅ Protected routes not accessible
✅ No error pages displayed

### Pass Criteria
All protected routes require authentication

---

## Test 6: Logout Functionality

### Objective
Verify user can successfully log out and session is cleared

### Steps
- [ ] Ensure you are logged in (use Test 2 or Test 3)
- [ ] Navigate to http://localhost:3000/dashboard or /profile
- [ ] Locate "Sign Out" or "Logout" button in navigation
- [ ] Click the logout button
- [ ] Verify immediate redirect to homepage or sign-in page
- [ ] Confirm user avatar/name removed from navigation
- [ ] Try to navigate back to /dashboard
- [ ] Verify redirect to /auth/signin occurs (no access to protected route)
- [ ] Open browser DevTools → Application → Cookies
- [ ] Verify NextAuth session cookies are removed or expired

### Expected Results
✅ Successful logout with session cleared
✅ Redirect to public page
✅ Protected routes no longer accessible
✅ Session cookies removed

### Pass Criteria
Complete logout with proper cleanup and protection

---

## Test 7: Error Handling - Provider Not Available

### Objective
Test error handling when authentication provider fails to load

### Steps
- [ ] Open browser DevTools → Network tab
- [ ] Navigate to http://localhost:3000/auth/signin
- [ ] In Network tab, enable "Offline" mode (or throttle to "Offline")
- [ ] Refresh the page
- [ ] Verify error message appears: "Failed to load authentication options"
- [ ] Confirm error is displayed in user-friendly format (not raw error)
- [ ] Check that a "Retry" or "Refresh" button is available
- [ ] Disable offline mode in Network tab
- [ ] Click "Retry" or "Refresh" button
- [ ] Verify page reloads and providers appear correctly

### Expected Results
✅ Graceful error handling
✅ Clear error message displayed
✅ Recovery option provided

### Pass Criteria
Error state handled properly with user recovery path

---

## Test 8: Mobile Responsive - Authentication Flow

### Objective
Verify authentication works on mobile viewport sizes

### Steps
- [ ] Open browser DevTools (F12)
- [ ] Toggle device toolbar (Ctrl+Shift+M or Cmd+Shift+M)
- [ ] Select "iPhone 12 Pro" or similar mobile device preset
- [ ] Navigate to http://localhost:3000/auth/signin
- [ ] Verify page layout adapts to mobile screen (no horizontal scroll)
- [ ] Confirm provider buttons are full-width and easily tappable
- [ ] Check that text is readable without zooming
- [ ] Tap "Continue with Google" button
- [ ] Verify OAuth flow works on mobile (external redirect and callback)
- [ ] After authentication, check dashboard/profile on mobile view
- [ ] Verify navigation menu is accessible (hamburger menu if present)

### Expected Results
✅ Responsive design works on mobile
✅ Authentication flow functions on mobile
✅ Touch-friendly UI elements

### Pass Criteria
Full authentication workflow functional on mobile devices

---

## Test 9: API Authentication - Backend Token Validation

### Objective
Verify JWT tokens are sent with API requests and validated by backend

### Steps
- [ ] Ensure you are logged in (use Test 2 or Test 3)
- [ ] Open browser DevTools → Network tab
- [ ] Navigate to a page that makes API calls (e.g., /dashboard)
- [ ] In Network tab, filter for "Fetch/XHR" requests
- [ ] Locate API requests to backend (http://localhost:8000/api/v1/...)
- [ ] Click on an API request and view "Headers" tab
- [ ] Verify "Authorization" header is present with "Bearer [token]" format
- [ ] Check Response status code is 200 (not 401 Unauthorized)
- [ ] Log out and try to access the same page
- [ ] Verify API requests either don't fire or return 401 status

### Expected Results
✅ JWT tokens included in API requests
✅ Backend validates tokens successfully
✅ Unauthenticated requests rejected

### Pass Criteria
API authentication middleware working correctly

---

## Test 10: Browser Compatibility - Chrome, Firefox, Safari

### Objective
Verify authentication works across major browsers

### Steps

**Chrome:**
- [ ] Test complete OAuth flow in Google Chrome (Tests 2 & 3)
- [ ] Verify no console errors specific to Chrome
- [ ] Check session persistence works

**Firefox:**
- [ ] Test complete OAuth flow in Mozilla Firefox (Tests 2 & 3)
- [ ] Verify no console errors specific to Firefox
- [ ] Check session persistence works

**Safari (if available):**
- [ ] Test complete OAuth flow in Safari (Tests 2 & 3)
- [ ] Verify no console errors specific to Safari
- [ ] Check session persistence works
- [ ] Verify cookies are not blocked by Safari's tracking prevention

### Expected Results
✅ Authentication works in all browsers
✅ Consistent behavior across browsers
✅ No browser-specific errors

### Pass Criteria
Full authentication support in Chrome, Firefox, and Safari

---

## Test Summary Checklist

Complete all tests and mark overall status:

- [ ] Test 1: Sign-In Page Load and Display - PASSED
- [ ] Test 2: Google OAuth Authentication Flow - PASSED
- [ ] Test 3: Microsoft OAuth Authentication Flow - PASSED
- [ ] Test 4: Session Persistence - PASSED
- [ ] Test 5: Protected Route Access - PASSED
- [ ] Test 6: Logout Functionality - PASSED
- [ ] Test 7: Error Handling - PASSED
- [ ] Test 8: Mobile Responsive - PASSED
- [ ] Test 9: API Authentication - PASSED
- [ ] Test 10: Browser Compatibility - PASSED

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
- Node Version: __________________
- Date Tested: __________________
- Tester Name: __________________