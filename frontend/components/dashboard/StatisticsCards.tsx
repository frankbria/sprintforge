/**
 * Dashboard statistics cards showing key metrics
 */

"use client"

import Link from "next/link"
import {
  FileSpreadsheet,
  FolderKanban,
  TrendingUp,
  Activity,
} from "lucide-react"

export interface DashboardStats {
  totalProjects: number
  activeProjects: number
  totalGenerations: number
  recentGenerations: number
}

interface StatisticsCardsProps {
  stats: DashboardStats
  isLoading?: boolean
}

export function StatisticsCards({ stats, isLoading = false }: StatisticsCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white overflow-hidden shadow rounded-lg animate-pulse">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-12 w-12 bg-gray-200 rounded-full"></div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <div className="h-4 bg-gray-200 rounded w-20 mb-2"></div>
                  <div className="h-8 bg-gray-200 rounded w-12"></div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  const cards = [
    {
      id: "total-projects",
      name: "Total Projects",
      value: stats.totalProjects,
      icon: FolderKanban,
      iconBgColor: "bg-blue-100",
      iconColor: "text-blue-600",
      link: null,
      linkText: null,
    },
    {
      id: "active-projects",
      name: "Active Projects",
      value: stats.activeProjects,
      icon: Activity,
      iconBgColor: "bg-green-100",
      iconColor: "text-green-600",
      link: null,
      linkText: null,
      subtitle: "Recently updated",
    },
    {
      id: "total-generations",
      name: "Excel Reports Generated",
      value: stats.totalGenerations,
      icon: FileSpreadsheet,
      iconBgColor: "bg-purple-100",
      iconColor: "text-purple-600",
      link: null,
      linkText: null,
    },
    {
      id: "recent-activity",
      name: "Recent Activity",
      value: stats.recentGenerations,
      icon: TrendingUp,
      iconBgColor: "bg-orange-100",
      iconColor: "text-orange-600",
      link: null,
      linkText: null,
      subtitle: "Last 7 days",
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card) => {
        const Icon = card.icon

        return (
          <div
            key={card.id}
            className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
          >
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div
                    className={`${card.iconBgColor} rounded-full p-3`}
                  >
                    <Icon className={`h-6 w-6 ${card.iconColor}`} />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {card.name}
                    </dt>
                    <dd className="flex items-baseline">
                      <div className="text-2xl font-semibold text-gray-900">
                        {card.value.toLocaleString()}
                      </div>
                    </dd>
                    {card.subtitle && (
                      <dd className="text-xs text-gray-500 mt-1">
                        {card.subtitle}
                      </dd>
                    )}
                  </dl>
                </div>
              </div>
            </div>

            {card.link && card.linkText && (
              <div className="bg-gray-50 px-5 py-3">
                <div className="text-sm">
                  <Link
                    href={card.link}
                    className="font-medium text-blue-600 hover:text-blue-500"
                  >
                    {card.linkText}
                  </Link>
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
