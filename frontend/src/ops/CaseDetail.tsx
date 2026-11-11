import { ArrowLeft, FileCheck2, FilePlus2, Gavel, MessageSquareQuote, MessagesSquare, Network, StickyNote, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import CaseGraph from '../components/CaseGraph'
import CaseSummary from '../components/CaseSummary'
import { Avatar, Button, Card, Empty, Input, PageLoader, Select, Tabs } from '../components/ui'
import { api, useLoad } from '../lib/api'
import { describeNeeds, shortDate } from '../lib/labels'
import ReviewCard, { type Review } from './ReviewCard'
import Transcript from './Transcript'

export default function CaseDetail() {
  const { id } = useParams()
  const detail = useLoad(`/ops/cases/${id}`, 8)
  const catalogue = useLoad<any[]>('/ops/catalogue')
  const [tab, setTab] = useState<'overview' | 'activity'>('overview')
  const [document, setDocument] = useState('')
  const [note, setNote] = useState('')
  const subject = useLoad(detail.data ? `/ops/subjects/${detail.data.subject_id}` : null, 8)
  if (!detail.data || !catalogue.data || !subject.data) {
    return <PageLoader error={detail.error || catalogue.error || subject.error} retry={() => Promise.all([detail.reload(), catalogue.reload(), subject.reload()])} />
  }

  const { summary, graph, reported, decisions, notes, sessions } = detail.data
  const reviews: Review[] = detail.data.reviews.filter((r: Review) => r.status !== 'closed')
  const documents = catalogue.data.flatMap((pack) => pack.documents)
  const name = (documentId: string) => documents.find((d: any) => d.id === documentId)?.name ?? documentId
  const reload = () => { detail.reload(); subject.reload() }
  const details = subject.data.details

  async function issue() {
    await api(`/ops/subjects/${subject.data.id}/documents`, { body: { document } })
    setDocument('')
    reload()
  }

  async function remove(documentId: string) {
    await api(`/ops/subjects/${subject.data.id}/documents/${documentId}`, { method: 'DELETE' })
    reload()
  }

  async function addNote() {
    await api(`/ops/cases/${id}/notes`, { body: { text: note } })
    setNote('')
    reload()
  }

  return (
    <>
      <Link to="/ops/cases" className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink">
        <ArrowLeft size={15} /> All cases
      </Link>
      <div className="mb-6 flex items-center gap-4">
        <Avatar name={summary.subject} />
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{summary.subject}</h1>
          <p className="text-muted">
            {subject.data.identifier}
            {details.ward && <> · {details.ward} · Bed {details.bed} · {details.doctor}</>}
            {details.team && <> · {details.team}</>}
          </p>
        </div>
      </div>

      <Tabs value={tab} onChange={setTab} tabs={[
        { id: 'overview', label: 'Overview', count: reviews.filter((r) => r.status === 'open').length || undefined },
        { id: 'activity', label: 'Activity', count: decisions.length + notes.length + sessions.length || undefined },
      ]} />

      {tab === 'overview' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="min-w-0 space-y-6 lg:col-span-2">
            <Card><CaseSummary summary={summary} hideQuestions /></Card>
            {reviews.length > 0 && (
              <div>
                <h2 className="mb-3 text-sm font-semibold">Answer for your office</h2>
                <div className="space-y-3">{reviews.map((r) => <ReviewCard key={r.id} review={r} onDone={reload} />)}</div>
              </div>
            )}
            <Card title="How the documents depend on each other" icon={Network}><CaseGraph graph={graph} /></Card>
          </div>

          <div className="space-y-6">
            <Card title="Documents on file" icon={FileCheck2}>
              <ul className="mb-4 divide-y divide-line">
                {subject.data.documents.map((d: any) => (
                  <li key={d.id} className="group flex items-center justify-between gap-2 py-2 first:pt-0">
                    <span className="text-sm text-ink">
                      {name(d.document)}
                      {d.expires_on && <span className="block text-xs text-muted">expires {d.expires_on}</span>}
                    </span>
                    <Button variant="ghost" size="sm" icon={Trash2} onClick={() => remove(d.id)}
                      aria-label={`Remove ${name(d.document)}`} title="Remove" className="!h-7 !px-1.5 hover:!text-red-600" />
                  </li>
                ))}
              </ul>
              <div className="flex gap-2">
                <Select value={document} onChange={(e) => setDocument(e.target.value)}>
                  <option value="">Issue a document…</option>
                  {documents.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </Select>
                <Button icon={FilePlus2} disabled={!document} onClick={issue}>Issue</Button>
              </div>
            </Card>

            <Card title="Reported by the person" icon={MessageSquareQuote}>
              {reported.length === 0 && <Empty icon={MessageSquareQuote}>Nothing reported. What the person says an office told them appears here, unverified.</Empty>}
              {reported.map((r: any) => (
                <div key={r.id} className="mb-3 last:mb-0">
                  <p className="text-sm"><b>{r.office}</b> issues <b>{r.issues}</b> only after: {describeNeeds(r.needs_first, name)}</p>
                  {r.quote && <p className="mt-1 border-l-2 border-line pl-2 text-xs text-muted italic">"{r.quote}"</p>}
                </div>
              ))}
            </Card>
          </div>
        </div>
      )}

      {tab === 'activity' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card title="Staff decisions" icon={Gavel}>
            {decisions.length === 0 && <Empty icon={Gavel}>No decisions recorded.</Empty>}
            <ul className="space-y-4">
              {decisions.map((d: any) => (
                <li key={d.at} className="flex gap-3">
                  <Avatar name={d.by} size="sm" />
                  <div>
                    <p className="text-sm text-ink"><b>{d.by}</b> · {d.kind.replaceAll('_', ' ')}</p>
                    <p className="text-xs text-muted">{d.target} · {d.office} · {shortDate(d.at)}</p>
                    {d.note && <p className="mt-1 text-sm">{d.note}</p>}
                  </div>
                </li>
              ))}
            </ul>
          </Card>

          <Card title="Notes" icon={StickyNote}>
            <ul className="mb-4 space-y-3">
              {notes.map((n: any) => (
                <li key={n.at} className="rounded-lg bg-slate-50 p-3">
                  <p className="text-sm text-ink">{n.text}</p>
                  <p className="mt-1 text-xs text-muted">{n.author} · {shortDate(n.at)}</p>
                </li>
              ))}
            </ul>
            <div className="flex gap-2">
              <Input placeholder="Add a note" value={note} onChange={(e) => setNote(e.target.value)} />
              <Button variant="plain" disabled={!note} onClick={addNote}>Add</Button>
            </div>
          </Card>

          <Card title="Conversations" icon={MessagesSquare} className="lg:col-span-2">
            {sessions.length === 0 && <Empty icon={MessagesSquare}>No conversation is linked to this case yet.</Empty>}
            {sessions.map((s: any) => (
              <div key={s.id} className="mb-5 last:mb-0">
                <p className="mb-2 text-xs text-muted">{s.channel} · {shortDate(s.started_at)}</p>
                <Transcript lines={s.transcript} />
              </div>
            ))}
          </Card>
        </div>
      )}
    </>
  )
}
