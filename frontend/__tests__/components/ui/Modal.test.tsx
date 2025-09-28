import { render, screen, fireEvent } from '@testing-library/react'
import { Modal, ConfirmationModal } from '../../../components/ui/Modal'

// Mock createPortal
jest.mock('react-dom', () => ({
  ...jest.requireActual('react-dom'),
  createPortal: (node: React.ReactNode) => node,
}))

describe('Modal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    children: <div>Modal content</div>,
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders when open', () => {
    render(<Modal {...defaultProps} />)
    expect(screen.getByText('Modal content')).toBeInTheDocument()
  })

  it('does not render when closed', () => {
    render(<Modal {...defaultProps} isOpen={false} />)
    expect(screen.queryByText('Modal content')).not.toBeInTheDocument()
  })

  it('renders with title', () => {
    render(<Modal {...defaultProps} title="Test Modal" />)
    expect(screen.getByText('Test Modal')).toBeInTheDocument()
  })

  it('renders close button by default', () => {
    render(<Modal {...defaultProps} title="Test" />)
    expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument()
  })

  it('hides close button when showCloseButton is false', () => {
    render(<Modal {...defaultProps} title="Test" showCloseButton={false} />)
    expect(screen.queryByRole('button', { name: 'Close' })).not.toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const onClose = jest.fn()
    render(<Modal {...defaultProps} onClose={onClose} title="Test" />)
    
    fireEvent.click(screen.getByRole('button', { name: 'Close' }))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when backdrop is clicked', () => {
    const onClose = jest.fn()
    render(<Modal {...defaultProps} onClose={onClose} />)
    
    const backdrop = document.querySelector('.fixed.inset-0.bg-gray-500')
    expect(backdrop).toBeInTheDocument()
    fireEvent.click(backdrop!)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('does not call onClose when backdrop is clicked and closeOnBackdropClick is false', () => {
    const onClose = jest.fn()
    render(<Modal {...defaultProps} onClose={onClose} closeOnBackdropClick={false} />)
    
    const backdrop = document.querySelector('.fixed.inset-0.bg-gray-500')
    fireEvent.click(backdrop!)
    expect(onClose).not.toHaveBeenCalled()
  })

  it('applies different sizes', () => {
    const { rerender } = render(<Modal {...defaultProps} size="sm" />)
    expect(document.querySelector('.max-w-sm')).toBeInTheDocument()

    rerender(<Modal {...defaultProps} size="md" />)
    expect(document.querySelector('.max-w-md')).toBeInTheDocument()

    rerender(<Modal {...defaultProps} size="lg" />)
    expect(document.querySelector('.max-w-lg')).toBeInTheDocument()

    rerender(<Modal {...defaultProps} size="xl" />)
    expect(document.querySelector('.max-w-xl')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<Modal {...defaultProps} className="custom-modal" />)
    expect(document.querySelector('.custom-modal')).toBeInTheDocument()
  })

  it('handles escape key press', () => {
    const onClose = jest.fn()
    render(<Modal {...defaultProps} onClose={onClose} />)
    
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})

describe('ConfirmationModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    onConfirm: jest.fn(),
    title: 'Confirm Action',
    message: 'Are you sure you want to proceed?',
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders with title and message', () => {
    render(<ConfirmationModal {...defaultProps} />)
    
    expect(screen.getByText('Confirm Action')).toBeInTheDocument()
    expect(screen.getByText('Are you sure you want to proceed?')).toBeInTheDocument()
  })

  it('renders default button texts', () => {
    render(<ConfirmationModal {...defaultProps} />)
    
    expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
  })

  it('renders custom button texts', () => {
    render(
      <ConfirmationModal
        {...defaultProps}
        confirmText="Delete"
        cancelText="Keep"
      />
    )
    
    expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Keep' })).toBeInTheDocument()
  })

  it('calls onConfirm when confirm button is clicked', () => {
    const onConfirm = jest.fn()
    render(<ConfirmationModal {...defaultProps} onConfirm={onConfirm} />)
    
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }))
    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when cancel button is clicked', () => {
    const onClose = jest.fn()
    render(<ConfirmationModal {...defaultProps} onClose={onClose} />)
    
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('shows loading state', () => {
    render(<ConfirmationModal {...defaultProps} loading />)
    
    expect(screen.getByText('Processing...')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Processing...' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled()
  })

  it('renders different types with appropriate styling', () => {
    const { rerender } = render(<ConfirmationModal {...defaultProps} type="danger" />)
    expect(document.querySelector('.bg-red-100')).toBeInTheDocument()
    expect(document.querySelector('.bg-red-600')).toBeInTheDocument()

    rerender(<ConfirmationModal {...defaultProps} type="warning" />)
    expect(document.querySelector('.bg-yellow-100')).toBeInTheDocument()
    expect(document.querySelector('.bg-yellow-600')).toBeInTheDocument()

    rerender(<ConfirmationModal {...defaultProps} type="info" />)
    expect(document.querySelector('.bg-blue-100')).toBeInTheDocument()
    expect(document.querySelector('.bg-blue-600')).toBeInTheDocument()
  })

  it('does not render close button', () => {
    render(<ConfirmationModal {...defaultProps} />)
    expect(screen.queryByRole('button', { name: 'Close' })).not.toBeInTheDocument()
  })
})