import { render, screen, fireEvent } from '@testing-library/react'
import { useSearchParams } from 'next/navigation'
import AuthError from '../../../app/auth/error/page'

// Mock useSearchParams
jest.mock('next/navigation', () => ({
  useSearchParams: jest.fn(),
}))

const mockUseSearchParams = useSearchParams as jest.MockedFunction<typeof useSearchParams>

const createMockSearchParams = (error?: string) => {
  const params = new URLSearchParams()
  if (error) params.set('error', error)
  
  return {
    get: jest.fn((key: string) => params.get(key)),
    has: jest.fn((key: string) => params.has(key)),
    entries: jest.fn(() => params.entries()),
    forEach: jest.fn((callback: (value: string, key: string) => void) => {
      params.forEach(callback)
    }),
    keys: jest.fn(() => params.keys()),
    values: jest.fn(() => params.values()),
    toString: jest.fn(() => params.toString()),
  }
}

describe('AuthError Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: { href: '', reload: jest.fn() },
      writable: true,
    })
  })

  it('renders default error when no specific error code', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams())

    render(<AuthError />)

    expect(screen.getByText('Authentication Error')).toBeInTheDocument()
    expect(screen.getByText('An unexpected authentication error occurred.')).toBeInTheDocument()
    expect(screen.getByText('Please try again. If the problem persists, contact support.')).toBeInTheDocument()
  })

  it('renders signin error', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams('Signin'))

    render(<AuthError />)

    expect(screen.getByText('Sign-in Error')).toBeInTheDocument()
    expect(screen.getByText('There was a problem signing you in. Please try with a different account.')).toBeInTheDocument()
    expect(screen.getByText('Try using a different authentication provider or check your account status.')).toBeInTheDocument()
  })

  it('renders OAuth signin error', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams('OAuthSignin'))

    render(<AuthError />)

    expect(screen.getByText('OAuth Provider Error')).toBeInTheDocument()
    expect(screen.getByText('The authentication provider encountered an error.')).toBeInTheDocument()
    expect(screen.getByText('This is usually temporary. Please try again in a few moments.')).toBeInTheDocument()
  })

  it('renders OAuth callback error', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams('OAuthCallback'))

    render(<AuthError />)

    expect(screen.getByText('OAuth Callback Error')).toBeInTheDocument()
    expect(screen.getByText('There was an error during the authentication callback.')).toBeInTheDocument()
    expect(screen.getByText('Please try signing in again. If the problem persists, clear your browser cache.')).toBeInTheDocument()
  })

  it('renders credentials signin error', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams('CredentialsSignin'))

    render(<AuthError />)

    expect(screen.getByText('Invalid Credentials')).toBeInTheDocument()
    expect(screen.getByText('The credentials you provided are incorrect.')).toBeInTheDocument()
    expect(screen.getByText('Please check your username and password, then try again.')).toBeInTheDocument()
  })

  it('renders session required error', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams('SessionRequired'))

    render(<AuthError />)

    expect(screen.getByText('Authentication Required')).toBeInTheDocument()
    expect(screen.getByText('You need to sign in to access this page.')).toBeInTheDocument()
    expect(screen.getByText('Please sign in with your account to continue.')).toBeInTheDocument()
  })

  it('displays error code when present', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams('OAuthSignin'))

    render(<AuthError />)

    expect(screen.getByText('Error Code:')).toBeInTheDocument()
    expect(screen.getByText('OAuthSignin')).toBeInTheDocument()
    expect(screen.getByText('Reference this code when contacting support')).toBeInTheDocument()
  })

  it('handles retry button click', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams('Signin'))

    render(<AuthError />)

    const retryButton = screen.getByRole('button', { name: 'Try Signing In Again' })
    fireEvent.click(retryButton)

    expect(window.location.href).toBe('/auth/signin')
  })

  it('handles contact support button click', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams('OAuthSignin'))

    render(<AuthError />)

    const contactButton = screen.getByRole('button', { name: 'Contact Support' })
    fireEvent.click(contactButton)

    expect(window.location.href).toContain('mailto:support@sprintforge.com')
    expect(window.location.href).toContain('subject=Authentication Error')
    expect(decodeURIComponent(window.location.href)).toContain('Error Code: OAuthSignin')
  })

  it('handles back to home link', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams())

    render(<AuthError />)

    const homeLink = screen.getByRole('link', { name: 'Back to Home' })
    expect(homeLink).toHaveAttribute('href', '/')
  })

  it('renders help section with troubleshooting tips', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams())

    render(<AuthError />)

    expect(screen.getByText('Need help?')).toBeInTheDocument()
    expect(screen.getByText('If you continue experiencing issues, try:')).toBeInTheDocument()
    expect(screen.getByText('• Clearing your browser cache and cookies')).toBeInTheDocument()
    expect(screen.getByText('• Trying a different browser or device')).toBeInTheDocument()
    expect(screen.getByText('• Checking if your account is active')).toBeInTheDocument()
    expect(screen.getByText('• Using a different authentication provider')).toBeInTheDocument()
  })

  it('renders keyboard navigation help', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams())

    render(<AuthError />)

    expect(screen.getByText('Use Tab to navigate • Enter to select • Esc to go back')).toBeInTheDocument()
  })

  it('renders appropriate error icon', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams('Signin'))

    render(<AuthError />)

    // Check for SVG error icon
    const errorIcon = document.querySelector('svg[viewBox="0 0 24 24"]')
    expect(errorIcon).toBeInTheDocument()
    expect(errorIcon).toHaveClass('h-8', 'w-8', 'text-red-600')
  })

  it('has proper responsive design classes', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams())

    const { container } = render(<AuthError />)

    const outerContainer = container.firstChild
    expect(outerContainer).toHaveClass('min-h-screen', 'flex', 'items-center', 'justify-center')
  })

  it('includes proper ARIA labels and accessibility', () => {
    mockUseSearchParams.mockReturnValue(createMockSearchParams())

    render(<AuthError />)

    const errorIcon = document.querySelector('svg[aria-hidden="true"]')
    expect(errorIcon).toBeInTheDocument()
  })
})