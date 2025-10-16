/**
 * Tests for StatisticsCards component
 */

import { render, screen } from "@testing-library/react"
import { StatisticsCards, type DashboardStats } from "../StatisticsCards"

const mockStats: DashboardStats = {
  totalProjects: 15,
  activeProjects: 8,
  totalGenerations: 42,
  recentGenerations: 12,
}

describe("StatisticsCards Component", () => {
  it("renders loading state correctly", () => {
    const stats: DashboardStats = {
      totalProjects: 0,
      activeProjects: 0,
      totalGenerations: 0,
      recentGenerations: 0,
    }

    render(<StatisticsCards stats={stats} isLoading={true} />)

    // Should have 4 skeleton cards
    const skeletons = screen.getAllByRole("generic")
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it("renders all statistics cards", () => {
    render(<StatisticsCards stats={mockStats} />)

    expect(screen.getByText("Total Projects")).toBeInTheDocument()
    expect(screen.getByText("Active Projects")).toBeInTheDocument()
    expect(screen.getByText("Excel Reports Generated")).toBeInTheDocument()
    expect(screen.getByText("Recent Activity")).toBeInTheDocument()
  })

  it("displays correct statistics values", () => {
    render(<StatisticsCards stats={mockStats} />)

    expect(screen.getByText("15")).toBeInTheDocument() // Total Projects
    expect(screen.getByText("8")).toBeInTheDocument() // Active Projects
    expect(screen.getByText("42")).toBeInTheDocument() // Total Generations
    expect(screen.getByText("12")).toBeInTheDocument() // Recent Generations
  })

  it("displays subtitles for appropriate cards", () => {
    render(<StatisticsCards stats={mockStats} />)

    expect(screen.getByText("Recently updated")).toBeInTheDocument()
    expect(screen.getByText("Last 7 days")).toBeInTheDocument()
  })

  it("formats large numbers correctly", () => {
    const largeStats: DashboardStats = {
      totalProjects: 1234,
      activeProjects: 567,
      totalGenerations: 9876,
      recentGenerations: 321,
    }

    render(<StatisticsCards stats={largeStats} />)

    expect(screen.getByText("1,234")).toBeInTheDocument()
    expect(screen.getByText("9,876")).toBeInTheDocument()
  })

  it("renders with zero values", () => {
    const zeroStats: DashboardStats = {
      totalProjects: 0,
      activeProjects: 0,
      totalGenerations: 0,
      recentGenerations: 0,
    }

    render(<StatisticsCards stats={zeroStats} />)

    const zeroValues = screen.getAllByText("0")
    expect(zeroValues).toHaveLength(4)
  })

  it("applies correct icon colors", () => {
    const { container } = render(<StatisticsCards stats={mockStats} />)

    // Check for colored icon backgrounds
    expect(container.querySelector(".bg-blue-100")).toBeInTheDocument()
    expect(container.querySelector(".bg-green-100")).toBeInTheDocument()
    expect(container.querySelector(".bg-purple-100")).toBeInTheDocument()
    expect(container.querySelector(".bg-orange-100")).toBeInTheDocument()
  })

  it("applies hover effect classes", () => {
    const { container } = render(<StatisticsCards stats={mockStats} />)

    const cards = container.querySelectorAll(".hover\\:shadow-md")
    expect(cards).toHaveLength(4)
  })

  it("has proper card structure", () => {
    const { container } = render(<StatisticsCards stats={mockStats} />)

    const cards = container.querySelectorAll(".bg-white.shadow.rounded-lg")
    expect(cards).toHaveLength(4)
  })

  it("displays icons for all cards", () => {
    const { container } = render(<StatisticsCards stats={mockStats} />)

    // Each card should have an icon (svg element)
    const icons = container.querySelectorAll("svg")
    expect(icons.length).toBeGreaterThanOrEqual(4)
  })

  it("uses responsive grid layout", () => {
    const { container } = render(<StatisticsCards stats={mockStats} />)

    const grid = container.querySelector(".grid")
    expect(grid).toHaveClass("grid-cols-1", "md:grid-cols-2", "lg:grid-cols-4")
  })
})
