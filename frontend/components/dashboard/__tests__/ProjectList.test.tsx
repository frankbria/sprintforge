/**
 * Tests for ProjectList component
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { ProjectList } from "../ProjectList"
import type { ProjectResponse } from "@/types/project"

const mockProjects: ProjectResponse[] = [
  {
    id: "project-1",
    name: "Test Project 1",
    description: "Description for project 1",
    template_id: "agile-basic",
    owner_id: "user-1",
    configuration: {},
    template_version: "1.0.0",
    is_public: false,
    created_at: "2025-10-01T10:00:00Z",
    updated_at: "2025-10-05T10:00:00Z",
    last_generated_at: "2025-10-03T10:00:00Z",
  },
  {
    id: "project-2",
    name: "Test Project 2",
    description: "Description for project 2",
    template_id: "waterfall-basic",
    owner_id: "user-1",
    configuration: {},
    template_version: "1.0.0",
    is_public: true,
    created_at: "2025-10-02T10:00:00Z",
    updated_at: "2025-10-06T10:00:00Z",
  },
]

describe("ProjectList Component", () => {
  it("renders loading state correctly", () => {
    const { container } = render(<ProjectList projects={[]} total={0} isLoading={true} />)

    expect(container.querySelector(".animate-pulse")).toBeInTheDocument()
  })

  it("renders empty state when no projects", () => {
    render(<ProjectList projects={[]} total={0} />)

    expect(screen.getByText("No projects yet")).toBeInTheDocument()
    expect(screen.getByText("Get started by creating your first project.")).toBeInTheDocument()
    expect(screen.getByText("New Project")).toBeInTheDocument()
  })

  it("renders project list correctly", () => {
    render(<ProjectList projects={mockProjects} total={2} />)

    expect(screen.getByText("Test Project 1")).toBeInTheDocument()
    expect(screen.getByText("Test Project 2")).toBeInTheDocument()
    expect(screen.getByText("Description for project 1")).toBeInTheDocument()
    expect(screen.getByText("Description for project 2")).toBeInTheDocument()
  })

  it("displays public badge for public projects", () => {
    render(<ProjectList projects={mockProjects} total={2} />)

    const publicBadges = screen.getAllByText("Public")
    expect(publicBadges).toHaveLength(1)
  })

  it("calls onSearch when search input changes", async () => {
    const mockOnSearch = jest.fn()
    render(
      <ProjectList
        projects={mockProjects}
        total={2}
        onSearch={mockOnSearch}
      />
    )

    const searchInput = screen.getByPlaceholderText("Search projects...")
    fireEvent.change(searchInput, { target: { value: "test query" } })

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith("test query")
    })
  })

  it("calls onSort when sort button clicked", () => {
    const mockOnSort = jest.fn()
    render(
      <ProjectList
        projects={mockProjects}
        total={2}
        onSort={mockOnSort}
      />
    )

    const nameButton = screen.getByRole("button", { name: /Name/i })
    fireEvent.click(nameButton)

    expect(mockOnSort).toHaveBeenCalledWith("name")
  })

  it("toggles sort direction on repeated clicks", () => {
    const mockOnSort = jest.fn()
    render(
      <ProjectList
        projects={mockProjects}
        total={2}
        onSort={mockOnSort}
      />
    )

    const nameButton = screen.getByRole("button", { name: /Name/i })

    // First click - ascending
    fireEvent.click(nameButton)
    expect(mockOnSort).toHaveBeenCalledWith("name")

    // Second click - descending
    fireEvent.click(nameButton)
    expect(mockOnSort).toHaveBeenCalledWith("-name")
  })

  it("opens and closes action menu", async () => {
    const { container } = render(<ProjectList projects={mockProjects} total={2} />)

    const menuButtons = container.querySelectorAll(".inline-flex.items-center.justify-center")
    const firstMenuButton = menuButtons[0] as HTMLElement

    // Open menu
    fireEvent.click(firstMenuButton)

    await waitFor(() => {
      expect(screen.getByText("View Details")).toBeInTheDocument()
      expect(screen.getByText("Generate Excel")).toBeInTheDocument()
      expect(screen.getByText("Edit")).toBeInTheDocument()
      expect(screen.getByText("Delete")).toBeInTheDocument()
    })

    // Close menu by clicking outside
    const overlays = container.querySelectorAll(".fixed.inset-0")
    if (overlays.length > 0) {
      fireEvent.click(overlays[0])
    }

    await waitFor(() => {
      expect(screen.queryByText("View Details")).not.toBeInTheDocument()
    })
  })

  it("calls onGenerate when generate button clicked", async () => {
    const mockOnGenerate = jest.fn()
    const { container } = render(
      <ProjectList
        projects={mockProjects}
        total={2}
        onGenerate={mockOnGenerate}
      />
    )

    // Open menu
    const menuButtons = container.querySelectorAll(".inline-flex.items-center.justify-center")
    fireEvent.click(menuButtons[0] as HTMLElement)

    // Click generate
    await waitFor(() => {
      const generateButton = screen.getByText("Generate Excel")
      fireEvent.click(generateButton)
    })

    expect(mockOnGenerate).toHaveBeenCalledWith("project-1")
  })

  it("calls onDelete when delete button clicked", async () => {
    const mockOnDelete = jest.fn()
    const { container } = render(
      <ProjectList
        projects={mockProjects}
        total={2}
        onDelete={mockOnDelete}
      />
    )

    // Open menu
    const menuButtons = container.querySelectorAll(".inline-flex.items-center.justify-center")
    fireEvent.click(menuButtons[0] as HTMLElement)

    // Click delete
    await waitFor(() => {
      const deleteButton = screen.getByText("Delete")
      fireEvent.click(deleteButton)
    })

    expect(mockOnDelete).toHaveBeenCalledWith("project-1")
  })

  it("displays correct pagination info", () => {
    render(<ProjectList projects={mockProjects} total={10} />)

    expect(screen.getByText("Showing 2 of 10 projects")).toBeInTheDocument()
  })

  it("displays singular project text when total is 1", () => {
    render(<ProjectList projects={[mockProjects[0]]} total={1} />)

    expect(screen.getByText("Showing 1 of 1 project")).toBeInTheDocument()
  })

  it("formats dates correctly", () => {
    render(<ProjectList projects={mockProjects} total={2} />)

    const dateElements = screen.getAllByText(/Oct/)
    expect(dateElements.length).toBeGreaterThan(0)
  })
})
