/**
 * Tests for ActivityFeed component
 */

import { render, screen } from "@testing-library/react"
import { ActivityFeed, type Activity } from "../ActivityFeed"

const mockActivities: Activity[] = [
  {
    id: "activity-1",
    type: "created",
    projectId: "project-1",
    projectName: "Test Project 1",
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5 minutes ago
  },
  {
    id: "activity-2",
    type: "generated",
    projectId: "project-2",
    projectName: "Test Project 2",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
  },
  {
    id: "activity-3",
    type: "updated",
    projectId: "project-3",
    projectName: "Test Project 3",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(), // 3 days ago
  },
  {
    id: "activity-4",
    type: "shared",
    projectId: "project-4",
    projectName: "Test Project 4",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24 * 10).toISOString(), // 10 days ago
    metadata: {
      shareId: "share-1",
    },
  },
]

describe("ActivityFeed Component", () => {
  it("renders loading state correctly", () => {
    render(<ActivityFeed activities={[]} isLoading={true} />)

    const skeletons = screen.getAllByRole("generic")
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it("renders empty state when no activities", () => {
    render(<ActivityFeed activities={[]} />)

    expect(screen.getByText("Recent Activity")).toBeInTheDocument()
    expect(screen.getByText("No recent activity. Create a project to get started!")).toBeInTheDocument()
  })

  it("renders activity list correctly", () => {
    render(<ActivityFeed activities={mockActivities} />)

    expect(screen.getByText("Test Project 1")).toBeInTheDocument()
    expect(screen.getByText("Test Project 2")).toBeInTheDocument()
    expect(screen.getByText("Test Project 3")).toBeInTheDocument()
    expect(screen.getByText("Test Project 4")).toBeInTheDocument()
  })

  it("displays correct activity text for each type", () => {
    render(<ActivityFeed activities={mockActivities} />)

    expect(screen.getByText(/You created/)).toBeInTheDocument()
    expect(screen.getByText(/You generated Excel report for/)).toBeInTheDocument()
    expect(screen.getByText(/You updated/)).toBeInTheDocument()
    expect(screen.getByText(/You shared publicly/)).toBeInTheDocument()
  })

  it("displays relative timestamps correctly", () => {
    render(<ActivityFeed activities={mockActivities} />)

    expect(screen.getByText("5m ago")).toBeInTheDocument()
    expect(screen.getByText("2h ago")).toBeInTheDocument()
    expect(screen.getByText("3d ago")).toBeInTheDocument()
  })

  it("displays absolute dates for old activities", () => {
    render(<ActivityFeed activities={mockActivities} />)

    // Activity 4 is 10 days old, should show date
    expect(screen.getByText(/Oct \d+/)).toBeInTheDocument()
  })

  it("shows View link for generated activities", () => {
    render(<ActivityFeed activities={mockActivities} />)

    const viewLinks = screen.getAllByText("View")
    expect(viewLinks).toHaveLength(1) // Only one generated activity
  })

  it("shows Public badge for shared activities", () => {
    render(<ActivityFeed activities={mockActivities} />)

    const publicBadges = screen.getAllByText("Public")
    expect(publicBadges).toHaveLength(1) // Only one shared activity
  })

  it("limits activities to maxItems", () => {
    const manyActivities = Array.from({ length: 15 }, (_, i) => ({
      id: `activity-${i}`,
      type: "created" as const,
      projectId: `project-${i}`,
      projectName: `Project ${i}`,
      timestamp: new Date().toISOString(),
    }))

    render(<ActivityFeed activities={manyActivities} maxItems={5} />)

    // Should only show 5 activities
    expect(screen.getAllByText(/You created/)).toHaveLength(5)
  })

  it("shows view all link when activities exceed maxItems", () => {
    const manyActivities = Array.from({ length: 15 }, (_, i) => ({
      id: `activity-${i}`,
      type: "created" as const,
      projectId: `project-${i}`,
      projectName: `Project ${i}`,
      timestamp: new Date().toISOString(),
    }))

    render(<ActivityFeed activities={manyActivities} maxItems={10} />)

    expect(screen.getByText("View all activity →")).toBeInTheDocument()
  })

  it("does not show view all link when activities within maxItems", () => {
    render(<ActivityFeed activities={mockActivities} maxItems={10} />)

    expect(screen.queryByText("View all activity →")).not.toBeInTheDocument()
  })

  it("applies correct icon colors for each activity type", () => {
    const { container } = render(<ActivityFeed activities={mockActivities} />)

    expect(container.querySelector(".bg-green-100")).toBeInTheDocument() // created
    expect(container.querySelector(".bg-purple-100")).toBeInTheDocument() // generated
    expect(container.querySelector(".bg-blue-100")).toBeInTheDocument() // updated
    expect(container.querySelector(".bg-orange-100")).toBeInTheDocument() // shared
  })

  it("has proper hover effects", () => {
    const { container } = render(<ActivityFeed activities={mockActivities} />)

    const activities = container.querySelectorAll(".hover\\:bg-gray-50")
    expect(activities.length).toBeGreaterThan(0)
  })

  it("renders project links correctly", () => {
    render(<ActivityFeed activities={mockActivities} />)

    const projectLinks = screen.getAllByRole("link")
    expect(projectLinks.length).toBeGreaterThan(0)

    // Check first link
    expect(projectLinks[0]).toHaveAttribute("href", "/projects/project-1")
  })

  it("handles just now timestamp", () => {
    const recentActivity: Activity = {
      id: "recent",
      type: "created",
      projectId: "project-recent",
      projectName: "Recent Project",
      timestamp: new Date(Date.now() - 100).toISOString(), // Less than 1 minute ago
    }

    render(<ActivityFeed activities={[recentActivity]} />)

    expect(screen.getByText("just now")).toBeInTheDocument()
  })
})
