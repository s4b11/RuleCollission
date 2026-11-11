import { LiveKitRoom, RoomAudioRenderer } from '@livekit/components-react'
import { FileText, IdCard, Mic, Phone, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { Button, ErrorText, PageLoader, SlowHint } from '../components/ui'
import { api, useLoad } from '../lib/api'
import CaseView from './CaseView'
import Conversation from './Conversation'
import Shell from './Shell'

type Session = { session_id: string; session_token: string; livekit_url: string; livekit_token: string }

export default function Assistant() {
  const { slug } = useParams()
  const [params] = useSearchParams()
  const location = params.get('loc') ?? ''
  const info = useLoad(`/public/agents/${slug}?loc=${location}`)
  const [session, setSession] = useState<Session | null>(null)
  const [error, setError] = useState('')
  const [starting, setStarting] = useState(false)
  const state = useLoad(session ? `/public/sessions/${session.session_id}?token=${session.session_token}` : null, 3)

  async function start() {
    setStarting(true)
    try {
      setSession(await api(`/public/agents/${slug}/sessions`, { body: { location_id: location } }))
    } catch (e) {
      setError((e as Error).message)
    }
    setStarting(false)
  }

  if (!info.data) return <Shell><PageLoader error={info.error} retry={info.reload} /></Shell>

  const points = [
    [IdCard, `Keep your ${info.data.identifier_label} ready`, 'The assistant asks for it before discussing your case.'],
    [FileText, 'Talk or type', 'A written record of the conversation is kept. Audio is never recorded.'],
    [ShieldCheck, 'Staff decide', 'The assistant explains and asks the right office. It cannot approve anything.'],
  ] as const

  return (
    <Shell context={[info.data.organization, info.data.location].filter(Boolean).join(' · ')}>
      {!session && (
        <>
          <h1 className="text-3xl leading-tight font-semibold tracking-tight">{info.data.name}</h1>
          <p className="mt-3 max-w-xl text-base text-muted">
            Stuck between two desks that each want the other's paper first? Tell the assistant what you were told.
            It will explain what is blocking you and who can fix it.
          </p>

          <div className="mt-8 rounded-xl border border-line bg-white p-6 shadow-card">
            <ul className="space-y-5">
              {points.map(([Icon, title, text]) => (
                <li key={title} className="flex gap-4">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-soft text-brand"><Icon size={19} /></span>
                  <span>
                    <span className="block font-medium text-ink">{title}</span>
                    <span className="text-sm text-muted">{text}</span>
                  </span>
                </li>
              ))}
            </ul>
            <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
              <Button size="lg" icon={Mic} onClick={start} disabled={!info.data.voice_ready} className="w-full sm:w-auto">Start talking</Button>
              <Link to="/case" className="text-center text-sm font-medium text-brand hover:underline">I already have a case code</Link>
            </div>
            <SlowHint active={starting} className="mt-4" />
            {!info.data.voice_ready && <p className="mt-4 text-xs text-muted">The voice service is not connected on this server yet.</p>}
            {info.data.phone_number && (
              <p className="mt-4 flex items-center gap-2 text-sm text-muted">
                <Phone size={15} /> Prefer to call? Dial <b>{info.data.phone_number}</b> (calls last up to 3 minutes).
              </p>
            )}
            {error && <div className="mt-4"><ErrorText>{error}</ErrorText></div>}
          </div>
        </>
      )}

      {session && (
        <div className="space-y-4">
          <LiveKitRoom serverUrl={session.livekit_url} token={session.livekit_token} connect audio onDisconnected={() => setSession(null)}>
            <RoomAudioRenderer />
            <Conversation onLeave={() => setSession(null)} />
          </LiveKitRoom>
          {state.data?.case && <CaseView view={state.data.case} />}
        </div>
      )}
    </Shell>
  )
}
