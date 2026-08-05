import { Badge, Card } from '../ui'
import { formatCurrency, formatPercent } from '../../utils/formatters'

export default function CalculatorResultSummary({ data, type, mode }) {
  if (!data) return null

  const Row = ({ label, value, highlight = false }) => (
    <div className={`flex items-center justify-between py-2 px-3 rounded ${highlight ? 'bg-surface-hover' : ''}`}>
      <span className="text-sm text-text-secondary">{label}</span>
      <span className="text-sm font-medium tabular-nums text-text-primary">{value}</span>
    </div>
  )

  if (type === 'historical-returns') {
    return (
      <div className="mt-6 space-y-4">
        <h3 className="text-sm font-medium uppercase tracking-wide text-text-secondary">Results</h3>
        <Card>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <Row label="Investment Date" value={data.invest_date} />
              <Row label="Invest Price" value={formatCurrency(data.invest_price)} />
              <Row label="Units Bought" value={Number(data.units_bought).toFixed(4)} />
            </div>
            <div>
              <Row label="Current Price" value={formatCurrency(data.current_price)} />
              <Row label="Current Date" value={data.current_date} />
              <Row label="Years Held" value={`${Number(data.years_held).toFixed(2)}`} />
            </div>
          </div>

          <div className="border-t border-border mt-4 pt-4 space-y-2">
            <Row label="Invested Amount" value={formatCurrency(data.invested_amount)} />
            <Row label="Current Value" value={formatCurrency(data.current_value)} highlight />
          </div>

          <div className="border-t border-border mt-4 pt-4 space-y-2">
            <Row
              label="Absolute Return"
              value={
                <span className={Number(data.absolute_return) >= 0 ? 'text-positive' : 'text-negative'}>
                  {Number(data.absolute_return) >= 0 ? '+' : ''}
                  {formatCurrency(data.absolute_return)}
                </span>
              }
            />
            <Row
              label="Return %"
              value={
                <span className={Number(data.absolute_return_pct) >= 0 ? 'text-positive' : 'text-negative'}>
                  {Number(data.absolute_return_pct) >= 0 ? '+' : ''}
                  {formatPercent(data.absolute_return_pct)}
                </span>
              }
            />
            <Row
              label="CAGR"
              value={
                <span className={Number(data.cagr_pct) >= 0 ? 'text-positive' : 'text-negative'}>
                  {Number(data.cagr_pct) >= 0 ? '+' : ''}
                  {formatPercent(data.cagr_pct)}
                </span>
              }
              highlight
            />
          </div>
        </Card>
      </div>
    )
  }

  if (type === 'sip') {
    const showXirr = mode === 'historical' && data.xirr_pct != null
    const isProjected = mode === 'projected'

    return (
      <div className="mt-6 space-y-4">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium uppercase tracking-wide text-text-secondary">Results</h3>
          <Badge tone={isProjected ? 'neutral' : 'accent'}>{isProjected ? 'Projected' : 'Historical'}</Badge>
        </div>

        <Card>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <Row label="Monthly Amount" value={formatCurrency(data.monthly_amount)} />
              {data.step_up_pct && <Row label="Annual Step-up" value={`${Number(data.step_up_pct).toFixed(2)}%`} />}
              {isProjected && <Row label="Expected Return" value={`${Number(data.annual_return_pct).toFixed(2)}%`} />}
              {isProjected && <Row label="Duration" value={`${Number(data.years).toFixed(1)} years`} />}
              {isProjected && <Row label="Months" value={data.months} />}
            </div>

            <div>
              {!isProjected && data.start_date && <Row label="Start Date" value={data.start_date} />}
              {!isProjected && data.end_date && <Row label="End Date" value={data.end_date} />}
              {!isProjected && data.current_date && <Row label="As of" value={data.current_date} />}
              {!isProjected && data.current_price && (
                <Row label="Current Price" value={formatCurrency(data.current_price)} />
              )}
            </div>
          </div>

          <div className="border-t border-border mt-4 pt-4 space-y-2">
            <Row label="Total Invested" value={formatCurrency(data.total_invested)} />
            {!isProjected && data.total_units && (
              <Row label="Total Units" value={Number(data.total_units).toFixed(4)} />
            )}
            <Row
              label={isProjected ? 'Final Value' : 'Current Value'}
              value={formatCurrency(data.final_value || data.current_value)}
              highlight
            />
          </div>

          <div className="border-t border-border mt-4 pt-4 space-y-2">
            <Row
              label="Total Return"
              value={
                <span className={Number(data.total_return) >= 0 ? 'text-positive' : 'text-negative'}>
                  {Number(data.total_return) >= 0 ? '+' : ''}
                  {formatCurrency(data.total_return)}
                </span>
              }
            />
            <Row
              label="Return %"
              value={
                <span className={Number(data.total_return_pct) >= 0 ? 'text-positive' : 'text-negative'}>
                  {Number(data.total_return_pct) >= 0 ? '+' : ''}
                  {formatPercent(data.total_return_pct)}
                </span>
              }
            />
            {showXirr && (
              <Row
                label="XIRR"
                value={
                  <span className={Number(data.xirr_pct) >= 0 ? 'text-positive' : 'text-negative'}>
                    {Number(data.xirr_pct) >= 0 ? '+' : ''}
                    {formatPercent(data.xirr_pct)}
                  </span>
                }
                highlight
              />
            )}
          </div>
        </Card>
      </div>
    )
  }

  return null
}
