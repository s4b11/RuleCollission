import { useState } from 'react'
import { Link, useNavigate, useOutletContext } from 'react-router-dom'
import type { Staff } from '../components/Layout'
import { Button, Card, PageTitle, Select, StatusBadge, Table } from '../components/ui'
import { api, useLoad } from '../lib/api'

type Person = {
  id: string; identifier: string; name: string; status: string; details: Record<string, any>
  documents: { id: string }[]; case: { id: string; status: string } | null
}

function BedBoard({ people }: { people: Person[] }) {
  const wards: Record<string, Person[]> = {}
  for (const person of people) {
    if (person.status === 'admitted') (wards[person.details.ward] ??= []).push(person)
  }
  return (
    <div className="mb-6 grid grid-cols-2 gap-4">
      {Object.entries(wards).sort().map(([ward, patients]) => (
        <Card key={ward} title={ward}>
          <div className="grid grid-cols-3 gap-2">
            {patients.sort((a, b) => a.details.bed.localeCompare(b.details.bed)).map((p) => (
              <Link key={p.id} to={p.case ? `/ops/cases/${p.case.id}` : '#'}
                className="rounded-md border border-line p-2 hover:border-brand">
                <div className="text-xs text-muted">Bed {p.details.bed}</div>
                <div className="truncate font-medium">{p.name}</div>
                <div className="mt-1">{p.case ? <StatusBadge status={p.case.status} /> : <span className="text-xs text-muted">No case</span>}</div>
              </Link>
            ))}
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
  if (!people.data || !catalogue.data) return null
  const pack = catalogue.data[0]
  const hasWards = people.data.some((p) => p.details.ward)

  async function openCase(person: Person) {
    const result = await api(`/ops/subjects/${person.id}/cases`, { body: { pack_id: pack.pack_id, goal } })
    navigate(`/ops/cases/${result.id}`)
  }

  return (
    <>
      <PageTitle title={`${staff.subject_label}s`} subtitle="Records from the organisation's own system (demo data, all fictional)" />
      {hasWards && <BedBoard people={people.data} />}
      <Card>
        <Table head={['Name', 'Identifier', 'Details', 'Documents on file', 'Case', '']}>
          {people.data.map((p) => (
            <tr key={p.id}>
              <td className="font-medium">{p.name}</td>
              <td className="font-mono text-xs">{p.identifier}</td>
              <td className="text-muted">
                {p.details.ward ? `${p.details.reason} · ${p.details.doctor}` : p.details.team}
              </td>
              <td>{p.documents.length}</td>
              <td>{p.case ? <StatusBadge status={p.case.status} /> : <span className="text-muted">—</span>}</td>
              <td className="text-right">
                {p.case && <Link to={`/ops/cases/${p.case.id}`} className="text-brand hover:underline">Open</Link>}
                {!p.case && opening !== p.id && <Button variant="plain" onClick={() => setOpening(p.id)}>Start a case</Button>}
                {!p.case && opening === p.id && (
                  <span className="flex items-center justify-end gap-2">
                    <Select value={goal} onChange={(e) => setGoal(e.target.value)} className="!w-56">
                      <option value="">What do they need?</option>
                      {pack.documents.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
                    </Select>
                    <Button disabled={!goal} onClick={() => openCase(p)}>Start</Button>
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
