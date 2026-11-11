import { BedDouble, Plus, Search } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useOutletContext } from 'react-router-dom'
import type { Staff } from '../components/Layout'
import { Avatar, Button, Card, Input, PageLoader, PageTitle, Select, StatusBadge, Table } from '../components/ui'
import { api, useLoad } from '../lib/api'
import { STATUS } from '../lib/labels'

type Person = {
  id: string; identifier: string; name: string; status: string; details: Record<string, any>
  documents: { id: string }[]; case: { id: string; status: string } | null
}

const EDGE: Record<string, string> = {
  green: 'border-l-emerald-500', amber: 'border-l-amber-500', red: 'border-l-red-500',
  blue: 'border-l-brand', gray: 'border-l-slate-300',
}

function BedBoard({ people }: { people: Person[] }) {
  const wards: Record<string, Person[]> = {}
  for (const person of people) {
    if (person.status === 'admitted') (wards[person.details.ward] ??= []).push(person)
  }
  return (
    <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
      {Object.entries(wards).sort().map(([ward, patients]) => (
        <Card key={ward} title={ward} icon={BedDouble}
          action={<span className="text-xs text-muted">{patients.length} occupied</span>}>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {patients.sort((a, b) => a.details.bed.localeCompare(b.details.bed)).map((p) => {
              const tone = p.case ? STATUS[p.case.status]?.tone ?? 'gray' : 'gray'
              return (
                <Link key={p.id} to={p.case ? `/ops/cases/${p.case.id}` : '#'}
                  className={`rounded-lg border border-l-4 border-line p-3 transition-shadow hover:shadow-pop ${EDGE[tone]}`}>
                  <div className="text-[11px] font-medium text-muted">BED {p.details.bed}</div>
                  <div className="truncate font-medium text-ink">{p.name}</div>
                  <div className="mt-1 truncate text-xs text-muted">
                    {p.case ? STATUS[p.case.status]?.label ?? p.case.status : 'No open case'}
                  </div>
                </Link>
              )
            })}
          </div>
        </Card>
      ))}
    </div>
  )
}

export default function People() {
  const staff = useOutletContext<Staff>()
  const navigate = useNavigate()
  const people = useLoad<Person[]>('/ops/subjects', 10)
  const catalogue = useLoad<any[]>('/ops/catalogue')
  const [opening, setOpening] = useState('')
  const [goal, setGoal] = useState('')
  const [query, setQuery] = useState('')
  if (!people.data || !catalogue.data) return <PageLoader error={people.error || catalogue.error} retry={() => Promise.all([people.reload(), catalogue.reload()])} />
  const pack = catalogue.data[0]
  const hasWards = people.data.some((p) => p.details.ward)
  const shown = people.data.filter((p) => `${p.name} ${p.identifier}`.toLowerCase().includes(query.toLowerCase()))

  async function openCase(person: Person) {
    const result = await api(`/ops/subjects/${person.id}/cases`, { body: { pack_id: pack.pack_id, goal } })
    navigate(`/ops/cases/${result.id}`)
  }

  return (
    <>
      <PageTitle title={`${staff.subject_label}s`} subtitle="Records from the organisation's own system. Demo data, all fictional." />
      {hasWards && <BedBoard people={people.data} />}
      <Card flush title={`All ${staff.subject_label.toLowerCase()}s`}
        action={
          <span className="relative block w-full sm:w-56">
            <Search size={15} className="absolute top-2.5 left-3 text-slate-400" />
            <Input placeholder="Search name or number" value={query} onChange={(e) => setQuery(e.target.value)} className="!py-1.5 !pl-9" />
          </span>
        }>
        <Table head={['Name', 'Identifier', 'Details', 'Documents', 'Case', '']}>
          {shown.map((p) => (
            <tr key={p.id}>
              <td><span className="flex items-center gap-3 font-medium text-ink"><Avatar name={p.name} size="sm" />{p.name}</span></td>
              <td className="font-mono text-xs">{p.identifier}</td>
              <td className="text-muted">{p.details.ward ? `${p.details.reason} · ${p.details.doctor}` : p.details.team}</td>
              <td>{p.documents.length}</td>
              <td>{p.case ? <StatusBadge status={p.case.status} /> : <span className="text-muted">—</span>}</td>
              <td className="text-right whitespace-nowrap">
                {p.case && <Link to={`/ops/cases/${p.case.id}`} className="font-medium text-brand hover:underline">Open</Link>}
                {!p.case && opening !== p.id && <Button variant="plain" size="sm" icon={Plus} onClick={() => setOpening(p.id)}>Start a case</Button>}
                {!p.case && opening === p.id && (
                  <span className="flex items-center justify-end gap-2">
                    <Select value={goal} onChange={(e) => setGoal(e.target.value)} className="!w-52 !py-1.5">
                      <option value="">What do they need?</option>
                      {pack.documents.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
                    </Select>
                    <Button size="sm" disabled={!goal} onClick={() => openCase(p)}>Start</Button>
                  </span>
                )}
              </td>
            </tr>
          ))}
        </Table>
      </Card>
    </>
  )
}
