import { render, screen, fireEvent } from '@testing-library/react'
import { ErrorMessage, InlineError } from '../../../components/ui/ErrorMessage'

describe('ErrorMessage', () => {
  it('renders with default props', () => {
    render(<ErrorMessage message="Something went wrong" />)
    
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    const errorContainer = screen.getByText('Something went wrong').closest('div')
    expect(errorContainer).toHaveClass('bg-red-50', 'border-red-200', 'text-red-800')
  })

  it('renders with title', () => {
    render(<ErrorMessage title="Error" message="Something went wrong" />)
    
    expect(screen.getByText('Error')).toBeInTheDocument()
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('renders different types', () => {
    const { rerender } = render(<ErrorMessage message="Error" type="error" />)
    let container = screen.getByText('Error').closest('div')
    expect(container).toHaveClass('bg-red-50', 'text-red-800')

    rerender(<ErrorMessage message="Warning" type="warning" />)
    container = screen.getByText('Warning').closest('div')
    expect(container).toHaveClass('bg-yellow-50', 'text-yellow-800')

    rerender(<ErrorMessage message="Info" type="info" />)
    container = screen.getByText('Info').closest('div')
    expect(container).toHaveClass('bg-blue-50', 'text-blue-800')
  })

  it('shows icon by default', () => {
    render(<ErrorMessage message="Error" type="error" />)
    const container = screen.getByText('Error').closest('div')
    expect(container).toContainHTML('svg')
  })

  it('hides icon when showIcon is false', () => {
    render(<ErrorMessage message="Error" showIcon={false} />)
    const container = screen.getByText('Error').closest('div')
    expect(container).not.toContainHTML('svg')
  })

  it('renders action button', () => {
    const handleAction = jest.fn()
    render(
      <ErrorMessage
        message="Error"
        actionButton={{ text: 'Retry', onClick: handleAction }}
      />
    )
    
    const button = screen.getByRole('button', { name: 'Retry' })
    expect(button).toBeInTheDocument()
    
    fireEvent.click(button)
    expect(handleAction).toHaveBeenCalledTimes(1)
  })

  it('renders close button and handles close', () => {
    const handleClose = jest.fn()
    render(<ErrorMessage message="Error" onClose={handleClose} />)
    
    const closeButton = screen.getByRole('button', { name: 'Dismiss' })
    expect(closeButton).toBeInTheDocument()
    
    fireEvent.click(closeButton)
    expect(handleClose).toHaveBeenCalledTimes(1)
  })

  it('applies custom className', () => {
    render(<ErrorMessage message="Error" className="custom-error" />)
    const container = screen.getByText('Error').closest('div')
    expect(container).toHaveClass('custom-error')
  })

  it('has proper accessibility attributes', () => {
    render(<ErrorMessage message="Error message" />)
    const container = screen.getByText('Error message').closest('div')
    expect(container).toBeInTheDocument()
    expect(container).toHaveClass('rounded-md', 'border', 'p-4')
  })
})

describe('InlineError', () => {
  it('renders error message', () => {
    render(<InlineError message="Field is required" />)
    
    const error = screen.getByText('Field is required')
    expect(error).toBeInTheDocument()
    expect(error).toHaveClass('text-sm', 'text-red-600', 'mt-1')
  })

  it('applies custom className', () => {
    render(<InlineError message="Error" className="custom-inline" />)
    expect(screen.getByText('Error')).toHaveClass('custom-inline')
  })

  it('renders with proper styling', () => {
    render(<InlineError message="Validation error" />)
    const error = screen.getByText('Validation error')
    expect(error.tagName).toBe('P')
    expect(error).toHaveClass('text-sm', 'text-red-600', 'mt-1')
  })
})