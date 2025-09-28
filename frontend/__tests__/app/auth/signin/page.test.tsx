import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { getProviders, signIn, getSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import SignIn from '../../../../app/auth/signin/page'

// Mock the dependencies
jest.mock('next-auth/react')
jest.mock('next/navigation')

const mockGetProviders = getProviders as jest.MockedFunction<typeof getProviders>
const mockSignIn = signIn as jest.MockedFunction<typeof signIn>
const mockGetSession = getSession as jest.MockedFunction<typeof getSession>
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>

describe('SignIn Page', () => {
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

  it('should display loading spinner initially', () => {
    mockGetSession.mockResolvedValue(null)
    mockGetProviders.mockResolvedValue({})

    render(<SignIn />)

    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument()
  })

  it('should redirect authenticated users to home page', async () => {
    mockGetSession.mockResolvedValue({
      user: { id: '123', email: 'test@example.com' },
      expires: '2024-12-31',
    })

    render(<SignIn />)

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/')
    })
  })

  it('should display sign-in form with providers', async () => {
    mockGetSession.mockResolvedValue(null)
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

    render(<SignIn />)

    await waitFor(() => {
      expect(screen.getByText('Welcome to SprintForge')).toBeInTheDocument()
    })

    expect(screen.getByText('Choose your preferred authentication method to get started')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /continue with azure active directory/i })).toBeInTheDocument()
  })

  it('should call signIn when Google button is clicked', async () => {
    mockGetSession.mockResolvedValue(null)
    mockGetProviders.mockResolvedValue({
      google: {
        id: 'google',
        name: 'Google',
        type: 'oauth',
        signinUrl: '/api/auth/signin/google',
        callbackUrl: '/api/auth/callback/google',
      },
    })

    mockSignIn.mockResolvedValue({ error: null, status: 200, ok: true, url: null })

    render(<SignIn />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /continue with google/i }))

    expect(mockSignIn).toHaveBeenCalledWith('google', { callbackUrl: '/' })
  })

  it('should call signIn when Azure AD button is clicked', async () => {
    mockGetSession.mockResolvedValue(null)
    mockGetProviders.mockResolvedValue({
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
      expect(screen.getByRole('button', { name: /continue with azure active directory/i })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /continue with azure active directory/i }))

    expect(mockSignIn).toHaveBeenCalledWith('azure-ad', { callbackUrl: '/' })
  })

  it('should handle sign-in errors gracefully', async () => {
    mockGetSession.mockResolvedValue(null)
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
    mockSignIn.mockRejectedValue(new Error('Sign-in failed'))

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

  it('should display terms and privacy message', async () => {
    mockGetSession.mockResolvedValue(null)
    mockGetProviders.mockResolvedValue({
      google: {
        id: 'google',
        name: 'Google',
        type: 'oauth',
        signinUrl: '/api/auth/signin/google',
        callbackUrl: '/api/auth/callback/google',
      },
    })

    render(<SignIn />)

    await waitFor(() => {
      // Check for the terms and privacy links which are always present
      expect(screen.getByText('Terms of Service')).toBeInTheDocument()
      expect(screen.getByText('Privacy Policy')).toBeInTheDocument()

      // Check for partial text that should be present
      expect(screen.getByText((content, element) => {
        return content.includes('By signing in, you agree to our')
      })).toBeInTheDocument()
    })
  })

  it('should display Google icon for Google provider', async () => {
    mockGetSession.mockResolvedValue(null)
    mockGetProviders.mockResolvedValue({
      google: {
        id: 'google',
        name: 'Google',
        type: 'oauth',
        signinUrl: '/api/auth/signin/google',
        callbackUrl: '/api/auth/callback/google',
      },
    })

    render(<SignIn />)

    await waitFor(() => {
      const googleButton = screen.getByRole('button', { name: /continue with google/i })
      expect(googleButton).toBeInTheDocument()
      // Check if SVG icon is present
      expect(googleButton.querySelector('svg')).toBeInTheDocument()
    })
  })

  it('should display Microsoft icon for Azure AD provider', async () => {
    mockGetSession.mockResolvedValue(null)
    mockGetProviders.mockResolvedValue({
      'azure-ad': {
        id: 'azure-ad',
        name: 'Azure Active Directory',
        type: 'oauth',
        signinUrl: '/api/auth/signin/azure-ad',
        callbackUrl: '/api/auth/callback/azure-ad',
      },
    })

    render(<SignIn />)

    await waitFor(() => {
      const azureButton = screen.getByRole('button', { name: /continue with azure active directory/i })
      expect(azureButton).toBeInTheDocument()
      // Check if SVG icon is present
      expect(azureButton.querySelector('svg')).toBeInTheDocument()
    })
  })
})