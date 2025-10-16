/**
 * Project listing component with search, filters, and pagination
 */

"use client"

import { useState } from "react"
import Link from "next/link"
import { Search, Calendar, FileSpreadsheet, MoreVertical } from "lucide-react"
import type { ProjectResponse } from "@/types/project"

interface ProjectListProps {
  projects: ProjectResponse[]
  total: number
  isLoading?: boolean
  onSearch?: (query: string) => void
  onSort?: (field: string) => void
  onDelete?: (projectId: string) => void
  onGenerate?: (projectId: string) => void
}

export function ProjectList({
  projects,
  total,
  isLoading = false,
  onSearch,
  onSort,
  onDelete,
  onGenerate,
}: ProjectListProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [sortField, setSortField] = useState("-created_at")
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)

  const handleSearch = (value: string) => {
    setSearchQuery(value)
    onSearch?.(value)
  }

  const handleSort = (field: string) => {
    const newSort = sortField === field ? `-${field}` : field
    setSortField(newSort)
    onSort?.(newSort)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  const handleMenuToggle = (projectId: string) => {
    setOpenMenuId(openMenuId === projectId ? null : projectId)
  }

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-10 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!projects.length && !searchQuery) {
    return (
      <div className="bg-white shadow rounded-lg p-8 text-center">
        <FileSpreadsheet className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No projects yet</h3>
        <p className="mt-1 text-sm text-gray-500">
          Get started by creating your first project.
        </p>
        <div className="mt-6">
          <Link
            href="/projects/new"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            New Project
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white shadow rounded-lg">
      {/* Search and Filters */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search projects..."
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleSort("name")}
              className={`px-3 py-2 text-sm font-medium rounded-md ${
                sortField.includes("name")
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              Name {sortField === "name" ? "↑" : sortField === "-name" ? "↓" : ""}
            </button>
            <button
              onClick={() => handleSort("updated_at")}
              className={`px-3 py-2 text-sm font-medium rounded-md ${
                sortField.includes("updated_at")
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              Updated {sortField === "updated_at" ? "↑" : sortField === "-updated_at" ? "↓" : ""}
            </button>
          </div>
        </div>
      </div>

      {/* Project List */}
      <ul className="divide-y divide-gray-200">
        {projects.map((project) => (
          <li key={project.id} className="hover:bg-gray-50 transition-colors">
            <div className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <Link
                    href={`/projects/${project.id}`}
                    className="text-sm font-medium text-blue-600 hover:text-blue-800 truncate"
                  >
                    {project.name}
                  </Link>
                  {project.description && (
                    <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                      {project.description}
                    </p>
                  )}
                  <div className="mt-2 flex items-center text-xs text-gray-500 space-x-4">
                    <div className="flex items-center">
                      <Calendar className="h-4 w-4 mr-1" />
                      Created {formatDate(project.created_at)}
                    </div>
                    {project.last_generated_at && (
                      <div className="flex items-center">
                        <FileSpreadsheet className="h-4 w-4 mr-1" />
                        Generated {formatDate(project.last_generated_at)}
                      </div>
                    )}
                    {project.is_public && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                        Public
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions Menu */}
                <div className="ml-4 flex-shrink-0 relative">
                  <button
                    onClick={() => handleMenuToggle(project.id)}
                    className="inline-flex items-center justify-center w-8 h-8 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded-full"
                  >
                    <MoreVertical className="h-5 w-5" />
                  </button>

                  {openMenuId === project.id && (
                    <>
                      <div
                        className="fixed inset-0 z-10"
                        onClick={() => setOpenMenuId(null)}
                      />
                      <div className="absolute right-0 z-20 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5">
                        <div className="py-1" role="menu">
                          <Link
                            href={`/projects/${project.id}`}
                            className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                            onClick={() => setOpenMenuId(null)}
                          >
                            View Details
                          </Link>
                          <button
                            onClick={() => {
                              onGenerate?.(project.id)
                              setOpenMenuId(null)
                            }}
                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            Generate Excel
                          </button>
                          <Link
                            href={`/projects/${project.id}/edit`}
                            className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                            onClick={() => setOpenMenuId(null)}
                          >
                            Edit
                          </Link>
                          <button
                            onClick={() => {
                              onDelete?.(project.id)
                              setOpenMenuId(null)
                            }}
                            className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>

      {/* Pagination Info */}
      {total > 0 && (
        <div className="bg-gray-50 px-4 py-3 border-t border-gray-200">
          <div className="text-sm text-gray-700">
            Showing {projects.length} of {total} project{total !== 1 ? "s" : ""}
          </div>
        </div>
      )}
    </div>
  )
}
