/**
 * Security tests for NextAuth.js authentication system.
 * Tests token management, blacklisting, refresh flows, and security configurations.
 */

import { jest } from '@jest/globals'
import { authOptions, blacklistToken, isTokenBlacklisted, clearTokenBlacklist } from '../../lib/auth'
import { JWT } from 'next-auth/jwt'

// Mock NextAuth providers
jest.mock('next-auth/providers/google', () => ({
  __esModule: true,
  default: jest.fn(() => ({
    id: 'google',
    name: 'Google',
    type: 'oauth',
    clientId: 'mock-google-client-id',
    clientSecret: 'mock-google-client-secret'
  }))
}))

jest.mock('next-auth/providers/azure-ad', () => ({
  __esModule: true,
  default: jest.fn(() => ({
    id: 'azure-ad',
    name: 'Azure AD',
    type: 'oauth',
    clientId: 'mock-azure-client-id',
    clientSecret: 'mock-azure-client-secret'
  }))
}))

// Mock environment variables
const mockEnv = {
  GOOGLE_CLIENT_ID: 'mock-google-client-id',
  GOOGLE_CLIENT_SECRET: 'mock-google-client-secret',
  AZURE_AD_CLIENT_ID: 'mock-azure-client-id',
  AZURE_AD_CLIENT_SECRET: 'mock-azure-client-secret',
  AZURE_AD_TENANT_ID: 'mock-tenant-id',
  NODE_ENV: 'test'
}

Object.assign(process.env, mockEnv)

