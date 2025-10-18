/**
 * Step 5: Feature Selection
 * Toggle advanced features
 */

'use client';

import * as React from 'react';
import { UseFormReturn } from 'react-hook-form';
import { Info, AlertTriangle } from 'lucide-react';
import { Label } from '@/components/ui/Label';
import { FEATURE_INFO } from '@/lib/wizard-constants';
import { cn } from '@/lib/utils';
import type { WizardFormData } from '@/lib/wizard-schema';

interface FeatureSelectionStepProps {
  form: UseFormReturn<WizardFormData>;
}

type FeatureKey = keyof typeof FEATURE_INFO;

export function FeatureSelectionStep({ form }: FeatureSelectionStepProps) {
  const { watch, setValue } = form;
  const features = watch('features');

  const toggleFeature = (key: FeatureKey) => {
    setValue(`features.${key}`, !features[key]);
  };

  const featureKeys = Object.keys(FEATURE_INFO) as FeatureKey[];

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Feature Selection:</strong> Enable advanced features for your
          project. Features can be enabled or disabled later in project settings.
        </p>
      </div>

      <div className="space-y-4">
        {featureKeys.map((key) => {
          const feature = FEATURE_INFO[key];
          const isEnabled = features[key];
          const hasDependencies = feature.dependencies.length > 0;
          const dependenciesMet = feature.dependencies.every(
            (dep) => features[dep as FeatureKey]
          );

          return (
            <div
              key={key}
              className={cn(
                'border-2 rounded-lg p-4 transition-all',
                isEnabled
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => toggleFeature(key)}
                      className={cn(
                        'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                        isEnabled ? 'bg-blue-600' : 'bg-gray-200'
                      )}
                    >
                      <span
                        className={cn(
                          'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                          isEnabled ? 'translate-x-6' : 'translate-x-1'
                        )}
                      />
                    </button>
                    <Label
                      className="font-medium text-gray-900 cursor-pointer"
                      onClick={() => toggleFeature(key)}
                    >
                      {feature.name}
                    </Label>
                  </div>

                  <p className="text-sm text-gray-800 mt-2 ml-14">
                    {feature.description}
                  </p>

                  {feature.warning && (
                    <div className="flex items-start gap-2 mt-2 ml-14 p-2 bg-yellow-50 border border-yellow-200 rounded">
                      <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                      <p className="text-xs text-yellow-800">
                        {feature.warning}
                      </p>
                    </div>
                  )}

                  {hasDependencies && (
                    <div className="flex items-start gap-2 mt-2 ml-14 p-2 bg-gray-50 border border-gray-200 rounded">
                      <Info className="h-4 w-4 text-gray-700 mt-0.5 flex-shrink-0" />
                      <p className="text-xs text-gray-800">
                        Requires:{' '}
                        {feature.dependencies
                          .map((dep) => FEATURE_INFO[dep as FeatureKey].name)
                          .join(', ')}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-2">Features Enabled</h4>
        <div className="flex flex-wrap gap-2">
          {featureKeys
            .filter((key) => features[key])
            .map((key) => (
              <span
                key={key}
                className="bg-blue-100 text-blue-700 text-xs font-medium px-2 py-1 rounded"
              >
                {FEATURE_INFO[key].name}
              </span>
            ))}
          {featureKeys.filter((key) => features[key]).length === 0 && (
            <span className="text-sm text-gray-700">
              No features enabled (basic configuration only)
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
