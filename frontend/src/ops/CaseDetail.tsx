import { useState } from 'react'
import { useParams } from 'react-router-dom'
import CaseGraph from '../components/CaseGraph'
import CaseSummary from '../components/CaseSummary'
import { Button, Card, Empty, Input, PageTitle, Select } from '../components/ui'
import { api, useLoad } from '../lib/api'
import { describeNeeds, shortDate } from '../lib/labels'
import ReviewCard, { type Review } from './ReviewCard'
import Transcript from './Transcript'

export default function CaseDetail() {
  const { id } = useParams()
  const detail = useLoad(`/ops/cases/${id}`, 8)
  const catalogue = useLoad<any[]>('/ops/catalogue')
  const [document, setDocument] = useState('')
  const [note, setNote] = useState('')
  const subject = useLoad(detail.data ? `/ops/subjects/${detail.data.subject_id}` : null, 8)
  if (!detail.data || !catalogue.data || !subject.data) return null

  const { summary, graph, reviews, reported, decisions, notes, sessions } = detail.data
  const documents = catalogue.data.flatMap((pack) => pack.documents)
  const name = (documentId: string) => documents.find((d: any) => d.id === documentId)?.name ?? documentId
  const reload = () => { detail.reload(); subject.reload() }

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
      <PageTitle title={summary.subject} subtitle={`${subject.data.identifier} · case ${summary.code}`} />
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <Card title="Where this case stands"><CaseSummary summary={summary} /></Card>
          <Card title="How the documents depend on each other"><CaseGraph graph={graph} /></Card>
          <div>
            <h2 className="mb-3 text-sm font-semibold">Questions for staff</h2>
            <div className="space-y-3">
              {reviews.filter((r: Review) => r.status !== 'closed').map((r: Review) => (
                <ReviewCard key={r.id} review={r} onDone={reload} />
              ))}
              {reviews.length === 0 && <Card><Empty>No questions on this case.</Empty></Card>}
            </div>
          </div>
          <Card title="Conversations">
            {sessions.length === 0 && <Empty>No conversation is linked to this case yet.</Empty>}
            {sessions.map((s: any) => (
              <div key={s.id} className="mb-4 last:mb-0">
                <p className="mb-2 text-xs text-muted">{s.channel} · {shortDate(s.started_at)}</p>
                <Transcript lines={s.transcript} />
              </div>
            ))}
          </Card>
        </div>

        <div className="space-y-6">
          <Card title="Documents on file">
            <ul className="mb-3 space-y-1.5">
              {subject.data.documents.map((d: any) => (
                <li key={d.id} className="flex items-center justify-between gap-2">
                  <span>{name(d.document)}{d.expires_on && <span className="text-xs text-muted"> · expires {d.expires_on}</span>}</span>
                  <button onClick={() => remove(d.id)} className="text-xs text-muted hover:text-red-700">Remove</button>
                </li>
              ))}
            </ul>
            <div className="flex gap-2">
              <Select value={document} onChange={(e) => setDocument(e.target.value)}>
                <option value="">Issue a document…</option>
                {documents.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </Select>
              <Button disabled={!document} onClick={issue}>Issue</Button>
            </div>
          </Card>

          <Card title="Reported by the person (unverified)">
            {reported.length === 0 && <Empty>Nothing reported.</Empty>}
            {reported.map((r: any) => (
              <div key={r.id} className="mb-3 last:mb-0">
                <p><b>{r.office}</b> issues <b>{r.issues}</b> only after: {describeNeeds(r.needs_first, name)}</p>
                {r.quote && <p className="mt-1 text-xs text-muted">"{r.quote}"</p>}
              </div>
            ))}
          </Card>

          <Card title="Staff decisions">
            {decisions.length === 0 && <Empty>No decisions recorded.</Empty>}
            {decisions.map((d: any) => (
              <div key={d.at} className="mb-3 last:mb-0">
                <p><b>{d.kind.replaceAll('_', ' ')}</b>: {d.target}</p>
                <p className="text-xs text-muted">{d.by} ({d.office}) · {shortDate(d.at)}{d.note && ` · ${d.note}`}</p>
              </div>
            ))}
          </Card>

          <Card title="Notes">
            {notes.map((n: any) => (
              <div key={n.at} className="mb-3">
                <p>{n.text}</p>
                <p className="text-xs text-muted">{n.author} · {shortDate(n.at)}</p>
              </div>
            ))}
            <div className="flex gap-2">
              <Input placeholder="Add a note" value={note} onChange={(e) => setNote(e.target.value)} />
              <Button variant="plain" disabled={!note} onClick={addNote}>Add</Button>
            </div>
          </Card>
        </div>
      </div>
    </>
  )
}
