import { render, screen } from '@testing-library/react'
import { useSearchParams } from 'next/navigation'
import AuthError from '../../../../app/auth/error/page'
import { createMockSearchParams } from '../../../utils/mockUtils'

const mockUseSearchParams = useSearchParams as jest.MockedFunction<typeof useSearchParams>

describe('AuthError Page', () => {
  beforeEach(() => {
    // Reset to default empty params
    const mockSearchParams = createMockSearchParams()
    mockUseSearchParams.mockReturnValue(mockSearchParams)
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('should display default error message when no error code provided', () => {
    const mockSearchParams = createMockSearchParams()
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    render(<AuthError />)

    expect(screen.getByText('Authentication Error')).toBeInTheDocument()
    expect(screen.getByText('An unexpected authentication error occurred.')).toBeInTheDocument()
    expect(screen.getByText('Please try again. If the problem persists, contact support.')).toBeInTheDocument()
  })

  it('should display specific error message for OAuthSignin error', () => {
    const mockSearchParams = createMockSearchParams({ error: 'OAuthSignin' })
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    render(<AuthError />)

    expect(screen.getByText('OAuth Provider Error')).toBeInTheDocument()
    expect(screen.getByText('The authentication provider encountered an error.')).toBeInTheDocument()
    expect(screen.getByText('This is usually temporary. Please try again in a few moments.')).toBeInTheDocument()
  })

  it('should display specific error message for OAuthAccountNotLinked error', () => {
    const mockSearchParams = createMockSearchParams({ error: 'OAuthAccountNotLinked' })
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    render(<AuthError />)

    expect(screen.getByText('Account Not Linked')).toBeInTheDocument()
    expect(screen.getByText('This account is not linked to your existing profile.')).toBeInTheDocument()
    expect(screen.getByText('To link accounts, sign in with your original authentication method first.')).toBeInTheDocument()
  })

  it('should display specific error message for CredentialsSignin error', () => {
    const mockSearchParams = createMockSearchParams({ error: 'CredentialsSignin' })
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    render(<AuthError />)

    expect(screen.getByText('Invalid Credentials')).toBeInTheDocument()
    expect(screen.getByText('The credentials you provided are incorrect.')).toBeInTheDocument()
    expect(screen.getByText('Please check your username and password, then try again.')).toBeInTheDocument()
  })

  it('should display specific error message for SessionRequired error', () => {
    const mockSearchParams = createMockSearchParams({ error: 'SessionRequired' })
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    render(<AuthError />)

    expect(screen.getByText('Authentication Required')).toBeInTheDocument()
    expect(screen.getByText('You need to sign in to access this page.')).toBeInTheDocument()
    expect(screen.getByText('Please sign in with your account to continue.')).toBeInTheDocument()
  })

  it('should display Try Again button with correct link', () => {
    const mockSearchParams = createMockSearchParams({ error: 'OAuthSignin' })
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    // Mock window.location.href
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
    })

    render(<AuthError />)

    const tryAgainButton = screen.getByRole('button', { name: /try signing in again/i })
    expect(tryAgainButton).toBeInTheDocument()
  })

  it('should display Back to home link', () => {
    const mockSearchParams = createMockSearchParams({ error: 'OAuthSignin' })
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    render(<AuthError />)

    const backToHomeLink = screen.getByRole('link', { name: /back to home/i })
    expect(backToHomeLink).toBeInTheDocument()
    expect(backToHomeLink).toHaveAttribute('href', '/')
  })

  it('should display error icon', () => {
    const mockSearchParams = createMockSearchParams({ error: 'OAuthSignin' })
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    render(<AuthError />)

    // Check if the warning SVG icon is present
    const errorIcon = document.querySelector('svg[aria-hidden="true"]')
    expect(errorIcon).toBeInTheDocument()
  })

  it('should display support message', () => {
    const mockSearchParams = createMockSearchParams({ error: 'OAuthSignin' })
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    render(<AuthError />)

    expect(screen.getByText('If you continue experiencing issues, try:')).toBeInTheDocument()
  })

  it('should render with loading fallback initially', () => {
    render(<AuthError />)

    // The component should render even during suspense
    expect(screen.getByText('Authentication Error')).toBeInTheDocument()
  })
})