import { GET, POST } from '../../../../app/api/auth/[...nextauth]/route'

// Mock NextAuth
jest.mock('next-auth', () => {
  const mockHandler = jest.fn()
  return jest.fn(() => mockHandler)
})

// Mock auth options
jest.mock('../../../../lib/auth', () => ({
  authOptions: {
    providers: [],
    callbacks: {},
  },
}))

describe('NextAuth Route Handlers', () => {
  it('should export GET handler', () => {
    expect(GET).toBeDefined()
    expect(typeof GET).toBe('function')
  })

  it('should export POST handler', () => {
    expect(POST).toBeDefined()
    expect(typeof POST).toBe('function')
  })

  it('should use the same handler for both GET and POST', () => {
    expect(GET).toBe(POST)
  })
})