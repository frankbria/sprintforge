import { Session } from 'next-auth'

// Mock session data factory
export const createMockSession = (overrides: Partial<Session> = {}): Session => ({
  user: {
    id: 'test-user-123',
    name: 'Test User',
    email: 'test@example.com',
    image: 'https://example.com/avatar.jpg',
  },
  provider: 'google',
  accessToken: 'mock-access-token',
  expires: '2024-12-31T23:59:59.999Z',
  ...overrides,
})

// Mock user data factory
export const createMockUser = (overrides: any = {}) => ({
  id: 'test-user-123',
  name: 'Test User',
  email: 'test@example.com',
  image: 'https://example.com/avatar.jpg',
  ...overrides,
})

// Mock providers data
export const mockProviders = {
  google: {
    id: 'google',
    name: 'Google',
    type: 'oauth',
    signinUrl: '/api/auth/signin/google',
    callbackUrl: '/api/auth/callback/google',
  },
  'azure-ad': {
    id: 'azure-ad',
    name: 'Azure Active Directory',
    type: 'oauth',
    signinUrl: '/api/auth/signin/azure-ad',
    callbackUrl: '/api/auth/callback/azure-ad',
  },
}

// Mock router functions
export const createMockRouter = () => ({
  push: jest.fn(),
  replace: jest.fn(),
  prefetch: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  refresh: jest.fn(),
})

// Mock search params
export const createMockSearchParams = (params: Record<string, string> = {}) => {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    searchParams.set(key, value)
  })

  // Mock the get method
  searchParams.get = jest.fn().mockImplementation((key: string) => {
    return params[key] || null
  })

  return searchParams
}

// Console spy utilities
export const suppressConsoleError = () => {
  const originalError = console.error
  beforeAll(() => {
    console.error = jest.fn()
  })
  afterAll(() => {
    console.error = originalError
  })
  return console.error as jest.MockedFunction<typeof console.error>
}

// Test wrapper utilities
export const renderWithProviders = (ui: React.ReactElement, options: any = {}) => {
  // This would typically wrap with providers but we're mocking them
  return ui
}

// Mock environment variables
export const mockEnvVars = (vars: Record<string, string>) => {
  const originalEnv = process.env
  beforeAll(() => {
    process.env = { ...originalEnv, ...vars }
  })
  afterAll(() => {
    process.env = originalEnv
  })
}

// Test data generators
export const generateTestId = () => `test-${Math.random().toString(36).substr(2, 9)}`

export const generateTestEmail = () => `test-${generateTestId()}@example.com`

export const generateTestUser = (overrides: any = {}) => ({
  id: generateTestId(),
  name: `Test User ${Math.floor(Math.random() * 1000)}`,
  email: generateTestEmail(),
  image: `https://example.com/avatar-${generateTestId()}.jpg`,
  ...overrides,
})