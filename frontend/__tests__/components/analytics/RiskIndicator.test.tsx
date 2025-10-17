/**
 * Tests for RiskIndicator component
 */

import { render, screen } from '@testing-library/react';
import RiskIndicator from '@/components/analytics/RiskIndicator';

describe('RiskIndicator Component', () => {
  it('renders low risk indicator correctly', () => {
    render(<RiskIndicator riskLevel="low" />);

    expect(screen.getByText('Low Risk')).toBeInTheDocument();

    const element = screen.getByRole('status');
    expect(element).toHaveClass('bg-green-100', 'text-green-800');
  });

  it('renders medium risk indicator correctly', () => {
    render(<RiskIndicator riskLevel="medium" />);

    expect(screen.getByText('Medium Risk')).toBeInTheDocument();

    const element = screen.getByRole('status');
    expect(element).toHaveClass('bg-yellow-100', 'text-yellow-800');
  });

  it('renders high risk indicator correctly', () => {
    render(<RiskIndicator riskLevel="high" />);

    expect(screen.getByText('High Risk')).toBeInTheDocument();

    const element = screen.getByRole('status');
    expect(element).toHaveClass('bg-red-100', 'text-red-800');
  });

  it('displays risk score when provided', () => {
    render(<RiskIndicator riskLevel="medium" riskScore={65} />);

    expect(screen.getByText('(65)')).toBeInTheDocument();
  });

  it('renders small size variant', () => {
    render(<RiskIndicator riskLevel="low" size="sm" />);

    const element = screen.getByRole('status');
    expect(element).toHaveClass('px-2', 'py-1', 'text-xs');
  });

  it('renders medium size variant (default)', () => {
    render(<RiskIndicator riskLevel="low" />);

    const element = screen.getByRole('status');
    expect(element).toHaveClass('px-3', 'py-1.5', 'text-sm');
  });

  it('renders large size variant', () => {
    render(<RiskIndicator riskLevel="low" size="lg" />);

    const element = screen.getByRole('status');
    expect(element).toHaveClass('px-4', 'py-2', 'text-base');
  });

  it('has proper ARIA label without score', () => {
    render(<RiskIndicator riskLevel="low" />);

    const element = screen.getByRole('status');
    expect(element).toHaveAttribute(
      'aria-label',
      'Low Risk: Project is on track with minimal risks'
    );
  });

  it('has proper ARIA label with score', () => {
    render(<RiskIndicator riskLevel="high" riskScore={85} />);

    const element = screen.getByRole('status');
    expect(element).toHaveAttribute(
      'aria-label',
      'High Risk: Risk score 85 out of 100. Significant risks require immediate action'
    );
  });

  it('includes tooltip title matching aria-label', () => {
    render(<RiskIndicator riskLevel="medium" riskScore={50} />);

    const element = screen.getByRole('status');
    const expectedText = 'Medium Risk: Risk score 50 out of 100. Some risks identified that need attention';

    expect(element).toHaveAttribute('aria-label', expectedText);
    expect(element).toHaveAttribute('title', expectedText);
  });

  it('renders appropriate icon for each risk level', () => {
    const { container: lowContainer } = render(<RiskIndicator riskLevel="low" />);
    expect(lowContainer.querySelector('svg')).toBeInTheDocument();

    const { container: mediumContainer } = render(<RiskIndicator riskLevel="medium" />);
    expect(mediumContainer.querySelector('svg')).toBeInTheDocument();

    const { container: highContainer } = render(<RiskIndicator riskLevel="high" />);
    expect(highContainer.querySelector('svg')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <RiskIndicator riskLevel="low" className="custom-class" />
    );

    const element = screen.getByRole('status');
    expect(element).toHaveClass('custom-class');
  });

  it('icon has aria-hidden attribute', () => {
    const { container } = render(<RiskIndicator riskLevel="low" />);

    const icon = container.querySelector('svg');
    expect(icon).toHaveAttribute('aria-hidden', 'true');
  });
});
