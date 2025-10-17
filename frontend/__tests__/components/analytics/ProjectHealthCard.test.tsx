/**
 * Tests for ProjectHealthCard component
 */

import { render, screen } from '@testing-library/react';
import ProjectHealthCard from '@/components/analytics/ProjectHealthCard';

describe('ProjectHealthCard Component', () => {
  it('renders card title and description', () => {
    render(<ProjectHealthCard healthScore={85} />);

    expect(screen.getByText('Project Health Score')).toBeInTheDocument();
    expect(screen.getByText('Overall project health based on multiple factors')).toBeInTheDocument();
  });

  it('renders with excellent health status for scores >= 70', () => {
    render(<ProjectHealthCard healthScore={85} />);

    expect(screen.getByText('85')).toBeInTheDocument();
    expect(screen.getByText('Excellent')).toBeInTheDocument();
    expect(screen.getByText('out of 100')).toBeInTheDocument();
  });

  it('renders with fair health status for scores 40-69', () => {
    render(<ProjectHealthCard healthScore={55} />);

    expect(screen.getByText('55')).toBeInTheDocument();
    expect(screen.getByText('Fair')).toBeInTheDocument();
  });

  it('renders with at risk health status for scores < 40', () => {
    render(<ProjectHealthCard healthScore={25} />);

    expect(screen.getByText('25')).toBeInTheDocument();
    expect(screen.getByText('At Risk')).toBeInTheDocument();
  });

  it('displays health indicators for excellent health', () => {
    render(<ProjectHealthCard healthScore={75} />);

    expect(screen.getByText(/Schedule adherence:/)).toBeInTheDocument();
    expect(screen.getByText(/On track/)).toBeInTheDocument();
    expect(screen.getByText(/Resource utilization:/)).toBeInTheDocument();
    expect(screen.getByText(/Optimal/)).toBeInTheDocument();
    expect(screen.getByText(/Risk level:/)).toBeInTheDocument();
    expect(screen.getByText(/Low/)).toBeInTheDocument();
  });

  it('displays health indicators for fair health', () => {
    render(<ProjectHealthCard healthScore={55} />);

    expect(screen.getByText(/Behind/)).toBeInTheDocument();
    expect(screen.getByText(/Review needed/)).toBeInTheDocument();
    expect(screen.getByText(/Medium/)).toBeInTheDocument();
  });

  it('displays health indicators for poor health', () => {
    render(<ProjectHealthCard healthScore={25} />);

    expect(screen.getByText(/Behind/)).toBeInTheDocument();
    expect(screen.getByText(/Review needed/)).toBeInTheDocument();
    expect(screen.getByText(/High/)).toBeInTheDocument();
  });

  it('applies correct color styling for excellent health', () => {
    render(<ProjectHealthCard healthScore={85} />);

    const status = screen.getByText('Excellent');
    expect(status).toHaveClass('text-green-600');
  });

  it('applies correct color styling for fair health', () => {
    render(<ProjectHealthCard healthScore={55} />);

    const status = screen.getByText('Fair');
    expect(status).toHaveClass('text-yellow-600');
  });

  it('applies correct color styling for at risk health', () => {
    render(<ProjectHealthCard healthScore={25} />);

    const status = screen.getByText('At Risk');
    expect(status).toHaveClass('text-red-600');
  });

  it('renders without crashing', () => {
    const { container } = render(<ProjectHealthCard healthScore={75} />);
    expect(container).toBeInTheDocument();
  });
});
