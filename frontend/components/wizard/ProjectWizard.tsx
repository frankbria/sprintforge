/**
 * Main Project Wizard Component
 * Multi-step wizard for creating new projects
 */

'use client';

import * as React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, Check } from 'lucide-react';
import { useProjectWizard } from '@/hooks/useProjectWizard';
import { Button } from '@/components/ui/Button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import { WIZARD_STEPS } from '@/lib/wizard-constants';
import { cn } from '@/lib/utils';
import type { ProjectCreate } from '@/types/project';

// Step components
import { ProjectBasicsStep } from './steps/ProjectBasicsStep';
import { TemplateSelectionStep } from './steps/TemplateSelectionStep';
import { SprintConfigStep } from './steps/SprintConfigStep';
import { HolidayCalendarStep } from './steps/HolidayCalendarStep';
import { FeatureSelectionStep } from './steps/FeatureSelectionStep';
import { ReviewStep } from './steps/ReviewStep';

interface ProjectWizardProps {
  onComplete: (data: ProjectCreate) => Promise<void>;
  onCancel?: () => void;
  className?: string;
}

const variants = {
  hidden: { opacity: 0, x: 50 },
  enter: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -50 },
};

export function ProjectWizard({
  onComplete,
  onCancel,
  className,
}: ProjectWizardProps) {
  const {
    form,
    currentStep,
    totalSteps,
    isSubmitting,
    nextStep,
    prevStep,
    goToStep,
    handleSubmit,
    handleTemplateChange,
    addHolidayPreset,
    removeHoliday,
    addHoliday,
  } = useProjectWizard({ onComplete });

  const progress = (currentStep / totalSteps) * 100;

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return <ProjectBasicsStep form={form} />;
      case 2:
        return (
          <TemplateSelectionStep
            form={form}
            onTemplateChange={handleTemplateChange}
          />
        );
      case 3:
        return <SprintConfigStep form={form} />;
      case 4:
        return (
          <HolidayCalendarStep
            form={form}
            onAddPreset={addHolidayPreset}
            onRemoveHoliday={removeHoliday}
            onAddHoliday={addHoliday}
          />
        );
      case 5:
        return <FeatureSelectionStep form={form} />;
      default:
        return <ReviewStep form={form} />;
    }
  };

  const currentStepInfo = WIZARD_STEPS[currentStep - 1];

  return (
    <Card className={cn('w-full max-w-4xl mx-auto', className)}>
      <CardHeader>
        <CardTitle>Create New Project</CardTitle>
        <CardDescription>
          Follow the steps below to set up your project configuration
        </CardDescription>
        <div className="flex items-center gap-4 pt-4">
          <Progress value={progress} className="flex-1" />
          <span className="text-sm text-gray-700 whitespace-nowrap">
            Step {currentStep} of {totalSteps}
          </span>
        </div>
      </CardHeader>

      {/* Progress Steps Indicator */}
      <div className="px-6 pb-4">
        <div className="flex items-center justify-between">
          {WIZARD_STEPS.map((step, index) => (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center gap-2">
                <button
                  type="button"
                  onClick={() => goToStep(step.id)}
                  disabled={step.id > currentStep}
                  className={cn(
                    'flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all',
                    step.id === currentStep
                      ? 'border-blue-600 bg-blue-600 text-white'
                      : step.id < currentStep
                      ? 'border-blue-600 bg-blue-600 text-white cursor-pointer hover:scale-110'
                      : 'border-gray-300 bg-white text-gray-600 cursor-not-allowed opacity-50'
                  )}
                >
                  {step.id < currentStep ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <span className="text-sm font-medium">{step.id}</span>
                  )}
                </button>
                <div className="hidden md:flex flex-col items-center text-center">
                  <span
                    className={cn(
                      'text-xs font-medium',
                      step.id === currentStep
                        ? 'text-gray-900'
                        : 'text-gray-700'
                    )}
                  >
                    {step.title}
                  </span>
                  <span className="text-xs text-gray-600 max-w-[100px] truncate">
                    {step.description}
                  </span>
                </div>
              </div>
              {index < WIZARD_STEPS.length - 1 && (
                <div
                  className={cn(
                    'h-[2px] flex-1 transition-all',
                    step.id < currentStep ? 'bg-blue-600' : 'bg-gray-300'
                  )}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <CardContent className="min-h-[400px]">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              variants={variants}
              initial="hidden"
              animate="enter"
              exit="exit"
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            >
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-1">
                  {currentStepInfo?.title}
                </h3>
                <p className="text-sm text-gray-700">
                  {currentStepInfo?.description}
                </p>
              </div>
              {renderStepContent()}
            </motion.div>
          </AnimatePresence>
        </CardContent>

        <CardFooter className="flex justify-between border-t pt-6">
          <div className="flex gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={prevStep}
              disabled={currentStep === 1 || isSubmitting}
            >
              <ChevronLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            {onCancel && (
              <Button
                type="button"
                variant="ghost"
                onClick={onCancel}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            )}
          </div>
          <Button
            type={currentStep === totalSteps ? 'submit' : 'button'}
            onClick={currentStep === totalSteps ? undefined : nextStep}
            loading={isSubmitting}
            disabled={isSubmitting}
          >
            {currentStep === totalSteps ? (
              <>
                Create Project
                <Check className="h-4 w-4 ml-2" />
              </>
            ) : (
              <>
                Next
                <ChevronRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
