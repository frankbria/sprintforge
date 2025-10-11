/**
 * Tests for ProjectWizard component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ProjectWizard } from '@/components/wizard/ProjectWizard';

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe('ProjectWizard', () => {
  const mockOnComplete = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders wizard with first step', () => {
    render(<ProjectWizard onComplete={mockOnComplete} />);

    expect(screen.getByText('Create New Project')).toBeInTheDocument();
    expect(screen.getByText('Project Basics')).toBeInTheDocument();
    expect(screen.getByLabelText(/project name/i)).toBeInTheDocument();
  });

  it('shows all wizard steps in progress indicator', () => {
    render(<ProjectWizard onComplete={mockOnComplete} />);

    expect(screen.getByText('Project Basics')).toBeInTheDocument();
    expect(screen.getByText('Template Selection')).toBeInTheDocument();
    expect(screen.getByText('Sprint Configuration')).toBeInTheDocument();
    expect(screen.getByText('Holiday Calendar')).toBeInTheDocument();
    expect(screen.getByText('Feature Selection')).toBeInTheDocument();
  });

  it('validates required fields before advancing', async () => {
    render(<ProjectWizard onComplete={mockOnComplete} />);

    const nextButton = screen.getByRole('button', { name: /next/i });
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(/project name is required/i)).toBeInTheDocument();
    });
  });

  it('allows navigation to next step when form is valid', async () => {
    render(<ProjectWizard onComplete={mockOnComplete} />);

    const nameInput = screen.getByLabelText(/project name/i);
    fireEvent.change(nameInput, { target: { value: 'Test Project' } });

    const nextButton = screen.getByRole('button', { name: /next/i });
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText('Template Selection')).toBeInTheDocument();
    });
  });

  it('calls onCancel when cancel button is clicked', () => {
    render(
      <ProjectWizard onComplete={mockOnComplete} onCancel={mockOnCancel} />
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('disables back button on first step', () => {
    render(<ProjectWizard onComplete={mockOnComplete} />);

    const backButton = screen.getByRole('button', { name: /back/i });
    expect(backButton).toBeDisabled();
  });

  it('shows progress indicator correctly', () => {
    render(<ProjectWizard onComplete={mockOnComplete} />);

    expect(screen.getByText('Step 1 of 6')).toBeInTheDocument();
  });
});
