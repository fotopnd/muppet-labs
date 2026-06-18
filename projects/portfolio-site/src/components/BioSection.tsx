export default function BioSection() {
  return (
    <section id="about" className="py-20 px-6 lg:px-12 bg-surface-muted">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-2xl font-bold text-text-primary mb-8">About</h2>
        <p className="text-base text-text-primary leading-relaxed mb-4">
          Data engineer at Meta London with 14 years across data engineering, analytics
          engineering, and business intelligence. Current focus: account security and
          authentication analytics on the Account Access and Recovery team. Languages: Python,
          TypeScript, SQL.
        </p>
        <p className="text-base text-text-secondary leading-relaxed mb-4">
          These projects came out of a sustained effort to build and evaluate AI safety
          infrastructure hands-on — training classifiers, running structured attack campaigns,
          and measuring the human review layer with a controlled experiment. Each one is
          end-to-end: built, instrumented, and tested.
        </p>
        <p className="text-base text-text-secondary leading-relaxed mb-8">
          The AI development harness is built for fast prototyping and rapid iteration —
          role-based agent workflows, shared evaluation infrastructure, and a monorepo that lets
          a new project go from brief to running demo in a single session.
        </p>
        <div className="flex flex-col gap-2 text-sm">
          <a
            href="https://github.com/fotopnd/muppet-labs"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-accent hover:text-accent-hover transition-colors duration-150 font-medium"
          >
            GitHub →
          </a>
          <a
            href="https://www.linkedin.com/in/fotopnd"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-accent hover:text-accent-hover transition-colors duration-150 font-medium"
          >
            LinkedIn →
          </a>
          <a
            href="mailto:fotopnd@gmail.com"
            className="inline-flex items-center gap-1.5 text-text-secondary hover:text-text-primary transition-colors duration-150"
          >
            fotopnd@gmail.com
          </a>
        </div>
      </div>
    </section>
  )
}
