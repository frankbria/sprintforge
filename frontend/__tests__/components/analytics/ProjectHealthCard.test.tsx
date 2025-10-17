/**
 * Tests for ProjectHealthCard component
 */

import { render, screen } from '@testing-library/react';
import ProjectHealthCard from '@/components/analytics/ProjectHealthCard';

// Mock Recharts components
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  RadialBarChart: ({ children }: any) => <div data-testid="radial-bar-chart">{children}</div>,
  RadialBar: () => <div data-testid="radial-bar" />,
  PolarAngleAxis: () => <div data-testid="polar-angle-axis" />,
}));

describe('ProjectHealthCard Component', () => {
  it('renders with excellent health status for scores >= 70', () => {
    render(<ProjectHealthCard healthScore={85} />);

    expect(screen.getByText('Project Health Score')).toBeInTheDocument();
    expect(screen.getByText('85')).toBeInTheDocument();
    expect(screen.getByText('Excellent Health')).toBeInTheDocument();
    expect(screen.getByText('Project is healthy and on track')).toBeInTheDocument();
  });

  it('renders with fair health status for scores 40-69', () => {
    render(<ProjectHealthCard healthScore={55} />);

    expect(screen.getByText('55')).toBeInTheDocument();
    expect(screen.getByText('Fair Health')).toBeInTheDocument();
    expect(screen.getByText('Some areas need attention')).toBeInTheDocument();
  });

  it('renders with poor health status for scores < 40', () => {
    render(<ProjectHealthCard healthScore={25} />);

    expect(screen.getByText('25')).toBeInTheDocument();
    expect(screen.getByText('Poor Health')).toBeInTheDocument();
    expect(screen.getByText('Project requires immediate action')).toBeInTheDocument();
  });

  it('displays custom description when provided', () => {
    const customDescription = 'Custom health description';
    render(<ProjectHealthCard healthScore={80} description={customDescription} />);

    expect(screen.getByText(customDescription)).toBeInTheDocument();
  });

  it('clamps health score to 0-100 range', () => {
    const { rerender } = render(<ProjectHealthCard healthScore={150} />);
    expect(screen.getByText('100')).toBeInTheDocument();

    rerender(<ProjectHealthCard healthScore={-10} />);
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('renders all health factors', () => {
    render(<ProjectHealthCard healthScore={75} />);

    expect(screen.getByText(/Schedule Adherence/)).toBeInTheDocument();
    expect(screen.getByText(/Critical Path Stability/)).toBeInTheDocument();
    expect(screen.getByText(/Resource Utilization/)).toBeInTheDocument();
    expect(screen.getByText(/Risk Level/)).toBeInTheDocument();
    expect(screen.getByText(/Completion Rate/)).toBeInTheDocument();
  });

  it('displays correct weight percentages for health factors', () => {
    render(<ProjectHealthCard healthScore={80} />);

    expect(screen.getByText('(30%)')).toBeInTheDocument(); // Schedule Adherence
    expect(screen.getByText('(25%)')).toBeInTheDocument(); // Critical Path Stability
    expect(screen.getByText('(20%)')).toBeInTheDocument(); // Resource Utilization
    expect(screen.getByText('(15%)')).toBeInTheDocument(); // Risk Level
    expect(screen.getByText('(10%)')).toBeInTheDocument(); // Completion Rate
  });

  it('renders Recharts components', () => {
    render(<ProjectHealthCard healthScore={75} />);

    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    expect(screen.getByTestId('radial-bar-chart')).toBeInTheDocument();
    expect(screen.getByTestId('radial-bar')).toBeInTheDocument();
  });

  it('has proper ARIA label for gauge chart', () => {
    render(<ProjectHealthCard healthScore={85} />);

    const gauge = screen.getByLabelText('Health score gauge showing 85 out of 100');
    expect(gauge).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <ProjectHealthCard healthScore={75} className="custom-class" />
    );

    const card = container.firstChild;
    expect(card).toHaveClass('custom-class');
  });

  it('applies correct color styling for excellent health', () => {
    const { container } = render(<ProjectHealthCard healthScore={85} />);

    const badge = screen.getByText('Excellent Health').closest('div');
    expect(badge).toHaveClass('bg-green-100', 'text-green-800');
  });

  it('applies correct color styling for fair health', () => {
    const { container } = render(<ProjectHealthCard healthScore={55} />);

    const badge = screen.getByText('Fair Health').closest('div');
    expect(badge).toHaveClass('bg-amber-100', 'text-amber-800');
  });

  it('applies correct color styling for poor health', () => {
    const { container } = render(<ProjectHealthCard healthScore={25} />);

    const badge = screen.getByText('Poor Health').closest('div');
    expect(badge).toHaveClass('bg-red-100', 'text-red-800');
  });

  it('health factors list has proper ARIA role', () => {
    render(<ProjectHealthCard healthScore={75} />);

    const factorsList = screen.getByLabelText('Health factors');
    expect(factorsList).toBeInTheDocument();
  });
});
