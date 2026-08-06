import { FileText } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { Button } from '../ui'

/** Opens the §15.6 report template, which prints to PDF from the browser. */
export default function ReportExportButton() {
  const navigate = useNavigate()
  return (
    <Button variant="secondary" onClick={() => navigate('/report')}>
      <FileText className="h-4 w-4" />
      Report
    </Button>
  )
}