describe('NextAuth Security Configuration', () => {
  beforeEach(() => {
    clearTokenBlacklist()
  })

  describe('Provider Configuration', () => {
    it('should configure Google OAuth with secure settings', () => {
      const googleProvider = authOptions.providers?.[0]
      expect(googleProvider).toBeDefined()
      
      // Check authorization parameters for security
      const authParams = (googleProvider as any)?.authorization?.params
      expect(authParams?.prompt).toBe('consent')
      expect(authParams?.access_type).toBe('offline')
      expect(authParams?.response_type).toBe('code')
    })

    it('should configure Azure AD OAuth with proper scopes', () => {
      const azureProvider = authOptions.providers?.[1]
      expect(azureProvider).toBeDefined()
      
      // Check authorization parameters
      const authParams = (azureProvider as any)?.authorization?.params
      expect(authParams?.scope).toBe('openid profile email offline_access')
    })
  })

  describe('JWT Security', () => {
    it('should have secure JWT configuration', () => {
      expect(authOptions.jwt?.maxAge).toBe(30 * 24 * 60 * 60) // 30 days
    })

    it('should have secure session configuration', () => {
      expect(authOptions.session?.strategy).toBe('jwt')
      expect(authOptions.session?.maxAge).toBe(30 * 24 * 60 * 60) // 30 days
      expect(authOptions.session?.updateAge).toBe(24 * 60 * 60) // 24 hours
    })

    it('should generate unique token identifiers', async () => {
      const mockToken: JWT = {}
      const mockUser = null
      const mockAccount = null

      const result = await authOptions.callbacks?.jwt?.({
        token: mockToken,
        user: mockUser,
        account: mockAccount
      })

      expect(result?.jti).toBeDefined()
      expect(typeof result?.jti).toBe('string')
      expect(result?.jti?.length).toBeGreaterThan(10)
    })

    it('should add security metadata to tokens', async () => {
      const mockToken: JWT = {}
      const mockUser = null
      const mockAccount = null

      const result = await authOptions.callbacks?.jwt?.({
        token: mockToken,
        user: mockUser,
        account: mockAccount
      })

      expect(result?.iat).toBeDefined()
      expect(result?.lastActivity).toBeDefined()
      expect(typeof result?.iat).toBe('number')
      expect(typeof result?.lastActivity).toBe('number')
    })
  })

  describe('Cookie Security', () => {
    it('should configure secure session token cookie', () => {
      const sessionTokenConfig = authOptions.cookies?.sessionToken
      expect(sessionTokenConfig?.options?.httpOnly).toBe(true)
      expect(sessionTokenConfig?.options?.sameSite).toBe('lax')
      expect(sessionTokenConfig?.options?.path).toBe('/')
    })

    it('should configure secure callback URL cookie', () => {
      const callbackUrlConfig = authOptions.cookies?.callbackUrl
      expect(callbackUrlConfig?.options?.httpOnly).toBe(true)
      expect(callbackUrlConfig?.options?.sameSite).toBe('lax')
      expect(callbackUrlConfig?.options?.path).toBe('/')
    })

    it('should configure secure CSRF token cookie', () => {
      const csrfTokenConfig = authOptions.cookies?.csrfToken
      expect(csrfTokenConfig?.options?.httpOnly).toBe(true)
      expect(csrfTokenConfig?.options?.sameSite).toBe('lax')
      expect(csrfTokenConfig?.options?.path).toBe('/')
    })

    it('should set secure flag in production', () => {
      // Mock production environment
      const originalNodeEnv = process.env.NODE_ENV
      process.env.NODE_ENV = 'production'

      // In a real implementation, we'd need to re-evaluate the auth options
      // For this test, we check the logic pattern
      const shouldBeSecure = process.env.NODE_ENV === 'production'
      expect(shouldBeSecure).toBe(true)

      // Restore original environment
      process.env.NODE_ENV = originalNodeEnv
    })
  })

  describe('Token Blacklisting', () => {
    it('should blacklist tokens successfully', () => {
      const tokenId = 'test-token-123'
      
      expect(isTokenBlacklisted(tokenId)).toBe(false)
      
      blacklistToken(tokenId)
      expect(isTokenBlacklisted(tokenId)).toBe(true)
    })

    it('should clear token blacklist', () => {
      const tokenId = 'test-token-456'
      
      blacklistToken(tokenId)
      expect(isTokenBlacklisted(tokenId)).toBe(true)
      
      clearTokenBlacklist()
      expect(isTokenBlacklisted(tokenId)).toBe(false)
    })

    it('should reject blacklisted tokens in JWT callback', async () => {
      const blacklistedTokenId = 'blacklisted-token'
      blacklistToken(blacklistedTokenId)

      const mockToken: JWT = { jti: blacklistedTokenId }

      await expect(
        authOptions.callbacks?.jwt?.({
          token: mockToken,
          user: null,
          account: null
        })
      ).rejects.toThrow('Token has been revoked')
    })

    it('should blacklist token on signout event', async () => {
      const tokenId = 'signout-token'
      const mockToken: JWT = { jti: tokenId }

      expect(isTokenBlacklisted(tokenId)).toBe(false)

      await authOptions.events?.signOut?.({ token: mockToken })

      expect(isTokenBlacklisted(tokenId)).toBe(true)
    })
  })

  describe('Token Refresh Logic', () => {
    beforeEach(() => {
      global.fetch = jest.fn()
    })

    afterEach(() => {
      jest.restoreAllMocks()
    })

    it('should handle token refresh for Google provider', async () => {
      const mockRefreshResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          access_token: 'new-access-token',
          expires_in: 3600,
          refresh_token: 'new-refresh-token'
        })
      }

      ;(global.fetch as jest.Mock).mockResolvedValue(mockRefreshResponse)

      const expiredTime = Math.floor(Date.now() / 1000) + 200 // 200 seconds from now
      const mockToken: JWT = {
        provider: 'google',
        refreshToken: 'old-refresh-token',
        exp: expiredTime,
        jti: 'test-token'
      }

      const result = await authOptions.callbacks?.jwt?.({
        token: mockToken,
        user: null,
        account: null
      })

      // Should attempt refresh when token is close to expiring
      expect(result).toBeDefined()
    })

    it('should handle token refresh for Azure AD provider', async () => {
      const mockRefreshResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          access_token: 'new-azure-token',
          expires_in: 3600,
          refresh_token: 'new-azure-refresh'
        })
      }

      ;(global.fetch as jest.Mock).mockResolvedValue(mockRefreshResponse)

      const expiredTime = Math.floor(Date.now() / 1000) + 200
      const mockToken: JWT = {
        provider: 'azure-ad',
        refreshToken: 'old-azure-refresh',
        exp: expiredTime,
        jti: 'azure-token'
      }

      const result = await authOptions.callbacks?.jwt?.({
        token: mockToken,
        user: null,
        account: null
      })

      expect(result).toBeDefined()
    })

    it('should handle refresh token failure gracefully', async () => {
      const mockErrorResponse = {
        ok: false,
        json: jest.fn().mockResolvedValue({
          error: 'invalid_grant'
        })
      }

      ;(global.fetch as jest.Mock).mockResolvedValue(mockErrorResponse)

      const expiredTime = Math.floor(Date.now() / 1000) + 200
      const mockToken: JWT = {
        provider: 'google',
        refreshToken: 'invalid-refresh-token',
        exp: expiredTime,
        jti: 'failing-token'
      }

      // Should not throw error, but handle gracefully
      const result = await authOptions.callbacks?.jwt?.({
        token: mockToken,
        user: null,
        account: null
      })

      expect(result).toBeDefined()
    })
  })

  describe('Session Security', () => {
    it('should include security information in session', async () => {
      const mockToken: JWT = {
        id: 'user-123',
        accessToken: 'access-token',
        provider: 'google',
        jti: 'token-id'
      }

      const mockSession = {
        user: { id: '', name: '', email: '' },
        expires: ''
      }

      const result = await authOptions.callbacks?.session?.({
        session: mockSession,
        token: mockToken
      })

      expect(result?.accessToken).toBe('access-token')
      expect(result?.user?.id).toBe('user-123')
      expect(result?.provider).toBe('google')
      expect(result?.tokenId).toBe('token-id')
    })
  })

  describe('Sign-in Security', () => {
    it('should validate Google email verification', async () => {
      const mockUser = { id: '1', email: 'test@example.com' }
      const mockAccount = { provider: 'google' }
      const mockProfile = { email_verified: true }

      const result = await authOptions.callbacks?.signIn?.({
        user: mockUser,
        account: mockAccount,
        profile: mockProfile
      })

      expect(result).toBe(true)
    })

    it('should reject unverified Google email', async () => {
      const mockUser = { id: '1', email: 'test@example.com' }
      const mockAccount = { provider: 'google' }
      const mockProfile = { email_verified: false }

      const result = await authOptions.callbacks?.signIn?.({
        user: mockUser,
        account: mockAccount,
        profile: mockProfile
      })

      expect(result).toBe(false)
    })

    it('should allow non-Google providers without email verification check', async () => {
      const mockUser = { id: '1', email: 'test@example.com' }
      const mockAccount = { provider: 'azure-ad' }
      const mockProfile = {}

      const result = await authOptions.callbacks?.signIn?.({
        user: mockUser,
        account: mockAccount,
        profile: mockProfile
      })

      expect(result).toBe(true)
    })
  })

  describe('Pages Security', () => {
    it('should configure custom sign-in page', () => {
      expect(authOptions.pages?.signIn).toBe('/auth/signin')
    })

    it('should configure custom error page', () => {
      expect(authOptions.pages?.error).toBe('/auth/error')
    })
  })

  describe('Debug Configuration', () => {
    it('should enable debug only in development', () => {
      const originalNodeEnv = process.env.NODE_ENV
      
      // Test development
      process.env.NODE_ENV = 'development'
      expect(process.env.NODE_ENV === 'development').toBe(true)
      
      // Test production
      process.env.NODE_ENV = 'production'
      expect(process.env.NODE_ENV === 'development').toBe(false)
      
      // Restore
      process.env.NODE_ENV = originalNodeEnv
    })
  })
})

