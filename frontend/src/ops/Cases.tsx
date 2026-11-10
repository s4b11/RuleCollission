import { Link, useOutletContext } from 'react-router-dom'
import type { Staff } from '../components/Layout'
import { Card, PageTitle, StatusBadge, Table } from '../components/ui'
import { useLoad } from '../lib/api'
import { shortDate } from '../lib/labels'

export default function Cases() {
  const staff = useOutletContext<Staff>()
  const cases = useLoad<any[]>('/ops/cases', 10)
  return (
    <>
      <PageTitle title="Cases" subtitle="Every request the assistant or staff has opened" />
      <Card>
        <Table head={[staff.subject_label, 'Identifier', 'Case code', 'Status', 'Open questions', 'Updated']}>
          {(cases.data ?? []).map((c) => (
            <tr key={c.id}>
              <td><Link to={`/ops/cases/${c.id}`} className="font-medium text-brand hover:underline">{c.subject}</Link></td>
              <td className="font-mono text-xs">{c.identifier}</td>
              <td className="font-mono text-xs">{c.code}</td>
              <td><StatusBadge status={c.status} /></td>
              <td>{c.open_reviews || '—'}</td>
              <td className="text-muted">{shortDate(c.updated_at)}</td>
            </tr>
          ))}
        </Table>
      </Card>
    </>
  )
}
