import { render, screen } from '@testing-library/react'
import { useAuth } from '../../hooks/useAuth'
import { withAuth, withRequiredAuth, withRedirectIfAuthenticated } from '../../components/withAuth'

// Mock useAuth hook
jest.mock('../../hooks/useAuth')

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>

// Mock window.location.href
Object.defineProperty(window, 'location', {
  value: {
    href: '',
  },
  writable: true,
})

// Test component
const TestComponent = () => <div data-testid="test-component">Test Component</div>

describe('withAuth HOC', () => {
  const mockRequireAuth = jest.fn()

  beforeEach(() => {
    mockRequireAuth.mockClear()
    window.location.href = ''
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('withAuth', () => {
    it('should show loading spinner when auth is loading', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        requireAuth: mockRequireAuth,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      const WrappedComponent = withAuth(TestComponent)
      render(<WrappedComponent />)

      expect(screen.getByRole('status')).toBeInTheDocument()
      expect(screen.queryByTestId('test-component')).not.toBeInTheDocument()
    })

    it('should render component when authenticated and not redirectIfAuthenticated', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        requireAuth: mockRequireAuth,
        user: { id: '123', name: 'Test User', email: 'test@example.com' },
        login: jest.fn(),
        logout: jest.fn(),
      })

      const WrappedComponent = withAuth(TestComponent)
      render(<WrappedComponent />)

      expect(screen.getByTestId('test-component')).toBeInTheDocument()
    })

    it('should call requireAuth when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        requireAuth: mockRequireAuth,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      const WrappedComponent = withAuth(TestComponent)
      render(<WrappedComponent />)

      expect(mockRequireAuth).toHaveBeenCalled()
      expect(screen.queryByTestId('test-component')).not.toBeInTheDocument()
    })

    it('should redirect when authenticated and redirectIfAuthenticated is true', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        requireAuth: mockRequireAuth,
        user: { id: '123', name: 'Test User', email: 'test@example.com' },
        login: jest.fn(),
        logout: jest.fn(),
      })

      const WrappedComponent = withAuth(TestComponent, { redirectIfAuthenticated: true })
      render(<WrappedComponent />)

      expect(window.location.href).toBe('/dashboard')
      expect(screen.queryByTestId('test-component')).not.toBeInTheDocument()
    })

    it('should not redirect during loading state', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        requireAuth: mockRequireAuth,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      const WrappedComponent = withAuth(TestComponent, { redirectIfAuthenticated: true })
      render(<WrappedComponent />)

      expect(window.location.href).toBe('')
      expect(mockRequireAuth).not.toHaveBeenCalled()
    })

    it('should render component when not authenticated and redirectIfAuthenticated is true', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        requireAuth: mockRequireAuth,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      const WrappedComponent = withAuth(TestComponent, { redirectIfAuthenticated: true })
      render(<WrappedComponent />)

      expect(screen.getByTestId('test-component')).toBeInTheDocument()
      expect(mockRequireAuth).not.toHaveBeenCalled()
      expect(window.location.href).toBe('')
    })
  })

  describe('withRequiredAuth', () => {
    it('should wrap component with auth requirement', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        requireAuth: mockRequireAuth,
        user: { id: '123', name: 'Test User', email: 'test@example.com' },
        login: jest.fn(),
        logout: jest.fn(),
      })

      const WrappedComponent = withRequiredAuth(TestComponent)
      render(<WrappedComponent />)

      expect(screen.getByTestId('test-component')).toBeInTheDocument()
    })

    it('should require auth when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        requireAuth: mockRequireAuth,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      const WrappedComponent = withRequiredAuth(TestComponent)
      render(<WrappedComponent />)

      expect(mockRequireAuth).toHaveBeenCalled()
      expect(screen.queryByTestId('test-component')).not.toBeInTheDocument()
    })
  })

  describe('withRedirectIfAuthenticated', () => {
    it('should render component when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        requireAuth: mockRequireAuth,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      const WrappedComponent = withRedirectIfAuthenticated(TestComponent)
      render(<WrappedComponent />)

      expect(screen.getByTestId('test-component')).toBeInTheDocument()
      expect(window.location.href).toBe('')
    })

    it('should redirect to dashboard when authenticated', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        requireAuth: mockRequireAuth,
        user: { id: '123', name: 'Test User', email: 'test@example.com' },
        login: jest.fn(),
        logout: jest.fn(),
      })

      const WrappedComponent = withRedirectIfAuthenticated(TestComponent)
      render(<WrappedComponent />)

      expect(window.location.href).toBe('/dashboard')
      expect(screen.queryByTestId('test-component')).not.toBeInTheDocument()
    })

    it('should show loading spinner during auth check', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        requireAuth: mockRequireAuth,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      const WrappedComponent = withRedirectIfAuthenticated(TestComponent)
      render(<WrappedComponent />)

      expect(screen.getByRole('status')).toBeInTheDocument()
      expect(screen.queryByTestId('test-component')).not.toBeInTheDocument()
    })
  })

  describe('component props forwarding', () => {
    it('should forward props to wrapped component', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        requireAuth: mockRequireAuth,
        user: { id: '123', name: 'Test User', email: 'test@example.com' },
        login: jest.fn(),
        logout: jest.fn(),
      })

      const PropsTestComponent = ({ testProp }: { testProp: string }) => (
        <div data-testid="props-component">{testProp}</div>
      )

      const WrappedComponent = withAuth(PropsTestComponent)
      render(<WrappedComponent testProp="test value" />)

      expect(screen.getByTestId('props-component')).toBeInTheDocument()
      expect(screen.getByText('test value')).toBeInTheDocument()
    })
  })
})