import { renderHook, waitFor } from '@testing-library/react'
import { useSession, signIn, signOut } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../hooks/useAuth'

// Mock the dependencies
jest.mock('next-auth/react')
jest.mock('next/navigation')

const mockUseSession = useSession as jest.MockedFunction<typeof useSession>
const mockSignIn = signIn as jest.MockedFunction<typeof signIn>
const mockSignOut = signOut as jest.MockedFunction<typeof signOut>
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>

describe('useAuth', () => {
  const mockPush = jest.fn()

  beforeEach(() => {
    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('loading state', () => {
    it('should return loading state when session is loading', () => {
      mockUseSession.mockReturnValue({
        data: null,
        status: 'loading',
        update: jest.fn(),
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.isLoading).toBe(true)
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBe(null)
    })
  })

  describe('authenticated state', () => {
    it('should return authenticated state when user is logged in', () => {
      const mockSession = {
        user: {
          id: 'user-123',
          name: 'John Doe',
          email: 'john@example.com',
          image: 'https://example.com/avatar.jpg',
        },
        provider: 'google',
        accessToken: 'mock-access-token',
        expires: '2024-12-31',
      }

      mockUseSession.mockReturnValue({
        data: mockSession,
        status: 'authenticated',
        update: jest.fn(),
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.isLoading).toBe(false)
      expect(result.current.isAuthenticated).toBe(true)
      expect(result.current.user).toEqual({
        id: 'user-123',
        name: 'John Doe',
        email: 'john@example.com',
        image: 'https://example.com/avatar.jpg',
      })
      expect(result.current.provider).toBe('google')
      expect(result.current.accessToken).toBe('mock-access-token')
    })
  })

  describe('unauthenticated state', () => {
    it('should return unauthenticated state when user is not logged in', () => {
      mockUseSession.mockReturnValue({
        data: null,
        status: 'unauthenticated',
        update: jest.fn(),
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.isLoading).toBe(false)
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBe(null)
      expect(result.current.provider).toBeUndefined()
      expect(result.current.accessToken).toBeUndefined()
    })
  })

  describe('login functionality', () => {
    it('should call signIn with correct parameters', async () => {
      mockUseSession.mockReturnValue({
        data: null,
        status: 'unauthenticated',
        update: jest.fn(),
      })

      mockSignIn.mockResolvedValue({ error: null, status: 200, ok: true, url: null })

      const { result } = renderHook(() => useAuth())

      await result.current.login('google', '/custom-callback')

      expect(mockSignIn).toHaveBeenCalledWith('google', { callbackUrl: '/custom-callback' })
    })

    it('should use default provider and callback when not specified', async () => {
      mockUseSession.mockReturnValue({
        data: null,
        status: 'unauthenticated',
        update: jest.fn(),
      })

      mockSignIn.mockResolvedValue({ error: null, status: 200, ok: true, url: null })

      const { result } = renderHook(() => useAuth())

      await result.current.login()

      expect(mockSignIn).toHaveBeenCalledWith('google', { callbackUrl: '/onboarding' })
    })

    it('should handle login errors', async () => {
      mockUseSession.mockReturnValue({
        data: null,
        status: 'unauthenticated',
        update: jest.fn(),
      })

      const loginError = new Error('Login failed')
      mockSignIn.mockRejectedValue(loginError)

      const { result } = renderHook(() => useAuth())

      await expect(result.current.login()).rejects.toThrow('Login failed')
    })
  })

  describe('logout functionality', () => {
    it('should call signOut with correct parameters', async () => {
      mockUseSession.mockReturnValue({
        data: { user: { id: '123' } },
        status: 'authenticated',
        update: jest.fn(),
      })

      mockSignOut.mockResolvedValue({ url: 'http://localhost:3000' })

      const { result } = renderHook(() => useAuth())

      await result.current.logout('/custom-redirect')

      expect(mockSignOut).toHaveBeenCalledWith({ callbackUrl: '/custom-redirect' })
    })

    it('should use default callback when not specified', async () => {
      mockUseSession.mockReturnValue({
        data: { user: { id: '123' } },
        status: 'authenticated',
        update: jest.fn(),
      })

      mockSignOut.mockResolvedValue({ url: 'http://localhost:3000' })

      const { result } = renderHook(() => useAuth())

      await result.current.logout()

      expect(mockSignOut).toHaveBeenCalledWith({ callbackUrl: '/' })
    })

    it('should handle logout errors', async () => {
      mockUseSession.mockReturnValue({
        data: { user: { id: '123' } },
        status: 'authenticated',
        update: jest.fn(),
      })

      const logoutError = new Error('Logout failed')
      mockSignOut.mockRejectedValue(logoutError)

      const { result } = renderHook(() => useAuth())

      await expect(result.current.logout()).rejects.toThrow('Logout failed')
    })
  })

  describe('requireAuth functionality', () => {
    it('should redirect to signin when user is not authenticated', () => {
      mockUseSession.mockReturnValue({
        data: null,
        status: 'unauthenticated',
        update: jest.fn(),
      })

      const { result } = renderHook(() => useAuth())

      result.current.requireAuth()

      expect(mockPush).toHaveBeenCalledWith('/auth/signin')
    })

    it('should not redirect when user is authenticated', () => {
      mockUseSession.mockReturnValue({
        data: { user: { id: '123' } },
        status: 'authenticated',
        update: jest.fn(),
      })

      const { result } = renderHook(() => useAuth())

      result.current.requireAuth()

      expect(mockPush).not.toHaveBeenCalled()
    })

    it('should not redirect when session is loading', () => {
      mockUseSession.mockReturnValue({
        data: null,
        status: 'loading',
        update: jest.fn(),
      })

      const { result } = renderHook(() => useAuth())

      result.current.requireAuth()

      expect(mockPush).not.toHaveBeenCalled()
    })
  })

  describe('edge cases', () => {
    it('should handle session with missing user data', () => {
      mockUseSession.mockReturnValue({
        data: { user: null },
        status: 'authenticated',
        update: jest.fn(),
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.user).toBe(null)
    })

    it('should handle partial user data', () => {
      const mockSession = {
        user: {
          id: 'user-123',
          email: 'john@example.com',
          // missing name and image
        },
        expires: '2024-12-31',
      }

      mockUseSession.mockReturnValue({
        data: mockSession,
        status: 'authenticated',
        update: jest.fn(),
      })

      const { result } = renderHook(() => useAuth())

      expect(result.current.user).toEqual({
        id: 'user-123',
        name: undefined,
        email: 'john@example.com',
        image: undefined,
      })
    })
  })
})