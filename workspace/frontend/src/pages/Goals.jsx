/**
 * Goals page (§15 item 5, over §14.7's CRUD).
 *
 * Progress is measured against total portfolio value, and the page says so
 * plainly: goals are NOT tied to specific holdings, so two goals both read the
 * same portfolio and their progress bars are not independent buckets. Implying
 * otherwise would turn this into net-worth allocation, which §0.3 item 20 puts
 * out of scope.
 */

import { useState } from 'react'
import { Plus, Target, Trash2 } from 'lucide-react'

import { Button, Card, EmptyState, Input, Skeleton, showToast } from '../components/ui'
import { useCreateGoal, useDeleteGoal, useGoals } from '../hooks/useAdvancedAnalytics'
import { usePortfolioSummary } from '../hooks/useAnalytics'
import { getApiErrorMessage } from '../utils/apiError'
import { formatCurrency, formatDate } from '../utils/formatters'

function GoalCard({ goal, onDelete, deleting }) {
  const progress = Math.min(100, Math.max(0, Number(goal.progress_pct)))
  const reached = goal.is_reached

  return (
    <Card className="space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate font-medium text-text-primary">{goal.name}</h3>
          <p className="mt-0.5 text-sm text-text-secondary">
            {formatCurrency(goal.current_amount)} of {formatCurrency(goal.target_amount)}
            {goal.target_date && ` · by ${formatDate(goal.target_date)}`}
          </p>
        </div>
        <button
          type="button"
          onClick={() => onDelete(goal.goal_id)}
          disabled={deleting}
          aria-label={`Delete goal ${goal.name}`}
          className="shrink-0 rounded p-1.5 text-text-muted transition-colors hover:bg-surface-hover hover:text-negative"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>

      <div>
        <div className="mb-1.5 flex items-baseline justify-between">
          <span
            className={`text-2xl font-semibold tabular-nums ${
              reached ? 'text-positive' : 'text-text-primary'
            }`}
          >
            {Number(goal.progress_pct).toFixed(1)}%
          </span>
          {!reached && (
            <span className="text-xs tabular-nums text-text-muted">
              {formatCurrency(goal.remaining_amount)} to go
            </span>
          )}
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-surface-hover">
          <div
            className={`h-full rounded-full transition-[width] duration-500 ${
              reached ? 'bg-positive' : 'bg-accent'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <p className="text-xs text-text-muted">
        {reached
          ? 'Target reached.'
          : goal.required_monthly_saving
            ? `About ${formatCurrency(goal.required_monthly_saving)}/month to get there${
                goal.days_remaining != null ? ` in ${goal.days_remaining} days` : ''
              }, assuming no investment growth.`
            : 'Set a target date to see the monthly saving needed.'}
      </p>
    </Card>
  )
}

export default function Goals() {
  const { data: goals = [], isLoading } = useGoals()
  const { data: summary } = usePortfolioSummary()
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
      { name: name.trim(), target_amount: targetAmount, target_date: targetDate || null },
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

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">Goals</h1>
          <p className="mt-1 text-text-secondary">
            Savings targets tracked against your total portfolio value
            {summary && (
              <>
                {' '}
                of{' '}
                <span className="tabular-nums text-text-primary">
                  {formatCurrency(summary.total_current)}
                </span>
              </>
            )}
            .
          </p>
        </div>
        {!adding && (
          <Button onClick={() => setAdding(true)}>
            <Plus className="h-4 w-4" />
            New goal
          </Button>
        )}
      </div>

      {adding && (
        <Card>
          <form onSubmit={submit} className="space-y-4">
            <Input
              id="goal_name"
              label="Goal name"
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Home down payment"
            />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
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
              <Button type="button" variant="secondary" onClick={reset}>
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={!name.trim() || !(Number(targetAmount) > 0) || createGoal.isPending}
              >
                Add goal
              </Button>
            </div>
          </form>
        </Card>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Skeleton className="h-44 w-full rounded" />
          <Skeleton className="h-44 w-full rounded" />
        </div>
      ) : goals.length === 0 && !adding ? (
        <EmptyState
          icon={Target}
          title="No goals yet"
          description="Add a savings target and track your portfolio against it."
          action={
            <Button onClick={() => setAdding(true)}>
              <Plus className="h-4 w-4" />
              New goal
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {goals.map((goal) => (
            <GoalCard
              key={goal.goal_id}
              goal={goal}
              onDelete={remove}
              deleting={deleteGoal.isPending}
            />
          ))}
        </div>
      )}

      <p className="border-t border-border pt-4 text-xs text-text-muted">
        Every goal measures the same total portfolio value — goals aren&apos;t tied to particular
        holdings, so they aren&apos;t separate pots of money. The monthly figure is a straight
        division of what&apos;s left by the months remaining and assumes no investment growth.
      </p>
    </div>
  )
}
