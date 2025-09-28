import React from 'react'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  color?: 'primary' | 'secondary' | 'white' | 'gray'
  className?: string
  'aria-label'?: string
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
  xl: 'h-12 w-12'
}

const colorClasses = {
  primary: 'border-blue-600',
  secondary: 'border-gray-600',
  white: 'border-white',
  gray: 'border-gray-900'
}

export function LoadingSpinner({
  size = 'md',
  color = 'primary',
  className = '',
  'aria-label': ariaLabel = 'Loading'
}: LoadingSpinnerProps) {
  return (
    <div
      className={`animate-spin rounded-full border-2 border-t-transparent ${sizeClasses[size]} ${colorClasses[color]} ${className}`}
      role="status"
      aria-label={ariaLabel}
    >
      <span className="sr-only">{ariaLabel}</span>
    </div>
  )
}

interface LoadingOverlayProps {
  message?: string
  showSpinner?: boolean
  className?: string
}

export function LoadingOverlay({
  message = 'Loading...',
  showSpinner = true,
  className = ''
}: LoadingOverlayProps) {
  return (
    <div className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 ${className}`}>
      <div className="bg-white rounded-lg p-6 max-w-sm mx-4 flex flex-col items-center">
        {showSpinner && (
          <LoadingSpinner size="lg" className="mb-4" aria-label={message} />
        )}
        <p className="text-gray-700 text-center">{message}</p>
      </div>
    </div>
  )
}

interface PageLoadingProps {
  message?: string
  className?: string
}

export function PageLoading({
  message = 'Loading...',
  className = ''
}: PageLoadingProps) {
  return (
    <div className={`min-h-screen flex items-center justify-center bg-gray-50 ${className}`}>
      <div className="text-center">
        <LoadingSpinner size="xl" className="mx-auto mb-4" aria-label={message} />
        <p className="text-gray-600 text-lg">{message}</p>
      </div>
    </div>
  )
}