-- SprintForge Initial Database Schema
-- Compatible with NextAuth.js v4 and SprintForge requirements

-- Enable UUID extension for ID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Migration tracking table
CREATE TABLE migration_history (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    checksum VARCHAR(64) NOT NULL
);

-- NextAuth.js compatible tables
-- Users table (NextAuth.js accounts table references this)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified TIMESTAMP WITH TIME ZONE,
    image TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- SprintForge specific fields
    subscription_tier VARCHAR(50) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'enterprise')),
    subscription_status VARCHAR(50) DEFAULT 'active' CHECK (subscription_status IN ('active', 'canceled', 'expired')),
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    preferences JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true
);

-- NextAuth.js accounts table (OAuth provider accounts)
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(255) NOT NULL,
    provider VARCHAR(255) NOT NULL,
    provider_account_id VARCHAR(255) NOT NULL,
    refresh_token TEXT,
    access_token TEXT,
    expires_at BIGINT,
    token_type VARCHAR(255),
    scope VARCHAR(255),
    id_token TEXT,
    session_state VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(provider, provider_account_id)
);

-- NextAuth.js sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- NextAuth.js verification tokens table (for email verification)
CREATE TABLE verification_tokens (
    identifier VARCHAR(255) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    PRIMARY KEY (identifier, token)
);

-- SprintForge Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Project configuration stored as JSONB for flexibility
    configuration JSONB DEFAULT '{}',

    -- Template and version tracking
    template_version VARCHAR(50) DEFAULT '1.0',
    checksum VARCHAR(64),

    -- Sharing settings
    is_public BOOLEAN DEFAULT false,
    public_share_token VARCHAR(255) UNIQUE,
    share_expires_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_generated_at TIMESTAMP WITH TIME ZONE,

    -- Ensure project names are unique per user
    UNIQUE(owner_id, name)
);

-- Project memberships (for future team features)
CREATE TABLE project_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Role-based access control
    role VARCHAR(50) DEFAULT 'viewer' CHECK (role IN ('owner', 'admin', 'editor', 'viewer')),

    -- Invitation workflow
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('pending', 'active', 'declined')),
    invited_by UUID REFERENCES users(id),
    invited_at TIMESTAMP WITH TIME ZONE,
    joined_at TIMESTAMP WITH TIME ZONE,

    -- Permissions (future extensibility)
    permissions JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure unique membership per user per project
    UNIQUE(project_id, user_id)
);

-- Sync operations tracking (for Excel-server sync)
CREATE TABLE sync_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Operation details
    operation_type VARCHAR(50) NOT NULL CHECK (operation_type IN ('upload', 'download', 'sync')),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),

    -- File information
    file_name VARCHAR(255),
    file_size BIGINT,
    file_checksum VARCHAR(64),

    -- Sync metadata
    sync_data JSONB,
    error_message TEXT,

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance indexes
-- Users table indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_subscription ON users(subscription_tier, subscription_status);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;

-- Accounts table indexes
CREATE INDEX idx_accounts_user_id ON accounts(user_id);
CREATE INDEX idx_accounts_provider ON accounts(provider, provider_account_id);

-- Sessions table indexes
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token ON sessions(session_token);
CREATE INDEX idx_sessions_expires ON sessions(expires);

-- Projects table indexes
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_public ON projects(is_public) WHERE is_public = true;
CREATE INDEX idx_projects_share_token ON projects(public_share_token) WHERE public_share_token IS NOT NULL;
CREATE INDEX idx_projects_created_at ON projects(created_at);

-- Project memberships indexes
CREATE INDEX idx_memberships_project_id ON project_memberships(project_id);
CREATE INDEX idx_memberships_user_id ON project_memberships(user_id);
CREATE INDEX idx_memberships_role ON project_memberships(role);
CREATE INDEX idx_memberships_status ON project_memberships(status);

-- Sync operations indexes
CREATE INDEX idx_sync_project_id ON sync_operations(project_id);
CREATE INDEX idx_sync_user_id ON sync_operations(user_id);
CREATE INDEX idx_sync_status ON sync_operations(status);
CREATE INDEX idx_sync_created_at ON sync_operations(created_at);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memberships_updated_at BEFORE UPDATE ON project_memberships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Record this migration
INSERT INTO migration_history (migration_name, checksum)
VALUES ('001_initial_schema', md5('001_initial_schema.sql_v1'));

-- Comments for documentation
COMMENT ON TABLE users IS 'NextAuth.js compatible users table with SprintForge extensions';
COMMENT ON TABLE projects IS 'SprintForge projects with JSONB configuration for flexibility';
COMMENT ON TABLE project_memberships IS 'Team collaboration features (future implementation)';
COMMENT ON TABLE sync_operations IS 'Excel-server synchronization tracking';

COMMENT ON COLUMN projects.configuration IS 'JSONB field containing sprint patterns, working days, feature flags, etc.';
COMMENT ON COLUMN projects.checksum IS 'Hash of project configuration for change detection';
COMMENT ON COLUMN users.preferences IS 'User preferences like theme, notifications, default settings';