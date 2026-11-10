import { CircleCheckBig } from 'lucide-react'
import { useState } from 'react'
import { Card, Empty, PageTitle, Switch, Tabs } from '../components/ui'
import { useLoad } from '../lib/api'
import ReviewCard, { type Review } from './ReviewCard'

export default function Reviews() {
  const [mine, setMine] = useState(true)
  const [tab, setTab] = useState<'open' | 'done'>('open')
  const reviews = useLoad<Review[]>(`/ops/reviews?mine=${mine}`, 10)
  const list = reviews.data ?? []
  const open = list.filter((r) => r.status === 'open')
  const done = list.filter((r) => r.status !== 'open')
  const shown = tab === 'open' ? open : done

  return (
    <>
      <PageTitle title="Review inbox" subtitle="Only staff decide. Each answer applies to one case."
        action={
          <label className="flex items-center gap-2.5 text-sm">
            <Switch checked={mine} onChange={() => setMine(!mine)} label="Only my office" />
            Only my office
          </label>
        } />
      <Tabs value={tab} onChange={setTab} tabs={[
        { id: 'open', label: 'Open', count: open.length },
        { id: 'done', label: 'Answered', count: done.length },
      ]} />
      <div className="space-y-3">
        {shown.map((r) => <ReviewCard key={r.id} review={r} showCase onDone={reviews.reload} />)}
        {shown.length === 0 && (
          <Card><Empty icon={CircleCheckBig}>{tab === 'open' ? 'No open questions. You are all caught up.' : 'Nothing answered yet.'}</Empty></Card>
        )}
      </div>
    </>
  )
}
