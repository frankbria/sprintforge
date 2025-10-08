# Security Testing - Task 2.8

## Test Overview
Visual and functional security testing for authentication system (Task 2.6)

**Environment**: Frontend + Backend Development Servers
**Frontend URL**: http://localhost:3000
**Backend URL**: http://localhost:8000
**Prerequisites**: Both servers running, test accounts available

⚠️ **Note**: Security tests may involve simulating attacks. Use test environment only.

---

## Test 56: Token Security - JWT Storage

### Objective
Verify JWT tokens are stored securely and not exposed

### Steps
- [ ] Log in with OAuth (Google or Microsoft)
- [ ] Open browser DevTools (F12) → Application tab
- [ ] Navigate to Local Storage section
- [ ] Verify NO JWT tokens stored in localStorage
- [ ] Navigate to Session Storage section
- [ ] Verify NO JWT tokens stored in sessionStorage
- [ ] Navigate to Cookies section
- [ ] Check for NextAuth session cookies (should be HTTP-only)
- [ ] Verify cookie attributes:
  - [ ] `HttpOnly` flag set (prevents JavaScript access)
  - [ ] `Secure` flag set (HTTPS only - may not be set in dev)
  - [ ] `SameSite=Lax` or `SameSite=Strict` (CSRF protection)
- [ ] Open DevTools → Console
- [ ] Try to access cookies via JavaScript: `document.cookie`
- [ ] Verify JWT tokens are NOT visible in console output

### Expected Results
✅ Tokens stored in HTTP-only cookies only
✅ No token exposure via localStorage/sessionStorage
✅ Proper cookie security flags set

### Pass Criteria
JWT tokens cannot be accessed by JavaScript (XSS protection)

---

## Test 57: CSRF Protection - Token Validation

### Objective
Verify CSRF protection is enabled and functional

### Steps
- [ ] Log in to application
- [ ] Open browser DevTools → Application → Cookies
- [ ] Locate CSRF token cookie (e.g., `__Host-next-auth.csrf-token`)
- [ ] Verify CSRF cookie exists
- [ ] Open DevTools → Network tab
- [ ] Trigger an authenticated action (e.g., save profile)
- [ ] In Network tab, find the API request
- [ ] Click request → Headers tab
- [ ] Verify CSRF token included in request headers or body
- [ ] Check backend validates CSRF token (response is 200, not 403)
- [ ] Attempt to make API request without CSRF token (using curl or Postman):
  ```bash
  curl -X POST http://localhost:8000/api/v1/profile \
    -H "Authorization: Bearer [token]" \
    -H "Content-Type: application/json" \
    -d '{"name": "Test"}'
  ```
- [ ] Verify request is rejected (401 or 403 status)

### Expected Results
✅ CSRF tokens generated and validated
✅ Requests without valid CSRF tokens rejected
✅ NextAuth CSRF protection enabled

### Pass Criteria
CSRF attacks prevented through token validation

---

## Test 58: Rate Limiting - Login Attempts

### Objective
Test rate limiting on authentication endpoints

### Steps
- [ ] Log out completely
- [ ] Navigate to /auth/signin
- [ ] Attempt to sign in with Google OAuth
- [ ] Complete sign-in successfully (baseline test)
- [ ] Log out
- [ ] Rapidly attempt multiple sign-ins (5-10 times in quick succession)
- [ ] Observe for rate limiting responses:
  - [ ] Error message about too many attempts
  - [ ] Temporary lockout notification
  - [ ] Increased delay between attempts
- [ ] Check browser console for rate limit errors
- [ ] Wait for rate limit timeout (if implemented)
- [ ] Verify sign-in works again after timeout

**Note**: Rate limiting may be on backend API endpoints rather than OAuth providers.

### Expected Results
✅ Rate limiting active on authentication endpoints
✅ Clear communication to user about rate limits
✅ Automatic recovery after timeout

### Pass Criteria
Brute force attacks mitigated through rate limiting

---

## Test 59: Session Timeout - Token Expiration

### Objective
Verify JWT tokens expire and refresh properly

### Steps
- [ ] Log in to application
- [ ] Note current time and expected token expiration (check NextAuth config)
- [ ] Open browser DevTools → Application → Cookies
- [ ] Check session cookie expiration time
- [ ] Wait for token to approach expiration (or manually set short expiration in config)
- [ ] Perform authenticated action (e.g., load profile page)
- [ ] Verify automatic token refresh occurs (check Network tab for refresh requests)
- [ ] Confirm no user disruption (no logout or error)
- [ ] If token expires completely without refresh:
  - [ ] Verify automatic redirect to sign-in page
  - [ ] Check user session is cleared
