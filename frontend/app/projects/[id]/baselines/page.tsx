/**
 * Baselines List Page
 *
 * Displays all project baselines with create/manage actions.
 */

import { Metadata } from 'next';
import { BaselineList } from '@/components/baselines/BaselineList';

export const metadata: Metadata = {
  title: 'Baselines - SprintForge',
  description: 'Manage project baselines and track variance',
};

export default function BaselinesPage({
  params,
}: {
  params: { id: string };
}) {
  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Project Baselines</h1>
        <p className="text-gray-800 mt-2">
          Create and manage project baseline snapshots to track variance over time.
        </p>
      </div>

      <BaselineList projectId={params.id} />
    </div>
  );
}
