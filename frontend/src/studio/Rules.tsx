import { Check, FileCode2, History, ListChecks, MessageSquareText, Pencil, Send, Shuffle, X } from 'lucide-react'
import { useState } from 'react'
import { Badge, Button, Card, Empty, ErrorText, Input, PageLoader, PageTitle, Spinner, StatusBadge, Table, TextArea } from '../components/ui'
import { api, useLoad } from '../lib/api'
import { describeNeeds, shortDate } from '../lib/labels'
import { useProfile } from './useProfile'

function Draft({ draft, onDone }: { draft: any; onDone: () => void }) {
  const [text, setText] = useState(JSON.stringify(draft.proposal, null, 2))
  const [editing, setEditing] = useState(false)
  const [error, setError] = useState('')
  const { requirements = [], alternatives = [], documents = [], offices = [] } = draft.proposal

  async function review(action: 'approve' | 'reject') {
    try {
      const body = action === 'approve' ? { proposal: JSON.parse(text) } : undefined
      await api(`/studio/drafts/${draft.id}/${action}`, { method: 'POST', body })
      onDone()
    } catch (e) {
      setError(e instanceof SyntaxError ? 'The draft must be valid JSON' : (e as Error).message)
    }
  }

  return (
    <div className="rounded-xl border border-line bg-white p-5 shadow-card">
      <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-muted">
        <Badge tone="blue">{draft.source === 'chat' ? 'From rule chat' : 'From document'}</Badge>
        <span>{draft.source_ref}</span>
        <span className="ml-auto">{shortDate(draft.created_at)}</span>
        <StatusBadge status={draft.status} />
      </div>
      <ul className="space-y-1.5">
        {offices.map((o: any) => <li key={o.id}>New office: <b>{o.name}</b></li>)}
        {documents.map((d: any) => <li key={d.id}>New document: <b>{d.name}</b></li>)}
        {requirements.map((r: any) => (
          <li key={r.id}>
            <b>{r.office}</b> issues <b>{r.produces}</b> only after: {describeNeeds(r.prerequisites)}
            {r.source?.quote && <span className="block text-xs text-muted">"{r.source.quote}"</span>}
          </li>
        ))}
        {alternatives.map((a: any) => <li key={a.id}>Alternative: {a.description || a.id}</li>)}
      </ul>
      {draft.problems.map((problem: string) => <p key={problem} className="mt-2 text-xs text-red-700">{problem}</p>)}
      {draft.status === 'pending' && (
        <div className="mt-3 space-y-2">
          {editing && <TextArea rows={10} className="font-mono text-xs" value={text} onChange={(e) => setText(e.target.value)} />}
          <div className="flex flex-wrap gap-2">
            <Button icon={Check} onClick={() => review('approve')}>Approve and add to the rules</Button>
            <Button variant="plain" icon={Pencil} onClick={() => setEditing(!editing)}>{editing ? 'Hide editor' : 'Edit first'}</Button>
            <Button variant="danger" icon={X} onClick={() => review('reject')}>Reject</Button>
          </div>
          <ErrorText>{error}</ErrorText>
        </div>
      )}
    </div>
  )
}

function RuleChat({ packId, onDraft }: { packId: string; onDraft: () => void }) {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([])
  const [text, setText] = useState('')
  const [error, setError] = useState('')
  const [thinking, setThinking] = useState(false)

  async function send() {
    const next = [...messages, { role: 'user', content: text }]
    setMessages(next)
    setText('')
    setError('')
    setThinking(true)
    try {
      const answer = await api(`/studio/rulepacks/${packId}/drafts/chat`, { body: { messages: next } })
      setMessages([...next, { role: 'assistant', content: answer.reply }])
      if (answer.draft) onDraft()
    } catch (e) {
      setError((e as Error).message)
    }
    setThinking(false)
  }

  return (
    <Card title="Describe a rule in your own words" icon={MessageSquareText}>
      <p className="mb-3 text-xs text-muted">The assistant turns your description into a draft. Nothing changes until you approve it.</p>
      <div className="mb-3 max-h-72 space-y-2 overflow-auto">
        {messages.map((m, index) => (
          <p key={index} className={`max-w-[90%] rounded-2xl px-3.5 py-2 text-sm ${m.role === 'user' ? 'ml-auto rounded-tr-sm bg-brand text-white' : 'rounded-tl-sm bg-slate-100 text-ink'}`}>{m.content}</p>
        ))}
        {thinking && (
          <p className="flex w-fit items-center gap-2 rounded-2xl rounded-tl-sm bg-slate-100 px-3.5 py-2 text-sm text-muted">
            <Spinner size="sm" /> Drafting…
          </p>
        )}
      </div>
      <div className="flex gap-2">
        <Input placeholder="For example: Pharmacy gives clearance only after the final bill"
          value={text} disabled={thinking} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && text && !thinking && send()} />
        <Button icon={Send} disabled={!text} onClick={send} aria-label="Send" />
      </div>
      <div className="mt-2"><ErrorText>{error}</ErrorText></div>
    </Card>
  )
}

