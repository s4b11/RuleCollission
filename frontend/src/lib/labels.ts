export type Tone = 'gray' | 'green' | 'amber' | 'red' | 'blue'

export const STATUS: Record<string, { label: string; tone: Tone }> = {
  needs_information: { label: 'Needs information', tone: 'amber' },
  needs_decision: { label: 'Needs a decision', tone: 'amber' },
  unresolved: { label: 'Stuck', tone: 'red' },
  route_suggested: { label: 'Route suggested', tone: 'blue' },
  route_confirmed: { label: 'Route confirmed', tone: 'green' },
  completed: { label: 'Completed', tone: 'gray' },
  open: { label: 'Open', tone: 'amber' },
  answered: { label: 'Answered', tone: 'green' },
  declined: { label: 'Declined', tone: 'red' },
  pending: { label: 'Waiting for review', tone: 'amber' },
  approved: { label: 'Approved', tone: 'green' },
  rejected: { label: 'Rejected', tone: 'red' },
}

export const QUESTION_KIND: Record<string, string> = {
  missing_document: 'Missing document',
  unconfirmed_equivalence: 'Same document, different name?',
  applicability: 'Does this rule apply?',
  condition_conflict: 'Conflicting conditions',
  verify_requirement: 'Confirm a reported rule',
  alternative_approval: 'Approve an alternative',
  alternative_acceptance: 'Accept an alternative',
  decision_request: 'Decision needed',
}

export function shortDate(value: string) {
  if (!value) return ''
  return new Date(value).toLocaleString([], { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export function describeNeeds(prerequisites: any, name: (id: string) => string = (id) => id): string {
  if (!prerequisites) return 'nothing'
  if (typeof prerequisites === 'string') return name(prerequisites)
  const joiner = prerequisites.all_of ? ' and ' : ' or '
  return (prerequisites.all_of ?? prerequisites.any_of).map((item: any) => describeNeeds(item, name)).join(joiner)
}
