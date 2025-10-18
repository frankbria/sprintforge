/**
 * Notification Settings Page
 * Provides UI for managing notification rules and viewing notification history
 */

'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { Button } from '@/components/ui/Button';
import { Dialog } from '@/components/ui/Dialog';
import { NotificationRulesList } from '@/components/notifications/NotificationRulesList';
import { NotificationRuleForm } from '@/components/notifications/NotificationRuleForm';
import { NotificationHistoryTable } from '@/components/notifications/NotificationHistoryTable';
import {
  getNotificationRules,
  createNotificationRule,
  updateNotificationRule,
  deleteNotificationRule,
  getNotificationLogs,
} from '@/lib/api/notifications';
import type {
  NotificationRule,
  NotificationRuleCreate,
  NotificationRuleUpdate,
} from '@/types/notification';

export default function NotificationSettingsPage() {
  const [activeTab, setActiveTab] = React.useState('settings');
  const [showCreateDialog, setShowCreateDialog] = React.useState(false);
  const [editingRule, setEditingRule] = React.useState<NotificationRule | null>(null);
  const [logOffset, setLogOffset] = React.useState(0);

  const queryClient = useQueryClient();

  // Fetch notification rules
  const {
    data: rulesData,
    isLoading: rulesLoading,
    error: rulesError,
  } = useQuery({
    queryKey: ['notification-rules'],
    queryFn: getNotificationRules,
  });

  // Fetch notification logs
  const {
    data: logsData,
    isLoading: logsLoading,
  } = useQuery({
    queryKey: ['notification-logs', logOffset],
    queryFn: () => getNotificationLogs({ limit: 20, offset: logOffset }),
    enabled: activeTab === 'history',
  });

  // Create rule mutation
  const createMutation = useMutation({
    mutationFn: createNotificationRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-rules'] });
      setShowCreateDialog(false);
    },
  });

  // Update rule mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: NotificationRuleUpdate }) =>
      updateNotificationRule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-rules'] });
      setEditingRule(null);
    },
  });

  // Delete rule mutation
  const deleteMutation = useMutation({
    mutationFn: deleteNotificationRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-rules'] });
    },
  });

  // Toggle rule enabled/disabled
  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      updateNotificationRule(id, { enabled }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-rules'] });
    },
  });

  const handleCreateRule = async (data: NotificationRuleCreate) => {
    await createMutation.mutateAsync(data);
  };

  const handleUpdateRule = async (data: NotificationRuleCreate) => {
    if (editingRule) {
      await updateMutation.mutateAsync({
        id: editingRule.id,
        data,
      });
    }
  };

  const handleDeleteRule = async (id: string) => {
    if (confirm('Are you sure you want to delete this notification rule?')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  const handleToggleRule = async (id: string, enabled: boolean) => {
    await toggleMutation.mutateAsync({ id, enabled });
  };

  const handleEditRule = (rule: NotificationRule) => {
    setEditingRule(rule);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">
              Notification Settings
            </h1>
            <p className="mt-2 text-gray-800">
              Manage your notification preferences and view notification history
            </p>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="settings" value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="settings">Settings</TabsTrigger>
              <TabsTrigger value="history">History</TabsTrigger>
            </TabsList>

            {/* Settings Tab */}
            <TabsContent value="settings">
              <div className="mt-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">
                    Notification Rules
                  </h2>
                  <Button onClick={() => setShowCreateDialog(true)}>
                    Create Rule
                  </Button>
                </div>

                {rulesError ? (
                  <div className="bg-red-50 border border-red-200 rounded-md p-4">
                    <p className="text-sm text-red-800">
                      Failed to load notification rules. Please try again.
                    </p>
                  </div>
                ) : (
                  <NotificationRulesList
                    rules={rulesData?.rules || []}
                    loading={rulesLoading}
                    onEdit={handleEditRule}
                    onDelete={handleDeleteRule}
                    onToggle={handleToggleRule}
                  />
                )}
              </div>
            </TabsContent>

            {/* History Tab */}
            <TabsContent value="history">
              <div className="mt-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">
                  Notification History
                </h2>

                <NotificationHistoryTable
                  logs={logsData?.logs || []}
                  total={logsData?.total}
                  limit={logsData?.limit}
                  offset={logsData?.offset}
                  loading={logsLoading}
                  onPageChange={setLogOffset}
                />
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Create Rule Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        title="New Notification Rule"
      >
        <NotificationRuleForm
          onSubmit={handleCreateRule}
          onCancel={() => setShowCreateDialog(false)}
        />
      </Dialog>

      {/* Edit Rule Dialog */}
      <Dialog
        open={!!editingRule}
        onClose={() => setEditingRule(null)}
        title="Edit Notification Rule"
      >
        {editingRule && (
          <NotificationRuleForm
            rule={editingRule}
            onSubmit={handleUpdateRule}
            onCancel={() => setEditingRule(null)}
          />
        )}
      </Dialog>
    </div>
  );
}
