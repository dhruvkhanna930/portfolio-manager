import { cn } from '../../utils/cn'

export default function Skeleton({ className, style }) {
  return <div className={cn('animate-pulse rounded bg-surface-hover', className)} style={style} />
}
