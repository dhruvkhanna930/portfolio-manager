import { useState } from 'react'
import { Card, Tabs, showToast } from '../components/ui'
import HistoricalReturnsCalculator from '../components/calculators/HistoricalReturnsCalculator'
import SipCalculator from '../components/calculators/SipCalculator'

const CALCULATOR_TABS = [
  { key: 'historical-returns', label: 'Historical Returns' },
  { key: 'sip', label: 'SIP Calculator' },
]

export default function Calculators() {
  const [activeTab, setActiveTab] = useState('historical-returns')

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-text-primary">Investment Calculators</h1>
        <p className="mt-1 text-text-secondary">
          Explore what-if scenarios: historical returns, SIP projections, and step-up contributions.
        </p>
      </div>

      <div className="mb-6">
        <Tabs tabs={CALCULATOR_TABS} value={activeTab} onChange={setActiveTab} />
      </div>

      <Card>
        {activeTab === 'historical-returns' && <HistoricalReturnsCalculator />}
        {activeTab === 'sip' && <SipCalculator />}
      </Card>
    </div>
  )
}
