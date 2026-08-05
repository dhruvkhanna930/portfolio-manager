import { motion } from 'framer-motion'

export default function PageShell({ children }) {
  return (
    <motion.main
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.2 }}
      className="mx-auto w-full max-w-7xl flex-1 px-6 py-8"
    >
      {children}
    </motion.main>
  )
}
