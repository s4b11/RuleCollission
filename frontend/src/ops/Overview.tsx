import { Link, useOutletContext } from 'react-router-dom'
import type { Staff } from '../components/Layout'
import { Card, Empty, PageTitle, StatusBadge, Table } from '../components/ui'
import { useLoad } from '../lib/api'
import { shortDate } from '../lib/labels'
import ReviewCard, { type Review } from './ReviewCard'

function Tile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-line bg-white p-4">
      <div className="text-2xl font-semibold">{value}</div>
      <div className="mt-1 text-xs text-muted">{label}</div>
    </div>
  )
}

export default function Overview() {
  const staff = useOutletContext<Staff>()
  const overview = useLoad('/ops/overview', 10)
  const reviews = useLoad<Review[]>('/ops/reviews', 10)
  const cases = useLoad<any[]>('/ops/cases', 10)
  if (!overview.data) return null
  const byStatus = overview.data.cases_by_status
  const waiting = (byStatus.needs_decision ?? 0) + (byStatus.needs_information ?? 0) + (byStatus.unresolved ?? 0)
  const open = (reviews.data ?? []).filter((r) => r.status === 'open')

  return (
    <>
      <PageTitle title="Overview" subtitle={`${staff.organization} · signed in as ${staff.name}`} />
      <div className="mb-6 grid grid-cols-4 gap-4">
        <Tile label={`${staff.subject_label}s on record`} value={overview.data.subjects} />
        <Tile label="Cases waiting on staff" value={waiting} />
        <Tile label="Questions for your office" value={overview.data.my_reviews} />
        <Tile label="Routes confirmed" value={byStatus.route_confirmed ?? 0} />
      </div>
      <div className="grid grid-cols-2 gap-6">
        <div>
          <h2 className="mb-3 text-sm font-semibold">Questions for your office</h2>
          <div className="space-y-3">
            {open.slice(0, 4).map((review) => (
              <ReviewCard key={review.id} review={review} showCase onDone={() => { reviews.reload(); overview.reload(); cases.reload() }} />
            ))}
            {open.length === 0 && <Card><Empty>Nothing is waiting for your office.</Empty></Card>}
          </div>
        </div>
        <Card title="Recent cases">
          <Table head={[staff.subject_label, 'Status', 'Updated']}>
            {(cases.data ?? []).slice(0, 8).map((c) => (
              <tr key={c.id}>
                <td><Link to={`/ops/cases/${c.id}`} className="font-medium text-brand hover:underline">{c.subject}</Link></td>
                <td><StatusBadge status={c.status} /></td>
                <td className="text-muted">{shortDate(c.updated_at)}</td>
              </tr>
            ))}
          </Table>
        </Card>
      </div>
    </>
  )
}
