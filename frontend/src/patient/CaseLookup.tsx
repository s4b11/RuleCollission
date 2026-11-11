import { Search } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Button, ErrorText, Field, Input } from '../components/ui'
import { api } from '../lib/api'
import CaseView from './CaseView'
import Shell from './Shell'

export default function CaseLookup() {
  const [code, setCode] = useState('')
  const [identifier, setIdentifier] = useState('')
  const [view, setView] = useState<any>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    try {
      setView(await api('/public/cases/lookup', { body: { code, identifier } }))
      setError('')
    } catch (e) {
      setError((e as Error).message)
    }
    setBusy(false)
  }

  return (
    <Shell>
      <h1 className="text-2xl font-semibold tracking-tight">Check your case</h1>
      <p className="mt-1 mb-6 text-muted">Enter the case code you were given and your reference number.</p>
      <form onSubmit={submit} className="mb-6 grid gap-3 rounded-xl border border-line bg-white p-5 shadow-card sm:grid-cols-[1fr_1fr_auto] sm:items-end">
        <Field label="Case code"><Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="For example 227E3C" /></Field>
        <Field label="Reference number"><Input value={identifier} onChange={(e) => setIdentifier(e.target.value)} /></Field>
        <Button type="submit" icon={Search} loading={busy} disabled={!code || !identifier}>{busy ? 'Searching…' : 'Show'}</Button>
      </form>
      <ErrorText>{error}</ErrorText>
      {view && <CaseView view={view} />}
    </Shell>
  )
}
