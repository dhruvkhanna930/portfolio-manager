/**
 * On-demand portfolio report (§15.6).
 *
 * One template, printed through the browser's own PDF engine rather than a
 * canvas-rasterising library: text stays selectable and vector-sharp, charts
 * print as SVG, and there's no extra dependency to keep current. The page
 * switches the token set to the paper-white "report" theme (see theme.css) so
 * what's on screen is exactly what prints.
 *
 * Every figure is read from the same endpoints the app uses — the report is a
 * view, never a second source of numbers.
 */

import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Printer } from 'lucide-react'

import AllocationDonut from '../components/charts/AllocationDonut'
import PortfolioRadar from '../components/charts/PortfolioRadar'
import { useAllocation, usePortfolioSummary } from '../hooks/useAnalytics'
import { useHoldings } from '../hooks/useHoldings'
import { useRisk } from '../hooks/useAdvancedAnalytics'
import { useHealthScore } from '../hooks/useAdvancedAnalytics'
import { useWallet } from '../hooks/useWallet'
import { formatCurrency, formatDate, formatPercent } from '../utils/formatters'

function cleanSymbol(symbol) {
  return String(symbol ?? '').replace(/\.(NS|BO)$/, '')
}

function Metric({ label, value, hint }) {
  return (
    <div className="rounded border border-border p-3">
      <p className="text-[11px] uppercase tracking-wide text-text-secondary">{label}</p>
      <p className="mt-1 text-base font-semibold tabular-nums text-text-primary">{value}</p>
      {hint && <p className="mt-0.5 text-[10px] text-text-muted">{hint}</p>}
    </div>
  )
}

function pct(value, digits = 2) {
  return value == null ? '—' : `${(value * 100).toFixed(digits)}%`
}

function ratio(value, digits = 2) {
  return value == null ? '—' : value.toFixed(digits)
}

