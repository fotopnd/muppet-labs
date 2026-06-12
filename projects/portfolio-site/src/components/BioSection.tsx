export default function BioSection() {
  return (
    <section id="about" className="py-20 px-6 lg:px-12 bg-surface-muted">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-2xl font-bold text-text-primary mb-8">About</h2>
        <p className="text-base text-text-primary leading-relaxed mb-4">
          Data engineer at Meta London with ~14 years across data engineering, analytics
          engineering, and business intelligence. Current focus: account security and
          authentication analytics on the Account Access and Recovery team. Languages: Python,
          TypeScript, Rust.
        </p>
        <p className="text-base text-text-secondary leading-relaxed">
          These projects came out of a sustained effort to build and evaluate AI safety
          infrastructure hands-on — training classifiers, running structured attack campaigns,
          and measuring the human review layer with a controlled experiment. Each one is
          end-to-end: built, instrumented, and tested.
        </p>
      </div>
    </section>
  )
}