- [ ] Verify no "token expired" errors visible to user (graceful handling)

### Expected Results
✅ Tokens have reasonable expiration time
✅ Automatic refresh before expiration
✅ Graceful handling of expired tokens

### Pass Criteria
Session management prevents indefinite token validity

---

## Test 60: Token Blacklisting - Logout Security

### Objective
Verify tokens cannot be reused after logout

### Steps
- [ ] Log in to application
- [ ] Open browser DevTools → Network tab
- [ ] Perform an authenticated API call (e.g., GET /api/v1/profile)
- [ ] In Network tab, right-click request → Copy → Copy as cURL
- [ ] Save the cURL command (contains Authorization header with token)
- [ ] Execute the cURL command in terminal
- [ ] Verify request succeeds (200 status)
- [ ] Log out of application
- [ ] Execute the same cURL command again with old token
- [ ] Verify request fails (401 Unauthorized)
- [ ] Check response message indicates invalid or expired token
- [ ] Verify token cannot be reused even if not technically expired

### Expected Results
✅ Tokens invalidated on logout
✅ Old tokens cannot access protected resources
✅ Token blacklisting or revocation implemented

### Pass Criteria
Logout properly invalidates session tokens

---

## Test 61: Protected Routes - Authentication Enforcement

### Objective
Verify all protected routes require valid authentication

### Steps
- [ ] Log out completely
- [ ] Attempt to access each protected route directly:
  - [ ] http://localhost:3000/dashboard
  - [ ] http://localhost:3000/profile
  - [ ] http://localhost:3000/onboarding
  - [ ] Any other protected routes in application
- [ ] For each route:
  - [ ] Verify automatic redirect to /auth/signin
  - [ ] Check no protected content is briefly visible (no flash)
  - [ ] Confirm browser console shows no sensitive data
- [ ] Log in successfully
- [ ] Verify access to protected routes now allowed
- [ ] Log out via logout button
- [ ] Verify immediate revocation of access to protected routes

### Expected Results
✅ All protected routes redirect unauthenticated users
✅ No content leakage before redirect
✅ Authentication enforcement consistent

### Pass Criteria
Route protection prevents unauthorized access

---

## Test 62: API Authentication - Backend Validation

### Objective
Test backend API authentication middleware

### Steps
- [ ] Log in to application
- [ ] Open browser DevTools → Network tab
- [ ] Navigate to page that makes API calls
- [ ] In Network tab, find API requests to backend
- [ ] Verify all protected API endpoints include Authorization header
- [ ] Check header format: `Authorization: Bearer [jwt_token]`
- [ ] Note one API endpoint URL (e.g., GET /api/v1/user/profile)
- [ ] Use curl to call API without authentication:
  ```bash
  curl http://localhost:8000/api/v1/user/profile
  ```
- [ ] Verify request rejected (401 Unauthorized)
- [ ] Use curl with invalid token:
  ```bash
  curl -H "Authorization: Bearer invalid_token" \
    http://localhost:8000/api/v1/user/profile
  ```
- [ ] Verify request rejected (401 Unauthorized)
- [ ] Check error response is descriptive but not revealing (no stack traces)

### Expected Results
✅ All API endpoints validate JWT tokens
✅ Invalid or missing tokens rejected
✅ Error responses secure and informative

### Pass Criteria
Backend properly validates authentication on all protected endpoints

---

## Test 63: Password Security - OAuth Provider Security

### Objective
Verify SprintForge doesn't handle or store passwords

### Steps
- [ ] Inspect frontend codebase (sign-in page source)
- [ ] Verify NO password input fields exist
- [ ] Confirm authentication flows through OAuth only (Google/Microsoft)
- [ ] Check network traffic during sign-in (DevTools → Network)
- [ ] Verify NO password data transmitted to SprintForge servers
- [ ] Review backend database schema (if accessible)
- [ ] Confirm NO password columns in user tables
- [ ] Verify NO password hashing utilities in codebase
- [ ] Check application never prompts for password creation/reset

### Expected Results
✅ Zero password handling by application
✅ Complete delegation to OAuth providers
✅ No password storage infrastructure

### Pass Criteria
Application avoids password security risks through OAuth-only authentication

---

## Test 64: Session Hijacking - Cookie Security

### Objective
Test protection against session hijacking attacks

