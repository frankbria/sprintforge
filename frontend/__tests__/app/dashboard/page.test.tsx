import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useAuth } from '../../../hooks/useAuth'
import Dashboard from '../../../app/dashboard/page'

// Mock the useAuth hook
jest.mock('../../../hooks/useAuth')

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>

describe('Dashboard Page', () => {
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
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Dashboard />)

    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument()
  })

  it('should call requireAuth when user is not authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Dashboard />)

    expect(mockRequireAuth).toHaveBeenCalled()
  })

  it('should display dashboard content for authenticated users', () => {
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
      requireAuth: mockRequireAuth,
    })

    render(<Dashboard />)

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Manage your projects and generate Excel reports')).toBeInTheDocument()
    expect(screen.getByText('Welcome, John Doe')).toBeInTheDocument()
  })

  it('should display project statistics cards', () => {
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
      requireAuth: mockRequireAuth,
    })

    render(<Dashboard />)

    expect(screen.getByText('Total Projects')).toBeInTheDocument()
    expect(screen.getByText('Excel Reports Generated')).toBeInTheDocument()
    expect(screen.getByText('Profile')).toBeInTheDocument()

    // Check for initial counts
    expect(screen.getAllByText('0')).toHaveLength(2) // Projects and reports
  })

  it('should display user email in profile card', () => {
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
      requireAuth: mockRequireAuth,
    })

    render(<Dashboard />)

    expect(screen.getByText('john@example.com')).toBeInTheDocument()
  })

  it('should display action buttons in cards', () => {
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
      requireAuth: mockRequireAuth,
    })

    render(<Dashboard />)

    expect(screen.getByRole('button', { name: /create new project/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /generate report/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /edit profile/i })).toHaveAttribute('href', '/profile')
  })

  it('should display empty projects state', () => {
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
      requireAuth: mockRequireAuth,
    })

    render(<Dashboard />)

    expect(screen.getByText('Recent Projects')).toBeInTheDocument()
    expect(screen.getByText('No projects yet')).toBeInTheDocument()
    expect(screen.getByText('Get started by creating your first project.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /new project/i })).toBeInTheDocument()
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
      login: jest.fn(),
      logout: mockLogout,
      requireAuth: mockRequireAuth,
    })

    render(<Dashboard />)

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
      requireAuth: mockRequireAuth,
    })

    render(<Dashboard />)

    const signOutButton = screen.getByRole('button', { name: /sign out/i })
    fireEvent.click(signOutButton)

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Logout failed:', expect.any(Error))
    })

    consoleErrorSpy.mockRestore()
  })

  it('should display navigation with SprintForge link', () => {
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
      requireAuth: mockRequireAuth,
    })

    render(<Dashboard />)

    expect(screen.getByRole('link', { name: /sprintforge/i })).toHaveAttribute('href', '/')
  })

  it('should have proper accessibility labels', () => {
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
      requireAuth: mockRequireAuth,
    })

    render(<Dashboard />)

    // Check that navigation has proper structure
    expect(screen.getByRole('navigation')).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
  })
})