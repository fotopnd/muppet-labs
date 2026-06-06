import '@testing-library/jest-dom'

// Stub ResizeObserver for recharts and other components
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
