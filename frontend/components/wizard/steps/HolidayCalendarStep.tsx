/**
 * Step 4: Holiday Calendar
 * Add holidays and import presets
 */

'use client';

import * as React from 'react';
import { UseFormReturn } from 'react-hook-form';
import { Calendar, X, Plus } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Button } from '@/components/ui/Button';
import { HOLIDAY_PRESETS } from '@/lib/wizard-constants';
import { cn } from '@/lib/utils';
import type { WizardFormData } from '@/lib/wizard-schema';

interface HolidayCalendarStepProps {
  form: UseFormReturn<WizardFormData>;
  onAddPreset: (holidays: string[]) => void;
  onRemoveHoliday: (date: string) => void;
  onAddHoliday: (date: string) => void;
}

export function HolidayCalendarStep({
  form,
  onAddPreset,
  onRemoveHoliday,
  onAddHoliday,
}: HolidayCalendarStepProps) {
  const { watch, formState: { errors } } = form;
  const holidays = watch('holidays') || [];
  const [newHoliday, setNewHoliday] = React.useState('');
  const [selectedPreset, setSelectedPreset] = React.useState<string | null>(null);

  const handleAddHoliday = () => {
    if (newHoliday) {
      onAddHoliday(newHoliday);
      setNewHoliday('');
    }
  };

  const handleImportPreset = (presetId: string) => {
    const preset = HOLIDAY_PRESETS.find((p) => p.id === presetId);
    if (preset) {
      onAddPreset(preset.holidays.map((h) => h.date));
      setSelectedPreset(presetId);
    }
  };

  return (
    <div className="space-y-6">
      {/* Holiday Presets */}
      <div className="space-y-2">
        <Label>Import Holiday Preset</Label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {HOLIDAY_PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              onClick={() => handleImportPreset(preset.id)}
              className={cn(
                'p-3 border-2 rounded-lg text-left transition-all hover:shadow-md',
                selectedPreset === preset.id
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              )}
            >
              <div className="font-medium text-gray-900">{preset.name}</div>
              <div className="text-xs text-gray-700 mt-1">
                {preset.holidays.length} holidays
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Add Custom Holiday */}
      <div className="space-y-2">
        <Label htmlFor="new_holiday">Add Custom Holiday</Label>
        <div className="flex gap-2">
          <Input
            id="new_holiday"
            type="date"
            value={newHoliday}
            onChange={(e) => setNewHoliday(e.target.value)}
            className="flex-1"
          />
          <Button
            type="button"
            onClick={handleAddHoliday}
            disabled={!newHoliday}
            size="md"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Holiday List */}
      <div className="space-y-2">
        <Label>
          Selected Holidays ({holidays.length})
        </Label>
        {holidays.length > 0 ? (
          <div className="border border-gray-200 rounded-lg p-4 max-h-[300px] overflow-y-auto">
            <div className="space-y-2">
              {holidays.sort().map((date) => {
                const preset = HOLIDAY_PRESETS.flatMap((p) => p.holidays).find(
                  (h) => h.date === date
                );
                return (
                  <div
                    key={date}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded-md"
                  >
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-gray-700" />
                      <span className="font-medium text-gray-900">
                        {new Date(date + 'T00:00:00').toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </span>
                      {preset && (
                        <span className="text-sm text-gray-700">
                          ({preset.name})
                        </span>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => onRemoveHoliday(date)}
                      className="text-red-600 hover:text-red-700 transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="border border-dashed border-gray-300 rounded-lg p-8 text-center">
            <Calendar className="h-12 w-12 text-gray-600 mx-auto mb-2" />
            <p className="text-gray-700">No holidays added yet</p>
            <p className="text-sm text-gray-600">
              Import a preset or add custom holidays
            </p>
          </div>
        )}
        {errors.holidays && (
          <p className="text-sm text-red-600">{errors.holidays.message}</p>
        )}
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-sm text-gray-800">
          <strong>Tip:</strong> Holidays are automatically excluded from sprint
          calculations. You can add country-specific presets or custom dates.
        </p>
      </div>
    </div>
  );
}
