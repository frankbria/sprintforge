/**
 * New Project Page
 * Wizard for creating new projects
 */

'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { ProjectWizard } from '@/components/wizard/ProjectWizard';
import { createProject } from '@/lib/api/projects';
import type { ProjectCreate } from '@/types/project';

export default function NewProjectPage() {
  const router = useRouter();
  const { data: session } = useSession();
  const [error, setError] = React.useState<string | null>(null);

  const handleComplete = async (data: ProjectCreate) => {
    try {
      setError(null);

      // Get access token from session
      const accessToken = session?.accessToken;

      // Create project via API
      const project = await createProject(data, accessToken);

      // Redirect to project dashboard or detail page
      router.push(`/dashboard`);
    } catch (err) {
      console.error('Failed to create project:', err);
      setError(
        err instanceof Error ? err.message : 'Failed to create project'
      );
    }
  };

  const handleCancel = () => {
    router.push('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
            <p className="font-medium">Error creating project</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}

        <ProjectWizard onComplete={handleComplete} onCancel={handleCancel} />
      </div>
    </div>
  );
}
