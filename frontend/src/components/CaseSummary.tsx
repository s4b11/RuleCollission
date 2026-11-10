import type { LucideIcon } from 'lucide-react'
import { CheckCircle2, CircleHelp, GitCompareArrows, Info, ListChecks, OctagonAlert, Route } from 'lucide-react'
import { QUESTION_KIND, STATUS, type Tone } from '../lib/labels'
import { Badge } from './ui'

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

const HEADLINE: Record<string, { icon: LucideIcon; text: string }> = {
  route_confirmed: { icon: Route, text: 'There is a confirmed way forward. Follow these steps in order.' },
  route_suggested: { icon: ListChecks, text: 'These steps should work, but an office still needs to confirm a rule.' },
  needs_decision: { icon: CircleHelp, text: 'A decision from staff is needed before this can move forward.' },
  needs_information: { icon: CircleHelp, text: 'Some information is still missing.' },
  unresolved: { icon: OctagonAlert, text: "This is stuck. The offices need each other's documents and no approved alternative applies." },
  completed: { icon: CheckCircle2, text: 'Done. The document has been issued.' },
}

const BANNER: Record<Tone, string> = {
  green: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  amber: 'border-amber-200 bg-amber-50 text-amber-900',
  red: 'border-red-200 bg-red-50 text-red-900',
  blue: 'border-blue-200 bg-brand-soft text-brand-dark',
  gray: 'border-line bg-slate-50 text-body',
}

function Heading({ children }: { children: string }) {
  return <h3 className="mb-2.5 text-xs font-semibold tracking-wide text-muted uppercase">{children}</h3>
}

export default function CaseSummary({ summary, hideQuestions }: { summary: Summary; hideQuestions?: boolean }) {
  const status = STATUS[summary.status] ?? { label: summary.status, tone: 'gray' as Tone }
  const headline = HEADLINE[summary.status] ?? { icon: Info, text: '' }

  return (
    <div className="space-y-5">
      <div className={`flex gap-3 rounded-lg border p-4 ${BANNER[status.tone]}`}>
        <headline.icon size={20} className="mt-0.5 shrink-0" />
        <div>
          <p className="font-semibold">{status.label}</p>
          <p className="text-sm opacity-90">{headline.text}</p>
        </div>
      </div>

      <dl className="flex flex-wrap gap-x-8 gap-y-2 text-sm">
        <div><dt className="text-xs text-muted">Goal</dt><dd className="font-medium text-ink">{summary.goal}</dd></div>
        <div><dt className="text-xs text-muted">Case code</dt><dd className="font-mono font-medium text-ink">{summary.code}</dd></div>
        <div><dt className="text-xs text-muted">Documents on file</dt><dd className="font-medium text-ink">{summary.held.length}</dd></div>
      </dl>

      {summary.steps.length > 0 && (
        <div>
          <Heading>Steps to follow</Heading>
          <ol>
            {summary.steps.map((step, index) => (
              <li key={step.order} className="relative flex gap-3 pb-4 last:pb-0">
                {index < summary.steps.length - 1 && <span className="absolute top-7 left-3.5 h-full w-px bg-line" />}
                <span className="relative flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand text-xs font-semibold text-white">
                  {step.order}
                </span>
                <div className="pt-0.5">
                  <p className="font-medium text-ink">{step.document}</p>
                  <p className="text-xs text-muted">
                    from {step.office}
                    {step.via_alternative && <span className="ml-2"><Badge tone="blue">approved alternative</Badge></span>}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      {summary.blockers.map((blocker) => (
        <div key={blocker.documents.join()} className="flex gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-900">
          <GitCompareArrows size={18} className="mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-semibold">Waiting on each other</p>
            <p className="mt-1 flex flex-wrap items-center gap-2 text-sm">
              {blocker.documents.map((document, index) => (
                <span key={document} className="flex items-center gap-2">
                  {index > 0 && <span className="text-red-400">⇄</span>}
                  <span className="rounded-md bg-white px-2 py-0.5 font-medium ring-1 ring-red-200">{document}</span>
                </span>
              ))}
            </p>
          </div>
        </div>
      ))}

      {!hideQuestions && summary.questions.length > 0 && (
        <div>
          <Heading>Questions waiting for staff</Heading>
          <ul className="space-y-2">
            {summary.questions.map((q) => (
              <li key={q.kind + q.question} className="rounded-lg border border-line p-3.5">
                <div className="mb-1.5 flex flex-wrap items-center gap-2 text-xs text-muted">
                  <Badge tone={q.status === 'declined' ? 'red' : 'amber'}>{QUESTION_KIND[q.kind] ?? q.kind}</Badge>
                  {q.office && <span>for {q.office}</span>}
                  {q.status === 'declined' && <span>· declined</span>}
                </div>
                <p className="text-sm">{q.question}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {summary.notes.length > 0 && (
        <ul className="space-y-1.5 text-sm text-muted">
          {summary.notes.map((note) => (
            <li key={note} className="flex gap-2"><Info size={15} className="mt-0.5 shrink-0" />{note}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
