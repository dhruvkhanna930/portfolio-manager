import { useState } from 'react'
import { Mail } from 'lucide-react'
import {
  Button,
  Card,
  Badge,
  Input,
  Select,
  Tabs,
  KpiCard,
  DataTable,
  EmptyState,
  Skeleton,
  Modal,
  showToast,
} from '../components/ui'

const MOCK_HOLDINGS = [
  { id: 1, name: 'HDFC Bank', type: 'Stock', qty: 40, value: 189000, pnl: 12500 },
  { id: 2, name: 'Axis Bluechip Fund', type: 'Mutual Fund', qty: 320.42, value: 96000, pnl: -3200 },
  { id: 3, name: 'Reliance Industries', type: 'Stock', qty: 15, value: 42750, pnl: 5400 },
  { id: 4, name: '7.1% GOI 2032', type: 'Bond', qty: 10, value: 105000, pnl: -800 },
]

const DATATABLE_COLUMNS = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'type', label: 'Type', sortable: true },
  { key: 'qty', label: 'Qty', align: 'right', sortable: true },
  { key: 'value', label: 'Value (₹)', align: 'right', sortable: true },
  { key: 'pnl', label: 'P/L (₹)', align: 'right', sortable: true, pnl: true },
]

function Section({ title, children }) {
  return (
    <section className="mb-12">
      <h2 className="mb-4 text-lg font-semibold text-text-primary">{title}</h2>
      <div className="space-y-4">{children}</div>
    </section>
  )
}

export default function Styleguide() {
  const [tab, setTab] = useState('overview')
  const [modalOpen, setModalOpen] = useState(false)
  const [tableLoading, setTableLoading] = useState(false)

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold text-text-primary">Style Guide</h1>
      <p className="mb-10 text-text-secondary">
        Every shared UI component, in its loading / empty / populated / positive / negative
        states. Mock data only — nothing here calls the API.
      </p>

      <Section title="Buttons">
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
          <Button variant="primary" disabled>
            Disabled
          </Button>
          <Button variant="primary" size="sm">
            Small
          </Button>
          <Button variant="primary" size="lg">
            Large
          </Button>
        </div>
      </Section>

      <Section title="Badges (gain / loss pills)">
        <div className="flex flex-wrap items-center gap-3">
          <Badge tone="positive">+4.32%</Badge>
          <Badge tone="negative">-2.18%</Badge>
          <Badge tone="neutral">Neutral</Badge>
          <Badge tone="warning">Stale price</Badge>
          <Badge tone="accent">New</Badge>
        </div>
      </Section>

      <Section title="Inputs & Select">
        <div className="grid max-w-xl grid-cols-1 gap-4 sm:grid-cols-2">
          <Input label="Holding name" placeholder="e.g. HDFC Bank" />
          <Input label="Email" icon={Mail} placeholder="you@example.com" />
          <Input label="Quantity" type="number" defaultValue={12} error="Must be greater than 0" />
          <Select
            label="Asset type"
            options={[
              { value: 'stock', label: 'Stock' },
              { value: 'mutual_fund', label: 'Mutual Fund' },
              { value: 'bond', label: 'Bond' },
            ]}
          />
        </div>
      </Section>

      <Section title="Tabs">
        <Tabs
          tabs={[
            { key: 'overview', label: 'Overview' },
            { key: 'holdings', label: 'Holdings' },
            { key: 'transactions', label: 'Transactions' },
          ]}
          value={tab}
          onChange={setTab}
        />
        <p className="text-sm text-text-secondary">Active tab: {tab}</p>
      </Section>

      <Section title="KPI Cards">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard label="Total Invested" value={842300} changePct={0} format="currency" />
          <KpiCard label="Current Value" value={912480} changePct={8.33} format="currency" />
          <KpiCard label="Day P/L" value={-4210} changePct={-1.24} format="currency" />
          <KpiCard label="XIRR" value={14.6} format="percent" />
          <KpiCard label="Loading example" value={0} loading />
        </div>
      </Section>

      <Section title="Cards">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Card>
            <p className="text-sm text-text-secondary">Static card</p>
            <p className="mt-1 text-text-primary">No hover animation.</p>
          </Card>
          <Card hover>
            <p className="text-sm text-text-secondary">Hover me</p>
            <p className="mt-1 text-text-primary">Lifts slightly on hover.</p>
          </Card>
        </div>
      </Section>

      <Section title="Data Table">
        <div className="mb-3 flex gap-2">
          <Button size="sm" variant="secondary" onClick={() => setTableLoading((v) => !v)}>
            Toggle loading
          </Button>
        </div>
        <DataTable columns={DATATABLE_COLUMNS} data={MOCK_HOLDINGS} loading={tableLoading} />
        <p className="mt-2 text-xs text-text-muted">Empty state (no data):</p>
        <DataTable columns={DATATABLE_COLUMNS} data={[]} />
      </Section>

      <Section title="Empty State">
        <Card>
          <EmptyState
            title="No holdings yet"
            description="Add your first stock, mutual fund, or bond to get started."
            action={<Button size="sm">Add holding</Button>}
          />
        </Card>
      </Section>

      <Section title="Skeleton">
        <div className="max-w-sm space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-24 w-full" />
        </div>
      </Section>

      <Section title="Modal">
        <Button onClick={() => setModalOpen(true)}>Open modal</Button>
        <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Confirm action">
          <p className="text-sm text-text-secondary">
            This is a demo modal with mock content — no real action wired up.
          </p>
          <div className="mt-6 flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => setModalOpen(false)}>Confirm</Button>
          </div>
        </Modal>
      </Section>

      <Section title="Toasts">
        <div className="flex flex-wrap gap-3">
          <Button variant="secondary" onClick={() => showToast.success('Holding added successfully')}>
            Success toast
          </Button>
          <Button variant="secondary" onClick={() => showToast.error('Failed to sync prices')}>
            Error toast
          </Button>
          <Button variant="secondary" onClick={() => showToast.info('Prices last synced 4 minutes ago')}>
            Info toast
          </Button>
        </div>
      </Section>
    </div>
  )
}
