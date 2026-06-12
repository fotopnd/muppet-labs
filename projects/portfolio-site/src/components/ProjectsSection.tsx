import type { Project } from '@/data/projects'
import ProjectCard from './ProjectCard'

type ProjectsSectionProps = {
  projects: Project[]
}

export default function ProjectsSection({ projects }: ProjectsSectionProps) {
  return (
    <section id="projects" className="py-20 px-6 lg:px-12 bg-canvas">
      <h2 className="text-2xl font-bold text-text-primary mb-12 text-center">The Work</h2>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {projects.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>
    </section>
  )
}
