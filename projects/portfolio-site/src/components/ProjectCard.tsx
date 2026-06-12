import type { Project } from '@/data/projects'
import MetricsTable from './MetricsTable'

type ProjectCardProps = {
  project: Project
}

export default function ProjectCard({ project }: ProjectCardProps) {
  return (
    <article className="bg-surface rounded-xl border border-border p-6 flex flex-col gap-4 transition-colors duration-150 hover:border-accent/60">
      <h3 className="text-lg font-semibold text-text-primary leading-snug">{project.name}</h3>
      <p className="text-sm text-text-secondary leading-relaxed">{project.tagline}</p>
      <MetricsTable rows={project.metrics} />
      <p className="text-sm text-text-primary leading-relaxed grow">{project.description}</p>
      <div className="pt-4 border-t border-border">
        {project.demoUrl !== null ? (
          <a
            href={project.demoUrl}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="View Demo"
            className="inline-flex items-center gap-1 text-sm font-medium text-accent hover:text-accent-hover transition-colors duration-150"
          >
            View Demo →
          </a>
        ) : (
          <span className="text-sm italic text-text-secondary">Demo coming soon</span>
        )}
      </div>
    </article>
  )
}
