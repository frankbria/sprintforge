import { render, screen } from '@testing-library/react'
import { SessionProvider } from 'next-auth/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Providers } from '../../components/providers'

// Mock the dependencies
jest.mock('next-auth/react')
jest.mock('@tanstack/react-query')

const mockSessionProvider = SessionProvider as jest.MockedFunction<typeof SessionProvider>
const mockQueryClientProvider = QueryClientProvider as jest.MockedFunction<typeof QueryClientProvider>
const mockQueryClient = QueryClient as jest.MockedClass<typeof QueryClient>

describe('Providers Component', () => {
  beforeEach(() => {
    // Mock SessionProvider to just render children
    mockSessionProvider.mockImplementation(({ children }) => <div data-testid="session-provider">{children}</div>)

    // Mock QueryClientProvider to just render children
    mockQueryClientProvider.mockImplementation(({ children }) => <div data-testid="query-provider">{children}</div>)

    // Mock QueryClient constructor
    mockQueryClient.mockImplementation(() => ({} as any))
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('should render children within providers', () => {
    const TestChild = () => <div data-testid="test-child">Test Content</div>

    render(
      <Providers>
        <TestChild />
      </Providers>
    )

    expect(screen.getByTestId('test-child')).toBeInTheDocument()
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('should wrap children with SessionProvider', () => {
    const TestChild = () => <div data-testid="test-child">Test Content</div>

    render(
      <Providers>
        <TestChild />
      </Providers>
    )

    expect(screen.getByTestId('session-provider')).toBeInTheDocument()
    expect(mockSessionProvider).toHaveBeenCalled()
  })

  it('should wrap children with QueryClientProvider', () => {
    const TestChild = () => <div data-testid="test-child">Test Content</div>

    render(
      <Providers>
        <TestChild />
      </Providers>
    )

    expect(screen.getByTestId('query-provider')).toBeInTheDocument()
    expect(mockQueryClientProvider).toHaveBeenCalled()
  })

  it('should create a QueryClient instance', () => {
    const TestChild = () => <div>Test</div>

    render(
      <Providers>
        <TestChild />
      </Providers>
    )

    expect(mockQueryClient).toHaveBeenCalled()
  })

  it('should render multiple children', () => {
    render(
      <Providers>
        <div data-testid="child-1">Child 1</div>
        <div data-testid="child-2">Child 2</div>
        <div data-testid="child-3">Child 3</div>
      </Providers>
    )

    expect(screen.getByTestId('child-1')).toBeInTheDocument()
    expect(screen.getByTestId('child-2')).toBeInTheDocument()
    expect(screen.getByTestId('child-3')).toBeInTheDocument()
  })

  it('should handle empty children', () => {
    render(<Providers></Providers>)

    // Should still render the provider structure
    expect(screen.getByTestId('session-provider')).toBeInTheDocument()
    expect(screen.getByTestId('query-provider')).toBeInTheDocument()
  })

  it('should handle React fragment as children', () => {
    render(
      <Providers>
        <>
          <div data-testid="fragment-child-1">Fragment Child 1</div>
          <div data-testid="fragment-child-2">Fragment Child 2</div>
        </>
      </Providers>
    )

    expect(screen.getByTestId('fragment-child-1')).toBeInTheDocument()
    expect(screen.getByTestId('fragment-child-2')).toBeInTheDocument()
  })

  it('should maintain provider hierarchy', () => {
    const TestChild = () => <div data-testid="test-child">Test Content</div>

    render(
      <Providers>
        <TestChild />
      </Providers>
    )

    const sessionProvider = screen.getByTestId('session-provider')
    const queryProvider = screen.getByTestId('query-provider')
    const testChild = screen.getByTestId('test-child')

    // QueryClient should wrap SessionProvider
    expect(queryProvider).toContainElement(sessionProvider)
    expect(sessionProvider).toContainElement(testChild)
  })
})