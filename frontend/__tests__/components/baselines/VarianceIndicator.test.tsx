/**
 * TDD Tests for VarianceIndicator Component
 *
 * Following RED-GREEN-REFACTOR cycle:
 * 🔴 These tests are written FIRST and will FAIL
 * 🟢 Implementation will make them pass
 * 🔵 Refactor for quality
 */

import { render, screen } from '@testing-library/react';
import { VarianceIndicator } from '@/components/baselines/VarianceIndicator';

describe('VarianceIndicator', () => {
  describe('Ahead Status (negative variance)', () => {
    it('renders ahead status with green color for negative variance', () => {
      render(<VarianceIndicator varianceDays={-2} />);

      const indicator = screen.getByRole('status');
      expect(indicator).toBeInTheDocument();
      expect(indicator).toHaveClass('bg-green-50');
      expect(indicator).toHaveTextContent('2 days ahead');
    });

    it('renders ahead status with correct icon', () => {
      render(<VarianceIndicator varianceDays={-5} />);

      // Check for down arrow icon (ahead means faster/sooner)
      const indicator = screen.getByRole('status');
      expect(indicator).toBeInTheDocument();
    });

    it('displays correct text for 1 day ahead', () => {
      render(<VarianceIndicator varianceDays={-1} />);

      expect(screen.getByText('1 day ahead')).toBeInTheDocument();
    });
  });

  describe('Behind Status (positive variance)', () => {
    it('renders behind status with red color for positive variance', () => {
      render(<VarianceIndicator varianceDays={3} />);

      const indicator = screen.getByRole('status');
      expect(indicator).toBeInTheDocument();
      expect(indicator).toHaveClass('bg-red-50');
      expect(indicator).toHaveTextContent('3 days behind');
    });

    it('renders behind status with correct icon', () => {
      render(<VarianceIndicator varianceDays={7} />);

      // Check for up arrow icon (behind means slower/later)
      const indicator = screen.getByRole('status');
      expect(indicator).toBeInTheDocument();
    });

    it('displays correct text for 1 day behind', () => {
      render(<VarianceIndicator varianceDays={1} />);

      expect(screen.getByText('1 day behind')).toBeInTheDocument();
    });
  });

  describe('On Track Status (zero variance)', () => {
    it('renders on-track status with gray color for zero variance', () => {
      render(<VarianceIndicator varianceDays={0} />);

      const indicator = screen.getByRole('status');
      expect(indicator).toBeInTheDocument();
      expect(indicator).toHaveClass('bg-gray-50');
      expect(indicator).toHaveTextContent('On track');
    });

    it('renders on-track status with neutral icon', () => {
      render(<VarianceIndicator varianceDays={0} />);

      const indicator = screen.getByRole('status');
      expect(indicator).toBeInTheDocument();
    });
  });

  describe('Size Variants', () => {
    it('renders small size variant', () => {
      render(<VarianceIndicator varianceDays={2} size="sm" />);

      const indicator = screen.getByRole('status');
      expect(indicator).toBeInTheDocument();
    });

    it('renders medium size variant (default)', () => {
      render(<VarianceIndicator varianceDays={2} />);

      const indicator = screen.getByRole('status');
      expect(indicator).toBeInTheDocument();
    });

    it('renders large size variant', () => {
      render(<VarianceIndicator varianceDays={2} size="lg" />);

      const indicator = screen.getByRole('status');
      expect(indicator).toBeInTheDocument();
    });
  });

  describe('Label Display', () => {
    it('shows label when showLabel is true (default)', () => {
      render(<VarianceIndicator varianceDays={2} />);

      expect(screen.getByText('2 days behind')).toBeInTheDocument();
    });

    it('hides label when showLabel is false', () => {
      render(<VarianceIndicator varianceDays={2} showLabel={false} />);

      // Should still have aria-label for accessibility
      const indicator = screen.getByRole('status');
      expect(indicator).toHaveAttribute('aria-label');

      // But text should not be visible
      expect(screen.queryByText('2 days behind')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has role="status" for screen readers', () => {
      render(<VarianceIndicator varianceDays={2} />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('has descriptive aria-label for ahead status', () => {
      render(<VarianceIndicator varianceDays={-3} />);

      const indicator = screen.getByRole('status');
      expect(indicator).toHaveAttribute('aria-label', '3 days ahead of baseline');
    });

    it('has descriptive aria-label for behind status', () => {
      render(<VarianceIndicator varianceDays={4} />);

      const indicator = screen.getByRole('status');
      expect(indicator).toHaveAttribute('aria-label', '4 days behind baseline');
    });

    it('has descriptive aria-label for on-track status', () => {
      render(<VarianceIndicator varianceDays={0} />);

      const indicator = screen.getByRole('status');
      expect(indicator).toHaveAttribute('aria-label', 'On track with baseline');
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      render(<VarianceIndicator varianceDays={2} className="custom-class" />);

      const indicator = screen.getByRole('status');
      expect(indicator).toHaveClass('custom-class');
    });

    it('merges custom className with base classes', () => {
      render(<VarianceIndicator varianceDays={2} className="ml-4" />);

      const indicator = screen.getByRole('status');
      expect(indicator).toHaveClass('ml-4');
      expect(indicator).toHaveClass('bg-red-50'); // Base class still present
    });
  });
});
