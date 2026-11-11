import { GitCompareArrows, MessageCircleQuestion, ShieldCheck } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Logo } from './components/Layout'
import { Button, ErrorText, Field, Input } from './components/ui'
import { api, setToken } from './lib/api'

const DEMO = [
  ['admin@sunrise.example', 'Hospital administrator', 'Agent Studio'],
  ['billing@sunrise.example', 'Billing approver', 'Hospital'],
  ['tpa@sunrise.example', 'Insurance (TPA) approver', 'Hospital'],
  ['ward@sunrise.example', 'Ward nurse', 'Hospital'],
  ['admin@northwind.example', 'Company administrator', 'Second organisation'],
]

const POINTS = [
  [GitCompareArrows, 'Finds the loop', 'Shows exactly which offices are waiting on each other, and why.'],
  [MessageCircleQuestion, 'Asks the right person', 'Sends one precise question to the office that can answer it.'],
  [ShieldCheck, 'Staff decide', 'The assistant explains and proposes. Only signed-in staff approve.'],
] as const

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const result = await api('/auth/login', { body: { email, password } })
      setToken(result.token)
      window.location.href = '/ops'
    } catch (e) {
      setError((e as Error).message)
      setBusy(false)
    }
  }

  return (
    <div className="grid grid-cols-1 min-h-screen lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-side p-12 lg:flex">
        <Logo light />
        <div>
          <h1 className="max-w-md text-3xl leading-tight font-semibold tracking-tight !text-white">
            When two desks each want the other's paper first.
          </h1>
          <ul className="mt-10 space-y-6">
            {POINTS.map(([Icon, title, text]) => (
              <li key={title} className="flex gap-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white/10 text-white"><Icon size={19} /></span>
                <span>
                  <span className="block font-medium text-white">{title}</span>
                  <span className="text-sm text-slate-400">{text}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-slate-500">Demo data is fictional.</p>
      </div>

      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden"><Logo /></div>
          <h2 className="text-2xl font-semibold tracking-tight">Staff sign-in</h2>
          <p className="mt-1 mb-6 text-muted">Use your work account to open the dashboard.</p>
          <form onSubmit={submit} className="space-y-4">
            <Field label="Email"><Input value={email} onChange={(e) => setEmail(e.target.value)} autoFocus /></Field>
            <Field label="Password">
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </Field>
            <ErrorText>{error}</ErrorText>
            <Button type="submit" className="w-full" loading={busy}>{busy ? 'Signing in…' : 'Sign in'}</Button>
          </form>

          <div className="mt-8 rounded-xl border border-line bg-white shadow-card">
            <p className="border-b border-line px-4 py-2.5 text-xs font-medium text-muted">Demo accounts — click one to fill the email</p>
            {DEMO.map(([address, role, group]) => (
              <button key={address} type="button" onClick={() => setEmail(address)}
                className="flex w-full items-center justify-between gap-3 border-b border-line px-4 py-2.5 text-left last:border-0 hover:bg-slate-50">
                <span>
                  <span className="block text-sm font-medium text-ink">{role}</span>
                  <span className="text-xs text-muted">{address}</span>
                </span>
                <span className="text-xs text-muted">{group}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
