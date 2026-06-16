export default function HeroSection() {
  return (
    <section className="py-24 lg:py-32 px-6 bg-canvas">
      <div className="max-w-3xl mx-auto text-center flex flex-col items-center gap-4">
        <p className="text-xs font-mono font-semibold tracking-[0.2em] uppercase text-accent">
          AI Safety · Portfolio
        </p>
        <p className="text-lg text-text-secondary max-w-xl leading-relaxed">
          End-to-end projects in AI safety engineering — classifier training, structured
          red-teaming, and controlled measurement of human review.
        </p>
        <a
          href="#projects"
          className="inline-flex items-center bg-accent hover:bg-accent-hover text-text-inverse text-sm font-semibold rounded-lg px-6 py-3 mt-2 transition-colors duration-150"
        >
          See the work
        </a>
      </div>
    </section>
  )
}
