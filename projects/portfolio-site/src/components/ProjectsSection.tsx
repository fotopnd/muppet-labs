import type { Project } from '@/data/projects'
import ProjectCard from './ProjectCard'

type ProjectsSectionProps = {
  projects: Project[]
}

export default function ProjectsSection({ projects }: ProjectsSectionProps) {
  const row1 = projects.slice(0, 3)
  const row2 = projects.slice(3)

  return (
    <section id="projects" className="py-20 px-6 lg:px-12 bg-canvas">
      <h2 className="text-2xl font-bold text-text-primary mb-12 text-center">The Work</h2>
      <div className="max-w-6xl mx-auto flex flex-col gap-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {row1.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
        {row2.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="hidden lg:block" />
            {row2.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
            <div className="hidden lg:block" />
          </div>
        )}
      </div>
    </section>
  )
}
