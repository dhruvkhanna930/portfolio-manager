import EmptyState from '../components/ui/EmptyState'

export default function ComingSoon({ title }) {
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <EmptyState title={title} description="This page hasn't been built yet." />
    </div>
  )
}
