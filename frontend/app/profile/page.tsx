"use client"

import { useAuth } from "../../hooks/useAuth"
import Link from "next/link"
import Image from "next/image"
import { useState, useCallback } from "react"
import { Button } from "../../components/ui/Button"
import { ErrorMessage, InlineError } from "../../components/ui/ErrorMessage"
import { ConfirmationModal } from "../../components/ui/Modal"
import { PageLoading } from "../../components/ui/LoadingSpinner"

function ProfileContent() {
  const { user, logout, provider } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({
    name: user?.name || '',
    email: user?.email || '',
    emailNotifications: true,
    projectReminders: true
  })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})

  const handleLogout = async () => {
    try {
      await logout("/")
    } catch (error) {
      console.error("Logout failed:", error)
    }
  }

  const handleEditToggle = useCallback(() => {
    if (isEditing) {
      // Reset form when canceling edit
      setEditForm({
        name: user?.name || '',
        email: user?.email || '',
        emailNotifications: true,
        projectReminders: true
      })
      setFormErrors({})
      setSaveError(null)
    }
    setIsEditing(!isEditing)
  }, [isEditing, user])

  const validateForm = useCallback(() => {
    const errors: Record<string, string> = {}

    if (!editForm.name.trim()) {
      errors.name = 'Display name is required'
    } else if (editForm.name.length > 100) {
      errors.name = 'Display name must be 100 characters or less'
    }

    if (!editForm.email.trim()) {
      errors.email = 'Email address is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(editForm.email)) {
      errors.email = 'Please enter a valid email address'
    }

    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }, [editForm])

  const handleSave = useCallback(async () => {
    if (!validateForm()) {
      return
    }

    setIsSaving(true)
    setSaveError(null)

    try {
      // Simulate API call to save profile
      await new Promise(resolve => setTimeout(resolve, 1500))

      // In a real app, this would update the user session/context
      console.log('Profile saved:', editForm)

      setIsEditing(false)
    } catch (error) {
      console.error('Save failed:', error)
      setSaveError('Failed to save profile. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }, [editForm, validateForm])

  const handleDeleteAccount = useCallback(async () => {
    setIsDeleting(true)

    try {
      // Simulate API call to delete account
      await new Promise(resolve => setTimeout(resolve, 2000))

      // In a real app, this would call an API to delete the account
      console.log('Account deletion requested')

      // Logout after deletion
      await logout('/')
    } catch (error) {
      console.error('Account deletion failed:', error)
      setIsDeleting(false)
      setShowDeleteConfirm(false)
    }
  }, [logout])

  const handleInputChange = useCallback((field: string, value: string | boolean) => {
    setEditForm(prev => ({ ...prev, [field]: value }))
    // Clear field error when user starts typing
    if (formErrors[field]) {
      setFormErrors(prev => ({ ...prev, [field]: '' }))
    }
  }, [formErrors])

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="text-xl font-bold text-gray-900">
                SprintForge
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/dashboard"
                className="text-sm text-gray-800 hover:text-gray-900"
              >
                Dashboard
              </Link>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-800 hover:text-gray-900 bg-transparent border border-gray-300 hover:border-gray-400 px-3 py-1 rounded-md transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
            <p className="mt-2 text-gray-800">
              Manage your account information and preferences
            </p>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-5">
                  <div className="flex-shrink-0">
                    {user?.image ? (
                      <Image
                        className="h-20 w-20 rounded-full object-cover"
                        src={user.image}
                        alt="Profile"
                        width={80}
                        height={80}
                      />
                    ) : (
                      <div className="h-20 w-20 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center">
                        <svg className="h-10 w-10 text-white" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M24 20.993V24H0v-2.996A14.977 14.977 0 0112.004 15c4.904 0 9.26 2.354 11.996 5.993zM16.002 8.999a4 4 0 11-8 0 4 4 0 018 0z" />
                        </svg>
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      {user?.name || "No name provided"}
                    </h3>
                    <p className="text-sm text-gray-700">
                      {user?.email}
                    </p>
                    {provider && (
                      <div className="flex items-center mt-1">
                        <div className="h-2 w-2 bg-green-400 rounded-full mr-2"></div>
                        <p className="text-sm text-gray-700">
                          Connected via {provider.charAt(0).toUpperCase() + provider.slice(1)}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex-shrink-0">
                  <Button
                    onClick={handleEditToggle}
                    variant={isEditing ? "ghost" : "primary"}
                    size="sm"
                    disabled={isSaving}
                  >
                    {isEditing ? 'Cancel' : 'Edit Profile'}
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Save Error Message */}
          {saveError && (
            <div className="mt-6">
              <ErrorMessage
                message={saveError}
                onClose={() => setSaveError(null)}
                actionButton={{
                  text: "Retry",
                  onClick: handleSave
                }}
              />
            </div>
          )}

          <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Account Information
                  </h3>
                  {isEditing && (
                    <Button
                      onClick={handleSave}
                      loading={isSaving}
                      loadingText="Saving..."
                      size="sm"
                      disabled={Object.keys(formErrors).length > 0}
                    >
                      Save Changes
                    </Button>
                  )}
                </div>

                {isEditing ? (
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                        Display Name
                      </label>
                      <input
                        type="text"
                        id="name"
                        value={editForm.name}
                        onChange={(e) => handleInputChange('name', e.target.value)}
                        className={`block w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors ${
                          formErrors.name ? 'border-red-300 bg-red-50' : 'border-gray-300'
                        }`}
                        placeholder="Enter your display name"
                        maxLength={100}
                      />
                      {formErrors.name && <InlineError message={formErrors.name} />}
                    </div>

                    <div>
                      <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                        Email Address
                      </label>
                      <input
                        type="email"
                        id="email"
                        value={editForm.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        className={`block w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors ${
                          formErrors.email ? 'border-red-300 bg-red-50' : 'border-gray-300'
                        }`}
                        placeholder="Enter your email address"
                      />
                      {formErrors.email && <InlineError message={formErrors.email} />}
                    </div>

                    <div className="pt-2">
                      <dt className="text-sm font-medium text-gray-700">User ID</dt>
                      <dd className="text-sm text-gray-900 font-mono mt-1 p-2 bg-gray-50 rounded border">{user?.id}</dd>
                      <p className="text-xs text-gray-700 mt-1">This cannot be changed</p>
                    </div>
                  </div>
                ) : (
                  <dl className="space-y-3">
                    <div>
                      <dt className="text-sm font-medium text-gray-700">User ID</dt>
                      <dd className="text-sm text-gray-900 font-mono">{user?.id}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-700">Email Address</dt>
                      <dd className="text-sm text-gray-900">{user?.email}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-700">Display Name</dt>
                      <dd className="text-sm text-gray-900">{user?.name || "Not set"}</dd>
                    </div>
                  </dl>
                )}
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Preferences
                </h3>
                <div className="mt-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Email notifications</span>
                      <p className="text-xs text-gray-700">Receive email updates about your projects</p>
                    </div>
                    <button
                      onClick={() => isEditing && handleInputChange('emailNotifications', !editForm.emailNotifications)}
                      disabled={!isEditing}
                      className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                        editForm.emailNotifications ? 'bg-blue-600' : 'bg-gray-200'
                      } ${!isEditing ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                          editForm.emailNotifications ? 'translate-x-5' : 'translate-x-0'
                        }`}
                      ></span>
                    </button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Project reminders</span>
                      <p className="text-xs text-gray-700">Get reminded about upcoming deadlines</p>
                    </div>
                    <button
                      onClick={() => isEditing && handleInputChange('projectReminders', !editForm.projectReminders)}
                      disabled={!isEditing}
                      className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                        editForm.projectReminders ? 'bg-blue-600' : 'bg-gray-200'
                      } ${!isEditing ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <span
                        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                          editForm.projectReminders ? 'translate-x-5' : 'translate-x-0'
                        }`}
                      ></span>
                    </button>
                  </div>
                  {isEditing && (
                    <div className="pt-4 border-t border-gray-100">
                      <p className="text-xs text-gray-700">
                        Toggle switches to change your notification preferences
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                  </svg>
                </div>
                <div className="ml-3 flex-1">
                  <h3 className="text-lg leading-6 font-medium text-red-800 mb-2">
                    Danger Zone
                  </h3>
                  <div className="space-y-3">
                    <p className="text-sm text-red-700">
                      Once you delete your account, there is no going back. This action will:
                    </p>
                    <ul className="text-sm text-red-700 list-disc list-inside space-y-1 ml-4">
                      <li>Permanently delete all your projects and data</li>
                      <li>Remove your account from all shared projects</li>
                      <li>Cancel any active subscriptions</li>
                      <li>Cannot be undone or recovered</li>
                    </ul>
                    <div className="pt-2">
                      <Button
                        onClick={() => setShowDeleteConfirm(true)}
                        variant="danger"
                        size="sm"
                        disabled={isEditing || isSaving}
                      >
                        Delete Account
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Account Deletion Confirmation Modal */}
          <ConfirmationModal
            isOpen={showDeleteConfirm}
            onClose={() => setShowDeleteConfirm(false)}
            onConfirm={handleDeleteAccount}
            title="Delete Account"
            message="Are you absolutely sure you want to delete your account? This action cannot be undone and will permanently delete all your data, projects, and account information."
            confirmText="Yes, Delete My Account"
            cancelText="Cancel"
            type="danger"
            loading={isDeleting}
          />
        </div>
      </main>
    </div>
  )
}

export default function Profile() {
  const { isLoading, isAuthenticated, requireAuth } = useAuth()

  // Handle authentication check
  if (isLoading) {
    return <PageLoading message="Loading your profile..." />
  }

  if (!isAuthenticated) {
    requireAuth()
    return null
  }

  return <ProfileContent />
}