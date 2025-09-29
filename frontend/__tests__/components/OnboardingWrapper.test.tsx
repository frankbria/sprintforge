import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import { OnboardingWrapper, withOnboarding } from '../../components/OnboardingWrapper'

// Mock the hooks
jest.mock('../../hooks/useAuth')
jest.mock('../../hooks/useOnboarding')
jest.mock('../../components/ui/LoadingSpinner', () => ({
  PageLoading: ({ message }: { message: string }) => <div data-testid="page-loading">{message}</div>
}))

const mockUseAuth = require('../../hooks/useAuth').useAuth as jest.MockedFunction<any>
const mockUseOnboarding = require('../../hooks/useOnboarding').useOnboarding as jest.MockedFunction<any>
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>

describe('OnboardingWrapper', () => {
  const mockPush = jest.fn()
  const TestContent = () => <div data-testid="test-content">Test Content</div>

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
  })

  describe('loading states', () => {
    it('should show loading when auth is loading', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
      })
      mockUseOnboarding.mockReturnValue({
        isOnboardingCompleted: false,
        isLoading: false,
      })

      render(
        <OnboardingWrapper>
          <TestContent />
        </OnboardingWrapper>
      )

      expect(screen.getByTestId('page-loading')).toBeInTheDocument()
      expect(screen.getByText('Checking your account...')).toBeInTheDocument()
      expect(screen.queryByTestId('test-content')).not.toBeInTheDocument()
    })

    it('should show loading when onboarding is loading', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
      })
      mockUseOnboarding.mockReturnValue({
        isOnboardingCompleted: false,
        isLoading: true,
      })

      render(
        <OnboardingWrapper>
          <TestContent />
        </OnboardingWrapper>
      )

      expect(screen.getByTestId('page-loading')).toBeInTheDocument()
      expect(screen.getByText('Checking your account...')).toBeInTheDocument()
      expect(screen.queryByTestId('test-content')).not.toBeInTheDocument()
    })

    it('should show loading when both are loading', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
      })
      mockUseOnboarding.mockReturnValue({
        isOnboardingCompleted: false,
        isLoading: true,
      })

      render(
        <OnboardingWrapper>
          <TestContent />
        </OnboardingWrapper>
      )

      expect(screen.getByTestId('page-loading')).toBeInTheDocument()
      expect(screen.queryByTestId('test-content')).not.toBeInTheDocument()
    })
  })

  describe('authentication redirection', () => {
    it('should redirect to signin when not authenticated', async () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
      })
      mockUseOnboarding.mockReturnValue({
        isOnboardingCompleted: true,
        isLoading: false,
      })

      render(
        <OnboardingWrapper>
          <TestContent />
        </OnboardingWrapper>
      )

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/auth/signin')
      })
      expect(screen.queryByTestId('test-content')).not.toBeInTheDocument()
    })

    it('should not redirect when loading states are active', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
      })
      mockUseOnboarding.mockReturnValue({
        isOnboardingCompleted: false,
        isLoading: false,
      })

      render(
        <OnboardingWrapper>
          <TestContent />
        </OnboardingWrapper>
      )

      expect(mockPush).not.toHaveBeenCalled()
    })

    it('should not render content when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
      })
      mockUseOnboarding.mockReturnValue({
        isOnboardingCompleted: true,
        isLoading: false,
      })

      render(
        <OnboardingWrapper>
          <TestContent />
        </OnboardingWrapper>
      )

      expect(screen.queryByTestId('test-content')).not.toBeInTheDocument()
    })
  })

  describe('onboarding redirection', () => {
    it('should redirect to onboarding when authenticated but onboarding not completed', async () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
      })
      mockUseOnboarding.mockReturnValue({
        isOnboardingCompleted: false,
        isLoading: false,
      })

      render(
        <OnboardingWrapper>
          <TestContent />
        </OnboardingWrapper>
      )

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/onboarding')
      })
      expect(screen.queryByTestId('test-content')).not.toBeInTheDocument()
    })

    it('should not redirect to onboarding when requireOnboarding is false', async () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
      })
      mockUseOnboarding.mockReturnValue({
        isOnboardingCompleted: false,
        isLoading: false,
      })

      render(
        <OnboardingWrapper requireOnboarding={false}>
          <TestContent />
        </OnboardingWrapper>
      )

      expect(mockPush).not.toHaveBeenCalled()
      expect(screen.getByTestId('test-content')).toBeInTheDocument()
    })

    it('should not render content when onboarding is required but not completed', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
      })
      mockUseOnboarding.mockReturnValue({
        isOnboardingCompleted: false,
        isLoading: false,
      })

      render(
        <OnboardingWrapper requireOnboarding={true}>
          <TestContent />
        </OnboardingWrapper>
      )

      expect(screen.queryByTestId('test-content')).not.toBeInTheDocument()
    })
  })

  describe('successful rendering', () => {
    it('should render children when authenticated and onboarding completed', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
      })
      mockUseOnboarding.mockReturnValue({
        isOnboardingCompleted: true,
        isLoading: false,
      })

      render(
        <OnboardingWrapper>
          <TestContent />
        </OnboardingWrapper>
      )

      expect(screen.getByTestId('test-content')).toBeInTheDocument()
      expect(mockPush).not.toHaveBeenCalled()
    })

    it('should render children when authenticated and onboarding not required', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
      })
      mockUseOnboarding.mockReturnValue({
        isOnboardingCompleted: false,
        isLoading: false,
      })

      render(
        <OnboardingWrapper requireOnboarding={false}>
          <TestContent />
        </OnboardingWrapper>
      )

      expect(screen.getByTestId('test-content')).toBeInTheDocument()
      expect(mockPush).not.toHaveBeenCalled()
    })
  })

  describe('effect dependencies', () => {
    it('should re-run effect when dependencies change', async () => {
      const { rerender } = render(
        <OnboardingWrapper>
          <TestContent />
        </OnboardingWrapper>
      )

      // Initial state - loading
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
      })
      mockUseOnboarding.mockReturnValue({
        isOnboardingCompleted: false,
        isLoading: false,
      })

      rerender(
        <OnboardingWrapper>
          <TestContent />
        </OnboardingWrapper>
      )

      // Change to authenticated and completed
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
      })
      mockUseOnboarding.mockReturnValue({
        isOnboardingCompleted: true,
        isLoading: false,
      })

      rerender(
        <OnboardingWrapper>
          <TestContent />
        </OnboardingWrapper>
      )

      expect(screen.getByTestId('test-content')).toBeInTheDocument()
    })
  })
})

