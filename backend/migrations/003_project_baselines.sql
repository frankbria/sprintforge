-- Migration: Add project_baselines table for baseline management and comparison
-- Task: bd-5 (Baseline Management & Comparison)
-- Date: 2025-10-17

-- Create project_baselines table
CREATE TABLE IF NOT EXISTS project_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Complete project snapshot stored as JSONB
    -- Contains: project, tasks, critical_path, monte_carlo_results, snapshot_metadata
    snapshot_data JSONB NOT NULL,

    -- Active baseline flag - only one baseline per project can be active
    is_active BOOLEAN NOT NULL DEFAULT false,

    -- Snapshot size tracking for monitoring and constraints
    snapshot_size_bytes INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT baseline_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT snapshot_size_limit CHECK (snapshot_size_bytes IS NULL OR snapshot_size_bytes < 10485760)  -- 10MB limit
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_baselines_project_id ON project_baselines(project_id);
CREATE INDEX IF NOT EXISTS idx_baselines_created_at ON project_baselines(created_at DESC);

-- Unique partial index to enforce single active baseline per project
-- This ensures only one baseline per project can have is_active = true
CREATE UNIQUE INDEX IF NOT EXISTS unique_active_baseline_per_project
    ON project_baselines(project_id)
    WHERE is_active = true;

-- GIN index for efficient JSONB queries (optional but useful for future queries)
CREATE INDEX IF NOT EXISTS idx_baselines_snapshot_data_gin
    ON project_baselines USING GIN(snapshot_data);

-- Trigger function to automatically calculate snapshot size
CREATE OR REPLACE FUNCTION update_baseline_snapshot_size()
RETURNS TRIGGER AS $$
BEGIN
    NEW.snapshot_size_bytes := length(NEW.snapshot_data::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update snapshot size before insert or update
CREATE TRIGGER baseline_snapshot_size_trigger
    BEFORE INSERT OR UPDATE ON project_baselines
    FOR EACH ROW
    EXECUTE FUNCTION update_baseline_snapshot_size();

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_baseline_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER baseline_updated_at_trigger
    BEFORE UPDATE ON project_baselines
    FOR EACH ROW
    EXECUTE FUNCTION update_baseline_updated_at();

-- Add comments for documentation
COMMENT ON TABLE project_baselines IS 'Project baselines for snapshot and comparison functionality';
COMMENT ON COLUMN project_baselines.snapshot_data IS 'Complete immutable snapshot of project state including tasks, critical path, and Monte Carlo results';
COMMENT ON COLUMN project_baselines.is_active IS 'Only one baseline per project can be active for comparison';
COMMENT ON COLUMN project_baselines.snapshot_size_bytes IS 'Size of snapshot data in bytes (auto-calculated via trigger)';
COMMENT ON INDEX unique_active_baseline_per_project IS 'Ensures only one active baseline per project via partial unique index';
