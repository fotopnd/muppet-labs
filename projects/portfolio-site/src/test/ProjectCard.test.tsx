import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ProjectCard from '@/components/ProjectCard'
import type { Project } from '@/data/projects'

const baseProject: Project = {
  id: 'test-project',
  name: 'Test Project',
  tagline: 'A test tagline.',
  description: 'A test description.',
  metrics: [
    { label: 'F1 Score', value: '0.818' },
    { label: 'Precision', value: '0.792' },
  ],
  demoUrl: null,
}

describe('ProjectCard', () => {
  it('renders the project name', () => {
    render(<ProjectCard project={baseProject} />)
    expect(screen.getByRole('heading', { name: 'Test Project' })).toBeInTheDocument()
  })

  it('renders the tagline', () => {
    render(<ProjectCard project={baseProject} />)
    expect(screen.getByText('A test tagline.')).toBeInTheDocument()
  })

  it('renders all metric labels', () => {
    render(<ProjectCard project={baseProject} />)
    expect(screen.getByText('F1 Score')).toBeInTheDocument()
    expect(screen.getByText('Precision')).toBeInTheDocument()
  })

  it('shows "Demo coming soon" when demoUrl is null', () => {
    render(<ProjectCard project={baseProject} />)
    expect(screen.getByText('Demo coming soon')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /view demo/i })).not.toBeInTheDocument()
  })

  it('shows a demo link when demoUrl is set', () => {
    const project: Project = { ...baseProject, demoUrl: 'https://example.com' }
    render(<ProjectCard project={project} />)
    const link = screen.getByRole('link', { name: /view demo/i })
    expect(link).toHaveAttribute('href', 'https://example.com')
    expect(screen.queryByText('Demo coming soon')).not.toBeInTheDocument()
  })
})
