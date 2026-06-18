export default function HeroSection() {
  return (
    <section className="py-24 lg:py-32 px-6 bg-canvas">
      <div className="max-w-3xl mx-auto text-center flex flex-col items-center gap-4">
        <p className="text-xs font-mono font-semibold tracking-[0.2em] uppercase text-accent">
          AI Safety · Portfolio
        </p>
        <p className="text-lg text-text-secondary max-w-xl leading-relaxed">
          End-to-end projects in AI safety engineering — fine-tuned classifiers that match
          Llama Guard 3 at 80× lower latency, structured red-teaming across 13 strategies
          and 3 models, and a randomised controlled trial measuring human review uplift.
        </p>
      </div>
    </section>
  )
}
