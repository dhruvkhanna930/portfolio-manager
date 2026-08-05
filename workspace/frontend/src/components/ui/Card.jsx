import { motion } from 'framer-motion'
import { cn } from '../../utils/cn'

export default function Card({ children, className, hover = false, ...props }) {
  return (
    <motion.div
      whileHover={hover ? { y: -2 } : undefined}
      transition={{ duration: 0.15 }}
      className={cn(
        'rounded border border-border bg-surface p-5 shadow-sm',
        hover && 'cursor-pointer hover:shadow-lg',
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  )
}
