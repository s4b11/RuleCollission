export type Line = { role: string; text: string }

export default function Transcript({ lines }: { lines: Line[] }) {
  if (lines.length === 0) return <p className="text-muted">No transcript was recorded.</p>
  return (
    <div className="space-y-1.5">
      {lines.map((line, index) => (
        <p key={index}>
          <span className="mr-2 text-xs font-semibold uppercase text-muted">{line.role === 'assistant' ? 'Agent' : 'Person'}</span>
          {line.text}
        </p>
      ))}
    </div>
  )
}
