"use client"

import { getProviders, signIn, getSession } from "next-auth/react"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "../../../components/ui/Button"
import { PageLoading } from "../../../components/ui/LoadingSpinner"
import { ErrorMessage } from "../../../components/ui/ErrorMessage"

interface Provider {
  id: string
  name: string
  type: string
  signinUrl: string
  callbackUrl: string
}

export default function SignIn() {
  const [providers, setProviders] = useState<Record<string, Provider> | null>(null)
  const [loading, setLoading] = useState(true)
  const [signingIn, setSigningIn] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showCredentialsForm, setShowCredentialsForm] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const fetchData = async () => {
      try {
        const session = await getSession()
        if (session) {
          router.push("/")
          return
        }

        const providers = await getProviders()
        setProviders(providers)
      } catch (err) {
        console.error("Failed to fetch providers:", err)
        setError("Failed to load authentication options. Please refresh the page.")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [router])

  const handleSignIn = async (providerId: string) => {
    try {
      setSigningIn(providerId)
      setError(null)

      // For credentials provider, show the credentials form
      if (providerId === "credentials") {
        setShowCredentialsForm(true)
        setSigningIn(null)
        return
      }

      // For OAuth providers, use standard signIn
      await signIn(providerId, { callbackUrl: "/" })
    } catch (error) {
      console.error("Sign-in error:", error)
      setError("Sign-in failed. Please try again.")
      setSigningIn(null)
    }
  }

  const handleCredentialsSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const email = formData.get("email") as string
    const password = formData.get("password") as string

    try {
      setSigningIn("credentials")
      setError(null)

      const result = await signIn("credentials", {
        email,
        password,
        redirect: false,
      })

      if (result?.error) {
        setError("Invalid email or password. Please try again.")
        setSigningIn(null)
      } else if (result?.ok) {
        router.push("/")
      }
    } catch (error) {
      console.error("Credentials sign-in error:", error)
      setError("Sign-in failed. Please try again.")
      setSigningIn(null)
    }
  }

  const getProviderIcon = (providerId: string) => {
    switch (providerId) {
      case "google":
        return (
          <svg className="h-5 w-5" viewBox="0 0 24 24">
            <path
              fill="currentColor"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="currentColor"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="currentColor"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="currentColor"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
        )
      case "azure-ad":
      case "microsoft":
        return (
          <svg className="h-5 w-5" viewBox="0 0 24 24">
            <path fill="#F25022" d="M11.4 11.4H0V0h11.4z" />
            <path fill="#00A4EF" d="M24 11.4H12.6V0H24z" />
            <path fill="#7FBA00" d="M11.4 24H0V12.6h11.4z" />
            <path fill="#FFB900" d="M24 24H12.6V12.6H24z" />
          </svg>
        )
      default:
        return (
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clipRule="evenodd" />
          </svg>
        )
    }
  }

  if (loading) {
    return <PageLoading message="Loading sign in options..." />
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-blue-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-xl bg-blue-600 mb-6">
            <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to SprintForge
          </h1>
          <p className="text-gray-600 text-sm sm:text-base">
            Choose your preferred authentication method to get started
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6">
            <ErrorMessage
              message={error}
              onClose={() => setError(null)}
              actionButton={{
                text: "Retry",
                onClick: () => window.location.reload()
              }}
            />
          </div>
        )}

        {/* Sign In Form */}
        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8 border border-gray-100">
          {showCredentialsForm ? (
            <div>
              <button
                onClick={() => setShowCredentialsForm(false)}
                className="flex items-center text-sm text-gray-600 hover:text-gray-900 mb-6"
              >
                <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
                </svg>
                Back to sign-in options
              </button>
              <form onSubmit={handleCredentialsSubmit} className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    name="email"
                    id="email"
                    required
                    placeholder="demo@sprintforge.com"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    name="password"
                    id="password"
                    required
                    placeholder="Enter your password"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
                  <p className="font-medium mb-1">Demo Accounts:</p>
                  <p>• demo@sprintforge.com / demo123</p>
                  <p>• admin@sprintforge.com / admin123</p>
                </div>
                <Button
                  type="submit"
                  loading={signingIn === "credentials"}
                  loadingText="Signing in..."
                  disabled={!!signingIn}
                  fullWidth
                  size="lg"
                  variant="primary"
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Sign In
                </Button>
              </form>
            </div>
          ) : (
            <div className="space-y-4">
              {providers && Object.values(providers).length > 0 ? (
                Object.values(providers).map((provider) => (
                  <Button
                    key={provider.id}
                    onClick={() => handleSignIn(provider.id)}
                    loading={signingIn === provider.id}
                    loadingText={`Signing in with ${provider.name}...`}
                    disabled={!!signingIn}
                    fullWidth
                    size="lg"
                    variant="secondary"
                    icon={getProviderIcon(provider.id)}
                    className="justify-start pl-4 bg-white border-2 border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-700 transition-all duration-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <span className="flex-1 text-center font-medium">
                      Continue with {provider.name}
                    </span>
                  </Button>
                ))
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500 mb-4">No authentication providers available</p>
                  <Button
                    onClick={() => window.location.reload()}
                    variant="ghost"
                    size="sm"
                  >
                    Refresh Page
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Secure Authentication</span>
            </div>
          </div>

          {/* Security Features */}
          <div className="grid grid-cols-2 gap-4 text-xs text-gray-500">
            <div className="flex items-center">
              <svg className="h-4 w-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>OAuth 2.0</span>
            </div>
            <div className="flex items-center">
              <svg className="h-4 w-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
              </svg>
              <span>Encrypted</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-xs text-gray-500 leading-relaxed">
            By signing in, you agree to our{" "}
            <a href="#" className="text-blue-600 hover:text-blue-500 underline">
              Terms of Service
            </a>{" "}
            and{" "}
            <a href="#" className="text-blue-600 hover:text-blue-500 underline">
              Privacy Policy
            </a>
          </p>
        </div>

        {/* Keyboard Navigation Help */}
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-400">
            Use Tab to navigate • Enter to select
          </p>
        </div>
      </div>
    </div>
  )
}