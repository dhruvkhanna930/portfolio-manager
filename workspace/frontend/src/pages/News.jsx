import NewsList from '../components/news/NewsList'
import { useGeneralNews } from '../hooks/useNews'

export default function News() {
  const { data: news = [], isLoading, error } = useGeneralNews(30)

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-text-primary">Market News</h1>
        <p className="mt-1 text-text-secondary">Latest financial news from Indian markets.</p>
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
