/**
 * Tests for TrendIndicator component
 */

import { render, screen } from '@testing-library/react';
import TrendIndicator from '@/components/analytics/TrendIndicator';

describe('TrendIndicator Component', () => {
  it('renders current value without trend when no previous value provided', () => {
    render(<TrendIndicator value={100} />);
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('displays formatted value for number format', () => {
    render(<TrendIndicator value={1234.56} format="number" />);
    expect(screen.getByText('1,235')).toBeInTheDocument();
  });

  it('displays formatted value for percent format', () => {
    render(<TrendIndicator value={85.7} format="percent" />);
    expect(screen.getByText('85.7%')).toBeInTheDocument();
  });

  it('displays formatted value for currency format', () => {
    render(<TrendIndicator value={1500} format="currency" />);
    expect(screen.getByText('$1,500')).toBeInTheDocument();
  });

  it('shows positive trend indicator when value increases', () => {
    render(<TrendIndicator value={120} previousValue={100} />);

    // Should show percentage change
    expect(screen.getByText('20.0%')).toBeInTheDocument();

    // Should have green styling (good trend when higher is better)
    const trendElement = screen.getByRole('status');
    expect(trendElement).toHaveClass('text-green-600');
  });

  it('shows negative trend indicator when value decreases', () => {
    render(<TrendIndicator value={80} previousValue={100} />);

    expect(screen.getByText('20.0%')).toBeInTheDocument();

    // Should have red styling (bad trend when higher is better)
    const trendElement = screen.getByRole('status');
    expect(trendElement).toHaveClass('text-red-600');
  });

  it('respects higherIsBetter=false for inverse trends', () => {
    render(<TrendIndicator value={80} previousValue={100} higherIsBetter={false} />);

    // Decrease is good when lower is better
    const trendElement = screen.getByRole('status');
    expect(trendElement).toHaveClass('text-green-600');
  });

  it('shows neutral trend when value is unchanged', () => {
    render(<TrendIndicator value={100} previousValue={100} />);

    expect(screen.getByText('0.0%')).toBeInTheDocument();

    const trendElement = screen.getByRole('status');
    expect(trendElement).toHaveClass('text-gray-500');
  });

  it('handles zero previous value correctly', () => {
    render(<TrendIndicator value={50} previousValue={0} />);

    expect(screen.getByText('100.0%')).toBeInTheDocument();
  });

  it('has proper ARIA labels for accessibility', () => {
    render(<TrendIndicator value={120} previousValue={100} />);

    const valueElement = screen.getByLabelText(/Current value: 120/i);
    expect(valueElement).toBeInTheDocument();

    const trendElement = screen.getByLabelText(/Positive trend: 20.0% increase/i);
    expect(trendElement).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <TrendIndicator value={100} className="custom-class" />
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('calculates percentage change correctly for large differences', () => {
    render(<TrendIndicator value={200} previousValue={50} />);

    expect(screen.getByText('300.0%')).toBeInTheDocument();
  });

  it('calculates percentage change correctly for negative values', () => {
    render(<TrendIndicator value={-50} previousValue={-100} />);

    // From -100 to -50 is a 50% improvement
    expect(screen.getByText('50.0%')).toBeInTheDocument();
  });
});
