/**
 * Baseline Comparison Page
 *
 * Displays variance analysis between baseline and current state.
 */

import { Metadata } from 'next';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { BaselineComparisonView } from '@/components/baselines/BaselineComparisonView';

export const metadata: Metadata = {
  title: 'Baseline Comparison - SprintForge',
  description: 'Compare project baseline to current state',
};

export default function BaselineComparisonPage({
  params,
}: {
  params: { id: string; baselineId: string };
}) {
  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-6">
        <Link
          href={`/projects/${params.id}/baselines`}
          className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-800 mb-4"
        >
          <ArrowLeft size={16} />
          Back to Baselines
        </Link>
      </div>

      <BaselineComparisonView
        projectId={params.id}
        baselineId={params.baselineId}
      />
    </div>
  );
}
