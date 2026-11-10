import { Network } from 'lucide-react'
import CaseGraph, { type Graph } from '../components/CaseGraph'
import CaseSummary, { type Summary } from '../components/CaseSummary'
import { Card } from '../components/ui'

export default function CaseView({ view }: { view: { summary: Summary; graph: Graph } }) {
  return (
    <div className="space-y-4">
      <Card title={`Your request, ${view.summary.subject}`}><CaseSummary summary={view.summary} /></Card>
      <Card title="How the documents depend on each other" icon={Network}><CaseGraph graph={view.graph} /></Card>
    </div>
  )
}
