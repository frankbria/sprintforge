"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "../../../hooks/useAuth"
import { useOnboarding } from "../../../hooks/useOnboarding"
import { Button } from "../../../components/ui/Button"
import { ErrorMessage } from "../../../components/ui/ErrorMessage"
import { PageLoading } from "../../../components/ui/LoadingSpinner"

interface FormData {
  displayName: string
  email: string
  timezone: string
  language: string
  emailNotifications: boolean
  projectReminders: boolean
  weeklyDigest: boolean
}

interface FormErrors {
  displayName?: string
  email?: string
  timezone?: string
  language?: string
}

export default function OnboardingSetupPage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth()
  const { updatePreferences, completeOnboarding } = useOnboarding()
  const router = useRouter()

  const [formData, setFormData] = useState<FormData>({
    displayName: '',
    email: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: 'en',
    emailNotifications: true,
    projectReminders: true,
    weeklyDigest: false
  })

  const [formErrors, setFormErrors] = useState<FormErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  // Initialize form data when user loads
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/auth/signin")
      return
    }

    if (user) {
      setFormData(prev => ({
        ...prev,
        displayName: user.name || '',
        email: user.email || ''
      }))
    }
  }, [user, authLoading, isAuthenticated, router])

  const validateForm = (): boolean => {
    const errors: FormErrors = {}

    if (!formData.displayName.trim()) {
      errors.displayName = "Display name is required"
    } else if (formData.displayName.trim().length < 2) {
      errors.displayName = "Display name must be at least 2 characters"
    }

    if (!formData.email.trim()) {
      errors.email = "Email is required"
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = "Please enter a valid email address"
    }

    if (!formData.timezone) {
      errors.timezone = "Please select your timezone"
    }

    if (!formData.language) {
      errors.language = "Please select your language"
    }

    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleInputChange = (field: keyof FormData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }))

    // Clear error when user starts typing
    if (formErrors[field as keyof FormErrors]) {
      setFormErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    setIsSubmitting(true)
    setSubmitError(null)

    try {
      // Update user preferences
      await updatePreferences({
        theme: 'light',
        emailNotifications: formData.emailNotifications,
        projectReminders: formData.projectReminders,
        weeklyDigest: formData.weeklyDigest,
        language: formData.language,
        timezone: formData.timezone,
        completedAt: new Date().toISOString()
      })

      // Complete onboarding
      await completeOnboarding()

      // Redirect to dashboard
      router.push("/dashboard")
    } catch (error) {
      console.error("Failed to complete setup:", error)
      setSubmitError("Failed to save your preferences. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  const skipSetup = () => {
    router.push("/dashboard")
  }

  if (authLoading) {
    return <PageLoading message="Loading account setup..." />
  }

  if (!isAuthenticated) {
    return null
  }

  const timezones = [
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Asia/Tokyo',
    'Asia/Shanghai',
    'Australia/Sydney',
    'UTC'
  ]

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Español' },
    { code: 'fr', name: 'Français' },
    { code: 'de', name: 'Deutsch' },
    { code: 'pt', name: 'Português' },
    { code: 'ja', name: '日本語' },
    { code: 'zh', name: '中文' }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <span className="text-lg font-semibold text-gray-900">SprintForge</span>
            </div>
            <Button variant="ghost" onClick={skipSetup}>
              Skip for Now
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Complete Your Account Setup
            </h1>
            <p className="text-gray-800">
              Help us personalize your SprintForge experience by completing your profile and preferences.
            </p>
          </div>

          {submitError && (
            <div className="mb-6">
              <ErrorMessage message={submitError} onClose={() => setSubmitError(null)} />
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Personal Information */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Personal Information</h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="displayName" className="block text-sm font-medium text-gray-700 mb-1">
                    Display Name *
                  </label>
                  <input
                    type="text"
                    id="displayName"
                    value={formData.displayName}
                    onChange={(e) => handleInputChange('displayName', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      formErrors.displayName ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                    placeholder="Your name"
                  />
                  {formErrors.displayName && (
                    <p className="mt-1 text-sm text-red-600">{formErrors.displayName}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address *
                  </label>
                  <input
                    type="email"
                    id="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      formErrors.email ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                    placeholder="your.email@example.com"
                  />
                  {formErrors.email && (
                    <p className="mt-1 text-sm text-red-600">{formErrors.email}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Localization */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Localization</h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="timezone" className="block text-sm font-medium text-gray-700 mb-1">
                    Timezone *
                  </label>
                  <select
                    id="timezone"
                    value={formData.timezone}
                    onChange={(e) => handleInputChange('timezone', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      formErrors.timezone ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                  >
                    {timezones.map(tz => (
                      <option key={tz} value={tz}>{tz}</option>
                    ))}
                  </select>
                  {formErrors.timezone && (
                    <p className="mt-1 text-sm text-red-600">{formErrors.timezone}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-1">
                    Language *
                  </label>
                  <select
                    id="language"
                    value={formData.language}
                    onChange={(e) => handleInputChange('language', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      formErrors.language ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                  >
                    {languages.map(lang => (
                      <option key={lang.code} value={lang.code}>{lang.name}</option>
                    ))}
                  </select>
                  {formErrors.language && (
                    <p className="mt-1 text-sm text-red-600">{formErrors.language}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Notification Preferences */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Notification Preferences</h3>
              <div className="space-y-4">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="emailNotifications"
                    checked={formData.emailNotifications}
                    onChange={(e) => handleInputChange('emailNotifications', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="emailNotifications" className="ml-2 block text-sm text-gray-900">
                    Email notifications for project updates
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="projectReminders"
                    checked={formData.projectReminders}
                    onChange={(e) => handleInputChange('projectReminders', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="projectReminders" className="ml-2 block text-sm text-gray-900">
                    Project deadline reminders
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="weeklyDigest"
                    checked={formData.weeklyDigest}
                    onChange={(e) => handleInputChange('weeklyDigest', e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="weeklyDigest" className="ml-2 block text-sm text-gray-900">
                    Weekly progress digest
                  </label>
                </div>
              </div>
            </div>

            {/* Subscription Tiers Information */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-blue-900 mb-3">Subscription Tiers</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white rounded-lg p-4 border">
                  <h4 className="font-medium text-gray-900">Free</h4>
                  <p className="text-sm text-gray-800 mt-1">3 projects, basic features</p>
                  <p className="text-sm font-medium text-green-600 mt-2">Current Plan</p>
                </div>
                <div className="bg-white rounded-lg p-4 border">
                  <h4 className="font-medium text-gray-900">Pro</h4>
                  <p className="text-sm text-gray-800 mt-1">Unlimited projects, advanced analytics</p>
                  <p className="text-sm text-gray-700 mt-2">$19/month</p>
                </div>
                <div className="bg-white rounded-lg p-4 border">
                  <h4 className="font-medium text-gray-900">Team</h4>
                  <p className="text-sm text-gray-800 mt-1">Team collaboration, enterprise features</p>
                  <p className="text-sm text-gray-700 mt-2">$49/month</p>
                </div>
              </div>
            </div>

            {/* Submit Buttons */}
            <div className="flex items-center justify-between pt-6 border-t border-gray-200">
              <Button
                type="button"
                variant="ghost"
                onClick={skipSetup}
              >
                Skip for Now
              </Button>

              <Button
                type="submit"
                loading={isSubmitting}
                loadingText="Saving..."
                disabled={Object.keys(formErrors).length > 0}
              >
                Complete Setup
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}