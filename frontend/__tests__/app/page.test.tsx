import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useAuth } from '../../hooks/useAuth'
import Home from '../../app/page'

// Mock the useAuth hook
jest.mock('../../hooks/useAuth')

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>

describe('Home Page', () => {
  const mockLogout = jest.fn()

  beforeEach(() => {
    mockLogout.mockClear()
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('should display loading spinner when auth is loading', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: true,
      isAuthenticated: false,
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: jest.fn(),
    })

    render(<Home />)

    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument()
  })

  it('should display sign-in prompt for unauthenticated users', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: jest.fn(),
    })

    render(<Home />)

    expect(screen.getByText('SprintForge')).toBeInTheDocument()
    expect(screen.getByText('Get Started')).toBeInTheDocument()
    expect(screen.getByText(/sign in to create and manage your projects/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /sign in/i })).toHaveAttribute('href', '/auth/signin')
  })

  it('should display user information for authenticated users', () => {
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
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: jest.fn(),
    })

    render(<Home />)

    expect(screen.getByText('SprintForge')).toBeInTheDocument()
    expect(screen.getByText('Welcome back, John Doe!')).toBeInTheDocument()
    expect(screen.getByText('john@example.com')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /go to dashboard/i })).toHaveAttribute('href', '/dashboard')
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
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: jest.fn(),
    })

    render(<Home />)

    const avatar = screen.getByRole('img', { name: /profile/i })
    expect(avatar).toBeInTheDocument()
    expect(avatar).toHaveAttribute('src', 'https://example.com/avatar.jpg')
  })

  it('should call logout when sign out button is clicked', async () => {
    const mockUser = {
      id: 'user-123',
      name: 'John Doe',
      email: 'john@example.com',
      image: 'https://example.com/avatar.jpg',
    }

    mockLogout.mockResolvedValue()

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: jest.fn(),
    })

    render(<Home />)

    const signOutButton = screen.getByRole('button', { name: /sign out/i })
    fireEvent.click(signOutButton)

    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalledWith('/')
    })
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
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: jest.fn(),
    })

    render(<Home />)

    const signOutButton = screen.getByRole('button', { name: /sign out/i })
    fireEvent.click(signOutButton)

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Logout failed:', expect.any(Error))
    })

    consoleErrorSpy.mockRestore()
  })

  it('should display navigation links for authenticated users', () => {
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
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: jest.fn(),
    })

    render(<Home />)

    expect(screen.getByRole('link', { name: /dashboard/i })).toHaveAttribute('href', '/dashboard')
    expect(screen.getByRole('link', { name: /profile/i })).toHaveAttribute('href', '/profile')
  })

  it('should display feature cards', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: jest.fn(),
    })

    render(<Home />)

    expect(screen.getByText('Excel Generation')).toBeInTheDocument()
    expect(screen.getByText('Project Management')).toBeInTheDocument()
    expect(screen.getByText('Open Source')).toBeInTheDocument()

    expect(screen.getByText(/generate sophisticated excel spreadsheets/i)).toBeInTheDocument()
    expect(screen.getByText(/plan, track, and manage your projects/i)).toBeInTheDocument()
    expect(screen.getByText(/built with modern technologies/i)).toBeInTheDocument()
  })

  it('should display footer with links', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: jest.fn(),
    })

    render(<Home />)

    expect(screen.getByText('© 2025 SprintForge')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /privacy/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /terms/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /github/i })).toBeInTheDocument()
  })

  it('should be responsive - show project description on mobile', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: jest.fn(),
    })

    render(<Home />)

    // Check that the mobile-only description is present
    expect(screen.getByText('Project Management & Excel Generation')).toBeInTheDocument()
  })
})