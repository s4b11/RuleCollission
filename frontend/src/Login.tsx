import { useState, type FormEvent } from 'react'
import { api, setToken } from './lib/api'
import { Button, ErrorText, Field, Input } from './components/ui'

const DEMO = [
  ['admin@sunrise.example', 'Hospital administrator (Agent Studio)'],
  ['billing@sunrise.example', 'Billing approver'],
  ['tpa@sunrise.example', 'Insurance (TPA) approver'],
  ['ward@sunrise.example', 'Ward nurse'],
  ['admin@northwind.example', 'Second organisation: Northwind Labs'],
]

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    try {
      const result = await api('/auth/login', { body: { email, password } })
      setToken(result.token)
      window.location.href = '/ops'
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <h1 className="text-xl font-semibold">RuleCollision</h1>
        <p className="mt-1 mb-5 text-muted">Staff sign-in</p>
        <form onSubmit={submit} className="space-y-4 rounded-lg border border-line bg-white p-5">
          <Field label="Email"><Input value={email} onChange={(e) => setEmail(e.target.value)} autoFocus /></Field>
          <Field label="Password">
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </Field>
          <ErrorText>{error}</ErrorText>
          <Button type="submit" className="w-full">Sign in</Button>
        </form>
        <div className="mt-5 text-xs text-muted">
          <p className="mb-2">Demo accounts (fictional). Password: <code>demo1234</code></p>
          {DEMO.map(([address, role]) => (
            <button key={address} onClick={() => { setEmail(address); setPassword('demo1234') }}
              className="block w-full rounded px-2 py-1 text-left hover:bg-white">
              <span className="text-brand">{address}</span> — {role}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