describe('withOnboarding HOC', () => {
  const TestComponent = ({ testProp }: { testProp: string }) => (
    <div data-testid="hoc-content">HOC Content: {testProp}</div>
  )

  beforeEach(() => {
    jest.clearAllMocks()
    mockUseRouter.mockReturnValue({
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    })
  })

  it('should wrap component with OnboardingWrapper', () => {
    const WrappedComponent = withOnboarding(TestComponent)

    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
    })
    mockUseOnboarding.mockReturnValue({
      isOnboardingCompleted: true,
      isLoading: false,
    })

    render(<WrappedComponent testProp="test value" />)

    expect(screen.getByTestId('hoc-content')).toBeInTheDocument()
    expect(screen.getByText('HOC Content: test value')).toBeInTheDocument()
  })

  it('should pass requireOnboarding parameter correctly', () => {
    const WrappedComponent = withOnboarding(TestComponent, false)

    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
    })
    mockUseOnboarding.mockReturnValue({
      isOnboardingCompleted: false,
      isLoading: false,
    })

    render(<WrappedComponent testProp="test value" />)

    // Should render content even though onboarding is not completed
    // because requireOnboarding is false
    expect(screen.getByTestId('hoc-content')).toBeInTheDocument()
  })

  it('should set correct displayName', () => {
    const WrappedComponent = withOnboarding(TestComponent)
    expect(WrappedComponent.displayName).toBe('withOnboarding(TestComponent)')
  })

  it('should set displayName with fallback when component has no name', () => {
    const AnonymousComponent = () => <div>Anonymous</div>
    const WrappedComponent = withOnboarding(AnonymousComponent)
    expect(WrappedComponent.displayName).toBe('withOnboarding(AnonymousComponent)')
  })

  it('should preserve all props passed to wrapped component', () => {
    const ComplexComponent = ({
      prop1,
      prop2,
      prop3
    }: {
      prop1: string
      prop2: number
      prop3: boolean
    }) => (
      <div data-testid="complex-content">
        {prop1} - {prop2} - {prop3.toString()}
      </div>
    )

    const WrappedComponent = withOnboarding(ComplexComponent)

    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
    })
    mockUseOnboarding.mockReturnValue({
      isOnboardingCompleted: true,
      isLoading: false,
    })

    render(
      <WrappedComponent
        prop1="test"
        prop2={42}
        prop3={true}
      />
    )

    expect(screen.getByTestId('complex-content')).toBeInTheDocument()
    expect(screen.getByText('test - 42 - true')).toBeInTheDocument()
  })

  it('should handle authentication flow in HOC', () => {
    const WrappedComponent = withOnboarding(TestComponent)

    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
    })
    mockUseOnboarding.mockReturnValue({
      isOnboardingCompleted: false,
      isLoading: false,
    })

    render(<WrappedComponent testProp="test value" />)

    // Should not render content when not authenticated
    expect(screen.queryByTestId('hoc-content')).not.toBeInTheDocument()
  })
})