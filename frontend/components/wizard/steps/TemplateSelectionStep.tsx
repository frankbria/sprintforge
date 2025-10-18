/**
 * Step 2: Template Selection
 * Choose project template with preview
 */

'use client';

import * as React from 'react';
import { UseFormReturn } from 'react-hook-form';
import { Check, Star } from 'lucide-react';
import { PROJECT_TEMPLATES } from '@/lib/wizard-constants';
import { cn } from '@/lib/utils';
import type { WizardFormData } from '@/lib/wizard-schema';

interface TemplateSelectionStepProps {
  form: UseFormReturn<WizardFormData>;
  onTemplateChange: (templateId: string) => void;
}

export function TemplateSelectionStep({
  form,
  onTemplateChange,
}: TemplateSelectionStepProps) {
  const { watch } = form;
  const selectedTemplate = watch('template_id');

  const handleTemplateSelect = (templateId: string) => {
    onTemplateChange(templateId);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {PROJECT_TEMPLATES.map((template) => {
          const isSelected = selectedTemplate === template.id;

          return (
            <button
              key={template.id}
              type="button"
              onClick={() => handleTemplateSelect(template.id)}
              className={cn(
                'relative p-4 border-2 rounded-lg text-left transition-all hover:shadow-md',
                isSelected
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              )}
            >
              {template.recommended && (
                <div className="absolute -top-2 -right-2 bg-yellow-400 text-yellow-900 text-xs font-semibold px-2 py-1 rounded-full flex items-center gap-1">
                  <Star className="h-3 w-3 fill-current" />
                  Recommended
                </div>
              )}

              {isSelected && (
                <div className="absolute top-4 right-4 bg-blue-600 text-white rounded-full p-1">
                  <Check className="h-4 w-4" />
                </div>
              )}

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-gray-900">
                    {template.name}
                  </h4>
                  <span
                    className={cn(
                      'text-xs px-2 py-0.5 rounded-full font-medium',
                      template.category === 'agile'
                        ? 'bg-green-100 text-green-700'
                        : template.category === 'waterfall'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-purple-100 text-purple-700'
                    )}
                  >
                    {template.category}
                  </span>
                </div>

                <p className="text-sm text-gray-800">{template.description}</p>

                <div className="pt-2">
                  <p className="text-xs font-medium text-gray-700 mb-1">
                    Included Features:
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {template.features.map((feature) => (
                      <span
                        key={feature}
                        className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded"
                      >
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-2">Template Guide</h4>
        <ul className="text-sm text-gray-800 space-y-1">
          <li>
            <strong>Agile:</strong> Best for iterative development with sprints
          </li>
          <li>
            <strong>Waterfall:</strong> Sequential phases for traditional
            projects
          </li>
          <li>
            <strong>Hybrid:</strong> Combines agile sprints with waterfall
            phases
          </li>
        </ul>
      </div>
    </div>
  );
}
