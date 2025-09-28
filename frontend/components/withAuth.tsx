"use client"

import { useEffect } from "react"
import { useAuth } from "../hooks/useAuth"

interface WithAuthOptions {
  redirectTo?: string
  redirectIfAuthenticated?: boolean
}

export function withAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options: WithAuthOptions = {}
) {
  const {
    redirectIfAuthenticated = false,
  } = options

  return function AuthGuard(props: P) {
    const { isAuthenticated, isLoading, requireAuth } = useAuth()

    useEffect(() => {
      if (isLoading) return

      if (redirectIfAuthenticated && isAuthenticated) {
        window.location.href = "/dashboard"
        return
      }

      if (!redirectIfAuthenticated && !isAuthenticated) {
        requireAuth()
        return
      }
    }, [isAuthenticated, isLoading, requireAuth])

    // Show loading spinner while checking authentication
    if (isLoading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div
            className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"
            role="status"
            aria-label="Loading authentication"
          >
            <span className="sr-only">Loading...</span>
          </div>
        </div>
      )
    }

    // Don't render if user should be redirected
    if (redirectIfAuthenticated && isAuthenticated) {
      return null
    }

    if (!redirectIfAuthenticated && !isAuthenticated) {
      return null
    }

    return <WrappedComponent {...props} />
  }
}

// Convenience wrapper for pages that require authentication
export function withRequiredAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>
) {
  return withAuth(WrappedComponent, { redirectTo: "/auth/signin" })
}

// Convenience wrapper for pages that should redirect if already authenticated (like login pages)
export function withRedirectIfAuthenticated<P extends object>(
  WrappedComponent: React.ComponentType<P>
) {
  return withAuth(WrappedComponent, { 
    redirectIfAuthenticated: true,
    redirectTo: "/dashboard" 
  })
}