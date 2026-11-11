import { useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import type { Staff } from '../components/Layout'
import { Avatar, Badge, Card, Empty, PageLoader, PageTitle, StatusBadge, Table, Tabs } from '../components/ui'
import { useLoad } from '../lib/api'
import { shortDate } from '../lib/labels'

const WAITING = ['needs_decision', 'needs_information', 'unresolved']

export default function Cases() {
  const staff = useOutletContext<Staff>()
  const cases = useLoad<any[]>('/ops/cases', 10)
  const [tab, setTab] = useState<'waiting' | 'moving' | 'all'>('all')
  const all = cases.data ?? []
  const waiting = all.filter((c) => WAITING.includes(c.status))
  const moving = all.filter((c) => c.status.startsWith('route_'))
  const shown = { all, waiting, moving }[tab]

  return (
    <>
      <PageTitle title="Cases" subtitle="Every request the assistant or staff has opened" />
      <Tabs value={tab} onChange={setTab} tabs={[
        { id: 'all', label: 'All', count: all.length },
        { id: 'waiting', label: 'Waiting on staff', count: waiting.length },
        { id: 'moving', label: 'Route found', count: moving.length },
      ]} />
      <Card flush>
        {cases.loading && <PageLoader />}
        {cases.error && !cases.data && <PageLoader error={cases.error} retry={cases.reload} />}
        {cases.data && shown.length === 0 && <Empty>No cases here.</Empty>}
        {shown.length > 0 && (
          <Table head={[staff.subject_label, 'Identifier', 'Case code', 'Status', 'Open questions', 'Updated']}>
            {shown.map((c) => (
              <tr key={c.id}>
                <td>
                  <Link to={`/ops/cases/${c.id}`} className="flex items-center gap-3 font-medium text-ink hover:text-brand">
                    <Avatar name={c.subject} size="sm" />{c.subject}
                  </Link>
                </td>
                <td className="font-mono text-xs">{c.identifier}</td>
                <td className="font-mono text-xs">{c.code}</td>
                <td><StatusBadge status={c.status} /></td>
                <td>{c.open_reviews ? <Badge tone="amber">{c.open_reviews} open</Badge> : <span className="text-muted">—</span>}</td>
                <td className="text-xs whitespace-nowrap text-muted">{shortDate(c.updated_at)}</td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </>
  )
}
