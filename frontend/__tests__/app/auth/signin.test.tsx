import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useSession, signIn, getProviders } from 'next-auth/react'
import SignIn from '../../../app/auth/signin/page'

// Mock the hooks
jest.mock('next-auth/react')
const mockUseSession = useSession as jest.MockedFunction<typeof useSession>
const mockSignIn = signIn as jest.MockedFunction<typeof signIn>
const mockGetProviders = getProviders as jest.MockedFunction<typeof getProviders>

// Mock the router
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

const mockProviders = {
  google: {
    id: 'google',
    name: 'Google',
    type: 'oauth',
    signinUrl: '/api/auth/signin/google',
    callbackUrl: '/api/auth/callback/google',
  },
  'azure-ad': {
    id: 'azure-ad',
    name: 'Microsoft',
    type: 'oauth',
    signinUrl: '/api/auth/signin/azure-ad',
    callbackUrl: '/api/auth/callback/azure-ad',
  },
}

describe('SignIn Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseSession.mockReturnValue({
      data: null,
      status: 'unauthenticated',
      update: jest.fn(),
    })
    mockGetProviders.mockResolvedValue(mockProviders)
  })

  it('renders loading state initially', () => {
    mockUseSession.mockReturnValue({
      data: null,
      status: 'loading',
      update: jest.fn(),
    })

    render(<SignIn />)
    expect(screen.getByText('Loading sign in options...')).toBeInTheDocument()
  })

  it('redirects when user is already authenticated', async () => {
    mockUseSession.mockReturnValue({
      data: { user: { id: '1', email: 'test@example.com' } },
      status: 'authenticated',
      update: jest.fn(),
    })

    render(<SignIn />)
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/')
    })
  })

  it('renders sign in page with providers', async () => {
    render(<SignIn />)

    await waitFor(() => {
      expect(screen.getByText('Welcome to SprintForge')).toBeInTheDocument()
    })

    expect(screen.getByText('Choose your preferred authentication method to get started')).toBeInTheDocument()
    expect(screen.getByText('Continue with Google')).toBeInTheDocument()
    expect(screen.getByText('Continue with Microsoft')).toBeInTheDocument()
  })

  it('displays error when providers fail to load', async () => {
    mockGetProviders.mockRejectedValue(new Error('Failed to load providers'))

    render(<SignIn />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load authentication options. Please refresh the page.')).toBeInTheDocument()
    })

    const retryButton = screen.getByRole('button', { name: 'Retry' })
    expect(retryButton).toBeInTheDocument()
  })

  it('displays message when no providers available', async () => {
    mockGetProviders.mockResolvedValue(null)

    render(<SignIn />)

    await waitFor(() => {
      expect(screen.getByText('No authentication providers available')).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: 'Refresh Page' })).toBeInTheDocument()
  })

  it('handles Google sign in', async () => {
    render(<SignIn />)

    await waitFor(() => {
      expect(screen.getByText('Continue with Google')).toBeInTheDocument()
    })

    const googleButton = screen.getByRole('button', { name: /Continue with Google/i })
    fireEvent.click(googleButton)

    expect(mockSignIn).toHaveBeenCalledWith('google', { callbackUrl: '/' })
  })

  it('handles Microsoft sign in', async () => {
    render(<SignIn />)

    await waitFor(() => {
      expect(screen.getByText('Continue with Microsoft')).toBeInTheDocument()
    })

    const microsoftButton = screen.getByRole('button', { name: /Continue with Microsoft/i })
    fireEvent.click(microsoftButton)

    expect(mockSignIn).toHaveBeenCalledWith('azure-ad', { callbackUrl: '/' })
  })

  it('shows loading state while signing in', async () => {
    render(<SignIn />)

    await waitFor(() => {
      expect(screen.getByText('Continue with Google')).toBeInTheDocument()
    })

    const googleButton = screen.getByRole('button', { name: /Continue with Google/i })
    fireEvent.click(googleButton)

    expect(screen.getByText('Signing in with Google...')).toBeInTheDocument()
  })

  it('displays sign in error', async () => {
    mockSignIn.mockRejectedValue(new Error('Sign in failed'))

    render(<SignIn />)

    await waitFor(() => {
      expect(screen.getByText('Continue with Google')).toBeInTheDocument()
    })

    const googleButton = screen.getByRole('button', { name: /Continue with Google/i })
    fireEvent.click(googleButton)

    await waitFor(() => {
      expect(screen.getByText('Sign-in failed. Please try again.')).toBeInTheDocument()
    })
  })

  it('renders security features', async () => {
    render(<SignIn />)

    await waitFor(() => {
      expect(screen.getByText('OAuth 2.0')).toBeInTheDocument()
    })

    expect(screen.getByText('Encrypted')).toBeInTheDocument()
    expect(screen.getByText('Secure Authentication')).toBeInTheDocument()
  })

  it('renders terms and privacy links', async () => {
    render(<SignIn />)

    await waitFor(() => {
      expect(screen.getByText('By signing in, you agree to our')).toBeInTheDocument()
    })

    expect(screen.getByRole('link', { name: 'Terms of Service' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Privacy Policy' })).toBeInTheDocument()
  })

  it('renders keyboard navigation help', async () => {
    render(<SignIn />)

    await waitFor(() => {
      expect(screen.getByText('Use Tab to navigate • Enter to select')).toBeInTheDocument()
    })
  })

  it('handles refresh page action', async () => {
    mockGetProviders.mockResolvedValue(null)
    const reloadSpy = jest.spyOn(window.location, 'reload').mockImplementation(() => {})

    render(<SignIn />)

    await waitFor(() => {
      expect(screen.getByText('No authentication providers available')).toBeInTheDocument()
    })

    const refreshButton = screen.getByRole('button', { name: 'Refresh Page' })
    fireEvent.click(refreshButton)

    expect(reloadSpy).toHaveBeenCalled()

    reloadSpy.mockRestore()
  })
})