/**
 * Full fundamentals block (§15.4).
 *
 * Every row maps to a field the provider genuinely returns — yfinance `.info`
 * for stocks, mfapi.in's meta block for funds. Rows whose value is missing are
 * dropped entirely rather than shown as "—" or filled with a plausible-looking
 * default: yfinance omits different keys per ticker, and an invented P/B is
 * worse than an absent one.
 */

import { formatCurrency, formatDate, formatNumber } from '../../utils/formatters'

function present(value) {
  return value !== null && value !== undefined && value !== '' && !Number.isNaN(value)
}

function Group({ title, rows }) {
  const visible = rows.filter((r) => present(r.value))
  if (!visible.length) return null
  return (
    <div>
      <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-text-muted">{title}</p>
      <dl>
        {visible.map((row) => (
          <div
            key={row.label}
            className="flex items-baseline justify-between gap-3 border-b border-border/50 py-2 last:border-0"
          >
            <dt className="text-sm text-text-secondary">{row.label}</dt>
            <dd className="text-right text-sm tabular-nums text-text-primary">
              {row.value}
              {row.hint && <span className="ml-1.5 text-xs text-text-muted">{row.hint}</span>}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

const num = (v, digits = 2) => (present(v) ? Number(v).toFixed(digits) : null)
const money = (v, compact = false) => (present(v) ? formatCurrency(v, { compact }) : null)

// yfinance is NOT internally consistent about percentage units, so these two
// helpers must stay separate:
//   profitMargins / returnOnEquity -> fractions (0.0661 == 6.61%)
//   dividendYield                  -> already a percentage (0.45 == 0.45%)
// Running everything through one converter reported RELIANCE's 0.45% yield as
// 45%, which looks plausible enough on a dark dashboard to go unnoticed.
const fractionAsPct = (v, digits = 2) =>
  present(v) ? `${(Number(v) * 100).toFixed(digits)}%` : null
const alreadyPct = (v, digits = 2) => (present(v) ? `${Number(v).toFixed(digits)}%` : null)

export default function FundamentalsGrid({ asset }) {
  if (!asset) return null

  if (asset.asset_type === 'STOCK') {
    const range =
      present(asset.week52_low) && present(asset.week52_high) && present(asset.current_price)
        ? Math.max(
            0,
            Math.min(
              100,
              ((Number(asset.current_price) - Number(asset.week52_low)) /
                (Number(asset.week52_high) - Number(asset.week52_low))) *
                100
            )
          )
        : null

    return (
      <div className="space-y-5">
        <div className="grid grid-cols-1 gap-x-8 gap-y-5 sm:grid-cols-2 lg:grid-cols-3">
          <Group
            title="Classification"
            rows={[
              { label: 'Exchange', value: asset.exchange },
              { label: 'Sector', value: asset.sector },
              { label: 'Industry', value: asset.industry },
              { label: 'Country', value: asset.country },
              {
                label: 'Employees',
                value: present(asset.employees) ? formatNumber(asset.employees) : null,
              },
            ]}
          />
          <Group
            title="Valuation"
            rows={[
              { label: 'Market cap', value: money(asset.market_cap, true) },
              { label: 'P/E (trailing)', value: num(asset.pe_ratio) },
              { label: 'P/E (forward)', value: num(asset.forward_pe) },
              { label: 'Price / book', value: num(asset.price_to_book) },
              { label: 'Book value', value: money(asset.book_value) },
              { label: 'EPS (trailing)', value: money(asset.eps) },
              { label: 'Dividend yield', value: alreadyPct(asset.dividend_yield) },
            ]}
          />
          <Group
            title="Performance & risk"
            rows={[
              // Labelled as the provider's own figure: this app also computes a
              // beta against NIFTY 50 on the Analytics page, over a window we
              // control. The two legitimately differ, and showing both as plain
              // "Beta" would look like one of them is wrong.
              { label: 'Beta', value: num(asset.beta), hint: 'per yfinance' },
              { label: 'Profit margin', value: fractionAsPct(asset.profit_margin) },
              { label: 'Return on equity', value: fractionAsPct(asset.return_on_equity) },
              { label: 'Debt / equity', value: num(asset.debt_to_equity) },
              { label: 'Revenue', value: money(asset.revenue, true) },
            ]}
          />
          <Group
            title="Trading range"
            rows={[
              { label: '52-week high', value: money(asset.week52_high) },
              { label: '52-week low', value: money(asset.week52_low) },
              { label: "Day's high", value: money(asset.day_high) },
              { label: "Day's low", value: money(asset.day_low) },
              {
                label: 'Volume',
                value: present(asset.volume) ? formatNumber(asset.volume) : null,
              },
              {
                label: 'Avg volume',
                value: present(asset.avg_volume) ? formatNumber(asset.avg_volume) : null,
              },
            ]}
          />
        </div>

        {range != null && (
          <div className="border-t border-border pt-4">
            <div className="mb-1.5 flex items-baseline justify-between text-xs text-text-secondary">
              <span>52-week range</span>
              <span className="tabular-nums">{range.toFixed(0)}% of the way up</span>
            </div>
            <div className="relative h-1.5 w-full rounded-full bg-surface-hover">
              <div
                className="absolute top-1/2 h-3 w-3 -translate-y-1/2 rounded-full border-2 border-bg bg-accent"
                style={{ left: `calc(${range}% - 6px)` }}
              />
            </div>
            <div className="mt-1.5 flex justify-between text-xs tabular-nums text-text-muted">
              <span>{money(asset.week52_low)}</span>
              <span>{money(asset.week52_high)}</span>
            </div>
          </div>
        )}
      </div>
    )
  }

  if (asset.asset_type === 'MUTUAL_FUND') {
    return (
      <div className="grid grid-cols-1 gap-x-8 gap-y-5 sm:grid-cols-2">
        <Group
          title="Scheme"
          rows={[
            { label: 'Fund house', value: asset.fund_house },
            { label: 'Category', value: asset.category },
            { label: 'Sub-category', value: asset.sub_category },
            { label: 'Plan', value: asset.plan_type },
            { label: 'Option', value: asset.option_type },
          ]}
        />
        <Group
          title="Details"
          rows={[
            {
              label: 'Expense ratio',
              value: present(asset.expense_ratio) ? `${num(asset.expense_ratio)}%` : null,
            },
            { label: 'AUM', value: money(asset.aum, true) },
            { label: 'Risk level', value: asset.risk_level },
            { label: 'Benchmark', value: asset.benchmark },
          ]}
        />
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-x-8 gap-y-5 sm:grid-cols-2">
      <Group
        title="Terms"
        rows={[
          { label: 'Issuer', value: asset.issuer },
          {
            label: 'Coupon rate',
            value: present(asset.coupon_rate) ? `${num(asset.coupon_rate)}%` : null,
          },
          { label: 'Face value', value: money(asset.face_value) },
          {
            label: 'Maturity date',
            value: present(asset.maturity_date) ? formatDate(asset.maturity_date) : null,
          },
        ]}
      />
      <Group
        title="Yield & rating"
        rows={[
          { label: 'Credit rating', value: asset.credit_rating },
          { label: 'Payment frequency', value: asset.payment_frequency },
          {
            label: 'Current yield',
            value: present(asset.current_yield) ? `${num(asset.current_yield)}%` : null,
          },
        ]}
      />
    </div>
  )
}
