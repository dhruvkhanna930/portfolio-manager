/**
 * Recommendation model (Phase 16).
 *
 * Fills the "Recommendation Model" slot the Analytics menu previously showed as
 * "Soon". Framed per §13: educational, rule-led, every score decomposed on
 * screen rather than delivered as a verdict.
 */

import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Info, Cpu, AlertTriangle } from 'lucide-react'

import { Badge, Card, EmptyState, Select, Tabs } from '../components/ui'
import RecommendationCard from '../components/recommendations/RecommendationCard'
import RecommendationLoader from '../components/recommendations/RecommendationLoader'
import { useRecommendations } from '../hooks/useRecommendations'

const MODES = [
  { key: 'similar', label: 'Similar to yours' },
  { key: 'complementary', label: 'Diversifiers' },
  { key: 'risk_profile', label: 'By risk profile' },
]

const MODE_BLURB = {
  similar:
    'Candidates whose fundamentals sit closest to the average of what you already hold — for adding to a style you already run.',
  complementary:
    'Candidates that pull against your current concentration: sectors you hold little of, and lower beta than your portfolio average.',
  risk_profile:
    'A starting list matched to a stated risk appetite. This one needs no holdings, so it works from an empty portfolio.',
}

const RISK_PROFILES = [
  { value: 'conservative', label: 'Conservative' },
  { value: 'balanced', label: 'Balanced' },
  { value: 'assertive', label: 'Assertive' },
  { value: 'aggressive', label: 'Aggressive' },
]

function ModelBanner({ model }) {
  if (!model) return null

  const live = model.trained_models_available
  const gru = model.architecture?.gru
  const lstm = model.architecture?.lstm

  return (
    <div className="flex items-start gap-2.5 rounded border border-border bg-surface px-4 py-3">
      {live ? (
        <Cpu className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
      ) : (
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
      )}
      <div className="min-w-0 space-y-1">
        <p className="flex flex-wrap items-center gap-2 text-sm text-text-primary">
          Price model
          <Badge tone={live ? 'positive' : 'warning'}>
            {live ? 'trained network live' : 'momentum fallback'}
          </Badge>
        </p>
        <p className="text-xs text-text-secondary">
          {live ? (
            <>
              GRU 1-day ({gru?.parameters?.toLocaleString() ?? '—'} params) and LSTM 5-day (
              {lstm?.parameters?.toLocaleString() ?? '—'} params) running on{' '}
              {model.runtime ?? 'the local runtime'}, over{' '}
              {model.expected_input_shape?.join(' × ')} OHLCV windows.
            </>
          ) : (
            <>
              {model.reason}. Scores fall back to a trend estimate computed from our own
              cached price history, and the model component is dropped from the blend
              rather than filled in with a neutral placeholder.
            </>
          )}
        </p>
      </div>
    </div>
  )
}

export default function Recommendations() {
  const [mode, setMode] = useState('similar')
  const [riskProfile, setRiskProfile] = useState('balanced')

  const { data, isLoading, isFetching, isError } = useRecommendations({
    mode,
    riskProfile,
    limit: 8,
  })
  // keepPreviousData (useRecommendations.js) means switching modes refetches
  // in the background while the old ranking stays on screen -- isLoading only
  // fires once, on a session's very first request. This flags that quieter case.
  const isRefreshing = isFetching && !isLoading

  const items = data?.recommendations ?? []

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold text-text-primary">Recommendation model</h1>
          <p className="mt-1 max-w-2xl text-text-secondary">
            Candidates ranked against your own holdings using fundamentals, price trend,
            cached news tone, and a short-horizon price model.
          </p>
        </div>
        {mode === 'risk_profile' && (
          <div className="w-44">
            <Select
              id="risk_profile"
              label="Risk appetite"
              options={RISK_PROFILES}
              value={riskProfile}
              onChange={(e) => setRiskProfile(e.target.value)}
            />
          </div>
        )}
      </div>

      <div className="flex items-start gap-2.5 rounded border border-border bg-surface px-4 py-3 text-sm text-text-secondary">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
        <p>
          {data?.disclaimer ??
            'Educational information only — not investment advice. Nothing here places an order or suggests buying or selling.'}
        </p>
      </div>

      <ModelBanner model={data?.model} />

      <Tabs tabs={MODES} value={mode} onChange={setMode} />

      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-text-secondary">{MODE_BLURB[mode]}</p>
        {isRefreshing && (
          <span className="flex items-center gap-1.5 text-xs text-text-muted">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
            Updating ranking…
          </span>
        )}
      </div>

      {isError && (
        <EmptyState
          title="Couldn't build a ranking"
          description="The recommendation service didn't respond. Try again in a moment."
        />
      )}

      {isLoading && <RecommendationLoader />}

      {!isLoading && !isError && items.length === 0 && (
        <EmptyState
          title="Nothing to rank yet"
          description={
            data?.note ??
            'Add a few holdings, or switch to the risk-profile mode which works from an empty portfolio.'
          }
        />
      )}

      {!isLoading && items.length > 0 && (
        <AnimatePresence mode="wait">
          <motion.div
            key={`${mode}-${riskProfile}`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="space-y-3"
          >
            {items.map((item, index) => (
              <RecommendationCard key={item.asset_id} item={item} rank={index + 1} />
            ))}
          </motion.div>
        </AnimatePresence>
      )}

      {data && (
        <Card className="space-y-3">
          <h2 className="text-sm font-semibold text-text-primary">How this ranking was built</h2>
          <p className="text-sm text-text-secondary">
            Every candidate is scored 0–100 on four components, then blended at the weights
            below. Components without enough data are dropped and the remaining weights
            renormalized, so a stock with no news coverage isn&apos;t quietly pushed toward
            the middle.
          </p>
          <ul className="grid gap-2 sm:grid-cols-2">
            {Object.entries(data.weights ?? {}).map(([key, weight]) => (
              <li
                key={key}
                className="flex items-center justify-between rounded border border-border px-3 py-2 text-sm"
              >
                <span className="capitalize text-text-secondary">{key}</span>
                <span className="tabular-nums text-text-primary">
                  {(weight * 100).toFixed(0)}%
                </span>
              </li>
            ))}
          </ul>
          <p className="text-xs text-text-muted">
            {data.candidates_considered != null && (
              <>
                {data.candidates_considered} candidates considered
                {data.holdings_compared ? `, compared against ${data.holdings_compared} of your holdings` : ''}.{' '}
              </>
            )}
            Candidates exclude anything you already hold.
          </p>
        </Card>
      )}
    </div>
  )
}
