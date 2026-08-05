import { RefreshCw } from 'lucide-react'
import { Button, showToast } from '../components/ui'
import NewsList from '../components/news/NewsList'
import { useGeneralNews, useRefreshGeneralNews } from '../hooks/useNews'
import { getApiErrorMessage } from '../utils/apiError'

export default function News() {
  const { data: news = [], isLoading, error } = useGeneralNews(30)
  const refresh = useRefreshGeneralNews(30)

  const handleRefresh = () => {
    refresh.mutate(undefined, {
      onSuccess: (data) => showToast.success(`Refreshed — ${data.length} headlines`),
      onError: (err) => showToast.error(getApiErrorMessage(err, 'Could not refresh news')),
    })
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">Market News</h1>
          <p className="mt-1 text-text-secondary">Latest financial news from Indian markets.</p>
        </div>
        <Button variant="secondary" onClick={handleRefresh} disabled={refresh.isPending}>
          <RefreshCw className={`h-4 w-4 ${refresh.isPending ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <NewsList
        news={news}
        loading={isLoading}
        error={error}
        title="Market News"
        showAsset={false}
      />
    </div>
  )
}