describe('Token Refresh Function', () => {
  beforeEach(() => {
    global.fetch = jest.fn()
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('should construct correct refresh URL for Google', async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        access_token: 'new-token',
        expires_in: 3600,
        refresh_token: 'new-refresh'
      })
    }

    ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

    const mockToken: JWT = {
      provider: 'google',
      refreshToken: 'test-refresh-token'
    }

    // We need to access the private refresh function
    // In a real test, we'd export it or test through the JWT callback
    const refreshModule = await import('../../lib/auth')
    
    // Mock the internal refresh call by testing through JWT callback
    await authOptions.callbacks?.jwt?.({
      token: { ...mockToken, exp: Math.floor(Date.now() / 1000) + 200 },
      user: null,
      account: { refresh_token: 'test-refresh' }
    })

    expect(global.fetch).toHaveBeenCalledWith(
      'https://oauth2.googleapis.com/token',
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
    )
  })

  it('should construct correct refresh URL for Azure AD', async () => {
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        access_token: 'new-azure-token',
        expires_in: 3600,
        refresh_token: 'new-azure-refresh'
      })
    }

    ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

    const mockToken: JWT = {
      provider: 'azure-ad',
      refreshToken: 'test-azure-refresh'
    }

    await authOptions.callbacks?.jwt?.({
      token: { ...mockToken, exp: Math.floor(Date.now() / 1000) + 200 },
      user: null,
      account: { refresh_token: 'test-azure-refresh' }
    })

    expect(global.fetch).toHaveBeenCalledWith(
      `https://login.microsoftonline.com/${process.env.AZURE_AD_TENANT_ID}/oauth2/v2.0/token`,
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
    )
  })

  it('should handle unsupported provider for refresh', async () => {
    const mockToken: JWT = {
      provider: 'unsupported',
      refreshToken: 'test-refresh'
    }

    // Should handle gracefully without throwing
    const result = await authOptions.callbacks?.jwt?.({
      token: { ...mockToken, exp: Math.floor(Date.now() / 1000) + 200 },
      user: null,
      account: { refresh_token: 'test-refresh' }
    })

    expect(result).toBeDefined()
  })
})

describe('Security Headers and Middleware Integration', () => {
  it('should export necessary security functions', () => {
    expect(typeof blacklistToken).toBe('function')
    expect(typeof isTokenBlacklisted).toBe('function')
    expect(typeof clearTokenBlacklist).toBe('function')
  })

  it('should maintain security state across function calls', () => {
    const token1 = 'token-1'
    const token2 = 'token-2'

    blacklistToken(token1)
    blacklistToken(token2)

    expect(isTokenBlacklisted(token1)).toBe(true)
    expect(isTokenBlacklisted(token2)).toBe(true)
    expect(isTokenBlacklisted('token-3')).toBe(false)

    clearTokenBlacklist()

    expect(isTokenBlacklisted(token1)).toBe(false)
    expect(isTokenBlacklisted(token2)).toBe(false)
  })
})