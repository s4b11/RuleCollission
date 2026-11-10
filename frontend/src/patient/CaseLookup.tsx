import { useState, type FormEvent } from 'react'
import { Button, ErrorText, Field, Input } from '../components/ui'
import { api } from '../lib/api'
import CaseView from './CaseView'

export default function CaseLookup() {
  const [code, setCode] = useState('')
  const [identifier, setIdentifier] = useState('')
  const [view, setView] = useState<any>(null)
  const [error, setError] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    try {
      setView(await api('/public/cases/lookup', { body: { code, identifier } }))
      setError('')
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="text-xl font-semibold">Check your case</h1>
      <p className="mt-1 mb-5 text-muted">Enter the case code you were given and your reference number.</p>
      <form onSubmit={submit} className="mb-6 flex items-end gap-3 rounded-lg border border-line bg-white p-4">
        <Field label="Case code"><Input value={code} onChange={(e) => setCode(e.target.value)} /></Field>
        <Field label="Reference number"><Input value={identifier} onChange={(e) => setIdentifier(e.target.value)} /></Field>
        <Button type="submit" disabled={!code || !identifier}>Show</Button>
      </form>
      <ErrorText>{error}</ErrorText>
      {view && <CaseView view={view} />}
    </div>
  )
}
