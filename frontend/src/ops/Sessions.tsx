import { Link } from 'react-router-dom'
import { Badge, Card, Empty, PageTitle } from '../components/ui'
import { useLoad } from '../lib/api'
import { shortDate } from '../lib/labels'
import Transcript from './Transcript'

export default function Sessions() {
  const sessions = useLoad<any[]>('/ops/sessions', 15)
  const list = sessions.data ?? []
  return (
    <>
      <PageTitle title="Conversations" subtitle="Transcripts of web and phone sessions. Audio is never recorded." />
      <div className="space-y-4">
        {list.length === 0 && <Card><Empty>No conversations yet.</Empty></Card>}
        {list.map((s) => (
          <Card key={s.id} title={`${s.subject || 'Not identified'} · ${shortDate(s.started_at)}`}
            action={
              <span className="flex items-center gap-2 text-xs">
                <Badge tone={s.channel === 'phone' ? 'amber' : 'blue'}>{s.channel}</Badge>
                {s.location && <span className="text-muted">{s.location}</span>}
                {s.case_id && <Link to={`/ops/cases/${s.case_id}`} className="text-brand hover:underline">Open case</Link>}
              </span>
            }>
            <Transcript lines={s.transcript} />
          </Card>
        ))}
      </div>
    </>
  )
}
