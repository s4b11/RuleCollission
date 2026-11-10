import { LiveKitRoom, RoomAudioRenderer } from '@livekit/components-react'
import { useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { Button, ErrorText } from '../components/ui'
import { api, useLoad } from '../lib/api'
import CaseView from './CaseView'
import Conversation from './Conversation'

type Session = { session_id: string; session_token: string; livekit_url: string; livekit_token: string }

export default function Assistant() {
  const { slug } = useParams()
  const [params] = useSearchParams()
  const location = params.get('loc') ?? ''
  const info = useLoad(`/public/agents/${slug}?loc=${location}`)
  const [session, setSession] = useState<Session | null>(null)
  const [error, setError] = useState('')
  const state = useLoad(session ? `/public/sessions/${session.session_id}?token=${session.session_token}` : null, 3)

  async function start() {
    try {
      setSession(await api(`/public/agents/${slug}/sessions`, { body: { location_id: location } }))
    } catch (e) {
      setError((e as Error).message)
    }
  }

  if (info.error) return <div className="p-6"><ErrorText>{info.error}</ErrorText></div>
  if (!info.data) return null

  return (
    <div className="mx-auto max-w-3xl p-6">
      <p className="text-xs text-muted">{info.data.organization}{info.data.location && ` · ${info.data.location}`}</p>
      <h1 className="mt-1 text-xl font-semibold">{info.data.name}</h1>

      {!session && (
        <div className="mt-5 rounded-lg border border-line bg-white p-6">
          <p>Stuck between two desks that each want the other's paper first? Tell the assistant what you were told. It will explain what is blocking you and who can fix it.</p>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-muted">
            <li>Keep your {info.data.identifier_label} ready.</li>
            <li>You can talk or type. A written record of the conversation is kept; audio is not recorded.</li>
            <li>The assistant cannot approve anything. Only staff can.</li>
          </ul>
          <div className="mt-5 flex flex-wrap items-center gap-4">
            <Button onClick={start} disabled={!info.data.voice_ready}>Start talking</Button>
            <Link to="/case" className="text-brand hover:underline">I already have a case code</Link>
          </div>
          {!info.data.voice_ready && <p className="mt-3 text-xs text-muted">The voice service is not connected on this server yet.</p>}
          {info.data.phone_number && <p className="mt-3 text-xs text-muted">Prefer to call? Dial {info.data.phone_number} (calls last up to 3 minutes).</p>}
          <div className="mt-3"><ErrorText>{error}</ErrorText></div>
        </div>
      )}

      {session && (
        <div className="mt-5 space-y-4">
          <LiveKitRoom serverUrl={session.livekit_url} token={session.livekit_token} connect audio onDisconnected={() => setSession(null)}>
            <RoomAudioRenderer />
            <Conversation onLeave={() => setSession(null)} />
          </LiveKitRoom>
          {state.data?.case && <CaseView view={state.data.case} />}
        </div>
      )}
    </div>
  )
}
