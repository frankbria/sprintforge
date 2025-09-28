import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useAuth } from '../../../hooks/useAuth'
import Profile from '../../../app/profile/page'

// Mock the useAuth hook
jest.mock('../../../hooks/useAuth')

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>

describe('Profile Page', () => {
  const mockLogout = jest.fn()
  const mockRequireAuth = jest.fn()

  beforeEach(() => {
    mockLogout.mockClear()
    mockRequireAuth.mockClear()
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('should display loading spinner when auth is loading', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: true,
      isAuthenticated: false,
      provider: undefined,
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Profile />)

    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument()
  })

  it('should call requireAuth when user is not authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      provider: undefined,
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Profile />)

    expect(mockRequireAuth).toHaveBeenCalled()
  })

  it('should display profile content for authenticated users', () => {
    const mockUser = {
      id: 'user-123',
      name: 'John Doe',
      email: 'john@example.com',
      image: 'https://example.com/avatar.jpg',
    }

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      provider: 'google',
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Profile />)

    expect(screen.getByText('Profile')).toBeInTheDocument()
    expect(screen.getByText('Manage your account information and preferences')).toBeInTheDocument()
    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('john@example.com')).toBeInTheDocument()
  })

  it('should display user avatar when available', () => {
    const mockUser = {
      id: 'user-123',
      name: 'John Doe',
      email: 'john@example.com',
      image: 'https://example.com/avatar.jpg',
    }

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      provider: 'google',
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Profile />)

    const avatar = screen.getByRole('img', { name: /profile/i })
    expect(avatar).toBeInTheDocument()
    expect(avatar).toHaveAttribute('src', 'https://example.com/avatar.jpg')
  })

  it('should display default avatar when image is not available', () => {
    const mockUser = {
      id: 'user-123',
      name: 'John Doe',
      email: 'john@example.com',
      image: null,
    }

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      provider: 'google',
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Profile />)

    // Should display default avatar (SVG icon)
    const defaultAvatar = screen.getByRole('img', { hidden: true })
    expect(defaultAvatar).toBeInTheDocument()
  })

  it('should display authentication provider information', () => {
    const mockUser = {
      id: 'user-123',
      name: 'John Doe',
      email: 'john@example.com',
      image: null,
    }

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      provider: 'google',
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Profile />)

    expect(screen.getByText('Authenticated via Google')).toBeInTheDocument()
  })

  it('should display account information section', () => {
    const mockUser = {
      id: 'user-123',
      name: 'John Doe',
      email: 'john@example.com',
      image: null,
    }

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      provider: 'azure-ad',
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Profile />)

    expect(screen.getByText('Account Information')).toBeInTheDocument()
    expect(screen.getByText('User ID')).toBeInTheDocument()
    expect(screen.getByText('user-123')).toBeInTheDocument()
    expect(screen.getByText('Email Address')).toBeInTheDocument()
    expect(screen.getByText('Display Name')).toBeInTheDocument()
  })

  it('should handle missing user name gracefully', () => {
    const mockUser = {
      id: 'user-123',
      name: null,
      email: 'john@example.com',
      image: null,
    }

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      provider: 'google',
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Profile />)

    expect(screen.getByText('No name provided')).toBeInTheDocument()
    expect(screen.getByText('Not set')).toBeInTheDocument()
  })

  it('should display preferences section', () => {
    const mockUser = {
      id: 'user-123',
      name: 'John Doe',
      email: 'john@example.com',
      image: null,
    }

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      provider: 'google',
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Profile />)

    expect(screen.getByText('Preferences')).toBeInTheDocument()
    expect(screen.getByText('Email notifications')).toBeInTheDocument()
    expect(screen.getByText('Project reminders')).toBeInTheDocument()
  })

  it('should display danger zone section', () => {
    const mockUser = {
      id: 'user-123',
      name: 'John Doe',
      email: 'john@example.com',
      image: null,
    }

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      provider: 'google',
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Profile />)

    expect(screen.getByText('Danger Zone')).toBeInTheDocument()
    expect(screen.getByText(/once you delete your account, there is no going back/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /delete account/i })).toBeInTheDocument()
  })

  it('should call logout when sign out button is clicked', async () => {
    const mockUser = {
      id: 'user-123',
      name: 'John Doe',
      email: 'john@example.com',
      image: null,
    }

    mockLogout.mockResolvedValue()

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      provider: 'google',
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Profile />)

    const signOutButton = screen.getByRole('button', { name: /sign out/i })
    fireEvent.click(signOutButton)

    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalledWith('/')
    })
  })

  it('should display navigation links', () => {
    const mockUser = {
      id: 'user-123',
      name: 'John Doe',
      email: 'john@example.com',
      image: null,
    }

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      provider: 'google',
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Profile />)

    expect(screen.getByRole('link', { name: /sprintforge/i })).toHaveAttribute('href', '/')
    expect(screen.getByRole('link', { name: /dashboard/i })).toHaveAttribute('href', '/dashboard')
  })

  it('should handle logout errors gracefully', async () => {
    const mockUser = {
      id: 'user-123',
      name: 'John Doe',
      email: 'john@example.com',
      image: null,
    }

    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
    mockLogout.mockRejectedValue(new Error('Logout failed'))

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      provider: 'google',
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Profile />)

    const signOutButton = screen.getByRole('button', { name: /sign out/i })
    fireEvent.click(signOutButton)

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Logout failed:', expect.any(Error))
    })

    consoleErrorSpy.mockRestore()
  })
})