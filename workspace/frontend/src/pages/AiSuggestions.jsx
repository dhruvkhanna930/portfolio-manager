/**
 * AI Suggestions (Phase 17).
 *
 * Fills the last "Soon" row in the Analytics menu. One button, one prompt, one
 * model call -- no chat, no follow-ups.
 *
 * The page is built around showing its own work. The model is handed a fact
 * sheet computed by our own services and does no arithmetic; that fact sheet is
 * displayed underneath the prose, and every ₹/% figure in the prose is checked
 * against it server-side. Anything that doesn't reconcile is called out rather
 * than quietly rendered, because a fabricated number in a finance app is worse
 * than no number.
 */

import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  AlertTriangle,
  BadgeCheck,
  ChevronDown,
  CircleAlert,
  HelpCircle,
  Info,
  Loader2,
  Sparkles,
  TrendingUp,
} from 'lucide-react'

import { Badge, Button, Card, EmptyState, Skeleton } from '../components/ui'
import { useAiReview, useAiStatus } from '../hooks/useAiReview'
import { getApiErrorMessage } from '../utils/apiError'
import { cn } from '../utils/cn'

const SENTIMENT = {
  positive: { tone: 'positive', Icon: TrendingUp, bar: 'bg-positive' },
  concern: { tone: 'warning', Icon: CircleAlert, bar: 'bg-warning' },
  neutral: { tone: 'neutral', Icon: Info, bar: 'bg-border' },
}

function FactSheet({ facts }) {
  const [open, setOpen] = useState(false)
  const entries = Object.entries(facts ?? {})

  return (
    <Card className="space-y-3">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between text-left"
      >
        <span>
          <span className="block text-sm font-semibold text-text-primary">
            The fact sheet the model was given
          </span>
          <span className="block text-xs text-text-secondary">
            {entries.length} figures, all computed by this app — the model saw nothing else
            and calculated nothing itself.
          </span>
        </span>
        <ChevronDown
          className={cn(
            'h-4 w-4 shrink-0 text-text-muted transition-transform',
            open && 'rotate-180'
          )}
        />
      </button>

      {open && (
        <pre className="max-h-96 overflow-auto rounded border border-border bg-bg p-3 text-xs leading-relaxed text-text-secondary">
          {JSON.stringify(facts, null, 2)}
        </pre>
      )}
    </Card>
  )
}