export default function Report() {
  const { data: summary } = usePortfolioSummary()
  const { data: holdings = [] } = useHoldings()
  const { data: sectorAllocation } = useAllocation('sector')
  const { data: typeAllocation } = useAllocation('type')
  const { data: risk } = useRisk({ scope: 'portfolio', period: '1Y' })
  const { data: health } = useHealthScore('1Y')
  const { data: wallet } = useWallet()

  // Swap the whole token set to paper-white while this page is mounted, and put
  // it back on the way out so the rest of the app is untouched.
  useEffect(() => {
    const root = document.documentElement
    const previous = root.getAttribute('data-theme')
    root.setAttribute('data-theme', 'report')
    return () => {
      if (previous) root.setAttribute('data-theme', previous)
      else root.removeAttribute('data-theme')
    }
  }, [])

  const totalCurrent = summary ? Number(summary.total_current) : 0
  const totalInvested = summary ? Number(summary.total_invested) : 0
  const totalPl = summary ? Number(summary.unrealised_pl) : 0
  const totalPlPct = summary ? Number(summary.total_pl_pct) : 0

  const rows = [...holdings]
    .map((h) => ({
      symbol: cleanSymbol(h.asset?.symbol),
      name: h.asset?.name,
      type: h.asset?.asset_type?.replace('_', ' '),
      quantity: Number(h.quantity),
      avg: Number(h.avg_buy_price),
      price: h.current_price == null ? null : Number(h.current_price),
      invested: Number(h.invested_value ?? 0),
      current: h.current_value == null ? null : Number(h.current_value),
      pl: h.profit_loss == null ? null : Number(h.profit_loss),
      plPct: h.profit_loss_pct == null ? null : Number(h.profit_loss_pct),
      weight: h.weight_pct == null ? null : Number(h.weight_pct),
    }))
    .sort((a, b) => (b.current ?? 0) - (a.current ?? 0))

  return (
    <div className="min-h-screen bg-bg text-text-primary">
      <div className="no-print sticky top-0 z-10 border-b border-border bg-surface">
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-3 px-6 py-3">
          <Link
            to="/analytics"
            className="inline-flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to analytics
          </Link>
          <button
            type="button"
            onClick={() => window.print()}
            className="inline-flex items-center gap-2 rounded bg-accent px-3.5 py-2 text-sm font-medium text-white hover:bg-accent-hover"
          >
            <Printer className="h-4 w-4" />
            Save as PDF
          </button>
        </div>
        <p className="mx-auto max-w-4xl px-6 pb-2.5 text-xs text-text-muted">
          Opens your browser&apos;s print dialog — choose &ldquo;Save as PDF&rdquo; as the
          destination. Enable &ldquo;Background graphics&rdquo; to keep the gain/loss colours.
        </p>
      </div>

      <main className="mx-auto max-w-4xl px-6 py-8">
        <header className="print-block flex items-start justify-between gap-4 border-b border-border pb-5">
          <div>
            <h1 className="text-2xl font-semibold">Portfolio Report</h1>
            <p className="mt-1 text-sm text-text-secondary">
              Generated {formatDate(new Date().toISOString().slice(0, 10))} · all figures in INR
            </p>
          </div>
          <div className="text-right">
            <p className="text-[11px] uppercase tracking-wide text-text-secondary">Total value</p>
            <p className="text-2xl font-semibold tabular-nums">{formatCurrency(totalCurrent)}</p>
          </div>
        </header>

        <section className="print-block mt-6">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-text-secondary">
            Summary
          </h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Metric label="Invested" value={formatCurrency(totalInvested)} />
            <Metric
              label="Current value"
              value={formatCurrency(totalCurrent)}
              hint={`${holdings.length} holdings`}
            />
            <Metric
              label="Unrealised P/L"
              value={`${formatCurrency(totalPl)} (${formatPercent(totalPlPct)})`}
            />
            <Metric
              label="Cash"
              value={formatCurrency(wallet?.balance ?? 0)}
              hint="Wallet balance"
            />
          </div>
          {summary?.xirr_pct != null && (
            <p className="mt-2 text-xs text-text-muted">
              XIRR (money-weighted, from your actual cashflow dates):{' '}
              <span className="tabular-nums text-text-secondary">
                {formatPercent(Number(summary.xirr_pct))}
              </span>
            </p>
          )}
        </section>

        <section className="print-block mt-7">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-text-secondary">
            Risk metrics · 1 year
          </h2>
          {risk?.sufficient_data ? (
            <>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Metric label="Volatility" value={pct(risk.volatility)} hint="Annualized" />
                <Metric label="Sharpe" value={ratio(risk.sharpe)} />
                <Metric label="Sortino" value={ratio(risk.sortino)} />
                <Metric label="Max drawdown" value={pct(risk.max_drawdown)} />
                <Metric label="Value at Risk (95%)" value={pct(risk.var_95)} hint="Daily" />
                <Metric label="Calmar" value={ratio(risk.calmar)} />
                <Metric label="Beta" value={ratio(risk.beta)} hint={`vs ${risk.benchmark_code}`} />
                <Metric label="Tracking error" value={pct(risk.tracking_error)} />
              </div>
              <p className="mt-2 text-[10px] text-text-muted">
                From {risk.observations} daily observations. Portfolio returns are time-weighted, so
                deposits and purchases don&apos;t register as performance. Risk-free rate assumed at{' '}
                {Number(risk.risk_free_rate_pct).toFixed(2)}% — an assumption, not fetched data.
              </p>
            </>
          ) : (
            <p className="text-sm text-text-secondary">
              Not enough cached price history to compute risk metrics for this period.
            </p>
          )}
        </section>

        {health && !health.insufficient_data && (
          <section className="print-block mt-7">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-text-secondary">
              Health score
            </h2>
            <div className="flex flex-wrap items-baseline gap-3">
              <span className="text-3xl font-semibold tabular-nums">{health.health_score}</span>
              <span className="text-sm text-text-secondary">/ 100 · {health.band}</span>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {Object.entries(health.components).map(([name, c]) => (
                <Metric
                  key={name}
                  label={name.replace(/_/g, ' ')}
                  value={c.score == null ? '—' : c.score.toFixed(1)}
                  hint={`weight ×${c.weight}`}
                />
              ))}
            </div>
          </section>
        )}

        <section className="print-block mt-7">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-text-secondary">
            Allocation
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <p className="mb-1 text-xs text-text-secondary">By sector</p>
              <AllocationDonut items={sectorAllocation?.items ?? []} />
            </div>
            <div>
              <p className="mb-1 text-xs text-text-secondary">By asset class</p>
              <PortfolioRadar items={typeAllocation?.items ?? []} height={240} />
            </div>
          </div>
        </section>

        <section className="mt-7">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-text-secondary">
            Holdings
          </h2>
          {/* Scrolls on a narrow screen; prints full width, where A4 has the room. */}
          <div className="-mx-6 overflow-x-auto px-6 print:mx-0 print:overflow-visible print:px-0">
          <table className="w-full min-w-[38rem] text-xs print:min-w-0">
            <thead>
              <tr className="border-b border-border text-left text-text-secondary">
                <th className="py-2 pr-3 font-medium">Asset</th>
                <th className="py-2 pr-3 text-right font-medium">Qty</th>
                <th className="py-2 pr-3 text-right font-medium">Avg cost</th>
                <th className="py-2 pr-3 text-right font-medium">Price</th>
                <th className="py-2 pr-3 text-right font-medium">Invested</th>
                <th className="py-2 pr-3 text-right font-medium">Value</th>
                <th className="py-2 pr-3 text-right font-medium">P/L</th>
                <th className="py-2 text-right font-medium">Weight</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.symbol} className="border-b border-border/60">
                  <td className="py-1.5 pr-3">
                    <span className="font-medium text-text-primary">{r.symbol}</span>
                    <span className="block text-[10px] text-text-muted">{r.name}</span>
                  </td>
                  <td className="py-1.5 pr-3 text-right tabular-nums">{r.quantity}</td>
                  <td className="py-1.5 pr-3 text-right tabular-nums">{formatCurrency(r.avg)}</td>
                  <td className="py-1.5 pr-3 text-right tabular-nums">
                    {r.price == null ? '—' : formatCurrency(r.price)}
                  </td>
                  <td className="py-1.5 pr-3 text-right tabular-nums">
                    {formatCurrency(r.invested)}
                  </td>
                  <td className="py-1.5 pr-3 text-right tabular-nums">
                    {r.current == null ? '—' : formatCurrency(r.current)}
                  </td>
                  <td
                    className={`py-1.5 pr-3 text-right tabular-nums ${
                      r.pl == null ? '' : r.pl >= 0 ? 'text-positive' : 'text-negative'
                    }`}
                  >
                    {r.pl == null ? '—' : `${formatCurrency(r.pl)} (${formatPercent(r.plPct)})`}
                  </td>
                  <td className="py-1.5 text-right tabular-nums">
                    {r.weight == null ? '—' : `${r.weight.toFixed(1)}%`}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-2 border-border font-medium">
                <td className="py-2 pr-3">Total</td>
                <td colSpan={3} />
                <td className="py-2 pr-3 text-right tabular-nums">
                  {formatCurrency(totalInvested)}
                </td>
                <td className="py-2 pr-3 text-right tabular-nums">{formatCurrency(totalCurrent)}</td>
                <td
                  className={`py-2 pr-3 text-right tabular-nums ${
                    totalPl >= 0 ? 'text-positive' : 'text-negative'
                  }`}
                >
                  {formatCurrency(totalPl)}
                </td>
                <td className="py-2 text-right tabular-nums">100%</td>
              </tr>
            </tfoot>
          </table>
          </div>
        </section>

        <footer className="print-block mt-8 border-t border-border pt-4 text-[10px] leading-relaxed text-text-muted">
          <p>
            Educational information only — not investment advice. Figures are computed from your own
            recorded transactions and cached end-of-day prices, and may be stale if the last price
            sync failed. Risk statistics describe past price behaviour and do not predict future
            returns. This report is generated on demand and is not stored or sent anywhere.
          </p>
        </footer>
      </main>
    </div>
  )
}
