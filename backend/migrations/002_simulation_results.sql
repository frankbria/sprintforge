-- Migration: Add simulation_results table for Monte Carlo simulation storage
-- Phase C3: Database Integration
-- Date: 2025-10-15

-- Create simulation_results table
CREATE TABLE IF NOT EXISTS simulation_results (
    id SERIAL PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Simulation parameters
    iterations INTEGER NOT NULL,
    task_count INTEGER NOT NULL,
    project_start_date DATE NOT NULL,

    -- Results
    mean_duration DOUBLE PRECISION NOT NULL,
    median_duration DOUBLE PRECISION NOT NULL,
    std_deviation DOUBLE PRECISION NOT NULL,
    confidence_intervals JSONB NOT NULL,  -- {10: 45.2, 50: 51.5, 90: 61.5, ...}

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    simulation_duration_seconds DOUBLE PRECISION,

    CONSTRAINT simulation_results_iterations_positive CHECK (iterations > 0),
    CONSTRAINT simulation_results_task_count_positive CHECK (task_count > 0),
    CONSTRAINT simulation_results_mean_duration_positive CHECK (mean_duration > 0),
    CONSTRAINT simulation_results_median_duration_positive CHECK (median_duration > 0),
    CONSTRAINT simulation_results_std_deviation_nonnegative CHECK (std_deviation >= 0)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS ix_simulation_results_id ON simulation_results(id);
CREATE INDEX IF NOT EXISTS ix_simulation_results_project_id ON simulation_results(project_id);
CREATE INDEX IF NOT EXISTS ix_simulation_results_user_id ON simulation_results(user_id);
CREATE INDEX IF NOT EXISTS ix_simulation_results_created_at ON simulation_results(created_at);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS ix_simulation_results_project_created
    ON simulation_results(project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_simulation_results_user_created
    ON simulation_results(user_id, created_at DESC);

-- Add comment for documentation
COMMENT ON TABLE simulation_results IS 'Monte Carlo simulation results with statistical analysis and confidence intervals';
COMMENT ON COLUMN simulation_results.iterations IS 'Number of Monte Carlo iterations performed';
COMMENT ON COLUMN simulation_results.confidence_intervals IS 'JSON object with percentile values (e.g., {10: 45.2, 50: 51.5, 90: 61.5})';
COMMENT ON COLUMN simulation_results.simulation_duration_seconds IS 'Execution time of the simulation in seconds';
