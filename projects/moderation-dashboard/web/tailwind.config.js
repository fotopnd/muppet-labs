/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background:      { DEFAULT: '#f8fafc' },   // slate-50
        surface:         { DEFAULT: '#ffffff' },   // white
        border:          { DEFAULT: '#e2e8f0' },   // slate-200
        accent:          { DEFAULT: '#2563eb' },   // blue-600
        'accent-subtle': { DEFAULT: '#eff6ff' },   // blue-50
        'text-intense':  { DEFAULT: '#0f172a' },   // slate-900
        'text-default':  { DEFAULT: '#334155' },   // slate-700
        'text-muted':    { DEFAULT: '#94a3b8' },   // slate-400
        success:         { DEFAULT: '#059669' },   // emerald-600
        warning:         { DEFAULT: '#f59e0b' },   // amber-500
        danger:          { DEFAULT: '#dc2626' },   // red-600
      },
      fontFamily: {
        interface: ['Inter', 'SF Pro Display', 'Geist Sans', 'sans-serif'],
        data: ['JetBrains Mono', 'SF Mono', 'Geist Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
