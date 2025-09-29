"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "../hooks/useAuth"
import { useOnboarding } from "../hooks/useOnboarding"
import { PageLoading } from "./ui/LoadingSpinner"

interface OnboardingWrapperProps {
  children: React.ReactNode
  requireOnboarding?: boolean
}

export function OnboardingWrapper({ children, requireOnboarding = true }: OnboardingWrapperProps) {
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const { isOnboardingCompleted, isLoading: onboardingLoading } = useOnboarding()
  const router = useRouter()

  useEffect(() => {
    // Don't redirect if we're still loading
    if (authLoading || onboardingLoading) {
      return
    }

    // Redirect to login if not authenticated
    if (!isAuthenticated) {
      router.push("/auth/signin")
      return
    }

    // Redirect to onboarding if required and not completed
    if (requireOnboarding && !isOnboardingCompleted) {
      router.push("/onboarding")
      return
    }
  }, [isAuthenticated, isOnboardingCompleted, authLoading, onboardingLoading, requireOnboarding, router])

  // Show loading while checking authentication and onboarding status
  if (authLoading || onboardingLoading) {
    return <PageLoading message="Checking your account..." />
  }

  // Don't render children if not authenticated
  if (!isAuthenticated) {
    return null
  }

  // Don't render children if onboarding is required but not completed
  if (requireOnboarding && !isOnboardingCompleted) {
    return null
  }

  return <>{children}</>
}

// Higher-order component for pages that require onboarding
export function withOnboarding<P extends object>(
  Component: React.ComponentType<P>,
  requireOnboarding = true
) {
  const WrappedComponent = (props: P) => (
    <OnboardingWrapper requireOnboarding={requireOnboarding}>
      <Component {...props} />
    </OnboardingWrapper>
  )

  WrappedComponent.displayName = `withOnboarding(${Component.displayName || Component.name})`

  return WrappedComponent
}