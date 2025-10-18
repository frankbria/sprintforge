"use client"

import { useState, useCallback } from "react"
import { useAuth } from "../../hooks/useAuth"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import Link from "next/link"
import { useRouter } from "next/navigation"
import {
  getProjects,
  deleteProject as deleteProjectAPI,
  generateExcel,
} from "@/lib/api/projects"
import { StatisticsCards, type DashboardStats } from "@/components/dashboard/StatisticsCards"
import { ProjectList } from "@/components/dashboard/ProjectList"
import { ActivityFeed, type Activity } from "@/components/dashboard/ActivityFeed"
import { QuickActions } from "@/components/dashboard/QuickActions"
import { LoadingSpinner } from "@/components/ui/LoadingSpinner"

function DashboardContent() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const queryClient = useQueryClient()
  const [searchQuery, setSearchQuery] = useState("")
  const [sortField, setSortField] = useState("-created_at")
  const [deleteError, setDeleteError] = useState<string | null>(null)

  // Fetch projects
  const {
    data: projectsData,
    isLoading: isLoadingProjects,
    error: projectsError,
  } = useQuery({
    queryKey: ["projects", searchQuery, sortField],
    queryFn: () =>
      getProjects({
        limit: 50,
        offset: 0,
        sort: sortField,
        search: searchQuery || undefined,
      }),
  })

  // Delete project mutation
  const deleteMutation = useMutation({
    mutationFn: deleteProjectAPI,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] })
      setDeleteError(null)
    },
    onError: (error: Error) => {
      setDeleteError(error.message || "Failed to delete project")
    },
  })

  // Generate Excel mutation
  const generateMutation = useMutation({
    mutationFn: async (projectId: string) => {
      const blob = await generateExcel(projectId)

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `project-${projectId}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      return projectId
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] })
    },
  })

  const handleLogout = async () => {
    try {
      await logout("/")
    } catch (error) {
      console.error("Logout failed:", error)
    }
  }

  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query)
  }, [])

  const handleSort = useCallback((field: string) => {
    setSortField(field)
  }, [])

  const handleDelete = useCallback(
    async (projectId: string) => {
      if (
        confirm(
          "Are you sure you want to delete this project? This action cannot be undone."
        )
      ) {
        await deleteMutation.mutateAsync(projectId)
      }
    },
    [deleteMutation]
  )

  const handleGenerate = useCallback(
    async (projectId: string) => {
      await generateMutation.mutateAsync(projectId)
    },
    [generateMutation]
  )

  const handleGenerateFromActions = () => {
    // Navigate to project selection or use first project
    if (projectsData && projectsData.projects.length > 0) {
      handleGenerate(projectsData.projects[0].id)
    } else {
      router.push("/projects/new")
    }
  }

  // Calculate dashboard statistics
  const stats: DashboardStats = {
    totalProjects: projectsData?.total || 0,
    activeProjects:
      projectsData?.projects.filter((p) => {
        const daysSinceUpdate = Math.floor(
          (Date.now() - new Date(p.updated_at).getTime()) / (1000 * 60 * 60 * 24)
        )
        return daysSinceUpdate <= 7
      }).length || 0,
    totalGenerations:
      projectsData?.projects.filter((p) => p.last_generated_at).length || 0,
    recentGenerations:
      projectsData?.projects.filter((p) => {
        if (!p.last_generated_at) return false
        const daysSinceGen = Math.floor(
          (Date.now() - new Date(p.last_generated_at).getTime()) /
            (1000 * 60 * 60 * 24)
        )
        return daysSinceGen <= 7
      }).length || 0,
  }

  // Generate activity feed from projects
  const activities: Activity[] = (projectsData?.projects || [])
    .flatMap((project) => {
      const items: Activity[] = []

      // Add creation activity
      items.push({
        id: `${project.id}-created`,
        type: "created",
        projectId: project.id,
        projectName: project.name,
        timestamp: project.created_at,
      })

      // Add generation activity if exists
      if (project.last_generated_at) {
        items.push({
          id: `${project.id}-generated`,
          type: "generated",
          projectId: project.id,
          projectName: project.name,
          timestamp: project.last_generated_at,
        })
      }

      // Add update activity if different from creation
      if (project.updated_at !== project.created_at) {
        items.push({
          id: `${project.id}-updated`,
          type: "updated",
          projectId: project.id,
          projectName: project.name,
          timestamp: project.updated_at,
        })
      }

      // Add share activity if public
      if (project.is_public) {
        items.push({
          id: `${project.id}-shared`,
          type: "shared",
          projectId: project.id,
          projectName: project.name,
          timestamp: project.updated_at,
        })
      }

      return items
    })
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 10)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="text-xl font-bold text-gray-900">
                SprintForge
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/projects/new"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                New Project
              </Link>
              <span className="text-sm text-gray-800">
                Welcome, {user?.name}
              </span>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-800 hover:text-gray-900 bg-transparent border border-gray-300 hover:border-gray-400 px-3 py-1 rounded-md transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 sm:px-0">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="mt-2 text-gray-800">
              Manage your projects and generate Excel reports
            </p>
          </div>

          {/* Error Messages */}
          {deleteError && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-800">{deleteError}</p>
            </div>
          )}

          {projectsError && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-800">
                Failed to load projects. Please try again.
              </p>
            </div>
          )}

          {/* Statistics Cards */}
          <div className="mb-8">
            <StatisticsCards stats={stats} isLoading={isLoadingProjects} />
          </div>

          {/* Quick Actions */}
          <div className="mb-8">
            <QuickActions
              onGenerateExcel={handleGenerateFromActions}
              onUploadProject={() => router.push("/projects/import")}
            />
          </div>

          {/* Projects and Activity Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Project List (2/3 width) */}
            <div className="lg:col-span-2">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Your Projects
              </h2>
              <ProjectList
                projects={projectsData?.projects || []}
                total={projectsData?.total || 0}
                isLoading={isLoadingProjects}
                onSearch={handleSearch}
                onSort={handleSort}
                onDelete={handleDelete}
                onGenerate={handleGenerate}
              />
            </div>

            {/* Activity Feed (1/3 width) */}
            <div className="lg:col-span-1">
              <ActivityFeed
                activities={activities}
                isLoading={isLoadingProjects}
                maxItems={8}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default function Dashboard() {
  const { isLoading, isAuthenticated, requireAuth } = useAuth()

  // Handle authentication check
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    )
  }

  if (!isAuthenticated) {
    requireAuth()
    return null
  }

  return <DashboardContent />
}
