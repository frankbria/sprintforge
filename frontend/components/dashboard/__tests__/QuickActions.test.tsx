/**
 * Tests for QuickActions component
 */

import { render, screen, fireEvent } from "@testing-library/react"
import { QuickActions } from "../QuickActions"

describe("QuickActions Component", () => {
  it("renders all action cards", () => {
    render(<QuickActions />)

    expect(screen.getByText("New Project")).toBeInTheDocument()
    expect(screen.getByText("Generate Excel")).toBeInTheDocument()
    expect(screen.getByText("Import Project")).toBeInTheDocument()
    expect(screen.getByText("Documentation")).toBeInTheDocument()
    expect(screen.getByText("Settings")).toBeInTheDocument()
    expect(screen.getByText("Get Help")).toBeInTheDocument()
  })

  it("renders action descriptions", () => {
    render(<QuickActions />)

    expect(screen.getByText("Create a new project with the setup wizard")).toBeInTheDocument()
    expect(screen.getByText("Create Excel report from existing project")).toBeInTheDocument()
    expect(screen.getByText("Upload and import existing Excel file")).toBeInTheDocument()
    expect(screen.getByText("Learn how to use SprintForge")).toBeInTheDocument()
    expect(screen.getByText("Manage your account and preferences")).toBeInTheDocument()
    expect(screen.getByText("Support and troubleshooting resources")).toBeInTheDocument()
  })

  it("renders New Project as primary action", () => {
    const { container } = render(<QuickActions />)

    const primaryButton = container.querySelector(".bg-blue-600")
    expect(primaryButton).toBeInTheDocument()
    expect(primaryButton?.textContent).toContain("New Project")
  })

  it("calls onGenerateExcel when Generate Excel clicked", () => {
    const mockOnGenerate = jest.fn()
    render(<QuickActions onGenerateExcel={mockOnGenerate} />)

    const generateButton = screen.getByText("Generate Excel").closest("button")
    fireEvent.click(generateButton!)

    expect(mockOnGenerate).toHaveBeenCalledTimes(1)
  })

  it("calls onUploadProject when Import Project clicked", () => {
    const mockOnUpload = jest.fn()
    render(<QuickActions onUploadProject={mockOnUpload} />)

    const uploadButton = screen.getByText("Import Project").closest("button")
    fireEvent.click(uploadButton!)

    expect(mockOnUpload).toHaveBeenCalledTimes(1)
  })

  it("renders links for navigable actions", () => {
    render(<QuickActions />)

    const newProjectLink = screen.getByText("New Project").closest("a")
    expect(newProjectLink).toHaveAttribute("href", "/projects/new")

    const docsLink = screen.getByText("Documentation").closest("a")
    expect(docsLink).toHaveAttribute("href", "/docs")

    const settingsLink = screen.getByText("Settings").closest("a")
    expect(settingsLink).toHaveAttribute("href", "/settings")

    const helpLink = screen.getByText("Get Help").closest("a")
    expect(helpLink).toHaveAttribute("href", "/help")
  })

  it("disables buttons without callbacks", () => {
    render(<QuickActions />)

    const generateButton = screen.getByText("Generate Excel").closest("button")
    expect(generateButton).toBeDisabled()

    const uploadButton = screen.getByText("Import Project").closest("button")
    expect(uploadButton).toBeDisabled()
  })

  it("enables buttons with callbacks", () => {
    const mockOnGenerate = jest.fn()
    const mockOnUpload = jest.fn()

    render(
      <QuickActions
        onGenerateExcel={mockOnGenerate}
        onUploadProject={mockOnUpload}
      />
    )

    const generateButton = screen.getByText("Generate Excel").closest("button")
    expect(generateButton).not.toBeDisabled()

    const uploadButton = screen.getByText("Import Project").closest("button")
    expect(uploadButton).not.toBeDisabled()
  })

  it("applies correct variant styles", () => {
    const { container } = render(<QuickActions />)

    // Primary variant (blue)
    expect(container.querySelector(".bg-blue-600")).toBeInTheDocument()

    // Secondary variant (white with border)
    expect(container.querySelector(".bg-white.border-2")).toBeInTheDocument()

    // Tertiary variant (gray)
    expect(container.querySelector(".bg-gray-50")).toBeInTheDocument()
  })

  it("has proper grid layout", () => {
    const { container } = render(<QuickActions />)

    const grid = container.querySelector(".grid")
    expect(grid).toHaveClass(
      "grid-cols-1",
      "md:grid-cols-2",
      "lg:grid-cols-3"
    )
  })

  it("displays section header", () => {
    render(<QuickActions />)

    expect(screen.getByText("Quick Actions")).toBeInTheDocument()
    expect(screen.getByText("Common tasks and operations")).toBeInTheDocument()
  })

  it("renders icons for all actions", () => {
    const { container } = render(<QuickActions />)

    // Each action should have an icon (svg element)
    const icons = container.querySelectorAll("svg")
    expect(icons.length).toBeGreaterThanOrEqual(6)
  })

  it("applies hover effects to all cards", () => {
    const { container } = render(<QuickActions />)

    const cards = container.querySelectorAll(".hover\\:shadow-md, .hover\\:shadow-xl, .hover\\:shadow, .hover\\:bg-gray-100, .hover\\:border-blue-500")
    expect(cards.length).toBeGreaterThan(0)
  })

  it("has accessible focus styles", () => {
    const { container } = render(<QuickActions />)

    const focusableElements = container.querySelectorAll(".focus\\:ring-2")
    expect(focusableElements.length).toBeGreaterThanOrEqual(6)
  })

  it("renders with correct card structure", () => {
    const { container } = render(<QuickActions />)

    const cards = container.querySelectorAll("a.rounded-lg.p-6, button.rounded-lg.p-6")
    expect(cards).toHaveLength(6)
  })
})
