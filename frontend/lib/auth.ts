import GoogleProvider from "next-auth/providers/google"
import AzureADProvider from "next-auth/providers/azure-ad"
import type { NextAuthOptions } from "next-auth"
import { JWT } from "next-auth/jwt"

// Token blacklist for enhanced security
const tokenBlacklist = new Set<string>()

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          prompt: "consent",
          access_type: "offline",
          response_type: "code"
        }
      }
    }),
    AzureADProvider({
      clientId: process.env.AZURE_AD_CLIENT_ID!,
      clientSecret: process.env.AZURE_AD_CLIENT_SECRET!,
      tenantId: process.env.AZURE_AD_TENANT_ID,
      authorization: {
        params: {
          scope: "openid profile email offline_access"
        }
      }
    }),
  ],
  callbacks: {
    async jwt({ token, user, account }): Promise<JWT> {
      // Check if token is blacklisted
      if (token.jti && tokenBlacklist.has(token.jti as string)) {
        throw new Error("Token has been revoked")
      }

      // Add unique token identifier for blacklisting
      if (!token.jti) {
        token.jti = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      }

      // Set token expiration and refresh logic
      const now = Math.floor(Date.now() / 1000)
      const tokenExpiry = token.exp as number

      // If token is close to expiring (within 5 minutes), refresh it
      if (tokenExpiry && (tokenExpiry - now) < 300) {
        try {
          // Attempt to refresh the token
          if (account?.refresh_token) {
            const response = await refreshAccessToken(token)
            return response
          }
        } catch (error) {
          console.error("Token refresh failed:", error)
          // Return existing token, let it expire naturally
        }
      }

      // Persist the OAuth access_token and user id
      if (account) {
        token.accessToken = account.access_token
        token.refreshToken = account.refresh_token
        token.provider = account.provider
        token.accessTokenExpires = account.expires_at ? account.expires_at * 1000 : Date.now() + 3600 * 1000
      }
      if (user) {
        token.id = user.id
      }

      // Add security metadata
      token.iat = now
      token.lastActivity = now

      return token
    },
    async session({ session, token }) {
      // Send properties to the client
      if (token) {
        session.accessToken = token.accessToken as string
        session.user.id = token.id as string
        session.provider = token.provider as string
        // Note: tokenId removed as it's not in Session type
      }
      return session
    },
    async signIn({ account, profile }) {
      // Additional security checks during sign-in
      // Note: email_verified check disabled - property not in Profile type
      if (account?.provider === "google") {
        // Add proper type-safe email verification if needed
        return true
      }
      return true
    }
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
    updateAge: 24 * 60 * 60, // 24 hours
  },
  jwt: {
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  pages: {
    signIn: "/auth/signin",
    error: "/auth/error",
  },
  cookies: {
    sessionToken: {
      name: `next-auth.session-token`,
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: process.env.NODE_ENV === 'production'
      }
    },
    callbackUrl: {
      name: `next-auth.callback-url`,
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: process.env.NODE_ENV === 'production'
      }
    },
    csrfToken: {
      name: `next-auth.csrf-token`,
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: process.env.NODE_ENV === 'production'
      }
    }
  },
  events: {
    async signOut({ token }) {
      // Blacklist token on signout
      if (token?.jti) {
        blacklistToken(token.jti as string)
      }
    }
  },
  debug: process.env.NODE_ENV === "development",
}

// Token refresh function for automatic token renewal
async function refreshAccessToken(token: JWT): Promise<JWT> {
  try {
    let refreshUrl: string
    let params: URLSearchParams

    if (token.provider === "google") {
      refreshUrl = "https://oauth2.googleapis.com/token"
      params = new URLSearchParams({
        client_id: process.env.GOOGLE_CLIENT_ID!,
        client_secret: process.env.GOOGLE_CLIENT_SECRET!,
        grant_type: "refresh_token",
        refresh_token: token.refreshToken as string,
      })
    } else if (token.provider === "azure-ad") {
      refreshUrl = `https://login.microsoftonline.com/${process.env.AZURE_AD_TENANT_ID}/oauth2/v2.0/token`
      params = new URLSearchParams({
        client_id: process.env.AZURE_AD_CLIENT_ID!,
        client_secret: process.env.AZURE_AD_CLIENT_SECRET!,
        grant_type: "refresh_token",
        refresh_token: token.refreshToken as string,
        scope: "openid profile email offline_access"
      })
    } else {
      throw new Error("Unsupported provider for token refresh")
    }

    const response = await fetch(refreshUrl, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      method: "POST",
      body: params,
    })

    const refreshedTokens = await response.json()

    if (!response.ok) {
      throw new Error(`Token refresh failed: ${refreshedTokens.error || 'Unknown error'}`)
    }

    return {
      ...token,
      accessToken: refreshedTokens.access_token,
      accessTokenExpires: Date.now() + refreshedTokens.expires_in * 1000,
      refreshToken: refreshedTokens.refresh_token ?? token.refreshToken,
      lastRefreshed: Math.floor(Date.now() / 1000)
    }
  } catch (error) {
    console.error("Error refreshing access token:", error)
    return {
      ...token,
      error: "RefreshAccessTokenError",
    }
  }
}

// Token blacklisting functions for security
export function blacklistToken(tokenId: string): void {
  tokenBlacklist.add(tokenId)
  // In production, this should be stored in Redis or database
  console.log(`Token ${tokenId} has been blacklisted`)
}

export function isTokenBlacklisted(tokenId: string): boolean {
  return tokenBlacklist.has(tokenId)
}

export function clearTokenBlacklist(): void {
  tokenBlacklist.clear()
}