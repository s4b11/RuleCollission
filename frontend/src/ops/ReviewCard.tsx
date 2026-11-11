import { Check, X } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge, Button, ErrorText, Input, StatusBadge } from '../components/ui'
import { api } from '../lib/api'
import { QUESTION_KIND, shortDate } from '../lib/labels'

export type Review = {
  id: string; case_id: string; case_code: string; subject: string; kind: string; about: string; office: string
  office_name: string; question: string; status: string; answer: string; answered_by: string; created_at: string
}

const BUTTONS: Record<string, [string, string]> = {
  verify_requirement: ['Yes, that is our rule', 'No, that is not our rule'],
  alternative_approval: ['Approve for this case', 'Refuse'],
  alternative_acceptance: ['Accept for this case', 'Decline'],
  unconfirmed_equivalence: ['Yes, same document', 'No, different document'],
}

export default function ReviewCard({ review, showCase, onDone }: { review: Review; showCase?: boolean; onDone: () => void }) {
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [yes, no] = BUTTONS[review.kind] ?? ['Mark as answered', '']

  async function answer(agree: boolean) {
    try {
      await api(`/ops/reviews/${review.id}/answer`, { body: { agree, note } })
      onDone()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <div className="min-w-0 rounded-xl border border-line bg-white p-4 shadow-card sm:p-5">
      <div className="mb-2.5 flex flex-wrap items-center gap-2 text-xs text-muted">
        <Badge tone="blue">{QUESTION_KIND[review.kind] ?? review.kind}</Badge>
        {review.office_name && <span>for {review.office_name}</span>}
        {showCase && (
          <Link to={`/ops/cases/${review.case_id}`} className="font-medium text-brand hover:underline">
            {review.subject} · {review.case_code}
          </Link>
        )}
        <span className="w-full sm:ml-auto sm:w-auto">{shortDate(review.created_at)}</span>
      </div>
      <p className="text-ink">{review.question}</p>
      {review.status === 'open' ? (
        <div className="mt-4 space-y-3">
          <Input placeholder="Note or conditions (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
          <div className="flex flex-wrap gap-2">
            <Button icon={Check} onClick={() => answer(true)}>{yes}</Button>
            {no && <Button variant="danger" icon={X} onClick={() => answer(false)}>{no}</Button>}
          </div>
          <ErrorText>{error}</ErrorText>
        </div>
      ) : (
        <p className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted">
          <StatusBadge status={review.status} /> by {review.answered_by}{review.answer && ` — "${review.answer}"`}
        </p>
      )}
    </div>
  )
}
