/**
 * Table component for displaying notification history logs
 */

'use client';

import * as React from 'react';
import { Button } from '@/components/ui/Button';
import { Table } from '@/components/ui/Table';
import type { NotificationLog } from '@/types/notification';
import { cn } from '@/lib/utils';

interface NotificationHistoryTableProps {
  logs: NotificationLog[];
  total?: number;
  limit?: number;
  offset?: number;
  loading?: boolean;
  onPageChange?: (offset: number) => void;
}

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-800',
  sent: 'bg-blue-100 text-blue-800',
  failed: 'bg-red-100 text-red-800',
  delivered: 'bg-green-100 text-green-800',
};

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function NotificationHistoryTable({
  logs,
  total,
  limit = 20,
  offset = 0,
  loading,
  onPageChange,
}: NotificationHistoryTableProps) {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <p className="text-gray-700">Loading notification history...</p>
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="mx-auto h-12 w-12 text-gray-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">
          No Notification History
        </h3>
        <p className="mt-1 text-sm text-gray-700">
          Notification logs will appear here once notifications are sent.
        </p>
      </div>
    );
  }

  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = total ? Math.ceil(total / limit) : 1;
  const showingFrom = offset + 1;
  const showingTo = Math.min(offset + limit, total || logs.length);

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                Channel
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                Sent At
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                Details
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {log.channel}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={cn(
                      'inline-flex px-2 py-1 text-xs font-semibold rounded-full',
                      STATUS_STYLES[log.status] || STATUS_STYLES.pending
                    )}
                  >
                    {log.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                  {log.sent_at ? formatDate(log.sent_at) : '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-700">
                  {log.error_message ? (
                    <span className="text-red-600">{log.error_message}</span>
                  ) : log.delivered_at ? (
                    <span className="text-green-600">
                      Delivered at {formatDate(log.delivered_at)}
                    </span>
                  ) : (
                    '-'
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {total && total > limit && onPageChange && (
        <div className="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200 sm:px-6">
          <div className="flex-1 flex justify-between sm:hidden">
            <Button
              variant="ghost"
              onClick={() => onPageChange(Math.max(0, offset - limit))}
              disabled={offset === 0}
            >
              Previous
            </Button>
            <Button
              variant="ghost"
              onClick={() => onPageChange(offset + limit)}
              disabled={offset + limit >= total}
            >
              Next
            </Button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-800">
                Showing <span className="font-medium">{showingFrom}</span> to{' '}
                <span className="font-medium">{showingTo}</span> of{' '}
                <span className="font-medium">{total}</span> results
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <Button
                  variant="ghost"
                  onClick={() => onPageChange(Math.max(0, offset - limit))}
                  disabled={offset === 0}
                  className="rounded-l-md"
                >
                  Previous
                </Button>
                <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-800">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="ghost"
                  onClick={() => onPageChange(offset + limit)}
                  disabled={offset + limit >= total}
                  className="rounded-r-md"
                >
                  Next
                </Button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