### Steps
- [ ] Log in to application in Browser 1 (e.g., Chrome)
- [ ] Open browser DevTools → Application → Cookies
- [ ] Copy session cookie value
- [ ] Open different browser or incognito window (Browser 2)
- [ ] Open DevTools → Application → Cookies
- [ ] Attempt to manually create session cookie with copied value
- [ ] Try to access protected route in Browser 2
- [ ] Verify access denied or automatic re-authentication required
- [ ] Test cookie security attributes prevent hijacking:
  - [ ] SameSite attribute prevents cross-site cookie sending
  - [ ] HttpOnly prevents JavaScript access
  - [ ] Secure flag ensures HTTPS-only (production)
- [ ] Check if cookies include any anti-tampering mechanisms

### Expected Results
✅ Session cookies difficult to hijack
✅ Security attributes prevent common attacks
✅ Copied cookies don't grant automatic access

### Pass Criteria
Session hijacking attacks mitigated through cookie security

---

## Test 65: OAuth Security - Redirect URI Validation

### Objective
Verify OAuth redirect URIs are validated and whitelisted

### Steps
- [ ] Inspect OAuth configuration (Google/Microsoft OAuth apps)
- [ ] Verify authorized redirect URIs are explicitly listed
- [ ] Check only localhost:3000 (dev) and production domain listed
- [ ] Attempt OAuth flow with invalid redirect_uri parameter (if possible):
  ```
  https://accounts.google.com/o/oauth2/v2/auth?
    client_id=[client_id]&
    redirect_uri=https://evil-site.com&
    ...
  ```
- [ ] Verify OAuth provider rejects invalid redirect
- [ ] Confirm error from provider, not successful redirect
- [ ] Test that application validates OAuth callback origin
- [ ] Verify callback handler checks state parameter (CSRF protection)

### Expected Results
✅ Redirect URIs strictly validated
✅ Only whitelisted domains accepted
✅ OAuth CSRF protection via state parameter

### Pass Criteria
OAuth configuration prevents redirect attacks

---

## Test 66: Information Disclosure - Error Messages

### Objective
Verify error messages don't leak sensitive information

### Steps
- [ ] Trigger various error conditions:
  - [ ] Failed login (stop backend during OAuth callback)
  - [ ] Invalid API request
  - [ ] Expired token access
  - [ ] Network errors
- [ ] For each error, verify error messages:
  - [ ] Are user-friendly and generic
  - [ ] Don't reveal system architecture
  - [ ] Don't show stack traces or file paths
  - [ ] Don't expose database queries or schemas
  - [ ] Don't reveal API endpoint internals
- [ ] Check browser console for verbose errors (dev mode may show more)
- [ ] Verify production builds have minimal error disclosure
- [ ] Test error responses from API directly (curl)
- [ ] Confirm API errors are sanitized (no sensitive data)

### Expected Results
✅ User-friendly error messages
✅ No sensitive system information leaked
✅ Different error handling for dev vs production

### Pass Criteria
Error handling balances usability with security

---

## Test 67: Account Enumeration - User Existence

### Objective
Verify application doesn't reveal which users exist

### Steps
- [ ] Attempt to sign in with OAuth
- [ ] Observe error messages during failed authentication
- [ ] Check if error messages differentiate between:
  - User exists vs doesn't exist
  - Invalid password vs account locked (N/A for OAuth)
  - Email not verified vs wrong credentials (N/A for OAuth)
- [ ] For OAuth flow, verify no difference in behavior between:
  - First-time user (account creation)
  - Existing user (account login)
- [ ] Check if any API endpoints reveal user existence:
  - Profile lookup by email
  - "Forgot password" flows (N/A)
- [ ] Verify consistent timing for auth responses (no timing attacks)

### Expected Results
✅ Consistent error messages regardless of user existence
✅ No timing differences revealing information
✅ OAuth flows don't reveal existing accounts

### Pass Criteria
Application prevents account enumeration attacks

---

## Test 68: Dependency Security - Known Vulnerabilities

### Objective
Check for known security vulnerabilities in dependencies

### Steps
- [ ] Navigate to project root directory in terminal
- [ ] For frontend, run security audit:
  ```bash
  cd frontend
  npm audit
  ```
- [ ] Review audit results for critical/high vulnerabilities
- [ ] Check if vulnerabilities affect authentication system
- [ ] For backend, run security checks:
  ```bash
  cd backend
  pip list --outdated
  # Or use safety:
  safety check
  ```
- [ ] Document any NextAuth.js or auth-related vulnerabilities
- [ ] Check CVE databases for known issues with versions used
- [ ] Verify no use of deprecated authentication libraries

