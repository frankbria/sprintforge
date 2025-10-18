"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "../../hooks/useAuth"
import { Button } from "../../components/ui/Button"
import { PageLoading } from "../../components/ui/LoadingSpinner"

interface OnboardingStep {
  id: string
  title: string
  description: string
  content: React.ReactNode
}

export default function OnboardingPage() {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(0)
  const [isCompleting, setIsCompleting] = useState(false)

  // Check if user needs onboarding
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/auth/signin")
      return
    }

    // Check if user has already completed onboarding
    if (user && typeof window !== 'undefined') {
      const hasCompletedOnboarding = localStorage.getItem(`onboarding-completed-${user.id}`)
      if (hasCompletedOnboarding) {
        router.push("/dashboard")
      }
    }
  }, [isLoading, isAuthenticated, user, router])

  const steps: OnboardingStep[] = [
    {
      id: "welcome",
      title: "Welcome to SprintForge!",
      description: "Let's get you started with the basics",
      content: (
        <div className="text-center space-y-6">
          <div className="mx-auto h-24 w-24 flex items-center justify-center rounded-full bg-blue-100">
            <svg className="h-12 w-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Hello, {user?.name || 'there'}!
            </h3>
            <p className="text-gray-800">
              SprintForge helps you manage projects with powerful Excel-based Gantt charts and sprint planning.
              Let&apos;s walk through the key features to get you productive quickly.
            </p>
          </div>
        </div>
      )
    },
    {
      id: "features",
      title: "Key Features",
      description: "Discover what SprintForge can do for you",
      content: (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Excel-Based Gantt Charts</h4>
                <p className="text-sm text-gray-800">Generate sophisticated project timelines without macros</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Sprint Planning</h4>
                <p className="text-sm text-gray-800">Plan and track your agile development cycles</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center">
                <svg className="h-5 w-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Probabilistic Timelines</h4>
                <p className="text-sm text-gray-800">Monte Carlo simulations for realistic project estimates</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 h-8 w-8 bg-orange-100 rounded-full flex items-center justify-center">
                <svg className="h-5 w-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Team Collaboration</h4>
                <p className="text-sm text-gray-800">Share projects and coordinate with your team</p>
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      id: "project-creation",
      title: "Creating Your First Project",
      description: "Learn how to set up a new project",
      content: (
        <div className="space-y-6">
          <div className="bg-gray-50 rounded-lg p-6">
            <h4 className="font-medium text-gray-900 mb-4">Project Creation Process:</h4>
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">1</div>
                <span className="text-gray-700">Define project scope and timeline</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">2</div>
                <span className="text-gray-700">Add tasks and dependencies</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">3</div>
                <span className="text-gray-700">Configure team members and roles</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">4</div>
                <span className="text-gray-700">Generate Excel files and track progress</span>
              </div>
            </div>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <svg className="h-5 w-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h5 className="font-medium text-blue-900">Pro Tip</h5>
                <p className="text-sm text-blue-700">Start with a simple project to familiarize yourself with the interface, then scale up to more complex workflows.</p>
              </div>
            </div>
          </div>
        </div>
      )
    }
  ]

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const skipOnboarding = () => {
    if (user) {
      localStorage.setItem(`onboarding-completed-${user.id}`, 'true')
      router.push("/dashboard")
    }
  }

  const completeOnboarding = async () => {
    setIsCompleting(true)

    // Mark onboarding as completed
    if (user) {
      localStorage.setItem(`onboarding-completed-${user.id}`, 'true')

      // Initialize default user preferences
      const defaultPreferences = {
        theme: 'light',
        emailNotifications: true,
        projectReminders: true,
        weeklyDigest: false,
        completedAt: new Date().toISOString()
      }
      localStorage.setItem(`user-preferences-${user.id}`, JSON.stringify(defaultPreferences))
    }

    // Simulate API call for preference initialization
    await new Promise(resolve => setTimeout(resolve, 1000))

    setIsCompleting(false)
    router.push("/dashboard")
  }

  if (isLoading) {
    return <PageLoading message="Loading onboarding..." />
  }

  if (!isAuthenticated) {
    return null
  }

  const currentStepData = steps[currentStep]
  const isLastStep = currentStep === steps.length - 1

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <span className="text-lg font-semibold text-gray-900">SprintForge</span>
            </div>
            <Button variant="ghost" onClick={skipOnboarding}>
              Skip Setup
            </Button>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-medium text-gray-800">Getting Started</h2>
            <span className="text-sm text-gray-700">{currentStep + 1} of {steps.length}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-in-out"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {currentStepData.title}
            </h1>
            <p className="text-gray-800">
              {currentStepData.description}
            </p>
          </div>

          <div className="mb-8">
            {currentStepData.content}
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between pt-6 border-t border-gray-200">
            <Button
              variant="ghost"
              onClick={prevStep}
              disabled={currentStep === 0}
            >
              ← Previous
            </Button>

            <div className="flex space-x-2">
              {steps.map((_, index) => (
                <div
                  key={index}
                  className={`w-2 h-2 rounded-full ${
                    index === currentStep
                      ? 'bg-blue-600'
                      : index < currentStep
                      ? 'bg-blue-300'
                      : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>

            {isLastStep ? (
              <Button
                onClick={completeOnboarding}
                loading={isCompleting}
                loadingText="Setting up..."
              >
                Get Started →
              </Button>
            ) : (
              <Button onClick={nextStep}>
                Next →
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}