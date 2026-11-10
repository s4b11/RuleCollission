import { useChat, useLocalParticipant, useTranscriptions, useVoiceAssistant } from '@livekit/components-react'
import { useState } from 'react'
import { Button, Input } from '../components/ui'

const STATE: Record<string, string> = {
  connecting: 'Connecting…',
  initializing: 'Getting ready…',
  listening: 'Listening',
  thinking: 'Thinking…',
  speaking: 'Speaking',
}

export default function Conversation({ onLeave }: { onLeave: () => void }) {
  const { state } = useVoiceAssistant()
  const { localParticipant, isMicrophoneEnabled } = useLocalParticipant()
  const transcriptions = useTranscriptions()
  const { chatMessages, send } = useChat()
  const [text, setText] = useState('')

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
    <div className="rounded-lg border border-line bg-white">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <span className="font-medium">{STATE[state] ?? 'Connected'}</span>
        <span className="flex gap-2">
          <Button variant="plain" onClick={() => localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled)}>
            {isMicrophoneEnabled ? 'Mute microphone' : 'Unmute microphone'}
          </Button>
          <Button variant="danger" onClick={onLeave}>End</Button>
        </span>
      </div>
      <div className="h-72 space-y-2 overflow-auto p-4">
        {lines.map((line) => (
          <p key={line.id} className={`max-w-[85%] rounded-md px-3 py-2 ${line.mine ? 'ml-auto bg-brand-soft' : 'bg-slate-50'}`}>
            {line.text}
          </p>
        ))}
      </div>
      <div className="flex gap-2 border-t border-line p-3">
        <Input placeholder="Or type here" value={text} onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && text && sendText()} />
        <Button disabled={!text} onClick={sendText}>Send</Button>
      </div>
    </div>
  )
}
