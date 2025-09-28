#!/usr/bin/env python3
"""
Security Audit Script for SprintForge
Performs comprehensive security checks on authentication and authorization systems.
"""

import asyncio
import aiohttp
import time
import json
import sys
from typing import List, Dict, Any
from urllib.parse import urljoin
import secrets
import hashlib


class SecurityAuditResult:
    """Container for security audit results."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.critical_issues = []
        self.warnings = []
        self.recommendations = []
    
    def add_test_result(self, test_name: str, passed: bool, details: str = "", severity: str = "info"):
        """Add a test result to the audit."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            self.tests_failed += 1
            print(f"❌ {test_name}: FAILED - {details}")
            
            if severity == "critical":
                self.critical_issues.append(f"{test_name}: {details}")
            elif severity == "warning":
                self.warnings.append(f"{test_name}: {details}")
        
        if details and passed:
            print(f"   {details}")
    
    def add_recommendation(self, recommendation: str):
        """Add a security recommendation."""
        self.recommendations.append(recommendation)
    
    def print_summary(self):
        """Print audit summary."""
        print("\n" + "="*60)
        print("SECURITY AUDIT SUMMARY")
        print("="*60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.critical_issues:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.critical_issues)}):")
            for issue in self.critical_issues:
                print(f"  - {issue}")
        
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.recommendations:
            print(f"\n💡 RECOMMENDATIONS ({len(self.recommendations)}):")
            for rec in self.recommendations:
                print(f"  - {rec}")


