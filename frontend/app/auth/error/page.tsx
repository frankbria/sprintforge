"use client"

import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { Suspense } from "react"
import { Button } from "../../../components/ui/Button"
import { ErrorMessage } from "../../../components/ui/ErrorMessage"
import { PageLoading } from "../../../components/ui/LoadingSpinner"

const errorMessages = {
  Signin: {
    title: "Sign-in Error",
    message: "There was a problem signing you in. Please try with a different account.",
    suggestion: "Try using a different authentication provider or check your account status."
  },
  OAuthSignin: {
    title: "OAuth Provider Error",
    message: "The authentication provider encountered an error.",
    suggestion: "This is usually temporary. Please try again in a few moments."
  },
  OAuthCallback: {
    title: "OAuth Callback Error",
    message: "There was an error during the authentication callback.",
    suggestion: "Please try signing in again. If the problem persists, clear your browser cache."
  },
  OAuthCreateAccount: {
    title: "Account Creation Error",
    message: "Unable to create your account with this provider.",
    suggestion: "Try using a different authentication method or contact support."
  },
  EmailCreateAccount: {
    title: "Email Account Error",
    message: "Unable to create an account with this email address.",
    suggestion: "The email might already be in use with a different provider."
  },
  Callback: {
    title: "Authentication Callback Error",
    message: "The authentication process could not be completed.",
    suggestion: "Please try signing in again."
  },
  OAuthAccountNotLinked: {
    title: "Account Not Linked",
    message: "This account is not linked to your existing profile.",
    suggestion: "To link accounts, sign in with your original authentication method first."
  },
  EmailSignin: {
    title: "Email Authentication Error",
    message: "The verification email could not be sent.",
    suggestion: "Check your email address and try again."
  },
  CredentialsSignin: {
    title: "Invalid Credentials",
    message: "The credentials you provided are incorrect.",
    suggestion: "Please check your username and password, then try again."
  },
  SessionRequired: {
    title: "Authentication Required",
    message: "You need to sign in to access this page.",
    suggestion: "Please sign in with your account to continue."
  },
  default: {
    title: "Authentication Error",
    message: "An unexpected authentication error occurred.",
    suggestion: "Please try again. If the problem persists, contact support."
  }
}

function ErrorContent() {
  const searchParams = useSearchParams()
  const error = searchParams.get("error") as keyof typeof errorMessages
  const errorInfo = errorMessages[error] || errorMessages.default

  const handleRetry = () => {
    window.location.href = "/auth/signin"
  }

  const handleContactSupport = () => {
    // In a real app, this would open a support form or email
    window.location.href = "mailto:support@sprintforge.com?subject=Authentication Error&body=" +
      encodeURIComponent(`Error Code: ${error || "Unknown"}\nTime: ${new Date().toISOString()}\n\nPlease describe what you were trying to do when this error occurred:`)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 via-white to-red-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-lg w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-red-100 mb-6">
            <svg
              className="h-8 w-8 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {errorInfo.title}
          </h1>
          <p className="text-gray-800 text-sm sm:text-base max-w-md mx-auto">
            {errorInfo.message}
          </p>
        </div>

        {/* Error Details Card */}
        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8 border border-gray-100 mb-6">
          <ErrorMessage
            type="error"
            title="What happened?"
            message={errorInfo.suggestion}
            showIcon={false}
            className="border-0 bg-transparent p-0"
          />

          {error && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-800">
                <span className="font-medium">Error Code:</span> {error}
              </p>
              <p className="text-xs text-gray-700 mt-1">
                Reference this code when contacting support
              </p>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="space-y-4">
          <Button
            onClick={handleRetry}
            fullWidth
            size="lg"
            className="bg-blue-600 hover:bg-blue-700 focus:ring-blue-500"
          >
            Try Signing In Again
          </Button>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Button
              onClick={handleContactSupport}
              variant="ghost"
              size="md"
              fullWidth
              className="text-gray-800 hover:text-gray-700"
            >
              Contact Support
            </Button>

            <Link href="/" className="block">
              <Button
                variant="ghost"
                size="md"
                fullWidth
                className="text-gray-800 hover:text-gray-700"
              >
                Back to Home
              </Button>
            </Link>
          </div>
        </div>

        {/* Help Section */}
        <div className="mt-8 text-center">
          <div className="bg-blue-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-blue-900 mb-2">
              Need help?
            </h3>
            <p className="text-xs text-blue-700 leading-relaxed">
              If you continue experiencing issues, try:
            </p>
            <ul className="text-xs text-blue-700 mt-2 space-y-1">
              <li>• Clearing your browser cache and cookies</li>
              <li>• Trying a different browser or device</li>
              <li>• Checking if your account is active</li>
              <li>• Using a different authentication provider</li>
            </ul>
          </div>
        </div>

        {/* Keyboard Navigation Help */}
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-600">
            Use Tab to navigate • Enter to select • Esc to go back
          </p>
        </div>
      </div>
    </div>
  )
}

export default function AuthError() {
  return (
    <Suspense fallback={<PageLoading message="Loading error details..." />}>
      <ErrorContent />
    </Suspense>
  )
}