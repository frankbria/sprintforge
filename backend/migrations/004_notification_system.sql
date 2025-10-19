-- Migration: Add notification system tables
-- BD-6: Basic Notification System Implementation
-- Date: 2025-10-18

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'unread',
    metadata JSONB,
    read_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT notifications_status_check CHECK (status IN ('unread', 'read'))
);

-- Create notification_rules table
CREATE TABLE IF NOT EXISTS notification_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    channels JSONB NOT NULL DEFAULT '["in_app"]'::jsonb,
    conditions JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create notification_logs table
CREATE TABLE IF NOT EXISTS notification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    channel VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create notification_templates table
CREATE TABLE IF NOT EXISTS notification_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) UNIQUE NOT NULL,
    subject_template VARCHAR(255) NOT NULL,
    body_template_html TEXT NOT NULL,
    body_template_text TEXT NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS ix_notifications_id ON notifications(id);
CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS ix_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS ix_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications(created_at);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS ix_notifications_user_status
    ON notifications(user_id, status);

CREATE INDEX IF NOT EXISTS ix_notifications_user_created
    ON notifications(user_id, created_at DESC);

-- Notification rules indexes
CREATE INDEX IF NOT EXISTS ix_notification_rules_id ON notification_rules(id);
CREATE INDEX IF NOT EXISTS ix_notification_rules_user_id ON notification_rules(user_id);
CREATE INDEX IF NOT EXISTS ix_notification_rules_event_type ON notification_rules(event_type);

CREATE INDEX IF NOT EXISTS ix_notification_rules_user_event
    ON notification_rules(user_id, event_type);

-- Notification logs indexes
CREATE INDEX IF NOT EXISTS ix_notification_logs_id ON notification_logs(id);
CREATE INDEX IF NOT EXISTS ix_notification_logs_notification_id ON notification_logs(notification_id);

-- Notification templates indexes
CREATE INDEX IF NOT EXISTS ix_notification_templates_id ON notification_templates(id);
CREATE INDEX IF NOT EXISTS ix_notification_templates_event_type ON notification_templates(event_type);

-- Add comments for documentation
COMMENT ON TABLE notifications IS 'In-app notifications for users with status tracking';
COMMENT ON COLUMN notifications.metadata IS 'JSON object with notification-specific data';
COMMENT ON COLUMN notifications.read_at IS 'Timestamp when notification was marked as read';

COMMENT ON TABLE notification_rules IS 'User-defined notification delivery preferences';
COMMENT ON COLUMN notification_rules.channels IS 'Array of delivery channels (e.g., ["email", "in_app"])';
COMMENT ON COLUMN notification_rules.conditions IS 'JSON object with rule matching conditions';

COMMENT ON TABLE notification_logs IS 'Delivery logs for notification attempts';
COMMENT ON COLUMN notification_logs.error_message IS 'Error message if delivery failed';

COMMENT ON TABLE notification_templates IS 'Email templates for notification types';
COMMENT ON COLUMN notification_templates.subject_template IS 'Jinja2 template for email subject';
COMMENT ON COLUMN notification_templates.body_template_html IS 'Jinja2 template for HTML email body';
COMMENT ON COLUMN notification_templates.body_template_text IS 'Jinja2 template for plain text email body';