export default function Rules() {
  const { profile } = useProfile()
  const packId = profile?.pack_id
  const pack = useLoad(packId ? `/studio/rulepacks/${packId}` : null)
  const drafts = useLoad<any[]>(packId ? `/studio/rulepacks/${packId}/drafts` : null)
  const [yamlText, setYamlText] = useState<string | null>(null)
  const [error, setError] = useState('')
  if (!pack.data || !drafts.data || !packId) return <PageLoader error={pack.error || drafts.error} retry={() => Promise.all([pack.reload(), drafts.reload()])} />

  const { data } = pack.data
  const officeName = (id: string) => data.offices.find((o: any) => o.id === id)?.name ?? id
  const documentName = (id: string) => data.documents.find((d: any) => d.id === id)?.name ?? id
  const reload = () => { pack.reload(); drafts.reload() }
  const pending = drafts.data.filter((d) => d.status === 'pending')

  async function saveYaml() {
    try {
      await api(`/studio/rulepacks/${packId}`, { method: 'PUT', body: { yaml_text: yamlText } })
      setYamlText(null)
      setError('')
      reload()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <>
      <PageTitle title="Rules" subtitle={`${data.name} · version ${pack.data.versions[0].version}`}
        action={<Button variant="plain" icon={FileCode2} onClick={() => setYamlText(yamlText === null ? pack.data.yaml_text : null)}>{yamlText === null ? 'Edit as a file' : 'Close editor'}</Button>} />
      {yamlText !== null && (
        <Card title="Rule pack file (YAML)" icon={FileCode2} className="mb-6">
          <TextArea rows={18} className="font-mono text-xs" value={yamlText} onChange={(e) => setYamlText(e.target.value)} />
          <div className="mt-3 flex items-center gap-3"><Button onClick={saveYaml}>Check and save as a new version</Button></div>
          <div className="mt-2 whitespace-pre-wrap"><ErrorText>{error}</ErrorText></div>
        </Card>
      )}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="min-w-0 space-y-6 lg:col-span-2">
          <div>
            <h2 className="mb-3 text-sm font-semibold">Drafts waiting for your approval</h2>
            <div className="space-y-3">
              {pending.map((d) => <Draft key={d.id} draft={d} onDone={reload} />)}
              {pending.length === 0 && <Card><Empty>No drafts. Describe a rule in the chat, or draft rules from a document on the Knowledge page.</Empty></Card>}
            </div>
          </div>
          <Card title="Approved rules" icon={ListChecks} flush>
            <Table head={['Office', 'Issues', 'Only after']}>
              {data.requirements.map((r: any) => (
                <tr key={r.id}>
                  <td>{officeName(r.office)}</td>
                  <td className="font-medium text-ink">{documentName(r.produces)}</td>
                  <td className="text-muted">{describeNeeds(r.prerequisites, documentName)}</td>
                </tr>
              ))}
            </Table>
          </Card>
          <Card title="Approved alternatives" icon={Shuffle}>
            {data.alternatives.length === 0 && <Empty>None.</Empty>}
            {data.alternatives.map((a: any) => (
              <p key={a.id} className="mb-2">
                {a.description} <span className="text-xs text-muted">· approved by {officeName(a.approval_by)}, accepted by {a.in_offices.map(officeName).join(', ')}</span>
              </p>
            ))}
          </Card>
        </div>
        <div className="space-y-6">
          <RuleChat packId={packId} onDraft={drafts.reload} />
          <Card title="Version history" icon={History}>
            {pack.data.versions.map((v: any) => (
              <p key={v.version} className="mb-1.5">
                Version {v.version} {v.active && <Badge tone="green">in use</Badge>}
                <span className="block text-xs text-muted">{v.created_by} · {shortDate(v.created_at)}</span>
              </p>
            ))}
          </Card>
        </div>
      </div>
    </>
  )
}
