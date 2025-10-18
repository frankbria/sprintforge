/**
 * Recent activity feed component showing project updates and actions
 */

"use client"

import Link from "next/link"
import {
  FileSpreadsheet,
  FolderPlus,
  Edit,
  Share2,
  Clock,
} from "lucide-react"

export type ActivityType = "created" | "updated" | "generated" | "shared"

export interface Activity {
  id: string
  type: ActivityType
  projectId: string
  projectName: string
  timestamp: string
  metadata?: {
    shareId?: string
    version?: string
  }
}

interface ActivityFeedProps {
  activities: Activity[]
  isLoading?: boolean
  maxItems?: number
}

export function ActivityFeed({
  activities,
  isLoading = false,
  maxItems = 10,
}: ActivityFeedProps) {
  const getActivityIcon = (type: ActivityType) => {
    switch (type) {
      case "created":
        return { Icon: FolderPlus, bgColor: "bg-green-100", iconColor: "text-green-600" }
      case "updated":
        return { Icon: Edit, bgColor: "bg-blue-100", iconColor: "text-blue-600" }
      case "generated":
        return { Icon: FileSpreadsheet, bgColor: "bg-purple-100", iconColor: "text-purple-600" }
      case "shared":
        return { Icon: Share2, bgColor: "bg-orange-100", iconColor: "text-orange-600" }
      default:
        return { Icon: Clock, bgColor: "bg-gray-100", iconColor: "text-gray-800" }
    }
  }

  const getActivityText = (activity: Activity) => {
    switch (activity.type) {
      case "created":
        return "created"
      case "updated":
        return "updated"
      case "generated":
        return "generated Excel report for"
      case "shared":
        return "shared publicly"
      default:
        return "interacted with"
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return "just now"
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`

    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
    })
  }

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-start space-x-3">
                <div className="flex-shrink-0 h-10 w-10 bg-gray-200 rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-100 rounded w-1/4"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const displayedActivities = activities.slice(0, maxItems)

  if (!displayedActivities.length) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h2>
        <div className="text-center py-8">
          <Clock className="mx-auto h-12 w-12 text-gray-600" />
          <p className="mt-2 text-sm text-gray-700">
            No recent activity. Create a project to get started!
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-medium text-gray-900">Recent Activity</h2>
      </div>

      <div className="divide-y divide-gray-200">
        {displayedActivities.map((activity) => {
          const { Icon, bgColor, iconColor } = getActivityIcon(activity.type)

          return (
            <div key={activity.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className={`${bgColor} rounded-full p-2`}>
                    <Icon className={`h-5 w-5 ${iconColor}`} />
                  </div>
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">
                    You {getActivityText(activity)}{" "}
                    <Link
                      href={`/projects/${activity.projectId}`}
                      className="font-medium text-blue-600 hover:text-blue-800"
                    >
                      {activity.projectName}
                    </Link>
                  </p>
                  <p className="mt-1 text-xs text-gray-700">
                    {formatTimestamp(activity.timestamp)}
                  </p>
                </div>

                {activity.type === "generated" && (
                  <div className="flex-shrink-0">
                    <Link
                      href={`/projects/${activity.projectId}`}
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                    >
                      View
                    </Link>
                  </div>
                )}

                {activity.type === "shared" && activity.metadata?.shareId && (
                  <div className="flex-shrink-0">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                      Public
                    </span>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {activities.length > maxItems && (
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
          <Link
            href="/activity"
            className="text-sm font-medium text-blue-600 hover:text-blue-800"
          >
            View all activity →
          </Link>
        </div>
      )}
    </div>
  )
}
