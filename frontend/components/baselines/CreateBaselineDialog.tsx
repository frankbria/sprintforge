/**
 * CreateBaselineDialog Component
 *
 * Modal form for creating new baseline snapshots.
 * Uses React Hook Form + Zod for validation.
 *
 * Implemented following TDD RED-GREEN-REFACTOR cycle.
 */

'use client';

import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Textarea } from '@/components/ui/Textarea';
import { Alert } from '@/components/ui/Alert';
import { createBaseline } from '@/lib/api/baselines';

export interface CreateBaselineDialogProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

// Validation schema
const createBaselineSchema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .max(255, 'Name must be less than 255 characters')
    .transform((s) => s.trim()),
  description: z.string().optional(),
});

type CreateBaselineFormData = z.infer<typeof createBaselineSchema>;

export function CreateBaselineDialog({
  projectId,
  isOpen,
  onClose,
  onSuccess,
}: CreateBaselineDialogProps) {
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreateBaselineFormData>({
    resolver: zodResolver(createBaselineSchema),
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateBaselineFormData) => createBaseline(projectId, data),
    onSuccess: () => {
      reset();
      setErrorMessage(null);
      onSuccess();
    },
    onError: (error: Error) => {
      setErrorMessage(error.message);
    },
  });

  const onSubmit = (data: CreateBaselineFormData) => {
    setErrorMessage(null);
    // Ensure description is undefined if empty
    const payload = {
      name: data.name,
      description: data.description && data.description.trim() ? data.description : undefined,
    };
    createMutation.mutate(payload);
  };

  const handleClose = () => {
    if (!createMutation.isPending) {
      reset();
      setErrorMessage(null);
      onClose();
    }
  };

  // Reset form when dialog opens
  React.useEffect(() => {
    if (isOpen) {
      reset();
      setErrorMessage(null);
    }
  }, [isOpen, reset]);

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Create Baseline</DialogTitle>
            <DialogDescription>
              Create a snapshot of the current project state to track variance over
              time.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Error Alert */}
            {errorMessage && (
              <Alert variant="destructive">
                <p className="text-sm">{errorMessage}</p>
              </Alert>
            )}

            {/* Name Field */}
            <div className="space-y-2">
              <Label htmlFor="baseline-name">
                Name <span className="text-red-500">*</span>
              </Label>
              <Input
                id="baseline-name"
                {...register('name')}
                placeholder="e.g., Q4 2025 Baseline"
                disabled={createMutation.isPending}
                aria-required="true"
              />
              {errors.name && (
                <p className="text-sm text-red-600">{errors.name.message}</p>
              )}
            </div>

            {/* Description Field */}
            <div className="space-y-2">
              <Label htmlFor="baseline-description">Description</Label>
              <Textarea
                id="baseline-description"
                {...register('description')}
                placeholder="Optional description..."
                rows={3}
                disabled={createMutation.isPending}
              />
              {errors.description && (
                <p className="text-sm text-red-600">{errors.description.message}</p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={handleClose}
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              loading={createMutation.isPending}
              loadingText="Creating..."
            >
              Create
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
