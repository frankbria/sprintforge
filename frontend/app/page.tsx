"use client"

import { useAuth } from "../hooks/useAuth"
import Image from "next/image"
import Link from "next/link"

export default function Home() {
  const { user, isLoading, isAuthenticated, logout } = useAuth()

  const handleLogout = async () => {
    try {
      await logout("/")
    } catch (error) {
      console.error("Logout failed:", error)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div
          className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"
          role="status"
          aria-label="Loading application"
        >
          <span className="sr-only">Loading...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="font-sans grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-4 pb-10 gap-8 sm:p-8 sm:pb-20 sm:gap-16">
      <main className="flex flex-col gap-8 row-start-2 items-center sm:items-start max-w-6xl w-full">
        <div className="flex flex-col sm:flex-row items-center justify-between w-full gap-4">
          <div className="flex items-center gap-4">
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900">SprintForge</h1>
            <div className="text-sm text-gray-800 hidden sm:block">
              Project Management & Excel Generation
            </div>
          </div>
          {isAuthenticated && (
            <div className="flex items-center gap-4">
              <Link
                href="/dashboard"
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Dashboard
              </Link>
              <Link
                href="/profile"
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Profile
              </Link>
            </div>
          )}
        </div>

        <div className="text-sm text-gray-800 sm:hidden text-center">
          Project Management & Excel Generation
        </div>

        {isAuthenticated ? (
          <div className="w-full max-w-md mx-auto sm:mx-0">
            <div className="bg-white rounded-lg shadow-md p-6 border">
              <div className="flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-4">
                {user?.image && (
                  <Image
                    src={user.image}
                    alt="Profile"
                    width={48}
                    height={48}
                    className="rounded-full"
                  />
                )}
                <div className="text-center sm:text-left">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Welcome back, {user?.name}!
                  </h3>
                  <p className="text-sm text-gray-800">{user?.email}</p>
                </div>
              </div>
              <div className="mt-6 space-y-3">
                <Link
                  href="/dashboard"
                  className="block w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md text-center transition-colors"
                >
                  Go to Dashboard
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded-md transition-colors"
                >
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="w-full max-w-md mx-auto sm:mx-0">
            <div className="bg-white rounded-lg shadow-md p-6 border">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Get Started
              </h2>
              <p className="text-gray-800 mb-6">
                Sign in to create and manage your projects with advanced Excel generation capabilities.
              </p>
              <Link
                href="/auth/signin"
                className="block w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md text-center transition-colors"
              >
                Sign In
              </Link>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8 max-w-4xl w-full">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center mb-3">
              <svg className="h-8 w-8 text-blue-600 mr-3" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75A1.125 1.125 0 002.25 18.375m0-12.75C2.25 4.629 2.871 4 3.375 4h1.875c.621 0 1.125.504 1.125 1.125L5.25 5.625m-1.125 0H20.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125" />
              </svg>
              <h3 className="font-semibold text-lg text-gray-900">Excel Generation</h3>
            </div>
            <p className="text-gray-800 text-sm">
              Generate sophisticated Excel spreadsheets with Gantt charts and probabilistic timelines without macros.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center mb-3">
              <svg className="h-8 w-8 text-green-600 mr-3" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h3.26m-4.01 0a9 9 0 019.712 0m0 0A8.982 8.982 0 0113.5 15" />
              </svg>
              <h3 className="font-semibold text-lg text-gray-900">Project Management</h3>
            </div>
            <p className="text-gray-800 text-sm">
              Plan, track, and manage your projects with advanced scheduling algorithms and dependency solving.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center mb-3">
              <svg className="h-8 w-8 text-purple-600 mr-3" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
              </svg>
              <h3 className="font-semibold text-lg text-gray-900">Open Source</h3>
            </div>
            <p className="text-gray-800 text-sm">
              Built with modern technologies and available as an open-source solution for teams of all sizes.
            </p>
          </div>
        </div>
      </main>
      
      <footer className="row-start-3 flex gap-6 flex-wrap items-center justify-center text-sm text-gray-800">
        <span>© 2025 SprintForge</span>
        <span>•</span>
        <a href="#" className="hover:underline">Privacy</a>
        <span>•</span>
        <a href="#" className="hover:underline">Terms</a>
        <span>•</span>
        <a href="https://github.com/your-repo/sprintforge" className="hover:underline">GitHub</a>
      </footer>
    </div>
  )
}