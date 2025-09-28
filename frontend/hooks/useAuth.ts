"use client"

import { useSession, signIn, signOut } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useCallback } from "react"

export interface AuthUser {
  id: string
  name?: string | null
  email?: string | null
  image?: string | null
}

export interface AuthState {
  user: AuthUser | null
  isLoading: boolean
  isAuthenticated: boolean
  provider?: string
  accessToken?: string
}

export interface AuthActions {
  login: (provider?: string, callbackUrl?: string) => Promise<void>
  logout: (callbackUrl?: string) => Promise<void>
  requireAuth: () => void
}

export function useAuth(): AuthState & AuthActions {
  const { data: session, status } = useSession()
  const router = useRouter()

  const isLoading = status === "loading"
  const isAuthenticated = !!session?.user
  
  const user: AuthUser | null = session?.user ? {
    id: session.user.id,
    name: session.user.name,
    email: session.user.email,
    image: session.user.image,
  } : null

  const login = useCallback(async (provider = "google", callbackUrl = "/dashboard") => {
    try {
      await signIn(provider, { callbackUrl })
    } catch (error) {
      console.error("Login error:", error)
      throw error
    }
  }, [])

  const logout = useCallback(async (callbackUrl = "/") => {
    try {
      await signOut({ callbackUrl })
    } catch (error) {
      console.error("Logout error:", error)
      throw error
    }
  }, [])

  const requireAuth = useCallback(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/auth/signin")
    }
  }, [isLoading, isAuthenticated, router])

  return {
    user,
    isLoading,
    isAuthenticated,
    provider: session?.provider,
    accessToken: session?.accessToken,
    login,
    logout,
    requireAuth,
  }
}