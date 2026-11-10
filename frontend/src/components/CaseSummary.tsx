import { QUESTION_KIND } from '../lib/labels'
import { Badge, StatusBadge } from './ui'

export type Summary = {
  id: string
  code: string
  status: string
  goal: string
  subject: string
  held: string[]
  steps: { order: number; document: string; office: string; via_alternative: string | null }[]
  unverified_requirements: string[]
  blockers: { documents: string[]; requirements: string[] }[]
  questions: { kind: string; office: string; question: string; status: string }[]
  notes: string[]
}

const HEADLINE: Record<string, string> = {
  route_confirmed: 'There is a confirmed way forward. Follow these steps in order.',
  route_suggested: 'These steps should work, but one or more rules still need to be confirmed by the office.',
  needs_decision: 'A decision from staff is needed before this can move forward.',
  needs_information: 'Some information is still missing.',
  unresolved: 'This is stuck. The offices need each other\'s documents and no approved alternative applies.',
  completed: 'Done. The document has been issued.',
}

export default function CaseSummary({ summary }: { summary: Summary }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge status={summary.status} />
        <span className="text-muted">Goal: <b className="text-ink">{summary.goal}</b></span>
        <span className="text-muted">Case code: <b className="font-mono text-ink">{summary.code}</b></span>
      </div>
      <p>{HEADLINE[summary.status]}</p>

      {summary.steps.length > 0 && (
        <ol className="space-y-2">
          {summary.steps.map((step) => (
            <li key={step.order} className="flex gap-3 rounded-md border border-line px-3 py-2">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-soft text-xs font-semibold text-brand-dark">
                {step.order}
              </span>
              <span>
                Get the <b>{step.document}</b> from <b>{step.office}</b>
                {step.via_alternative && <> <Badge tone="blue">approved alternative</Badge></>}
              </span>
            </li>
          ))}
        </ol>
      )}

      {summary.blockers.map((blocker) => (
        <div key={blocker.documents.join()} className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-red-900">
          <b>Waiting on each other:</b> {blocker.documents.join(' ↔ ')}
        </div>
      ))}

      {summary.questions.length > 0 && (
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Questions waiting for staff</h3>
          <ul className="space-y-2">
            {summary.questions.map((q) => (
              <li key={q.kind + q.question} className="rounded-md border border-line px-3 py-2">
                <div className="mb-1 flex items-center gap-2 text-xs text-muted">
                  <Badge tone={q.status === 'declined' ? 'red' : 'amber'}>{QUESTION_KIND[q.kind] ?? q.kind}</Badge>
                  {q.office && <span>for {q.office}</span>}
                  {q.status === 'declined' && <span>· declined</span>}
                </div>
                {q.question}
              </li>
            ))}
          </ul>
        </div>
      )}

      {summary.notes.length > 0 && (
        <ul className="list-disc space-y-1 pl-5 text-muted">
          {summary.notes.map((note) => <li key={note}>{note}</li>)}
        </ul>
      )}
    </div>
  )
}
