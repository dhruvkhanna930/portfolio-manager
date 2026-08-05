import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Pause, Play, Trash2 } from 'lucide-react'
import { Badge, Button, Card, showToast } from '../ui'
import { useDeleteSip, useUpdateSip } from '../../hooks/useSips'
import { formatCurrency } from '../../utils/formatters'
import { getApiErrorMessage } from '../../utils/apiError'
import SipProjectionChart from './SipProjectionChart'

export default function SipCard({ sip }) {
  const [annualReturnPct, setAnnualReturnPct] = useState('12')
  const [years, setYears] = useState('10')
  const [stepUpPct, setStepUpPct] = useState('')
  const updateSip = useUpdateSip()
  const deleteSip = useDeleteSip()

  const handleToggleActive = () => {
    updateSip.mutate(
      { sipId: sip.sip_id, payload: { is_active: !sip.is_active } },
      {
        onSuccess: () => showToast.success(sip.is_active ? 'SIP paused' : 'SIP resumed'),
        onError: (error) => showToast.error(getApiErrorMessage(error, 'Could not update SIP')),
      }
    )
  }

  const handleDelete = () => {
    if (!window.confirm(`Delete this SIP plan for ${sip.asset.name}? This cannot be undone.`)) return
    deleteSip.mutate(sip.sip_id, {
      onSuccess: () => showToast.success('SIP deleted'),
      onError: (error) => showToast.error(getApiErrorMessage(error, 'Could not delete SIP')),
    })
  }

  return (
    <Card>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Link to={`/asset/${sip.asset_id}`} className="font-medium text-text-primary hover:text-accent hover:underline">
              {sip.asset.name}
            </Link>
            <Badge tone={sip.is_active ? 'positive' : 'neutral'}>
              {sip.is_active ? 'Active' : 'Paused'}
            </Badge>
          </div>
          <p className="mt-1 text-sm text-text-secondary">
            {formatCurrency(sip.amount)} · {sip.frequency.charAt(0) + sip.frequency.slice(1).toLowerCase()} · since{' '}
            {sip.start_date}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={handleToggleActive}
            disabled={updateSip.isPending}
          >
            {sip.is_active ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {sip.is_active ? 'Pause' : 'Resume'}
          </Button>
          <Button size="sm" variant="danger" onClick={handleDelete} disabled={deleteSip.isPending}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="mb-4 grid grid-cols-3 gap-3">
        <div>
          <label className="mb-1 block text-xs text-text-secondary">Assumed Return (%/yr)</label>
          <input
            type="number"
            value={annualReturnPct}
            onChange={(e) => setAnnualReturnPct(e.target.value)}
            step="0.5"
            className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-text-secondary">Duration (years)</label>
          <input
            type="number"
            value={years}
            onChange={(e) => setYears(e.target.value)}
            step="1"
            min="1"
            className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-text-secondary">
            Step-up %/yr <span className="text-text-muted">(optional)</span>
          </label>
          <input
            type="number"
            value={stepUpPct}
            onChange={(e) => setStepUpPct(e.target.value)}
            step="1"
            min="0"
            placeholder="0"
            className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>
      </div>

      {Number(annualReturnPct) > 0 && Number(years) > 0 && (
        <SipProjectionChart
          sip={sip}
          annualReturnPct={Number(annualReturnPct)}
          years={Number(years)}
          stepUpPct={stepUpPct ? Number(stepUpPct) : null}
        />
      )}
    </Card>
  )
}
