import { Globe, MessagesSquare, Phone } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Badge, Card, Empty, PageLoader, PageTitle } from '../components/ui'
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
        {!sessions.data && <PageLoader error={sessions.error} retry={sessions.reload} />}
        {sessions.data && list.length === 0 && <Card><Empty icon={MessagesSquare}>No conversations yet. They appear here as soon as someone talks to the assistant.</Empty></Card>}
        {list.map((s) => (
          <Card key={s.id} title={s.subject || 'Not identified'} icon={s.channel === 'phone' ? Phone : Globe}
            action={
              <span className="flex flex-wrap items-center gap-2 text-xs text-muted">
                <Badge tone={s.channel === 'phone' ? 'amber' : 'blue'}>{s.channel}</Badge>
                {s.location && <span>{s.location}</span>}
                <span>{shortDate(s.started_at)}</span>
                {s.case_id && <Link to={`/ops/cases/${s.case_id}`} className="font-medium text-brand hover:underline">Open case</Link>}
              </span>
            }>
            <Transcript lines={s.transcript} />
          </Card>
        ))}
      </div>
    </>
  )
}
