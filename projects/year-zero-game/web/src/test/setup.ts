import '@testing-library/jest-dom'
import { vi, beforeAll, afterEach, afterAll } from 'vitest'
import { server } from './server'

// jsdom does not implement EventSource
class MockEventSource {
  static readonly CONNECTING = 0
  static readonly OPEN = 1
  static readonly CLOSED = 2
  onmessage: ((e: MessageEvent) => void) | null = null
  onerror: ((e: Event) => void) | null = null
  close() {}
}
vi.stubGlobal('EventSource', MockEventSource)

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
