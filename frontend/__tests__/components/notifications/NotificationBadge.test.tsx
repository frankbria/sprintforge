/**
 * Tests for NotificationBadge component
 */

import { render, screen } from '@testing-library/react';
import { NotificationBadge } from '@/components/notifications/NotificationBadge';

describe('NotificationBadge', () => {
  it('should not render when count is 0', () => {
    const { container } = render(<NotificationBadge count={0} />);
    expect(container.firstChild).toBeNull();
  });

  it('should render count when greater than 0', () => {
    render(<NotificationBadge count={5} />);
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('should render 99+ when count exceeds 99', () => {
    render(<NotificationBadge count={150} />);
    expect(screen.getByText('99+')).toBeInTheDocument();
  });

  it('should apply default styling', () => {
    render(<NotificationBadge count={3} />);
    const badge = screen.getByText('3');
    expect(badge).toHaveClass('bg-red-500', 'text-white', 'rounded-full');
  });

  it('should support custom className', () => {
    render(<NotificationBadge count={2} className="custom-class" />);
    const badge = screen.getByText('2');
    expect(badge).toHaveClass('custom-class');
  });

  it('should have proper ARIA attributes', () => {
    render(<NotificationBadge count={7} />);
    const badge = screen.getByText('7');
    expect(badge).toHaveAttribute('aria-label', '7 unread notifications');
  });

  it('should handle large numbers correctly', () => {
    render(<NotificationBadge count={1000} />);
    expect(screen.getByText('99+')).toBeInTheDocument();
    expect(screen.getByText('99+')).toHaveAttribute(
      'aria-label',
      '1000 unread notifications'
    );
  });

  it('should render with small size variant', () => {
    render(<NotificationBadge count={1} size="sm" />);
    const badge = screen.getByText('1');
    expect(badge).toHaveClass('text-xs', 'min-w-[16px]', 'h-4');
  });

  it('should render with medium size variant (default)', () => {
    render(<NotificationBadge count={1} />);
    const badge = screen.getByText('1');
    expect(badge).toHaveClass('text-xs', 'min-w-[20px]', 'h-5');
  });
});
