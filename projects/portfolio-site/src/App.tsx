import NavBar from '@/components/NavBar'
import HeroSection from '@/components/HeroSection'
import ProjectsSection from '@/components/ProjectsSection'
import BioSection from '@/components/BioSection'
import { PROJECTS } from '@/data/projects'

export default function App() {
  return (
    <>
      <NavBar />
      <main>
        <HeroSection />
        <ProjectsSection projects={PROJECTS} />
        <BioSection />
      </main>
    </>
  )
}
