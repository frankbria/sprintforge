import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useSession, signIn, signOut, getProviders } from 'next-auth/react'
import { useRouter } from 'next/navigation'

// Import components
import Home from '../../app/page'
import SignIn from '../../app/auth/signin/page'
import Dashboard from '../../app/dashboard/page'

// Mock dependencies
jest.mock('next-auth/react')
jest.mock('next/navigation')

const mockUseSession = useSession as jest.MockedFunction<typeof useSession>
const mockSignIn = signIn as jest.MockedFunction<typeof signIn>
const mockSignOut = signOut as jest.MockedFunction<typeof signOut>
const mockGetProviders = getProviders as jest.MockedFunction<typeof getProviders>
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>

describe('Authentication Flow Integration', () => {
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

  describe('Complete Authentication Flow', () => {
    it('should handle complete login flow', async () => {
      // Step 1: User visits home page (unauthenticated)
      mockUseSession.mockReturnValue({
        data: null,
        status: 'unauthenticated',
        update: jest.fn(),
      })

      const { rerender } = render(<Home />)

      expect(screen.getByText('Get Started')).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument()

      // Step 2: User navigates to sign-in page
      mockGetProviders.mockResolvedValue({
        google: {
          id: 'google',
          name: 'Google',
          type: 'oauth',
          signinUrl: '/api/auth/signin/google',
          callbackUrl: '/api/auth/callback/google',
        },
      })

      rerender(<SignIn />)

      await waitFor(() => {
        expect(screen.getByText('Welcome to SprintForge')).toBeInTheDocument()
      })

      expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument()

      // Step 3: User clicks sign-in button
      mockSignIn.mockResolvedValue({ error: null, status: 200, ok: true, url: null })

      fireEvent.click(screen.getByRole('button', { name: /continue with google/i }))

      expect(mockSignIn).toHaveBeenCalledWith('google', { callbackUrl: '/' })

      // Step 4: Authentication succeeds, user is authenticated
      mockUseSession.mockReturnValue({
        data: {
          user: {
            id: 'user-123',
            name: 'John Doe',
            email: 'john@example.com',
            image: 'https://example.com/avatar.jpg',
          },
          provider: 'google',
          accessToken: 'mock-token',
          expires: '2024-12-31',
        },
        status: 'authenticated',
        update: jest.fn(),
      })

      // Step 5: User navigates to dashboard
      rerender(<Dashboard />)

      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Welcome, John Doe')).toBeInTheDocument()
      expect(screen.getByText('john@example.com')).toBeInTheDocument()
    })

    it('should handle logout flow', async () => {
      // Start with authenticated user
      mockUseSession.mockReturnValue({
        data: {
          user: {
            id: 'user-123',
            name: 'John Doe',
            email: 'john@example.com',
            image: 'https://example.com/avatar.jpg',
          },
          provider: 'google',
          accessToken: 'mock-token',
          expires: '2024-12-31',
        },
        status: 'authenticated',
        update: jest.fn(),
      })

      const { rerender } = render(<Home />)

      expect(screen.getByText('Welcome back, John Doe!')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument()

      // User clicks sign out
      mockSignOut.mockResolvedValue({ url: 'http://localhost:3000' })

      fireEvent.click(screen.getByRole('button', { name: /sign out/i }))

      await waitFor(() => {
        expect(mockSignOut).toHaveBeenCalledWith({ callbackUrl: '/' })
      })

      // User is now unauthenticated
      mockUseSession.mockReturnValue({
        data: null,
        status: 'unauthenticated',
        update: jest.fn(),
      })

      rerender(<Home />)

      expect(screen.getByText('Get Started')).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument()
    })

    it('should redirect unauthenticated users from protected pages', () => {
      // User tries to access dashboard without authentication
      mockUseSession.mockReturnValue({
        data: null,
        status: 'unauthenticated',
        update: jest.fn(),
      })

      render(<Dashboard />)

      // Should call requireAuth which triggers redirect
      expect(mockPush).toHaveBeenCalledWith('/auth/signin')
    })

    it('should handle authentication loading states', () => {
      // Authentication is loading
      mockUseSession.mockReturnValue({
        data: null,
        status: 'loading',
        update: jest.fn(),
      })

      render(<Home />)

      expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should handle sign-in errors gracefully', async () => {
      mockGetProviders.mockResolvedValue({
        google: {
          id: 'google',
          name: 'Google',
          type: 'oauth',
          signinUrl: '/api/auth/signin/google',
          callbackUrl: '/api/auth/callback/google',
        },
      })

      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
      mockSignIn.mockRejectedValue(new Error('Authentication failed'))

      render(<SignIn />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument()
      })

      fireEvent.click(screen.getByRole('button', { name: /continue with google/i }))

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith('Sign-in error:', expect.any(Error))
      })

      consoleErrorSpy.mockRestore()
    })

    it('should handle logout errors gracefully', async () => {
      mockUseSession.mockReturnValue({
        data: {
          user: {
            id: 'user-123',
            name: 'John Doe',
            email: 'john@example.com',
            image: null,
          },
          expires: '2024-12-31',
        },
        status: 'authenticated',
        update: jest.fn(),
      })

      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
      mockSignOut.mockRejectedValue(new Error('Logout failed'))

      render(<Home />)

      fireEvent.click(screen.getByRole('button', { name: /sign out/i }))

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith('Logout failed:', expect.any(Error))
      })

      consoleErrorSpy.mockRestore()
    })
  })

  describe('Provider-specific flows', () => {
    it('should handle multiple OAuth providers', async () => {
      mockGetProviders.mockResolvedValue({
        google: {
          id: 'google',
          name: 'Google',
          type: 'oauth',
          signinUrl: '/api/auth/signin/google',
          callbackUrl: '/api/auth/callback/google',
        },
        'azure-ad': {
          id: 'azure-ad',
          name: 'Azure Active Directory',
          type: 'oauth',
          signinUrl: '/api/auth/signin/azure-ad',
          callbackUrl: '/api/auth/callback/azure-ad',
        },
      })

      mockSignIn.mockResolvedValue({ error: null, status: 200, ok: true, url: null })

      render(<SignIn />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /continue with azure active directory/i })).toBeInTheDocument()
      })

      // Test Google sign-in
      fireEvent.click(screen.getByRole('button', { name: /continue with google/i }))
      expect(mockSignIn).toHaveBeenCalledWith('google', { callbackUrl: '/' })

      mockSignIn.mockClear()

      // Test Azure AD sign-in
      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /continue with azure active directory/i }))
        expect(mockSignIn).toHaveBeenCalledWith('azure-ad', { callbackUrl: '/' })
      })
    })
  })

  describe('Session persistence', () => {
    it('should maintain user state across page navigations', () => {
      const mockUser = {
        id: 'user-123',
        name: 'John Doe',
        email: 'john@example.com',
        image: 'https://example.com/avatar.jpg',
      }

      const mockSession = {
        user: mockUser,
        provider: 'google',
        accessToken: 'mock-token',
        expires: '2024-12-31',
      }

      mockUseSession.mockReturnValue({
        data: mockSession,
        status: 'authenticated',
        update: jest.fn(),
      })

      // Test on home page
      const { rerender } = render(<Home />)
      expect(screen.getByText('Welcome back, John Doe!')).toBeInTheDocument()

      // Test on dashboard
      rerender(<Dashboard />)
      expect(screen.getByText('Welcome, John Doe')).toBeInTheDocument()

      // Test on profile page
      const Profile = require('../../app/profile/page').default
      rerender(<Profile />)
      expect(screen.getByRole('heading', { name: 'John Doe' })).toBeInTheDocument()
    })
  })
})