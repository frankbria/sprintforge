import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import OnboardingSetupPage from '../../../../app/onboarding/setup/page'

// Mock the hooks and components
jest.mock('../../../../hooks/useAuth')
jest.mock('../../../../hooks/useOnboarding')
jest.mock('../../../../components/ui/Button', () => ({
  Button: ({ children, onClick, loading, disabled, variant, type, loadingText, ...props }: any) => (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      data-variant={variant}
      data-testid={props['data-testid'] || 'button'}
      {...props}
    >
      {loading ? loadingText || 'Loading...' : children}
    </button>
  )
}))
jest.mock('../../../../components/ui/ErrorMessage', () => ({
  ErrorMessage: ({ message, onClose }: { message: string; onClose: () => void }) => (
    <div data-testid="error-message">
      {message}
      <button onClick={onClose} data-testid="close-error">Close</button>
    </div>
  )
}))
jest.mock('../../../../components/ui/LoadingSpinner', () => ({
  PageLoading: ({ message }: { message: string }) => <div data-testid="page-loading">{message}</div>
}))

const mockUseAuth = require('../../../../hooks/useAuth').useAuth as jest.MockedFunction<any>
const mockUseOnboarding = require('../../../../hooks/useOnboarding').useOnboarding as jest.MockedFunction<any>
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>

