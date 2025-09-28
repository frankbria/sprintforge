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
    expect(screen.getByText('Unable to sign in.')).toBeInTheDocument()
    expect(screen.getByText('Error Code: Unknown')).toBeInTheDocument()
  })

  it('should display specific error message for OAuthSignin error', () => {
    const mockSearchParams = createMockSearchParams({ error: 'OAuthSignin' })
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    render(<AuthError />)

    expect(screen.getByText('Authentication Error')).toBeInTheDocument()
    expect(screen.getByText('Try signing in with a different account.')).toBeInTheDocument()
    expect(screen.getByText('Error Code: OAuthSignin')).toBeInTheDocument()
  })

  it('should display specific error message for OAuthAccountNotLinked error', () => {
    const mockSearchParams = createMockSearchParams({ error: 'OAuthAccountNotLinked' })
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    render(<AuthError />)

    expect(screen.getByText('Authentication Error')).toBeInTheDocument()
    expect(screen.getByText('To confirm your identity, sign in with the same account you used originally.')).toBeInTheDocument()
    expect(screen.getByText('Error Code: OAuthAccountNotLinked')).toBeInTheDocument()
  })

  it('should display specific error message for CredentialsSignin error', () => {
    const mockSearchParams = createMockSearchParams({ error: 'CredentialsSignin' })
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    render(<AuthError />)

    expect(screen.getByText('Authentication Error')).toBeInTheDocument()
    expect(screen.getByText('Sign in failed. Check the details you provided are correct.')).toBeInTheDocument()
    expect(screen.getByText('Error Code: CredentialsSignin')).toBeInTheDocument()
  })

  it('should display specific error message for SessionRequired error', () => {
    const mockSearchParams = createMockSearchParams({ error: 'SessionRequired' })
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    render(<AuthError />)

    expect(screen.getByText('Authentication Error')).toBeInTheDocument()
    expect(screen.getByText('Please sign in to access this page.')).toBeInTheDocument()
    expect(screen.getByText('Error Code: SessionRequired')).toBeInTheDocument()
  })

  it('should display Try Again button with correct link', () => {
    const mockSearchParams = createMockSearchParams({ error: 'OAuthSignin' })
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    render(<AuthError />)

    const tryAgainButton = screen.getByRole('link', { name: /try again/i })
    expect(tryAgainButton).toBeInTheDocument()
    expect(tryAgainButton).toHaveAttribute('href', '/auth/signin')
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
    const errorIcon = screen.getByRole('img', { hidden: true })
    expect(errorIcon).toBeInTheDocument()
  })

  it('should display support message', () => {
    const mockSearchParams = createMockSearchParams({ error: 'OAuthSignin' })
    mockUseSearchParams.mockReturnValue(mockSearchParams)

    render(<AuthError />)

    expect(screen.getByText(/if this error persists, please contact support/i)).toBeInTheDocument()
  })

  it('should render with loading fallback initially', () => {
    render(<AuthError />)

    // The component should render even during suspense
    expect(screen.getByText('Authentication Error')).toBeInTheDocument()
  })
})