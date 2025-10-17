/**
 * Tests for MetricsGrid component
 */

import { render, screen } from '@testing-library/react';
import MetricsGrid from '@/components/analytics/MetricsGrid';

const mockMetrics = {
  health_score: 85,
  critical_path_summary: {
    total_duration: 120,
    path_stability_score: 78.5,
    critical_tasks: [],
    risk_tasks: [],
    float_time: {},
  },
  resource_summary: {
    total_resources: 10,
    allocated_resources: 8,
    utilization_pct: 80.5,
    over_allocated: [],
    under_utilized: [],
    resource_timeline: {},
  },
  simulation_summary: {
    percentiles: { p10: 100, p50: 115, p75: 125, p90: 135, p95: 140 },
    mean_duration: 115.5,
    std_deviation: 10.2,
    risk_level: 'medium' as const,
    confidence_80pct_range: [105, 130],
    histogram_data: [],
  },
  progress_summary: {
    completion_pct: 65.5,
    tasks_completed: 50,
    tasks_total: 76,
    on_time_pct: 80,
    delayed_tasks: 5,
    burn_rate: 2.5,
    estimated_completion_date: '2025-12-31',
    variance_from_plan: -3,
  },
  generated_at: '2025-10-17T12:00:00Z',
};

describe('MetricsGrid Component', () => {
  it('renders all six metric cards', () => {
    const { container } = render(<MetricsGrid metrics={mockMetrics} />);

    const cards = container.querySelectorAll('.bg-white');
    expect(cards.length).toBe(6);
  });

  it('displays critical path duration', () => {
    render(<MetricsGrid metrics={mockMetrics} />);

    expect(screen.getByText('Critical Path Duration')).toBeInTheDocument();
    expect(screen.getByText('120 days')).toBeInTheDocument();
  });

  it('displays path stability', () => {
    render(<MetricsGrid metrics={mockMetrics} />);

    expect(screen.getByText('Path Stability')).toBeInTheDocument();
    expect(screen.getByText('78.5/100')).toBeInTheDocument();
  });

  it('displays resource utilization', () => {
    render(<MetricsGrid metrics={mockMetrics} />);

    expect(screen.getByText('Resource Utilization')).toBeInTheDocument();
    expect(screen.getByText('80.5%')).toBeInTheDocument();
  });

  it('displays completion progress', () => {
    render(<MetricsGrid metrics={mockMetrics} />);

    expect(screen.getByText('Completion Progress')).toBeInTheDocument();
    expect(screen.getByText('65.5%')).toBeInTheDocument();
  });

  it('displays tasks completed', () => {
    render(<MetricsGrid metrics={mockMetrics} />);

    expect(screen.getByText('Tasks Completed')).toBeInTheDocument();
    expect(screen.getByText('50 / 76')).toBeInTheDocument();
  });

  it('displays risk level', () => {
    render(<MetricsGrid metrics={mockMetrics} />);

    expect(screen.getByText('Risk Level')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
  });

  it('renders with 3-column grid layout', () => {
    const { container } = render(<MetricsGrid metrics={mockMetrics} />);

    const grid = container.querySelector('.grid');
    expect(grid).toHaveClass('md:grid-cols-2', 'lg:grid-cols-3');
  });

  it('displays appropriate icons for each metric', () => {
    render(<MetricsGrid metrics={mockMetrics} />);

    // Check that icons are rendered
    const icons = screen.getAllByText(/[🎯📊👥✅📝🟢🟡🔴]/);
    expect(icons.length).toBeGreaterThan(0);
  });

  it('shows yellow icon for medium risk', () => {
    render(<MetricsGrid metrics={mockMetrics} />);

    expect(screen.getByText('🟡')).toBeInTheDocument();
  });

  it('shows green icon for low risk', () => {
    const lowRiskMetrics = {
      ...mockMetrics,
      simulation_summary: {
        ...mockMetrics.simulation_summary,
        risk_level: 'low' as const,
      },
    };

    render(<MetricsGrid metrics={lowRiskMetrics} />);

    expect(screen.getByText('🟢')).toBeInTheDocument();
  });

  it('shows red icon for high risk', () => {
    const highRiskMetrics = {
      ...mockMetrics,
      simulation_summary: {
        ...mockMetrics.simulation_summary,
        risk_level: 'high' as const,
      },
    };

    render(<MetricsGrid metrics={highRiskMetrics} />);

    expect(screen.getByText('🔴')).toBeInTheDocument();
  });

  it('capitalizes risk level properly', () => {
    render(<MetricsGrid metrics={mockMetrics} />);

    // "medium" should be capitalized to "Medium"
    expect(screen.getByText('Medium')).toBeInTheDocument();
  });
});
