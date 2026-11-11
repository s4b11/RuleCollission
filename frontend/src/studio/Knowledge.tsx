import { FileText, Search, Sparkles, Trash2, Upload } from 'lucide-react'
import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Card, Empty, ErrorText, Field, Input, PageLoader, PageTitle, Table } from '../components/ui'
import { api, useLoad } from '../lib/api'
import { shortDate } from '../lib/labels'
import { useProfile } from './useProfile'

export default function Knowledge() {
  const navigate = useNavigate()
  const { profile } = useProfile()
  const documents = useLoad<any[]>('/studio/knowledge')
  const file = useRef<HTMLInputElement>(null)
  const [title, setTitle] = useState('')
  const [query, setQuery] = useState('')
  const [passages, setPassages] = useState<any[] | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')

  async function upload() {
    const chosen = file.current?.files?.[0]
    if (!chosen) return
    const form = new FormData()
    form.append('title', title || chosen.name)
    form.append('file', chosen)
    await api('/studio/knowledge', { form }).catch((e) => setError(e.message))
    setTitle('')
    file.current!.value = ''
    documents.reload()
  }

  async function draftRules(documentId: string) {
    setBusy(documentId)
    try {
      await api(`/studio/rulepacks/${profile!.pack_id}/drafts/from-document`, { body: { document_id: documentId } })
      navigate('/studio/rules')
    } catch (e) {
      setError((e as Error).message)
    }
    setBusy('')
  }

  return (
    <>
      <PageTitle title="Knowledge" subtitle="Documents the agent can search and quote. They explain; they never decide a case." />
      <ErrorText>{error}</ErrorText>
      <div className="mt-4 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="min-w-0 space-y-6 lg:col-span-2">
          <Card title="Documents" icon={FileText} flush>
            {!documents.data && <PageLoader error={documents.error} retry={documents.reload} />}
            {documents.data?.length === 0 && <Empty icon={FileText}>No documents uploaded.</Empty>}
            <Table head={['Title', 'Passages', 'Added', '']}>
              {(documents.data ?? []).map((d) => (
                <tr key={d.id}>
                  <td><span className="font-medium text-ink">{d.title}</span><br /><span className="text-xs text-muted">{d.filename}</span></td>
                  <td>{d.chunks}</td>
                  <td className="text-muted">{shortDate(d.created_at)}</td>
                  <td className="space-x-2 text-right whitespace-nowrap">
                    <Button variant="plain" size="sm" icon={Sparkles} disabled={busy === d.id} onClick={() => draftRules(d.id)}>
                      {busy === d.id ? 'Reading…' : 'Draft rules from this'}
                    </Button>
                    <Button variant="ghost" size="sm" icon={Trash2} aria-label="Delete document" onClick={() => api(`/studio/knowledge/${d.id}`, { method: 'DELETE' }).then(documents.reload)} />
                  </td>
                </tr>
              ))}
            </Table>
          </Card>
          <Card title="Try a search" icon={Search}>
            <div className="flex gap-2">
              <Input placeholder="Ask something the documents should answer" value={query} onChange={(e) => setQuery(e.target.value)} />
              <Button variant="plain" icon={Search} disabled={!query} onClick={() => api('/studio/knowledge/search', { body: { query } }).then(setPassages)}>Search</Button>
            </div>
            {passages?.length === 0 && <Empty>No matching passage.</Empty>}
            {passages?.map((p, index) => (
              <div key={index} className="mt-3 rounded-lg border border-line bg-slate-50/60 p-3.5">
                <p className="mb-1 text-xs text-muted">{p.document} · page {p.page} · match {p.score}</p>
                <p>{p.text}</p>
              </div>
            ))}
          </Card>
        </div>
        <Card title="Upload a document" icon={Upload}>
          <div className="space-y-3">
            <Field label="Title"><Input value={title} onChange={(e) => setTitle(e.target.value)} /></Field>
            <Field label="File" hint="PDF, text or Markdown."><input ref={file} type="file" accept=".pdf,.txt,.md" className="text-sm" /></Field>
            <Button icon={Upload} onClick={upload}>Upload</Button>
          </div>
        </Card>
      </div>
    </>
  )
}
