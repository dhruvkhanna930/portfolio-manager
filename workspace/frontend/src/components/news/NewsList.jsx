import { ExternalLink } from 'lucide-react'
import { EmptyState, Skeleton } from '../ui'
import { formatDate } from '../../utils/formatters'

function timeAgo(dateString) {
  if (!dateString) return 'unknown'
  const date = new Date(dateString)
  const now = new Date()
  const seconds = Math.floor((now - date) / 1000)

  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`
  return formatDate(date, { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function NewsList({ news = [], loading, error, title = 'Market News', showAsset = false }) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full rounded" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded border border-border bg-surface">
        <EmptyState
          title="News feed unavailable"
          description="The news API is not configured. Check your .env for NEWS_API_KEY and NEWS_API_PROVIDER."
        />
      </div>
    )
  }

  if (!news || news.length === 0) {
    return (
      <div className="rounded border border-border bg-surface">
        <EmptyState
          title="No news available"
          description={showAsset ? 'No recent news found for this asset.' : 'No market news available right now.'}
        />
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {news.map((article) => (
        <a
          key={article.news_id}
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="block rounded border border-border bg-surface p-3 transition-colors hover:bg-surface-hover"
        >
          <div className="flex gap-2.5">
            {article.thumbnail_url && (
              <img
                src={article.thumbnail_url}
                alt=""
                className="h-16 w-16 flex-shrink-0 rounded object-cover"
                onError={(e) => (e.currentTarget.style.display = 'none')}
              />
            )}
            <div className="min-w-0 flex-1">
              <h3 className="line-clamp-2 text-sm font-medium text-text-primary">
                {article.headline}
              </h3>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-text-secondary">
                {article.source_name && <span>{article.source_name}</span>}
                {article.published_at && <span>·</span>}
                {article.published_at && <span className="text-text-muted">{timeAgo(article.published_at)}</span>}
                {article.sentiment && (
                  <>
                    <span>·</span>
                    <span
                      className={`inline-block ${
                        article.sentiment === 'POSITIVE'
                          ? 'text-positive'
                          : article.sentiment === 'NEGATIVE'
                            ? 'text-negative'
                            : 'text-text-muted'
                      }`}
                    >
                      {article.sentiment}
                    </span>
                  </>
                )}
              </div>
            </div>
            <ExternalLink className="h-4 w-4 flex-shrink-0 text-text-muted flex-none mt-0.5" />
          </div>
        </a>
      ))}
    </div>
  )
}
