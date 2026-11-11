import { Link2, Phone, Plus, Printer, QrCode } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Button, Card, Field, Input, PageLoader, PageTitle } from '../components/ui'
import { api, API_URL, useLoad } from '../lib/api'
import { useProfile } from './useProfile'

export default function Channels() {
  const { profile, reload } = useProfile()
  const locations = useLoad<any[]>(profile ? `/studio/profiles/${profile.id}/locations` : null)
  const [label, setLabel] = useState('')
  const [phone, setPhone] = useState('')

  useEffect(() => { if (profile) setPhone(profile.phone_number) }, [profile])
  if (!profile) return <PageLoader />

  async function addLocation() {
    await api(`/studio/profiles/${profile!.id}/locations`, { body: { label } })
    setLabel('')
    locations.reload()
  }

  async function savePhone() {
    await api(`/studio/profiles/${profile!.id}`, { method: 'PUT', body: { ...profile, phone_number: phone } })
    reload()
  }

  return (
    <>
      <PageTitle title="QR codes and phone" subtitle="How people reach the assistant" />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="min-w-0 lg:col-span-2">
          <Card title="QR codes" icon={QrCode} action={<Button variant="plain" size="sm" icon={Printer} onClick={() => window.print()}>Print</Button>}>
            <p className="mb-4 text-muted">Each code opens the web app and tells the assistant where it was scanned.</p>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              {(locations.data ?? []).map((l) => (
                <div key={l.id} className="rounded-xl border border-line p-4 text-center">
                  <img src={`${API_URL}/public/qr/${l.id}.svg`} alt={`QR code for ${l.label}`} className="mx-auto h-40 w-40" />
                  <div className="mt-3 font-semibold text-ink">{l.label}</div>
                  <div className="text-xs text-muted">Scan to talk to the assistant</div>
                  <a href={l.link} className="block break-all text-xs text-brand hover:underline">{l.link}</a>
                  <button onClick={() => api(`/studio/locations/${l.id}`, { method: 'DELETE' }).then(locations.reload)}
                    className="mt-1 text-xs text-muted hover:text-red-700 print:hidden">Remove</button>
                </div>
              ))}
            </div>
            <div className="mt-4 flex gap-2 print:hidden">
              <Input placeholder="New location, for example Ward 5 Nursing Station" value={label} onChange={(e) => setLabel(e.target.value)} />
              <Button icon={Plus} disabled={!label} onClick={addLocation}>Add</Button>
            </div>
          </Card>
        </div>
        <div className="space-y-6 print:hidden">
          <Card title="Phone line" icon={Phone}>
            <div className="space-y-3">
              <Field label="Phone number linked to this assistant"
                hint="Enter the number from your LiveKit project. Calls to it reach this assistant and end after 3 minutes.">
                <Input placeholder="+1 555 010 0199" value={phone} onChange={(e) => setPhone(e.target.value)} />
              </Field>
              <Button variant="plain" onClick={savePhone}>Save number</Button>
            </div>
          </Card>
          <Card title="Web link" icon={Link2}>
            <a href={profile.web_link} className="break-all text-brand hover:underline">{profile.web_link}</a>
          </Card>
        </div>
      </div>
    </>
  )
}
