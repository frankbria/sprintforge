/**
 * Quick actions menu component for common dashboard operations
 */

"use client"

import Link from "next/link"
import {
  Plus,
  FileSpreadsheet,
  Upload,
  Settings,
  HelpCircle,
  BookOpen,
} from "lucide-react"

interface QuickAction {
  id: string
  label: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  href?: string
  onClick?: () => void
  variant: "primary" | "secondary" | "tertiary"
}

interface QuickActionsProps {
  onGenerateExcel?: () => void
  onUploadProject?: () => void
}

export function QuickActions({
  onGenerateExcel,
  onUploadProject,
}: QuickActionsProps) {
  const actions: QuickAction[] = [
    {
      id: "new-project",
      label: "New Project",
      description: "Create a new project with the setup wizard",
      icon: Plus,
      href: "/projects/new",
      variant: "primary",
    },
    {
      id: "generate-excel",
      label: "Generate Excel",
      description: "Create Excel report from existing project",
      icon: FileSpreadsheet,
      onClick: onGenerateExcel,
      variant: "secondary",
    },
    {
      id: "upload-project",
      label: "Import Project",
      description: "Upload and import existing Excel file",
      icon: Upload,
      onClick: onUploadProject,
      variant: "tertiary",
    },
    {
      id: "documentation",
      label: "Documentation",
      description: "Learn how to use SprintForge",
      icon: BookOpen,
      href: "/docs",
      variant: "tertiary",
    },
    {
      id: "settings",
      label: "Settings",
      description: "Manage your account and preferences",
      icon: Settings,
      href: "/settings",
      variant: "tertiary",
    },
    {
      id: "help",
      label: "Get Help",
      description: "Support and troubleshooting resources",
      icon: HelpCircle,
      href: "/help",
      variant: "tertiary",
    },
  ]

  const getButtonClasses = (variant: QuickAction["variant"]) => {
    const baseClasses = "group relative flex flex-col items-start p-6 rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2"

    switch (variant) {
      case "primary":
        return `${baseClasses} bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 shadow-lg hover:shadow-xl`
      case "secondary":
        return `${baseClasses} bg-white text-gray-900 border-2 border-gray-200 hover:border-blue-500 hover:shadow-md focus:ring-blue-500`
      case "tertiary":
        return `${baseClasses} bg-gray-50 text-gray-900 hover:bg-gray-100 hover:shadow focus:ring-gray-400`
      default:
        return baseClasses
    }
  }

  const getIconClasses = (variant: QuickAction["variant"]) => {
    switch (variant) {
      case "primary":
        return "text-blue-100 group-hover:text-white"
      case "secondary":
        return "text-blue-600 group-hover:text-blue-700"
      case "tertiary":
        return "text-gray-600 group-hover:text-gray-700"
      default:
        return "text-gray-600"
    }
  }

  const renderAction = (action: QuickAction) => {
    const Icon = action.icon
    const content = (
      <>
        <div className="flex items-center space-x-3 mb-2">
          <Icon className={`h-6 w-6 ${getIconClasses(action.variant)}`} />
          <span className="text-lg font-semibold">{action.label}</span>
        </div>
        <p
          className={`text-sm ${
            action.variant === "primary"
              ? "text-blue-100"
              : "text-gray-600"
          }`}
        >
          {action.description}
        </p>
      </>
    )

    if (action.href) {
      return (
        <Link
          key={action.id}
          href={action.href}
          className={getButtonClasses(action.variant)}
        >
          {content}
        </Link>
      )
    }

    return (
      <button
        key={action.id}
        onClick={action.onClick}
        className={`${getButtonClasses(action.variant)} w-full text-left`}
        disabled={!action.onClick}
      >
        {content}
      </button>
    )
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="mb-6">
        <h2 className="text-lg font-medium text-gray-900">Quick Actions</h2>
        <p className="mt-1 text-sm text-gray-500">
          Common tasks and operations
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {actions.map((action) => renderAction(action))}
      </div>
    </div>
  )
}
