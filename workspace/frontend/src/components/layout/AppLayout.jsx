import { AnimatePresence } from 'framer-motion'
import { Outlet, useLocation } from 'react-router-dom'
import CommandPalette from './CommandPalette'
import Navbar from './Navbar'
import PageShell from './PageShell'

export default function AppLayout() {
  const location = useLocation()
  return (
    <div className="flex min-h-screen flex-col bg-bg text-text-primary">
      <Navbar />
      <CommandPalette />
      <AnimatePresence mode="wait">
        <PageShell key={location.pathname}>
          <Outlet />
        </PageShell>
      </AnimatePresence>
    </div>
  )
}
