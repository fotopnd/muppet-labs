export default function NavBar() {
  return (
    <nav className="sticky top-0 z-50 h-14 flex items-center justify-between px-6 lg:px-12 bg-surface/95 backdrop-blur-sm border-b border-border">
      <span className="text-sm font-semibold text-text-primary">AI Safety · Projects</span>
      <div className="flex items-center gap-6">
        <a
          href="#projects"
          className="text-sm text-text-secondary hover:text-text-primary transition-colors duration-150"
        >
          Projects
        </a>
        <a
          href="#about"
          className="text-sm text-text-secondary hover:text-text-primary transition-colors duration-150"
        >
          About
        </a>
        <a
          href="https://github.com/fotopnd/muppet-labs"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-text-secondary hover:text-text-primary transition-colors duration-150"
          aria-label="GitHub"
        >
          GitHub
        </a>
      </div>
    </nav>
  )
}