### Expected Results
✅ No critical vulnerabilities in auth dependencies
✅ Up-to-date security patches applied
✅ Regular dependency updates maintained

### Pass Criteria
Dependencies don't introduce known security risks

---

## Test 69: Client-Side Security - XSS Prevention

### Objective
Test protection against Cross-Site Scripting (XSS) attacks

### Steps
- [ ] Log in and navigate to profile page
- [ ] Enter edit mode for profile
- [ ] Attempt to inject scripts in display name:
  ```
  <script>alert('XSS')</script>
  <img src=x onerror=alert('XSS')>
  ```
- [ ] Save profile and verify script doesn't execute
- [ ] Check that input is properly escaped/sanitized
- [ ] View page source and verify script tags are escaped
- [ ] Test email field with similar XSS attempts
- [ ] Try reflected XSS in URL parameters:
  ```
  http://localhost:3000/profile?name=<script>alert('XSS')</script>
  ```
- [ ] Verify any URL parameters displayed are escaped
- [ ] Check browser console for Content Security Policy (CSP) headers

### Expected Results
✅ All user input properly sanitized
✅ Script injection attempts blocked
✅ React's built-in XSS protection working

### Pass Criteria
Application resistant to common XSS attacks

---

## Test 70: Security Headers - HTTP Response Headers

### Objective
Verify security-related HTTP headers are properly configured

### Steps
- [ ] Open browser DevTools → Network tab
- [ ] Navigate to any page in application
- [ ] Select main document request (HTML page)
- [ ] View Response Headers
- [ ] Check for recommended security headers:
  - [ ] `X-Content-Type-Options: nosniff`
  - [ ] `X-Frame-Options: DENY` or `SAMEORIGIN`
  - [ ] `X-XSS-Protection: 1; mode=block`
  - [ ] `Strict-Transport-Security` (HSTS - production only)
  - [ ] `Content-Security-Policy` (CSP)
  - [ ] `Referrer-Policy: no-referrer` or `strict-origin`
- [ ] For each missing header, note as potential improvement
- [ ] Check if headers are consistent across all pages
- [ ] Verify API responses also include security headers

### Expected Results
✅ Key security headers present
✅ Headers properly configured
✅ Consistent security headers across application

### Pass Criteria
HTTP headers provide defense-in-depth security

---

## Test Summary Checklist

Complete all tests and mark overall status:

- [ ] Test 56: Token Security - JWT Storage - PASSED
- [ ] Test 57: CSRF Protection - Token Validation - PASSED
- [ ] Test 58: Rate Limiting - Login Attempts - PASSED
- [ ] Test 59: Session Timeout - Token Expiration - PASSED
- [ ] Test 60: Token Blacklisting - Logout Security - PASSED
- [ ] Test 61: Protected Routes - Authentication Enforcement - PASSED
- [ ] Test 62: API Authentication - Backend Validation - PASSED
- [ ] Test 63: Password Security - OAuth Provider Security - PASSED
- [ ] Test 64: Session Hijacking - Cookie Security - PASSED
- [ ] Test 65: OAuth Security - Redirect URI Validation - PASSED
- [ ] Test 66: Information Disclosure - Error Messages - PASSED
- [ ] Test 67: Account Enumeration - User Existence - PASSED
- [ ] Test 68: Dependency Security - Known Vulnerabilities - PASSED
- [ ] Test 69: Client-Side Security - XSS Prevention - PASSED
- [ ] Test 70: Security Headers - HTTP Response Headers - PASSED

---

## Security Test Summary

**Overall Security Assessment**: [PASS / FAIL / NEEDS IMPROVEMENT]

**Critical Issues Found**: [Number]
**High Priority Issues**: [Number]
**Medium Priority Issues**: [Number]
**Low Priority Issues**: [Number]

---

## Detailed Issue Log

```
Issue #: [Number]
Test: [Test Name]
Severity: [Critical/High/Medium/Low]
Category: [Authentication/Authorization/Data Protection/etc.]
Description: [Detailed description of security issue]
Impact: [What could an attacker do?]
Reproduction Steps: [How to reproduce the issue]
Recommendation: [How to fix the issue]
Status: [Open/In Progress/Fixed/Won't Fix]
```

---

## Notes and Observations

**Testing Environment:**
- Browser: __________________
- OS: __________________
- Frontend Version: __________________
- Backend Version: __________________
- Date Tested: __________________
- Tester Name: __________________

**Important Notes:**
- Use test accounts only for security testing
- Do not perform tests on production environment
- Document all vulnerabilities found immediately
- Report critical issues to development team urgently