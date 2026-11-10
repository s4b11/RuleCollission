import { useChat, useLocalParticipant, useTranscriptions, useVoiceAssistant } from '@livekit/components-react'
import { Mic, MicOff, PhoneOff, Send } from 'lucide-react'
import { useState } from 'react'
import { Button, Input } from '../components/ui'

const STATE: Record<string, { label: string; colour: string; live: boolean }> = {
  connecting: { label: 'Connecting…', colour: 'bg-slate-400', live: false },
  initializing: { label: 'Getting ready…', colour: 'bg-slate-400', live: false },
  listening: { label: 'Listening to you', colour: 'bg-emerald-500', live: true },
  thinking: { label: 'Thinking…', colour: 'bg-amber-500', live: true },
  speaking: { label: 'Speaking', colour: 'bg-brand', live: true },
}

export default function Conversation({ onLeave }: { onLeave: () => void }) {
  const { state } = useVoiceAssistant()
  const { localParticipant, isMicrophoneEnabled } = useLocalParticipant()
  const transcriptions = useTranscriptions()
  const { chatMessages, send } = useChat()
  const [text, setText] = useState('')
  const status = STATE[state] ?? { label: 'Connected', colour: 'bg-slate-400', live: false }

  const spoken = transcriptions.map((t) => ({
    id: t.streamInfo.id,
    mine: t.participantInfo.identity === localParticipant.identity,
    text: t.text,
    time: t.streamInfo.timestamp,
  }))
  const typed = chatMessages
    .filter((m) => m.from?.identity === localParticipant.identity)
    .map((m) => ({ id: m.id, mine: true, text: m.message, time: m.timestamp }))
  const lines = [...spoken, ...typed].sort((a, b) => a.time - b.time)

  function sendText() {
    send(text)
    setText('')
  }

  return (
    <div className="overflow-hidden rounded-xl border border-line bg-white shadow-card">
      <div className="flex items-center justify-between gap-3 border-b border-line px-5 py-3">
        <span className="flex items-center gap-3 font-medium text-ink">
          <span className="relative flex h-3 w-3">
            {status.live && <span className={`absolute inset-0 rounded-full ${status.colour}`} style={{ animation: 'pulse-ring 1.4s ease-out infinite' }} />}
            <span className={`relative h-3 w-3 rounded-full ${status.colour}`} />
          </span>
          {status.label}
        </span>
        <span className="flex gap-2">
          <Button variant="plain" size="sm" icon={isMicrophoneEnabled ? Mic : MicOff}
            onClick={() => localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled)}>
            {isMicrophoneEnabled ? 'Mute' : 'Unmute'}
          </Button>
          <Button variant="danger" size="sm" icon={PhoneOff} onClick={onLeave}>End</Button>
        </span>
      </div>
      <div className="h-80 space-y-2 overflow-auto bg-slate-50/60 p-5">
        {lines.length === 0 && <p className="pt-24 text-center text-sm text-muted">The assistant will greet you in a moment. Just start talking.</p>}
        {lines.map((line) => (
          <div key={line.id} className={`flex ${line.mine ? 'justify-end' : ''}`}>
            <p className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-sm ${line.mine ? 'rounded-tr-sm bg-brand text-white' : 'rounded-tl-sm bg-white text-ink ring-1 ring-line'}`}>
              {line.text}
            </p>
          </div>
        ))}
      </div>
      <div className="flex gap-2 border-t border-line p-3">
        <Input placeholder="Or type here" value={text} onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && text && sendText()} />
        <Button icon={Send} disabled={!text} onClick={sendText} aria-label="Send" />
      </div>
    </div>
  )
}