class SecurityAuditor:
    """Security auditor for SprintForge authentication system."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.result = SecurityAuditResult()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_rate_limiting(self):
        """Test rate limiting on authentication endpoints."""
        print("\n🔍 Testing Rate Limiting...")
        
        # Test login endpoint rate limiting
        login_url = urljoin(self.base_url, "/api/v1/auth/login")
        
        # Make rapid requests to trigger rate limiting
        start_time = time.time()
        responses = []
        
        for i in range(10):
            try:
                async with self.session.post(login_url, json={"email": "test@test.com", "password": "test"}) as resp:
                    responses.append((resp.status, dict(resp.headers)))
            except Exception as e:
                print(f"Request {i+1} failed: {e}")
        
        # Check if rate limiting kicks in
        rate_limited = any(resp[0] == 429 for resp in responses)
        
        if rate_limited:
            self.result.add_test_result(
                "Rate Limiting", 
                True, 
                "Rate limiting active on auth endpoints"
            )
            
            # Check for proper headers
            rate_limit_headers = None
            for status, headers in responses:
                if status == 429:
                    rate_limit_headers = headers
                    break
            
            if rate_limit_headers:
                has_retry_after = "retry-after" in rate_limit_headers
                has_rate_limit_info = any(h.startswith("x-ratelimit") for h in rate_limit_headers)
                
                self.result.add_test_result(
                    "Rate Limit Headers",
                    has_retry_after and has_rate_limit_info,
                    f"Retry-After: {has_retry_after}, Rate Info: {has_rate_limit_info}"
                )
        else:
            self.result.add_test_result(
                "Rate Limiting",
                False,
                "No rate limiting detected on auth endpoints",
                "critical"
            )
    
    async def test_security_headers(self):
        """Test security headers on API responses."""
        print("\n🔍 Testing Security Headers...")
        
        # Test health endpoint for security headers
        health_url = urljoin(self.base_url, "/health")
        
        try:
            async with self.session.get(health_url) as resp:
                headers = dict(resp.headers)
                
                # Check for essential security headers
                security_checks = [
                    ("X-Content-Type-Options", "nosniff"),
                    ("X-Frame-Options", ["DENY", "SAMEORIGIN"]),
                    ("X-XSS-Protection", "1; mode=block"),
                    ("Referrer-Policy", None),  # Just check presence
                ]
                
                for header, expected in security_checks:
                    header_lower = header.lower()
                    if header_lower in headers:
                        if expected is None:
                            # Just check presence
                            self.result.add_test_result(
                                f"Security Header: {header}",
                                True,
                                f"Present: {headers[header_lower]}"
                            )
                        elif isinstance(expected, list):
                            # Check if value is in list
                            present = headers[header_lower] in expected
                            self.result.add_test_result(
                                f"Security Header: {header}",
                                present,
                                f"Value: {headers[header_lower]}" if present else f"Expected one of {expected}"
                            )
                        else:
                            # Check exact value
                            correct = headers[header_lower] == expected
                            self.result.add_test_result(
                                f"Security Header: {header}",
                                correct,
                                f"Expected: {expected}, Got: {headers[header_lower]}"
                            )
                    else:
                        self.result.add_test_result(
                            f"Security Header: {header}",
                            False,
                            f"Header missing",
                            "warning"
                        )
                
                # Check for HSTS in production-like environments
                if "strict-transport-security" in headers:
                    self.result.add_test_result(
                        "HSTS Header",
                        True,
                        f"Present: {headers['strict-transport-security']}"
                    )
                else:
                    self.result.add_recommendation(
                        "Enable HSTS (Strict-Transport-Security) for HTTPS deployments"
                    )
                
        except Exception as e:
            self.result.add_test_result(
                "Security Headers Test",
                False,
                f"Failed to test security headers: {e}",
                "critical"
            )
    
    async def test_csrf_protection(self):
        """Test CSRF protection mechanisms."""
        print("\n🔍 Testing CSRF Protection...")
        
        # Test if CSRF tokens are provided
        auth_url = urljoin(self.base_url, "/api/v1/auth/login")
        
        try:
            # First request to get CSRF token
            async with self.session.options(auth_url) as resp:
                csrf_token = resp.headers.get("X-CSRF-Token")
                
                if csrf_token:
                    self.result.add_test_result(
                        "CSRF Token Generation",
                        True,
                        "CSRF token provided in response headers"
                    )
                    
                    # Test request without CSRF token
                    async with self.session.post(auth_url, json={"test": "data"}) as resp:
                        if resp.status == 403:
                            self.result.add_test_result(
                                "CSRF Protection",
                                True,
                                "Requests blocked without valid CSRF token"
                            )
                        else:
                            self.result.add_test_result(
                                "CSRF Protection",
                                False,
                                f"Request succeeded without CSRF token (status: {resp.status})",
                                "critical"
                            )
                else:
                    self.result.add_test_result(
                        "CSRF Token Generation",
                        False,
                        "No CSRF token found in response headers",
                        "warning"
                    )
                    self.result.add_recommendation("Implement CSRF protection for state-changing operations")
        
        except Exception as e:
            self.result.add_test_result(
                "CSRF Protection Test",
                False,
                f"Failed to test CSRF protection: {e}",
                "warning"
            )
    
    async def test_token_security(self):
        """Test JWT token security measures."""
        print("\n🔍 Testing Token Security...")
        
        # Test token validation with malformed tokens
        test_cases = [
            ("Empty Token", ""),
            ("Invalid Format", "invalid.token.format"),
            ("Malformed JWT", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid"),
            ("Expired Token", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiZXhwIjoxNTE2MjM5MDIyfQ.invalid"),
        ]
        
        protected_url = urljoin(self.base_url, "/api/v1/projects")  # Assuming this requires auth
        
        for test_name, token in test_cases:
            try:
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                async with self.session.get(protected_url, headers=headers) as resp:
                    # Should return 401 for invalid tokens
                    if resp.status == 401:
                        self.result.add_test_result(
                            f"Token Validation: {test_name}",
                            True,
                            "Invalid token properly rejected"
                        )
                    else:
                        self.result.add_test_result(
                            f"Token Validation: {test_name}",
                            False,
                            f"Invalid token accepted (status: {resp.status})",
                            "critical"
                        )
            except Exception as e:
                self.result.add_test_result(
                    f"Token Validation: {test_name}",
                    False,
                    f"Test failed: {e}",
                    "warning"
                )
    
    async def test_input_validation(self):
        """Test input validation and sanitization."""
        print("\n🔍 Testing Input Validation...")
        
        # Test SQL injection patterns
        sql_injection_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
        ]
        
        # Test XSS patterns
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]
        
        # Test extremely large payloads
        large_payload = "A" * 100000  # 100KB payload
        
        auth_url = urljoin(self.base_url, "/api/v1/auth/login")
        
        all_payloads = sql_injection_payloads + xss_payloads + [large_payload]
        
        for i, payload in enumerate(all_payloads):
            try:
                test_data = {"email": payload, "password": "test"}
                async with self.session.post(auth_url, json=test_data) as resp:
                    # Should return 400 for malicious input
                    if resp.status in [400, 422]:  # Bad request or validation error
                        self.result.add_test_result(
                            f"Input Validation: Payload {i+1}",
                            True,
                            "Malicious input properly rejected"
                        )
                    elif resp.status == 500:
                        self.result.add_test_result(
                            f"Input Validation: Payload {i+1}",
                            False,
                            "Input caused server error (potential vulnerability)",
                            "critical"
                        )
                    else:
                        self.result.add_test_result(
                            f"Input Validation: Payload {i+1}",
                            False,
                            f"Unexpected response to malicious input (status: {resp.status})",
                            "warning"
                        )
            except Exception as e:
                # Network errors are acceptable for large payloads
                if "large_payload" in str(payload):
                    self.result.add_test_result(
                        f"Input Validation: Large Payload",
                        True,
                        "Large payload properly rejected"
                    )
                else:
                    self.result.add_test_result(
                        f"Input Validation: Payload {i+1}",
                        False,
                        f"Test failed: {e}",
                        "warning"
                    )
    
    async def test_session_security(self):
        """Test session management security."""
        print("\n🔍 Testing Session Security...")
        
        # Test cookie security flags
        auth_url = urljoin(self.base_url, "/api/v1/auth/login")
        
        try:
            async with self.session.post(auth_url, json={"email": "test@test.com", "password": "test"}) as resp:
                # Check Set-Cookie headers for security flags
                set_cookies = resp.headers.getall('Set-Cookie', [])
                
                if set_cookies:
                    secure_cookies = 0
                    httponly_cookies = 0
                    samesite_cookies = 0
                    
                    for cookie in set_cookies:
                        if 'Secure' in cookie:
                            secure_cookies += 1
                        if 'HttpOnly' in cookie:
                            httponly_cookies += 1
                        if 'SameSite' in cookie:
                            samesite_cookies += 1
                    
                    total_cookies = len(set_cookies)
                    
                    self.result.add_test_result(
                        "Cookie Security: HttpOnly",
                        httponly_cookies == total_cookies,
                        f"{httponly_cookies}/{total_cookies} cookies have HttpOnly flag"
                    )
                    
                    self.result.add_test_result(
                        "Cookie Security: SameSite",
                        samesite_cookies == total_cookies,
                        f"{samesite_cookies}/{total_cookies} cookies have SameSite attribute"
                    )
                    
                    # Secure flag might not be present in development
                    if secure_cookies > 0:
                        self.result.add_test_result(
                            "Cookie Security: Secure",
                            True,
                            f"{secure_cookies}/{total_cookies} cookies have Secure flag"
                        )
                    else:
                        self.result.add_recommendation(
                            "Enable Secure flag on cookies for HTTPS deployments"
                        )
                else:
                    self.result.add_test_result(
                        "Session Cookies",
                        False,
                        "No session cookies found in response",
                        "warning"
                    )
        
        except Exception as e:
            self.result.add_test_result(
                "Session Security Test",
                False,
                f"Failed to test session security: {e}",
                "warning"
            )
    
    async def run_full_audit(self):
        """Run complete security audit."""
        print("🔒 Starting SprintForge Security Audit...")
        print(f"Target: {self.base_url}")
        
        # Run all security tests
        await self.test_rate_limiting()
        await self.test_security_headers()
        await self.test_csrf_protection()
        await self.test_token_security()
        await self.test_input_validation()
        await self.test_session_security()
        
        # Print final summary
        self.result.print_summary()
        
        return self.result


async def main():
    """Main audit function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SprintForge Security Audit Tool")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for API")
    parser.add_argument("--output", help="Output file for results (JSON)")
    args = parser.parse_args()
    
    async with SecurityAuditor(args.url) as auditor:
        result = await auditor.run_full_audit()
        
        if args.output:
            audit_data = {
                "timestamp": time.time(),
                "base_url": args.url,
                "tests_run": result.tests_run,
                "tests_passed": result.tests_passed,
                "tests_failed": result.tests_failed,
                "critical_issues": result.critical_issues,
                "warnings": result.warnings,
                "recommendations": result.recommendations
            }
            
            with open(args.output, 'w') as f:
                json.dump(audit_data, f, indent=2)
            print(f"\n📄 Audit results saved to {args.output}")
        
        # Exit with error code if critical issues found
        if result.critical_issues:
            print(f"\n🚨 {len(result.critical_issues)} critical security issues found!")
            sys.exit(1)
        elif result.tests_failed > 0:
            print(f"\n⚠️ {result.tests_failed} security tests failed.")
            sys.exit(1)
        else:
            print("\n✅ Security audit completed successfully!")
            sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())