export type Line = { role: string; text: string }

export default function Transcript({ lines }: { lines: Line[] }) {
  if (lines.length === 0) return <p className="text-sm text-muted">No transcript was recorded.</p>
  return (
    <div className="space-y-2">
      {lines.map((line, index) => {
        const agent = line.role === 'assistant'
        return (
          <div key={index} className={`flex ${agent ? '' : 'justify-end'}`}>
            <div className={`max-w-[80%] rounded-2xl px-3.5 py-2 text-sm ${agent ? 'rounded-tl-sm bg-slate-100 text-ink' : 'rounded-tr-sm bg-brand text-white'}`}>
              {line.text}
            </div>
          </div>
        )
      })}
    </div>
  )
}
