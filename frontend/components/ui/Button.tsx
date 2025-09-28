import React from 'react'
import { LoadingSpinner } from './LoadingSpinner'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  loadingText?: string
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right'
  fullWidth?: boolean
}

const variants = {
  primary: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500 text-white border-transparent',
  secondary: 'bg-gray-600 hover:bg-gray-700 focus:ring-gray-500 text-white border-transparent',
  danger: 'bg-red-600 hover:bg-red-700 focus:ring-red-500 text-white border-transparent',
  ghost: 'bg-transparent hover:bg-gray-50 focus:ring-gray-500 text-gray-700 border-gray-300'
}

const sizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base'
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  loadingText,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  className = '',
  children,
  disabled,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading

  const baseClasses = 'inline-flex items-center justify-center border font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-200'
  const variantClasses = variants[variant]
  const sizeClasses = sizes[size]
  const widthClasses = fullWidth ? 'w-full' : ''
  const disabledClasses = isDisabled ? 'opacity-50 cursor-not-allowed' : ''

  const buttonContent = loading ? (
    <>
      <LoadingSpinner size="sm" color="white" className="mr-2" />
      {loadingText || children}
    </>
  ) : (
    <>
      {icon && iconPosition === 'left' && (
        <span className="mr-2 flex-shrink-0">{icon}</span>
      )}
      {children}
      {icon && iconPosition === 'right' && (
        <span className="ml-2 flex-shrink-0">{icon}</span>
      )}
    </>
  )

  return (
    <button
      className={`${baseClasses} ${variantClasses} ${sizeClasses} ${widthClasses} ${disabledClasses} ${className}`}
      disabled={isDisabled}
      {...props}
    >
      {buttonContent}
    </button>
  )
}