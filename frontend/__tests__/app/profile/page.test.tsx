import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Profile from '../../../app/profile/page'
import { useAuth } from '../../../hooks/useAuth'

// Mock the useAuth hook
jest.mock('../../../hooks/useAuth')
const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>

const mockUser = {
  id: '123',
  name: 'John Doe',
  email: 'john@example.com',
  image: 'https://example.com/avatar.jpg',
}

const defaultAuthState = {
  user: mockUser,
  isLoading: false,
  isAuthenticated: true,
  provider: 'google',
  logout: jest.fn(),
  login: jest.fn(),
  requireAuth: jest.fn(),
}

describe('Profile Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue(defaultAuthState)
  })

  it('shows loading state when auth is loading', () => {
    mockUseAuth.mockReturnValue({
      ...defaultAuthState,
      isLoading: true,
      isAuthenticated: false,
    })

    render(<Profile />)
    expect(screen.getAllByText('Loading your profile...')[0]).toBeInTheDocument()
  })

  it('redirects when not authenticated', () => {
    const requireAuth = jest.fn()
    mockUseAuth.mockReturnValue({
      ...defaultAuthState,
      isAuthenticated: false,
      isLoading: false,
      requireAuth,
    })

    render(<Profile />)
    expect(requireAuth).toHaveBeenCalled()
  })

  it('renders profile information when authenticated', () => {
    render(<Profile />)

    expect(screen.getByText('Profile')).toBeInTheDocument()
    expect(screen.getByText('Manage your account information and preferences')).toBeInTheDocument()
    expect(screen.getAllByText('John Doe')[0]).toBeInTheDocument()
    expect(screen.getByText('john@example.com')).toBeInTheDocument()
    expect(screen.getByText('Connected via Google')).toBeInTheDocument()
  })

  it('renders edit profile button', () => {
    render(<Profile />)

    const editButton = screen.getByRole('button', { name: 'Edit Profile' })
    expect(editButton).toBeInTheDocument()
  })

  it('enters edit mode when edit button is clicked', () => {
    render(<Profile />)

    const editButton = screen.getByRole('button', { name: 'Edit Profile' })
    fireEvent.click(editButton)

    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Save Changes' })).toBeInTheDocument()
    expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument()
    expect(screen.getByDisplayValue('john@example.com')).toBeInTheDocument()
  })

  it('cancels edit mode and resets form', () => {
    render(<Profile />)

    // Enter edit mode
    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }))

    // Change some values
    const nameInput = screen.getByDisplayValue('John Doe')
    fireEvent.change(nameInput, { target: { value: 'Jane Doe' } })

    // Cancel
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(screen.getByRole('button', { name: 'Edit Profile' })).toBeInTheDocument()
    expect(screen.queryByDisplayValue('Jane Doe')).not.toBeInTheDocument()
  })

  it('validates form fields', async () => {
    render(<Profile />)

    // Enter edit mode
    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }))

    // Clear required fields
    const nameInput = screen.getByDisplayValue('John Doe')
    const emailInput = screen.getByDisplayValue('john@example.com')

    fireEvent.change(nameInput, { target: { value: '' } })
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })

    // Try to save
    const saveButton = screen.getByRole('button', { name: 'Save Changes' })
    expect(saveButton).toBeDisabled()

    await waitFor(() => {
      expect(screen.getByText('Display name is required')).toBeInTheDocument()
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument()
    })
  })

  it('saves profile changes', async () => {
    render(<Profile />)

    // Enter edit mode
    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }))

    // Change name
    const nameInput = screen.getByDisplayValue('John Doe')
    fireEvent.change(nameInput, { target: { value: 'Jane Smith' } })

    // Save changes
    const saveButton = screen.getByRole('button', { name: 'Save Changes' })
    fireEvent.click(saveButton)

    expect(screen.getByText('Saving...')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Edit Profile' })).toBeInTheDocument()
    }, { timeout: 2000 })
  })

  it('handles save error', async () => {
    // Mock a failed save by causing an error
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

    render(<Profile />)

    // Enter edit mode
    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }))

    // Change name to trigger an error condition (simulate network failure)
    const nameInput = screen.getByDisplayValue('John Doe')
    fireEvent.change(nameInput, { target: { value: 'Error User' } })

    // Save changes
    const saveButton = screen.getByRole('button', { name: 'Save Changes' })
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText('Failed to save profile. Please try again.')).toBeInTheDocument()
    }, { timeout: 2000 })

    consoleSpy.mockRestore()
  })

  it('toggles preferences in edit mode', () => {
    render(<Profile />)

    // Enter edit mode
    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }))

    const emailToggle = screen.getAllByRole('button').find(btn => 
      btn.parentElement?.textContent?.includes('Email notifications')
    )
    const projectToggle = screen.getAllByRole('button').find(btn => 
      btn.parentElement?.textContent?.includes('Project reminders')
    )

    expect(emailToggle).toBeInTheDocument()
    expect(projectToggle).toBeInTheDocument()

    // Toggles should be enabled in edit mode
    expect(emailToggle).not.toHaveClass('cursor-not-allowed')
    expect(projectToggle).not.toHaveClass('cursor-not-allowed')
  })

  it('disables preference toggles when not in edit mode', () => {
    render(<Profile />)

    const emailToggle = screen.getAllByRole('button').find(btn => 
      btn.parentElement?.textContent?.includes('Email notifications')
    )

    expect(emailToggle).toHaveClass('cursor-not-allowed')
  })

  it('shows delete account confirmation modal', () => {
    render(<Profile />)

    const deleteButton = screen.getByRole('button', { name: 'Delete Account' })
    fireEvent.click(deleteButton)

    expect(screen.getByText('Delete Account')).toBeInTheDocument()
    expect(screen.getByText('Are you absolutely sure you want to delete your account?')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Yes, Delete My Account' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
  })

  it('cancels account deletion', () => {
    render(<Profile />)

    // Open confirmation modal
    fireEvent.click(screen.getByRole('button', { name: 'Delete Account' }))

    // Cancel deletion
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(screen.queryByText('Are you absolutely sure you want to delete your account?')).not.toBeInTheDocument()
  })

  it('handles account deletion', async () => {
    const logout = jest.fn()
    mockUseAuth.mockReturnValue({
      ...defaultAuthState,
      logout,
    })

    render(<Profile />)

    // Open confirmation modal
    fireEvent.click(screen.getByRole('button', { name: 'Delete Account' }))

    // Confirm deletion
    fireEvent.click(screen.getByRole('button', { name: 'Yes, Delete My Account' }))

    await waitFor(() => {
      expect(logout).toHaveBeenCalledWith('/')
    }, { timeout: 3000 })
  })

  it('handles logout', () => {
    const logout = jest.fn()
    mockUseAuth.mockReturnValue({
      ...defaultAuthState,
      logout,
    })

    render(<Profile />)

    const logoutButton = screen.getByRole('button', { name: 'Sign Out' })
    fireEvent.click(logoutButton)

    expect(logout).toHaveBeenCalledWith('/')
  })

  it('renders navigation links', () => {
    render(<Profile />)

    expect(screen.getByRole('link', { name: 'SprintForge' })).toHaveAttribute('href', '/')
    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('href', '/dashboard')
  })

  it('renders user avatar or default icon', () => {
    render(<Profile />)

    const avatar = screen.getByAltText('Profile')
    expect(avatar).toBeInTheDocument()
    expect(avatar).toHaveAttribute('src', mockUser.image)
  })

  it('renders default avatar when no image provided', () => {
    mockUseAuth.mockReturnValue({
      ...defaultAuthState,
      user: { ...mockUser, image: null },
    })

    render(<Profile />)

    // Should render default avatar div instead of img
    const avatarContainer = document.querySelector('.h-20.w-20.rounded-full.bg-gradient-to-br')
    expect(avatarContainer).toBeInTheDocument()
  })

  it('renders account information correctly', () => {
    render(<Profile />)

    expect(screen.getByText('Account Information')).toBeInTheDocument()
    expect(screen.getByText('User ID')).toBeInTheDocument()
    expect(screen.getByText('123')).toBeInTheDocument()
    expect(screen.getByText('Email Address')).toBeInTheDocument()
    expect(screen.getByText('Display Name')).toBeInTheDocument()
  })

  it('renders preferences section', () => {
    render(<Profile />)

    expect(screen.getByText('Preferences')).toBeInTheDocument()
    expect(screen.getByText('Email notifications')).toBeInTheDocument()
    expect(screen.getByText('Receive email updates about your projects')).toBeInTheDocument()
    expect(screen.getByText('Project reminders')).toBeInTheDocument()
    expect(screen.getByText('Get reminded about upcoming deadlines')).toBeInTheDocument()
  })

  it('renders danger zone with proper warnings', () => {
    render(<Profile />)

    expect(screen.getByText('Danger Zone')).toBeInTheDocument()
    expect(screen.getByText('Once you delete your account, there is no going back. This action will:')).toBeInTheDocument()
    expect(screen.getByText('Permanently delete all your projects and data')).toBeInTheDocument()
    expect(screen.getByText('Remove your account from all shared projects')).toBeInTheDocument()
    expect(screen.getByText('Cancel any active subscriptions')).toBeInTheDocument()
    expect(screen.getByText('Cannot be undone or recovered')).toBeInTheDocument()
  })
})