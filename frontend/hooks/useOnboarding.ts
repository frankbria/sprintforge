"use client"

import { useState, useEffect, useCallback } from "react"
import { useAuth } from "./useAuth"

export interface UserPreferences {
  theme: 'light' | 'dark'
  emailNotifications: boolean
  projectReminders: boolean
  weeklyDigest: boolean
  language?: string
  timezone?: string
  completedAt: string
}

export interface OnboardingState {
  isOnboardingCompleted: boolean
  needsAccountSetup: boolean
  preferences: UserPreferences | null
  isLoading: boolean
}

export interface OnboardingActions {
  completeOnboarding: () => Promise<void>
  skipOnboarding: () => void
  updatePreferences: (preferences: Partial<UserPreferences>) => Promise<void>
  resetOnboarding: () => void
  checkOnboardingStatus: () => boolean
}

export function useOnboarding(): OnboardingState & OnboardingActions {
  const { user, isAuthenticated } = useAuth()
  const [isOnboardingCompleted, setIsOnboardingCompleted] = useState(false)
  const [needsAccountSetup, setNeedsAccountSetup] = useState(false)
  const [preferences, setPreferences] = useState<UserPreferences | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check onboarding status when user changes
  useEffect(() => {
    if (!user || !isAuthenticated) {
      setIsLoading(false)
      return
    }

    checkUserOnboardingStatus()
  }, [user, isAuthenticated])

  const checkUserOnboardingStatus = useCallback(() => {
    if (!user) return

    setIsLoading(true)

    try {
      // Check if onboarding was completed
      const onboardingCompleted = localStorage.getItem(`onboarding-completed-${user.id}`)
      const isCompleted = !!onboardingCompleted

      // Check if account setup is needed (missing profile information)
      const needsSetup = !user.name || !user.email

      // Load user preferences
      const savedPreferences = localStorage.getItem(`user-preferences-${user.id}`)
      let userPrefs: UserPreferences | null = null

      if (savedPreferences) {
        try {
          userPrefs = JSON.parse(savedPreferences)
        } catch (error) {
          console.error("Failed to parse user preferences:", error)
        }
      }

      // Set default preferences if none exist and user is authenticated
      if (!userPrefs && isAuthenticated) {
        userPrefs = {
          theme: 'light',
          emailNotifications: true,
          projectReminders: true,
          weeklyDigest: false,
          language: 'en',
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          completedAt: new Date().toISOString()
        }
      }

      setIsOnboardingCompleted(isCompleted)
      setNeedsAccountSetup(needsSetup)
      setPreferences(userPrefs)
    } catch (error) {
      console.error("Error checking onboarding status:", error)
    } finally {
      setIsLoading(false)
    }
  }, [user, isAuthenticated])

  const completeOnboarding = useCallback(async () => {
    if (!user) return

    try {
      // Mark onboarding as completed
      localStorage.setItem(`onboarding-completed-${user.id}`, 'true')

      // Ensure preferences are saved
      if (!preferences) {
        const defaultPreferences: UserPreferences = {
          theme: 'light',
          emailNotifications: true,
          projectReminders: true,
          weeklyDigest: false,
          language: 'en',
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          completedAt: new Date().toISOString()
        }

        localStorage.setItem(`user-preferences-${user.id}`, JSON.stringify(defaultPreferences))
        setPreferences(defaultPreferences)
      }

      // Simulate API call to save preferences to backend
      await new Promise(resolve => setTimeout(resolve, 500))

      setIsOnboardingCompleted(true)
      setNeedsAccountSetup(false)
    } catch (error) {
      console.error("Failed to complete onboarding:", error)
      throw error
    }
  }, [user, preferences])

  const skipOnboarding = useCallback(() => {
    if (!user) return

    // Mark onboarding as completed but skip preference setup
    localStorage.setItem(`onboarding-completed-${user.id}`, 'true')

    // Set minimal preferences
    const minimalPreferences: UserPreferences = {
      theme: 'light',
      emailNotifications: true,
      projectReminders: true,
      weeklyDigest: false,
      completedAt: new Date().toISOString()
    }

    localStorage.setItem(`user-preferences-${user.id}`, JSON.stringify(minimalPreferences))

    setIsOnboardingCompleted(true)
    setNeedsAccountSetup(false)
    setPreferences(minimalPreferences)
  }, [user])

  const updatePreferences = useCallback(async (newPreferences: Partial<UserPreferences>) => {
    if (!user || !preferences) return

    try {
      const updatedPreferences = {
        ...preferences,
        ...newPreferences
      }

      localStorage.setItem(`user-preferences-${user.id}`, JSON.stringify(updatedPreferences))
      setPreferences(updatedPreferences)

      // Simulate API call to save preferences
      await new Promise(resolve => setTimeout(resolve, 300))
    } catch (error) {
      console.error("Failed to update preferences:", error)
      throw error
    }
  }, [user, preferences])

  const resetOnboarding = useCallback(() => {
    if (!user) return

    localStorage.removeItem(`onboarding-completed-${user.id}`)
    localStorage.removeItem(`user-preferences-${user.id}`)

    setIsOnboardingCompleted(false)
    setNeedsAccountSetup(true)
    setPreferences(null)
  }, [user])

  const checkOnboardingStatus = useCallback(() => {
    if (!user) return false
    return !!localStorage.getItem(`onboarding-completed-${user.id}`)
  }, [user])

  return {
    isOnboardingCompleted,
    needsAccountSetup,
    preferences,
    isLoading,
    completeOnboarding,
    skipOnboarding,
    updatePreferences,
    resetOnboarding,
    checkOnboardingStatus
  }
}