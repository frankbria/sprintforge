import { render, screen } from '@testing-library/react'
import { LoadingSpinner, PageLoading } from '../../../components/ui/LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders with default props', () => {
    render(<LoadingSpinner />)
    
    const spinner = screen.getByRole('status')
    expect(spinner).toBeInTheDocument()
    expect(spinner).toHaveAttribute('aria-label', 'Loading')
    expect(spinner).toHaveClass('animate-spin', 'rounded-full', 'border-2', 'border-t-transparent')
  })

  it('renders with different sizes', () => {
    const { rerender } = render(<LoadingSpinner size="sm" />)
    expect(screen.getByRole('status')).toHaveClass('h-4', 'w-4')

    rerender(<LoadingSpinner size="md" />)
    expect(screen.getByRole('status')).toHaveClass('h-6', 'w-6')

    rerender(<LoadingSpinner size="lg" />)
    expect(screen.getByRole('status')).toHaveClass('h-8', 'w-8')

    rerender(<LoadingSpinner size="xl" />)
    expect(screen.getByRole('status')).toHaveClass('h-12', 'w-12')
  })

  it('renders with different colors', () => {
    const { rerender } = render(<LoadingSpinner color="primary" />)
    expect(screen.getByRole('status')).toHaveClass('border-blue-600')

    rerender(<LoadingSpinner color="secondary" />)
    expect(screen.getByRole('status')).toHaveClass('border-gray-600')

    rerender(<LoadingSpinner color="white" />)
    expect(screen.getByRole('status')).toHaveClass('border-white')
  })

  it('accepts custom aria-label', () => {
    render(<LoadingSpinner aria-label="Loading profile data" />)
    
    const spinner = screen.getByRole('status')
    expect(spinner).toHaveAttribute('aria-label', 'Loading profile data')
    expect(screen.getByText('Loading profile data')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<LoadingSpinner className="custom-class" />)
    expect(screen.getByRole('status')).toHaveClass('custom-class')
  })
})

describe('PageLoading', () => {
  it('renders with default message', () => {
    render(<PageLoading />)
    
    expect(screen.getByText('Loading...')).toBeInTheDocument()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders with custom message', () => {
    render(<PageLoading message="Loading your profile..." />)
    expect(screen.getByText('Loading your profile...')).toBeInTheDocument()
  })

  it('has proper loading page structure', () => {
    render(<PageLoading message="Test loading" />)
    
    const container = screen.getByText('Test loading').closest('div')
    expect(container).toHaveClass('min-h-screen', 'flex', 'items-center', 'justify-center')
    
    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('h-12', 'w-12')
  })

  it('applies custom className', () => {
    render(<PageLoading className="custom-page-loading" />)
    const containers = screen.getAllByText('Loading...')
    const container = containers[1].closest('div') // Get the outer container
    expect(container).toHaveClass('custom-page-loading')
  })
})