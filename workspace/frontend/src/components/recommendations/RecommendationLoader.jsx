/**
 * Loading state for the recommendation model (Phase 16).
 *
 * The first ranking of a session is genuinely slow -- ~5-6s. That's the
 * candidate universe getting fetched, fundamentals pulled and cached, and two
 * neural networks (GRU + LSTM, ~1.68M params combined) running inference per
 * candidate through services/keras_h5_runtime. A bare spinner reads as stuck;
 * this instead narrates the real pipeline stages in order, so the wait reads
 * as work happening rather than a hang. Every line names something the
 * backend is actually doing at that point -- see recommendation_service.py
 * and ml_forecast_service.py for the stages this mirrors.
 *
 * Cheap after the first load: React Query caches the ranking for 15 minutes
 * (useRecommendations.js), so this view is rare, not the common case.
 */

import { useEffect, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { TrendingUp } from 'lucide-react'

import { Card } from '../ui'

const STAGES = [
  'Pulling live prices for Nifty 50 candidates…',
  'Building 90-day OHLCV windows…',
  'Running GRU inference — 1-day forecast…',
  'Running LSTM inference — 5-day forecast…',
  'Scoring fundamentals fit against your holdings…',
  'Reading cached sector allocation…',
  'Blending fit, momentum, sentiment and ml…',
  'Ranking candidates…',
]

const STAGE_INTERVAL_MS = 1200
const BAR_COUNT = 28

// Deterministic per mount, not random on every render -- a fixed skyline that
// animates in place reads as a pulse; a skyline that reshuffles every render
// reads as noise.
function makeSkyline() {
  return Array.from({ length: BAR_COUNT }, (_, i) => {
    const wave = Math.sin(i * 0.7) * 0.5 + 0.5
    return 0.25 + wave * 0.65
  })
}

export default function RecommendationLoader() {
  const [stageIndex, setStageIndex] = useState(0)
  const [skyline] = useState(makeSkyline)
  const reduceMotion = useReducedMotion()

  useEffect(() => {
    const id = setInterval(() => {
      setStageIndex((i) => (i + 1) % STAGES.length)
    }, STAGE_INTERVAL_MS)
    return () => clearInterval(id)
  }, [])

  return (
    <Card className="space-y-5 py-8">
      <div
        className="flex h-20 items-end justify-center gap-1"
        role="img"
        aria-label="Analyzing market data"
      >
        {skyline.map((base, i) => (
          <motion.div
            key={i}
            className="w-1.5 rounded-t bg-accent/70"
            style={{ height: `${base * 100}%` }}
            animate={
              reduceMotion
                ? undefined
                : { scaleY: [1, 0.55 + (i % 3) * 0.15, 1] }
            }
            transition={{
              duration: 1.1 + (i % 5) * 0.12,
              repeat: Infinity,
              ease: 'easeInOut',
              delay: (i % 7) * 0.09,
            }}
          />
        ))}
      </div>

      <div className="flex flex-col items-center gap-2 text-center">
        <div className="flex items-center gap-2 text-accent">
          <TrendingUp className="h-4 w-4" />
          <span className="text-xs font-semibold uppercase tracking-wide">
            Making predictions
          </span>
        </div>

        <div className="h-5">
          <AnimatePresence mode="wait">
            <motion.p
              key={stageIndex}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.25 }}
              className="font-mono text-sm text-text-secondary"
            >
              {STAGES[stageIndex]}
            </motion.p>
          </AnimatePresence>
        </div>

        <p className="max-w-sm text-xs text-text-muted">
          First ranking of the session -- fundamentals and forecasts get cached for
          15 minutes after this.
        </p>
      </div>
    </Card>
  )
}