describe('OnboardingSetupPage', () => {
  const mockPush = jest.fn()
  const mockUpdatePreferences = jest.fn()
  const mockCompleteOnboarding = jest.fn()

  const mockUser = {
    id: 'user-123',
    name: 'John Doe',
    email: 'john@example.com',
    image: null,
  }

  beforeEach(() => {
    jest.clearAllMocks()
    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    })

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      isAuthenticated: true,
    })

    mockUseOnboarding.mockReturnValue({
      updatePreferences: mockUpdatePreferences,
      completeOnboarding: mockCompleteOnboarding,
    })

    // Mock Intl.DateTimeFormat
    const mockDateTimeFormat = {
      resolvedOptions: () => ({ timeZone: 'America/New_York' })
    }
    jest.spyOn(Intl, 'DateTimeFormat').mockImplementation(() => mockDateTimeFormat as any)
  })

  describe('loading and authentication states', () => {
    it('should show loading when auth is loading', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isLoading: true,
        isAuthenticated: false,
      })

      render(<OnboardingSetupPage />)

      expect(screen.getByTestId('page-loading')).toBeInTheDocument()
      expect(screen.getByText('Loading account setup...')).toBeInTheDocument()
    })

    it('should redirect to signin when not authenticated', async () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isLoading: false,
        isAuthenticated: false,
      })

      render(<OnboardingSetupPage />)

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/auth/signin')
      })
    })

    it('should not render content when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isLoading: false,
        isAuthenticated: false,
      })

      render(<OnboardingSetupPage />)

      expect(screen.queryByText('Complete Your Account Setup')).not.toBeInTheDocument()
    })
  })

  describe('form rendering and initialization', () => {
    it('should render the setup form with all fields', () => {
      render(<OnboardingSetupPage />)

      expect(screen.getByText('Complete Your Account Setup')).toBeInTheDocument()
      expect(screen.getByLabelText('Display Name *')).toBeInTheDocument()
      expect(screen.getByLabelText('Email Address *')).toBeInTheDocument()
      expect(screen.getByLabelText('Timezone *')).toBeInTheDocument()
      expect(screen.getByLabelText('Language *')).toBeInTheDocument()
      expect(screen.getByLabelText('Email notifications for project updates')).toBeInTheDocument()
      expect(screen.getByLabelText('Project deadline reminders')).toBeInTheDocument()
      expect(screen.getByLabelText('Weekly progress digest')).toBeInTheDocument()
    })

    it('should initialize form with user data', () => {
      render(<OnboardingSetupPage />)

      const displayNameInput = screen.getByDisplayValue('John Doe')
      const emailInput = screen.getByDisplayValue('john@example.com')

      expect(displayNameInput).toBeInTheDocument()
      expect(emailInput).toBeInTheDocument()
    })

    it('should initialize form with default values', () => {
      render(<OnboardingSetupPage />)

      const timezoneSelect = screen.getByDisplayValue('America/New_York')
      const languageSelect = screen.getByDisplayValue('en')
      const emailNotifications = screen.getByLabelText('Email notifications for project updates') as HTMLInputElement
      const projectReminders = screen.getByLabelText('Project deadline reminders') as HTMLInputElement
      const weeklyDigest = screen.getByLabelText('Weekly progress digest') as HTMLInputElement

      expect(timezoneSelect).toBeInTheDocument()
      expect(languageSelect).toBeInTheDocument()
      expect(emailNotifications.checked).toBe(true)
      expect(projectReminders.checked).toBe(true)
      expect(weeklyDigest.checked).toBe(false)
    })

    it('should render subscription tier information', () => {
      render(<OnboardingSetupPage />)

      expect(screen.getByText('Subscription Tiers')).toBeInTheDocument()
      expect(screen.getByText('Free')).toBeInTheDocument()
      expect(screen.getByText('Pro')).toBeInTheDocument()
      expect(screen.getByText('Team')).toBeInTheDocument()
      expect(screen.getByText('Current Plan')).toBeInTheDocument()
    })

    it('should render skip buttons', () => {
      render(<OnboardingSetupPage />)

      const skipButtons = screen.getAllByText('Skip for Now')
      expect(skipButtons).toHaveLength(2) // Header and footer
    })
  })

  describe('form validation', () => {
    it('should show error for empty display name', async () => {
      render(<OnboardingSetupPage />)

      const displayNameInput = screen.getByLabelText('Display Name *')
      fireEvent.change(displayNameInput, { target: { value: '' } })

      const submitButton = screen.getByText('Complete Setup')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Display name is required')).toBeInTheDocument()
      })
    })

    it('should show error for short display name', async () => {
      render(<OnboardingSetupPage />)

      const displayNameInput = screen.getByLabelText('Display Name *')
      fireEvent.change(displayNameInput, { target: { value: 'A' } })

      const submitButton = screen.getByText('Complete Setup')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Display name must be at least 2 characters')).toBeInTheDocument()
      })
    })

    it('should show error for empty email', async () => {
      render(<OnboardingSetupPage />)

      const emailInput = screen.getByLabelText('Email Address *')
      fireEvent.change(emailInput, { target: { value: '' } })

      const submitButton = screen.getByText('Complete Setup')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Email is required')).toBeInTheDocument()
      })
    })

    it('should show error for invalid email', async () => {
      render(<OnboardingSetupPage />)

      const emailInput = screen.getByLabelText('Email Address *')
      fireEvent.change(emailInput, { target: { value: 'invalid-email' } })

      const submitButton = screen.getByText('Complete Setup')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument()
      })
    })

    it('should clear errors when user starts typing', async () => {
      render(<OnboardingSetupPage />)

      const displayNameInput = screen.getByLabelText('Display Name *')
      fireEvent.change(displayNameInput, { target: { value: '' } })

      const submitButton = screen.getByText('Complete Setup')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Display name is required')).toBeInTheDocument()
      })

      // Start typing to clear error
      fireEvent.change(displayNameInput, { target: { value: 'New Name' } })

      await waitFor(() => {
        expect(screen.queryByText('Display name is required')).not.toBeInTheDocument()
      })
    })

    it('should disable submit button when there are validation errors', async () => {
      render(<OnboardingSetupPage />)

      const displayNameInput = screen.getByLabelText('Display Name *')
      fireEvent.change(displayNameInput, { target: { value: '' } })

      const submitButton = screen.getByText('Complete Setup')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(submitButton).toBeDisabled()
      })
    })
  })

  describe('form interactions', () => {
    it('should update checkbox values when clicked', () => {
      render(<OnboardingSetupPage />)

      const weeklyDigest = screen.getByLabelText('Weekly progress digest') as HTMLInputElement
      expect(weeklyDigest.checked).toBe(false)

      fireEvent.click(weeklyDigest)
      expect(weeklyDigest.checked).toBe(true)

      fireEvent.click(weeklyDigest)
      expect(weeklyDigest.checked).toBe(false)
    })

    it('should update select values when changed', () => {
      render(<OnboardingSetupPage />)

      const languageSelect = screen.getByLabelText('Language *') as HTMLSelectElement
      fireEvent.change(languageSelect, { target: { value: 'es' } })

      expect(languageSelect.value).toBe('es')
    })

    it('should update text input values when changed', () => {
      render(<OnboardingSetupPage />)

      const displayNameInput = screen.getByLabelText('Display Name *') as HTMLInputElement
      fireEvent.change(displayNameInput, { target: { value: 'New Display Name' } })

      expect(displayNameInput.value).toBe('New Display Name')
    })
  })

  describe('form submission', () => {
    beforeEach(() => {
      mockUpdatePreferences.mockResolvedValue(undefined)
      mockCompleteOnboarding.mockResolvedValue(undefined)
    })

    it('should submit form with valid data', async () => {
      render(<OnboardingSetupPage />)

      const submitButton = screen.getByText('Complete Setup')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(mockUpdatePreferences).toHaveBeenCalledWith({
          theme: 'light',
          emailNotifications: true,
          projectReminders: true,
          weeklyDigest: false,
          language: 'en',
          timezone: 'America/New_York',
          completedAt: expect.any(String),
        })
      })

      expect(mockCompleteOnboarding).toHaveBeenCalled()
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })

    it('should show loading state during submission', async () => {
      // Mock a delayed response
      mockUpdatePreferences.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

      render(<OnboardingSetupPage />)

      const submitButton = screen.getByText('Complete Setup')
      fireEvent.click(submitButton)

      expect(screen.getByText('Saving...')).toBeInTheDocument()
      expect(submitButton).toBeDisabled()

      await waitFor(() => {
        expect(screen.queryByText('Saving...')).not.toBeInTheDocument()
      })
    })

    it('should handle submission errors', async () => {
      const errorMessage = 'Failed to save preferences'
      mockUpdatePreferences.mockRejectedValue(new Error(errorMessage))

      render(<OnboardingSetupPage />)

      const submitButton = screen.getByText('Complete Setup')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument()
        expect(screen.getByText('Failed to save your preferences. Please try again.')).toBeInTheDocument()
      })

      expect(mockCompleteOnboarding).not.toHaveBeenCalled()
      expect(mockPush).not.toHaveBeenCalled()
    })

    it('should close error message when close button is clicked', async () => {
      mockUpdatePreferences.mockRejectedValue(new Error('Test error'))

      render(<OnboardingSetupPage />)

      const submitButton = screen.getByText('Complete Setup')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument()
      })

      const closeButton = screen.getByTestId('close-error')
      fireEvent.click(closeButton)

      expect(screen.queryByTestId('error-message')).not.toBeInTheDocument()
    })

    it('should not submit with invalid data', async () => {
      render(<OnboardingSetupPage />)

      const displayNameInput = screen.getByLabelText('Display Name *')
      fireEvent.change(displayNameInput, { target: { value: '' } })

      const submitButton = screen.getByText('Complete Setup')
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Display name is required')).toBeInTheDocument()
      })

      expect(mockUpdatePreferences).not.toHaveBeenCalled()
      expect(mockCompleteOnboarding).not.toHaveBeenCalled()
    })
  })

  describe('skip functionality', () => {
    it('should redirect to dashboard when skip button is clicked', () => {
      render(<OnboardingSetupPage />)

      const skipButton = screen.getAllByText('Skip for Now')[0]
      fireEvent.click(skipButton)

      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })
  })

  describe('edge cases', () => {
    it('should handle user without name gracefully', () => {
      const userWithoutName = {
        ...mockUser,
        name: null,
      }

      mockUseAuth.mockReturnValue({
        user: userWithoutName,
        isLoading: false,
        isAuthenticated: true,
      })

      render(<OnboardingSetupPage />)

      const displayNameInput = screen.getByLabelText('Display Name *') as HTMLInputElement
      expect(displayNameInput.value).toBe('')
    })

    it('should handle user without email gracefully', () => {
      const userWithoutEmail = {
        ...mockUser,
        email: null,
      }

      mockUseAuth.mockReturnValue({
        user: userWithoutEmail,
        isLoading: false,
        isAuthenticated: true,
      })

      render(<OnboardingSetupPage />)

      const emailInput = screen.getByLabelText('Email Address *') as HTMLInputElement
      expect(emailInput.value).toBe('')
    })

    it('should handle missing Intl.DateTimeFormat gracefully', () => {
      // Mock Intl.DateTimeFormat to be undefined
      jest.spyOn(Intl, 'DateTimeFormat').mockImplementation(() => {
        throw new Error('DateTimeFormat not available')
      })

      render(<OnboardingSetupPage />)

      // Should still render without crashing
      expect(screen.getByText('Complete Your Account Setup')).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('should have proper form labels', () => {
      render(<OnboardingSetupPage />)

      expect(screen.getByLabelText('Display Name *')).toBeInTheDocument()
      expect(screen.getByLabelText('Email Address *')).toBeInTheDocument()
      expect(screen.getByLabelText('Timezone *')).toBeInTheDocument()
      expect(screen.getByLabelText('Language *')).toBeInTheDocument()
    })

    it('should have proper heading hierarchy', () => {
      render(<OnboardingSetupPage />)

      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Complete Your Account Setup')
      expect(screen.getByRole('heading', { level: 3, name: 'Personal Information' })).toBeInTheDocument()
      expect(screen.getByRole('heading', { level: 3, name: 'Localization' })).toBeInTheDocument()
      expect(screen.getByRole('heading', { level: 3, name: 'Notification Preferences' })).toBeInTheDocument()
    })

    it('should associate error messages with form fields', async () => {
      render(<OnboardingSetupPage />)

      const displayNameInput = screen.getByLabelText('Display Name *')
      fireEvent.change(displayNameInput, { target: { value: '' } })

      const submitButton = screen.getByText('Complete Setup')
      fireEvent.click(submitButton)

      await waitFor(() => {
        const errorMessage = screen.getByText('Display name is required')
        expect(errorMessage).toBeInTheDocument()
      })
    })

    it('should have proper form structure', () => {
      render(<OnboardingSetupPage />)

      expect(screen.getByRole('textbox', { name: /display name/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /complete setup/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /skip for now/i })).toBeInTheDocument()
    })
  })
})