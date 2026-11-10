import { CircleCheckBig, FolderClock, Inbox, Users } from 'lucide-react'
import { Link, useOutletContext } from 'react-router-dom'
import type { Staff } from '../components/Layout'
import { Avatar, Card, Empty, PageTitle, StatTile, StatusBadge, Table } from '../components/ui'
import { useLoad } from '../lib/api'
import { shortDate } from '../lib/labels'
import ReviewCard, { type Review } from './ReviewCard'

export default function Overview() {
  const staff = useOutletContext<Staff>()
  const overview = useLoad('/ops/overview', 10)
  const reviews = useLoad<Review[]>('/ops/reviews', 10)
  const cases = useLoad<any[]>('/ops/cases', 10)
  if (!overview.data) return null
  const byStatus = overview.data.cases_by_status
  const waiting = (byStatus.needs_decision ?? 0) + (byStatus.needs_information ?? 0) + (byStatus.unresolved ?? 0)
  const open = (reviews.data ?? []).filter((r) => r.status === 'open')
  const reload = () => { reviews.reload(); overview.reload(); cases.reload() }

  return (
    <>
      <PageTitle title={`Welcome back, ${staff.name.split(' ')[0]}`} subtitle={staff.organization} />
      <div className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatTile icon={Users} label={`${staff.subject_label}s on record`} value={overview.data.subjects} />
        <StatTile icon={FolderClock} tone="amber" label="Cases waiting on staff" value={waiting} />
        <StatTile icon={Inbox} tone="red" label="Questions for your office" value={overview.data.my_reviews} />
        <StatTile icon={CircleCheckBig} tone="green" label="Routes confirmed" value={byStatus.route_confirmed ?? 0} />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Questions for your office</h2>
            <Link to="/ops/reviews" className="text-xs font-medium text-brand hover:underline">Open inbox</Link>
          </div>
          <div className="space-y-3">
            {open.slice(0, 3).map((review) => <ReviewCard key={review.id} review={review} showCase onDone={reload} />)}
            {open.length === 0 && <Card><Empty>Nothing is waiting for your office.</Empty></Card>}
          </div>
        </div>
        <Card title="Recent cases" flush
          action={<Link to="/ops/cases" className="text-xs font-medium text-brand hover:underline">View all</Link>}>
          <Table head={[staff.subject_label, 'Status', 'Updated']}>
            {(cases.data ?? []).slice(0, 7).map((c) => (
              <tr key={c.id}>
                <td>
                  <Link to={`/ops/cases/${c.id}`} className="flex items-center gap-3 font-medium text-ink hover:text-brand">
                    <Avatar name={c.subject} size="sm" />{c.subject}
                  </Link>
                </td>
                <td><StatusBadge status={c.status} /></td>
                <td className="text-xs whitespace-nowrap text-muted">{shortDate(c.updated_at)}</td>
              </tr>
            ))}
          </Table>
        </Card>
      </div>
    </>
  )
}
