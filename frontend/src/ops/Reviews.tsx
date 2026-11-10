import { useState } from 'react'
import { Button, Card, Empty, PageTitle } from '../components/ui'
import { useLoad } from '../lib/api'
import ReviewCard, { type Review } from './ReviewCard'

export default function Reviews() {
  const [mine, setMine] = useState(true)
  const reviews = useLoad<Review[]>(`/ops/reviews?mine=${mine}`, 10)
  const list = reviews.data ?? []
  const open = list.filter((r) => r.status === 'open')
  const done = list.filter((r) => r.status !== 'open')

  return (
    <>
      <PageTitle title="Review inbox" subtitle="Only staff decide. Each answer applies to one case."
        action={<Button variant="plain" onClick={() => setMine(!mine)}>{mine ? 'Show all offices' : 'Show my office only'}</Button>} />
      <div className="space-y-3">
        {open.map((r) => <ReviewCard key={r.id} review={r} showCase onDone={reviews.reload} />)}
        {open.length === 0 && <Card><Empty>No open questions.</Empty></Card>}
      </div>
      {done.length > 0 && <h2 className="mt-8 mb-3 text-sm font-semibold">Answered</h2>}
      <div className="space-y-3">
        {done.map((r) => <ReviewCard key={r.id} review={r} showCase onDone={reviews.reload} />)}
      </div>
    </>
  )
}
