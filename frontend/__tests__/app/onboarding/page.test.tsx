import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import OnboardingPage from '../../../app/onboarding/page'

// Mock the hooks and components
jest.mock('../../../hooks/useAuth')
jest.mock('../../../components/ui/Button', () => ({
  Button: ({ children, onClick, loading, disabled, variant, ...props }: any) => (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      data-variant={variant}
      data-testid={props['data-testid'] || 'button'}
      {...props}
    >
      {loading ? 'Loading...' : children}
    </button>
  )
}))
jest.mock('../../../components/ui/LoadingSpinner', () => ({
  PageLoading: ({ message }: { message: string }) => <div data-testid="page-loading">{message}</div>
}))

const mockUseAuth = require('../../../hooks/useAuth').useAuth as jest.MockedFunction<any>
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key]
    }),
    clear: jest.fn(() => {
      store = {}
    }),
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

describe('OnboardingPage', () => {
  const mockPush = jest.fn()
  const mockUser = {
    id: 'user-123',
    name: 'John Doe',
    email: 'john@example.com',
    image: null,
  }

  beforeEach(() => {
    jest.clearAllMocks()
    localStorageMock.clear()
    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    })

    // Mock window to avoid "undefined" errors
    Object.defineProperty(window, 'window', {
      value: window,
      writable: true,
    })
  })

  describe('loading and authentication states', () => {
    it('should show loading when auth is loading', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isLoading: true,
        isAuthenticated: false,
      })

      render(<OnboardingPage />)

      expect(screen.getByTestId('page-loading')).toBeInTheDocument()
      expect(screen.getByText('Loading onboarding...')).toBeInTheDocument()
    })

    it('should redirect to signin when not authenticated', async () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isLoading: false,
        isAuthenticated: false,
      })

      render(<OnboardingPage />)

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/auth/signin')
      })
    })

    it('should redirect to dashboard when onboarding already completed', async () => {
      localStorageMock.setItem(`onboarding-completed-${mockUser.id}`, 'true')

      mockUseAuth.mockReturnValue({
        user: mockUser,
        isLoading: false,
        isAuthenticated: true,
      })

      render(<OnboardingPage />)

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/dashboard')
      })
    })

    it('should not render content when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isLoading: false,
        isAuthenticated: false,
      })

      render(<OnboardingPage />)

      expect(screen.queryByText('Welcome to SprintForge!')).not.toBeInTheDocument()
    })
  })

  describe('onboarding flow rendering', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: mockUser,
        isLoading: false,
        isAuthenticated: true,
      })
    })

    it('should render the first step (welcome) by default', () => {
      render(<OnboardingPage />)

      expect(screen.getByText('Welcome to SprintForge!')).toBeInTheDocument()
      expect(screen.getByText("Let's get you started with the basics")).toBeInTheDocument()
      expect(screen.getByText('Hello, John Doe!')).toBeInTheDocument()
      expect(screen.getByText('1 of 3')).toBeInTheDocument()
    })

    it('should show progress bar with correct progress', () => {
      render(<OnboardingPage />)

      const progressElement = document.querySelector('[style*="width"]')
      expect(progressElement).toHaveStyle('width: 33.333333333333336%')
    })

    it('should render header with logo and skip button', () => {
      render(<OnboardingPage />)

      expect(screen.getByText('SprintForge')).toBeInTheDocument()
      expect(screen.getByText('Skip Setup')).toBeInTheDocument()
    })

    it('should show correct step indicators', () => {
      render(<OnboardingPage />)

      const indicators = screen.getAllByRole('generic').filter(el =>
        el.className.includes('rounded-full') && el.className.includes('w-2 h-2')
      )

      // Check that we have step indicators (should be 3)
      expect(indicators.length).toBeGreaterThanOrEqual(3)
    })
  })

  describe('navigation between steps', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: mockUser,
        isLoading: false,
        isAuthenticated: true,
      })
    })

    it('should navigate to next step when Next button is clicked', () => {
      render(<OnboardingPage />)

      const nextButton = screen.getByText('Next →')
      fireEvent.click(nextButton)

      expect(screen.getByText('Key Features')).toBeInTheDocument()
      expect(screen.getByText('Discover what SprintForge can do for you')).toBeInTheDocument()
      expect(screen.getByText('2 of 3')).toBeInTheDocument()
    })

    it('should navigate to previous step when Previous button is clicked', () => {
      render(<OnboardingPage />)

      // Go to step 2
      fireEvent.click(screen.getByText('Next →'))

      // Go back to step 1
      fireEvent.click(screen.getByText('← Previous'))

      expect(screen.getByText('Welcome to SprintForge!')).toBeInTheDocument()
      expect(screen.getByText('1 of 3')).toBeInTheDocument()
    })

    it('should disable Previous button on first step', () => {
      render(<OnboardingPage />)

      const previousButton = screen.getByText('← Previous')
      expect(previousButton).toBeDisabled()
    })

    it('should show "Get Started" button on last step', () => {
      render(<OnboardingPage />)

      // Navigate to last step
      fireEvent.click(screen.getByText('Next →')) // Step 2
      fireEvent.click(screen.getByText('Next →')) // Step 3

      expect(screen.getByText('Get Started →')).toBeInTheDocument()
      expect(screen.queryByText('Next →')).not.toBeInTheDocument()
    })

    it('should render all three steps with correct content', () => {
      render(<OnboardingPage />)

      // Step 1 - Welcome
      expect(screen.getByText('Welcome to SprintForge!')).toBeInTheDocument()

      // Step 2 - Features
      fireEvent.click(screen.getByText('Next →'))
      expect(screen.getByText('Key Features')).toBeInTheDocument()
      expect(screen.getByText('Excel-Based Gantt Charts')).toBeInTheDocument()
      expect(screen.getByText('Sprint Planning')).toBeInTheDocument()
      expect(screen.getByText('Probabilistic Timelines')).toBeInTheDocument()
      expect(screen.getByText('Team Collaboration')).toBeInTheDocument()

      // Step 3 - Project Creation
      fireEvent.click(screen.getByText('Next →'))
      expect(screen.getByText('Creating Your First Project')).toBeInTheDocument()
      expect(screen.getByText('Learn how to set up a new project')).toBeInTheDocument()
      expect(screen.getByText('Project Creation Process:')).toBeInTheDocument()
    })
  })

  describe('skip functionality', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: mockUser,
        isLoading: false,
        isAuthenticated: true,
      })
    })

    it('should skip onboarding when skip button in header is clicked', () => {
      render(<OnboardingPage />)

      fireEvent.click(screen.getByText('Skip Setup'))

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        `onboarding-completed-${mockUser.id}`,
        'true'
      )
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })
  })

  describe('onboarding completion', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: mockUser,
        isLoading: false,
        isAuthenticated: true,
      })

      // Mock setTimeout for the completion delay
      jest.useFakeTimers()
    })

    afterEach(() => {
      jest.useRealTimers()
    })

    it('should complete onboarding and redirect when Get Started is clicked', async () => {
      render(<OnboardingPage />)

      // Navigate to last step
      fireEvent.click(screen.getByText('Next →')) // Step 2
      fireEvent.click(screen.getByText('Next →')) // Step 3

      // Click Get Started
      fireEvent.click(screen.getByText('Get Started →'))

      // Button should show loading state
      expect(screen.getByText('Loading...')).toBeInTheDocument()

      // Fast-forward the simulated API call
      jest.advanceTimersByTime(1000)

      await waitFor(() => {
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          `onboarding-completed-${mockUser.id}`,
          'true'
        )
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          `user-preferences-${mockUser.id}`,
          expect.stringContaining('"theme":"light"')
        )
        expect(mockPush).toHaveBeenCalledWith('/dashboard')
      })
    })

    it('should save default preferences during completion', async () => {
      render(<OnboardingPage />)

      // Navigate to last step and complete
      fireEvent.click(screen.getByText('Next →'))
      fireEvent.click(screen.getByText('Next →'))
      fireEvent.click(screen.getByText('Get Started →'))

      jest.advanceTimersByTime(1000)

      await waitFor(() => {
        const savedPreferences = localStorageMock.setItem.mock.calls.find(call =>
          call[0].includes('user-preferences')
        )?.[1]

        expect(savedPreferences).toBeDefined()
        const preferences = JSON.parse(savedPreferences!)
        expect(preferences).toMatchObject({
          theme: 'light',
          emailNotifications: true,
          projectReminders: true,
          weeklyDigest: false,
        })
        expect(preferences.completedAt).toBeDefined()
      })
    })

    it('should disable Get Started button while completing', () => {
      render(<OnboardingPage />)

      // Navigate to last step
      fireEvent.click(screen.getByText('Next →'))
      fireEvent.click(screen.getByText('Next →'))

      // Click Get Started
      fireEvent.click(screen.getByText('Get Started →'))

      // Button should be disabled and show loading
      const button = screen.getByText('Loading...')
      expect(button).toBeDisabled()
    })
  })

  describe('edge cases', () => {
    it('should handle missing user name gracefully', () => {
      const userWithoutName = {
        ...mockUser,
        name: null,
      }

      mockUseAuth.mockReturnValue({
        user: userWithoutName,
        isLoading: false,
        isAuthenticated: true,
      })

      render(<OnboardingPage />)

      expect(screen.getByText('Hello, there!')).toBeInTheDocument()
    })

    it('should not complete onboarding when user is null', async () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isLoading: false,
        isAuthenticated: true,
      })

      render(<OnboardingPage />)

      // Navigate to last step - but this shouldn't happen with null user
      // This tests defensive programming
      fireEvent.click(screen.getByText('Next →'))
      fireEvent.click(screen.getByText('Next →'))
      fireEvent.click(screen.getByText('Get Started →'))

      expect(localStorageMock.setItem).not.toHaveBeenCalled()
    })

    it('should handle window being undefined', () => {
      const originalWindow = window

      // Temporarily make window undefined during component initialization
      const originalDescriptor = Object.getOwnPropertyDescriptor(global, 'window')
      delete (global as any).window

      mockUseAuth.mockReturnValue({
        user: mockUser,
        isLoading: false,
        isAuthenticated: true,
      })

      // This should not crash
      expect(() => render(<OnboardingPage />)).not.toThrow()

      // Restore window
      Object.defineProperty(global, 'window', originalDescriptor || {
        value: originalWindow,
        writable: true,
        enumerable: true,
        configurable: true,
      })
    })
  })

  describe('accessibility', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: mockUser,
        isLoading: false,
        isAuthenticated: true,
      })
    })

    it('should have proper heading hierarchy', () => {
      render(<OnboardingPage />)

      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Welcome to SprintForge!')
    })

    it('should have accessible button labels', () => {
      render(<OnboardingPage />)

      expect(screen.getByRole('button', { name: /skip setup/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument()
    })

    it('should have proper progress indication', () => {
      render(<OnboardingPage />)

      expect(screen.getByText('1 of 3')).toBeInTheDocument()
      expect(screen.getByText('Getting Started')).toBeInTheDocument()
    })
  })
})