/**
 * BaselineList Component
 *
 * Displays a table of all project baselines with actions.
 * Supports activating, comparing, and deleting baselines.
 *
 * Implemented following TDD RED-GREEN-REFACTOR cycle.
 */

'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { Eye, Trash2, CheckCircle, Plus } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Alert } from '@/components/ui/Alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog';
import { CreateBaselineDialog } from './CreateBaselineDialog';
import { getBaselines, deleteBaseline, setBaselineActive } from '@/lib/api/baselines';
import type { Baseline } from '@/types/baseline';

export interface BaselineListProps {
  projectId: string;
}

/**
 * Format bytes to human-readable size
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${Math.round(bytes / Math.pow(k, i))} ${sizes[i]}`;
}

/**
 * Format date to human-readable format
 */
function formatDate(dateString: string): string {
  try {
    return format(new Date(dateString), 'MMM d, yyyy');
  } catch {
    return dateString;
  }
}

export function BaselineList({ projectId }: BaselineListProps) {
  const queryClient = useQueryClient();
  const [createDialogOpen, setCreateDialogOpen] = React.useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [selectedBaseline, setSelectedBaseline] = React.useState<Baseline | null>(null);

  // Fetch baselines
  const {
    data: response,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['baselines', projectId],
    queryFn: () => getBaselines(projectId, 1, 50),
    refetchInterval: 30000, // Auto-refresh every 30s
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (baselineId: string) => deleteBaseline(projectId, baselineId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['baselines', projectId] });
      setDeleteDialogOpen(false);
      setSelectedBaseline(null);
    },
  });

  // Activate mutation
  const activateMutation = useMutation({
    mutationFn: (baselineId: string) => setBaselineActive(projectId, baselineId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['baselines', projectId] });
    },
  });

  const handleDeleteClick = (baseline: Baseline) => {
    setSelectedBaseline(baseline);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (selectedBaseline) {
      deleteMutation.mutate(selectedBaseline.id);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setSelectedBaseline(null);
  };

  const handleActivateClick = (baselineId: string) => {
    activateMutation.mutate(baselineId);
  };

  const handleCompareClick = (baselineId: string) => {
    // Navigate to comparison page
    window.location.href = `/projects/${projectId}/baselines/${baselineId}/compare`;
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-800">Loading baselines...</span>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert variant="destructive" className="my-4">
        <div className="flex items-center justify-between">
          <div>
            <strong className="font-semibold">Error loading baselines</strong>
            <p className="text-sm mt-1">
              {error instanceof Error ? error.message : 'Failed to fetch baselines'}
            </p>
          </div>
          <Button onClick={() => refetch()} size="sm">
            Retry
          </Button>
        </div>
      </Alert>
    );
  }

  const baselines = response?.baselines || [];

  // Empty state
  if (baselines.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-700 mb-4">No baselines found for this project.</p>
        <Button onClick={() => setCreateDialogOpen(true)} icon={<Plus size={16} />}>
          Create Baseline
        </Button>

        <CreateBaselineDialog
          projectId={projectId}
          isOpen={createDialogOpen}
          onClose={() => setCreateDialogOpen(false)}
          onSuccess={() => {
            setCreateDialogOpen(false);
            queryClient.invalidateQueries({ queryKey: ['baselines', projectId] });
          }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Create Button */}
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-900">Baselines ({baselines.length})</h2>
        <Button onClick={() => setCreateDialogOpen(true)} icon={<Plus size={16} />}>
          Create Baseline
        </Button>
      </div>

      {/* Baselines Table */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Created</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Size</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {baselines.map((baseline) => (
            <TableRow key={baseline.id}>
              <TableCell className="font-medium">
                <div>
                  <div>{baseline.name}</div>
                  {baseline.description && (
                    <div className="text-xs text-gray-700 mt-0.5">
                      {baseline.description}
                    </div>
                  )}
                </div>
              </TableCell>
              <TableCell>{formatDate(baseline.created_at)}</TableCell>
              <TableCell>
                {baseline.is_active ? (
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-green-50 text-green-700 text-xs font-medium border border-green-200">
                    <CheckCircle size={12} />
                    Active
                  </span>
                ) : (
                  <span className="text-gray-700 text-sm">Inactive</span>
                )}
              </TableCell>
              <TableCell>{formatBytes(baseline.snapshot_size_bytes)}</TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  {!baseline.is_active && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleActivateClick(baseline.id)}
                      disabled={activateMutation.isPending}
                    >
                      Set Active
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    icon={<Eye size={14} />}
                    onClick={() => handleCompareClick(baseline.id)}
                  >
                    Compare
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    icon={<Trash2 size={14} />}
                    onClick={() => handleDeleteClick(baseline)}
                    disabled={deleteMutation.isPending}
                  >
                    Delete
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* Create Baseline Dialog */}
      <CreateBaselineDialog
        projectId={projectId}
        isOpen={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSuccess={() => {
          setCreateDialogOpen(false);
          queryClient.invalidateQueries({ queryKey: ['baselines', projectId] });
        }}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent role="alertdialog">
          <DialogHeader>
            <DialogTitle>Delete Baseline</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedBaseline?.name}"? This action
              cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={handleDeleteCancel}
              disabled={deleteMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleDeleteConfirm}
              loading={deleteMutation.isPending}
              loadingText="Deleting..."
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
