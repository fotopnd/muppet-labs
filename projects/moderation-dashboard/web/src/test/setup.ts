import '@testing-library/jest-dom'

// jsdom doesn't implement ResizeObserver; recharts requires it
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
