import { useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'

import { Button, Input, Skeleton, showToast } from '../ui'
import { useCreateGoal, useDeleteGoal, useGoals } from '../../hooks/useAdvancedAnalytics'
import { getApiErrorMessage } from '../../utils/apiError'
import { formatCurrency, formatDate } from '../../utils/formatters'

function GoalRow({ goal, onDelete, deleting }) {
  const progress = Math.min(100, Math.max(0, Number(goal.progress_pct)))
  return (
    <div className="rounded border border-border bg-bg p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-medium text-text-primary">{goal.name}</p>
          <p className="text-xs text-text-secondary">
            {formatCurrency(goal.current_amount)} of {formatCurrency(goal.target_amount)}
            {goal.target_date && ` · by ${formatDate(goal.target_date)}`}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`tabular-nums text-sm ${goal.is_reached ? 'text-positive' : 'text-text-primary'}`}
          >
            {Number(goal.progress_pct).toFixed(1)}%
          </span>
          <Button size="sm" variant="danger" onClick={() => onDelete(goal.goal_id)} disabled={deleting}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-surface-hover">
        <div
          className={`h-full rounded-full ${goal.is_reached ? 'bg-positive' : 'bg-accent'}`}
          style={{ width: `${progress}%` }}
        />
      </div>

      <p className="mt-1.5 text-xs text-text-muted">
        {goal.is_reached
          ? 'Target reached.'
          : goal.required_monthly_saving
            ? `${formatCurrency(goal.remaining_amount)} to go — about ${formatCurrency(
                goal.required_monthly_saving
              )}/month to get there${goal.days_remaining != null ? ` in ${goal.days_remaining} days` : ''}.`
            : `${formatCurrency(goal.remaining_amount)} to go.`}
      </p>
    </div>
  )
}

export default function GoalsPanel() {
  const { data: goals = [], isLoading } = useGoals()
  const createGoal = useCreateGoal()
  const deleteGoal = useDeleteGoal()
  const [adding, setAdding] = useState(false)
  const [name, setName] = useState('')
  const [targetAmount, setTargetAmount] = useState('')
  const [targetDate, setTargetDate] = useState('')

  const reset = () => {
    setName('')
    setTargetAmount('')
    setTargetDate('')
    setAdding(false)
  }

  const submit = (e) => {
    e.preventDefault()
    createGoal.mutate(
      {
        name: name.trim(),
        target_amount: targetAmount,
        target_date: targetDate || null,
      },
      {
        onSuccess: () => {
          showToast.success('Goal created')
          reset()
        },
        onError: (error) => showToast.error(getApiErrorMessage(error, 'Could not create goal')),
      }
    )
  }

  const remove = (goalId) =>
    deleteGoal.mutate(goalId, {
      onSuccess: () => showToast.success('Goal deleted'),
      onError: (error) => showToast.error(getApiErrorMessage(error, 'Could not delete goal')),
    })

  if (isLoading) return <Skeleton className="h-40 w-full rounded" />

  return (
    <div className="space-y-3">
      {goals.length === 0 && !adding && (
        <p className="text-sm text-text-secondary">
          No goals yet. Add one to track progress against your portfolio value.
        </p>
      )}

      {goals.map((goal) => (
        <GoalRow key={goal.goal_id} goal={goal} onDelete={remove} deleting={deleteGoal.isPending} />
      ))}

      {adding ? (
        <form onSubmit={submit} className="space-y-3 rounded border border-border bg-bg p-3">
          <Input
            id="goal_name"
            label="Goal name"
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Home down payment"
          />
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Input
              id="goal_amount"
              label="Target amount (₹)"
              type="number"
              step="any"
              min="1"
              value={targetAmount}
              onChange={(e) => setTargetAmount(e.target.value)}
            />
            <Input
              id="goal_date"
              label="Target date (optional)"
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" size="sm" variant="secondary" onClick={reset}>
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={!name.trim() || !(Number(targetAmount) > 0) || createGoal.isPending}
            >
              Add goal
            </Button>
          </div>
        </form>
      ) : (
        <Button size="sm" variant="secondary" onClick={() => setAdding(true)}>
          <Plus className="h-4 w-4" />
          New goal
        </Button>
      )}

      <p className="text-xs text-text-muted">
        Progress is measured against your total portfolio value. Goals aren&apos;t tied to specific
        holdings, and the monthly figure assumes no investment growth.
      </p>
    </div>
  )
}