function GroundingPanel({ unverified, note }) {
  const clean = !unverified || unverified.length === 0

  return (
    <div
      className={cn(
        'flex items-start gap-2.5 rounded border px-4 py-3',
        clean ? 'border-border bg-surface' : 'border-warning/40 bg-warning-soft'
      )}
    >
      {clean ? (
        <BadgeCheck className="mt-0.5 h-4 w-4 shrink-0 text-positive" />
      ) : (
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
      )}
      <div className="min-w-0 space-y-1">
        <p className="text-sm font-medium text-text-primary">
          {clean ? 'Every figure reconciled' : 'Some figures could not be reconciled'}
        </p>
        <p className="text-xs text-text-secondary">{note}</p>
        {!clean && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {unverified.map((figure) => (
              <span
                key={figure}
                className="rounded border border-warning/40 px-2 py-0.5 font-mono text-xs text-warning"
              >
                {figure}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function AiSuggestions() {
  const { data: status, isLoading: statusLoading } = useAiStatus()
  const { mutate, data, isPending, error, reset } = useAiReview()

  const configured = status?.configured
  const review = data?.review
  const hasRun = Boolean(data) || Boolean(error)

  function generate(force = false) {
    reset()
    mutate({ period: '1Y', force })
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0">
          <h1 className="flex items-center gap-2 text-2xl font-semibold text-text-primary">
            <Sparkles className="h-5 w-5 text-accent" />
            AI suggestions
          </h1>
          <p className="mt-1 max-w-2xl text-text-secondary">
            A language model reads the same figures the Analytics pages show and writes them
            up in plain English. It does no maths of its own — every number below comes from
            this app.
          </p>
        </div>

        {configured && (
          <Button onClick={() => generate(hasRun)} disabled={isPending}>
            {isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Writing…
              </>
            ) : hasRun ? (
              'Regenerate'
            ) : (
              'Generate review'
            )}
          </Button>
        )}
      </div>

      <div className="flex items-start gap-2.5 rounded border border-border bg-surface px-4 py-3 text-sm text-text-secondary">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
        <p>
          {status?.disclaimer ??
            'Educational commentary only — not investment advice, and no part of it is a recommendation to buy or sell anything.'}
        </p>
      </div>

      {statusLoading && <Skeleton className="h-24 w-full rounded" />}

      {!statusLoading && !configured && (
        <EmptyState
          title="Model not configured"
          description={
            status?.reason ??
            'Set GROQ_API_KEY in the backend environment to enable this page.'
          }
        />
      )}

      {error && (
        <div className="flex items-start gap-2.5 rounded border border-negative/40 bg-negative-soft px-4 py-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-negative" />
          <div>
            <p className="text-sm font-medium text-text-primary">Couldn&apos;t generate a review</p>
            <p className="text-xs text-text-secondary">{getApiErrorMessage(error)}</p>
          </div>
        </div>
      )}

      {isPending && (
        <div className="space-y-3">
          <Skeleton className="h-28 w-full rounded" />
          <Skeleton className="h-24 w-full rounded" />
          <Skeleton className="h-24 w-full rounded" />
        </div>
      )}

      {!isPending && configured && !hasRun && (
        <EmptyState
          title="Nothing generated yet"
          description="Press Generate review and the model will summarise your holdings, concentration, risk metrics and health score in a few paragraphs."
        />
      )}

      {data && data.available === false && (
        <EmptyState title="Not enough to review" description={data.reason} />
      )}

      <AnimatePresence mode="wait">
        {!isPending && review && (
          <motion.div
            key={data.generated_at}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="space-y-4"
          >
            <Card className="space-y-2 border-accent/30 bg-gradient-to-br from-accent-soft/40 to-transparent">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-semibold text-text-primary">{review.headline}</h2>
                {data.cached && (
                  <Badge tone="neutral">cached {Math.round(data.cache_age_seconds / 60)}m ago</Badge>
                )}
              </div>
              <p className="text-sm leading-relaxed text-text-secondary">{review.summary}</p>
            </Card>

            <GroundingPanel
              unverified={data.unverified_figures}
              note={data.grounding_note}
            />

            <div className="grid gap-3 md:grid-cols-2">
              {review.observations.map((observation, index) => {
                const { tone, Icon, bar } = SENTIMENT[observation.sentiment] ?? SENTIMENT.neutral
                return (
                  <Card key={index} className="relative overflow-hidden pl-5">
                    <span className={cn('absolute inset-y-0 left-0 w-1', bar)} />
                    <div className="mb-1.5 flex items-center gap-2">
                      <Icon
                        className={cn(
                          'h-4 w-4 shrink-0',
                          tone === 'positive' && 'text-positive',
                          tone === 'warning' && 'text-warning',
                          tone === 'neutral' && 'text-text-muted'
                        )}
                      />
                      <h3 className="text-sm font-semibold text-text-primary">
                        {observation.title}
                      </h3>
                    </div>
                    <p className="text-sm leading-relaxed text-text-secondary">
                      {observation.body}
                    </p>
                  </Card>
                )
              })}
            </div>

            {review.questions_to_consider.length > 0 && (
              <Card className="space-y-3">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                  <HelpCircle className="h-4 w-4 text-accent" />
                  Questions to consider
                </h3>
                <p className="text-xs text-text-muted">
                  Prompts to think about, not instructions to act on.
                </p>
                <ul className="space-y-2">
                  {review.questions_to_consider.map((question) => (
                    <li
                      key={question}
                      className="rounded border border-border px-3 py-2 text-sm text-text-secondary"
                    >
                      {question}
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            {review.blind_spots.length > 0 && (
              <Card className="space-y-2">
                <h3 className="text-sm font-semibold text-text-primary">
                  What this review can&apos;t see
                </h3>
                <ul className="space-y-1.5">
                  {review.blind_spots.map((spot) => (
                    <li key={spot} className="flex gap-2 text-sm text-text-secondary">
                      <span className="text-text-muted">—</span>
                      <span>{spot}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            <FactSheet facts={data.facts} />

            {data.usage && (
              <p className="text-xs text-text-muted">
                {data.usage.model} · {data.usage.total_tokens} tokens ·{' '}
                {data.usage.response_seconds}s · results cached for{' '}
                {Math.round((status?.cache_ttl_seconds ?? 900) / 60)} minutes unless your
                holdings change.
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
