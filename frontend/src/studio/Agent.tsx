import { Eye, Fingerprint, Save, Sparkles, Volume2, Wrench } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Button, Card, ErrorText, Field, Input, PageLoader, PageTitle, Select, Switch, TextArea } from '../components/ui'
import { api, useLoad } from '../lib/api'
import { useProfile, type Profile } from './useProfile'

export default function Agent() {
  const { profile, reload } = useProfile()
  const tools = useLoad('/studio/tools')
  const catalogue = useLoad<any[]>('/ops/catalogue')
  const [form, setForm] = useState<Profile | null>(null)
  const [channel, setChannel] = useState('web')
  const [saved, setSaved] = useState('')
  const [error, setError] = useState('')
  const preview = useLoad(profile ? `/studio/profiles/${profile.id}/preview?channel=${channel}&v=${saved}` : null)

  useEffect(() => { if (profile) setForm(profile) }, [profile])
  if (!form || !tools.data || !catalogue.data) return <PageLoader error={tools.error || catalogue.error} retry={() => Promise.all([tools.reload(), catalogue.reload()])} />

  const set = (field: keyof Profile, value: any) => setForm({ ...form, [field]: value })
  const documents = catalogue.data.find((p) => p.pack_id === form.pack_id)?.documents ?? []

  function toggleTool(name: string) {
    const enabled = form!.enabled_tools.includes(name)
    set('enabled_tools', enabled ? form!.enabled_tools.filter((t) => t !== name) : [...form!.enabled_tools, name])
  }

  async function save() {
    try {
      await api(`/studio/profiles/${form!.id}`, { method: 'PUT', body: form })
      setError('')
      setSaved(new Date().toLocaleTimeString())
      reload()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <>
      <PageTitle title="Agent" subtitle="Changes apply to the next conversation. Nothing needs to be redeployed."
        action={<span className="flex items-center gap-3">{saved && <span className="text-xs text-muted">Saved {saved}</span>}<Button icon={Save} onClick={save}>Save changes</Button></span>} />
      {error && <div className="mb-4"><ErrorText>{error}</ErrorText></div>}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card title="Personality" icon={Sparkles}>
            <div className="space-y-4">
              <Field label="Name"><Input value={form.name} onChange={(e) => set('name', e.target.value)} /></Field>
              <Field label="Greeting" hint="Spoken at the start of every conversation.">
                <Input value={form.greeting} onChange={(e) => set('greeting', e.target.value)} />
              </Field>
              <Field label="Extra instructions"
                hint="Added after the fixed safety rules built into the agent. The safety rules cannot be changed here.">
                <TextArea rows={5} value={form.prompt} onChange={(e) => set('prompt', e.target.value)} />
              </Field>
            </div>
          </Card>

          <Card title="Voice" icon={Volume2}>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Speech to text">
                <Select value={form.stt_provider} onChange={(e) => set('stt_provider', e.target.value)}>
                  <option value="deepgram">Deepgram</option>
                  <option value="cartesia">Cartesia</option>
                </Select>
              </Field>
              <Field label="Text to speech">
                <Select value={form.tts_provider} onChange={(e) => set('tts_provider', e.target.value)}>
                  <option value="deepgram">Deepgram</option>
                  <option value="cartesia">Cartesia</option>
                </Select>
              </Field>
              <div className="col-span-2">
                <Field label="Voice" hint="A Deepgram voice model name or a Cartesia voice id. Leave empty for the default.">
                  <Input value={form.voice} onChange={(e) => set('voice', e.target.value)} />
                </Field>
              </div>
            </div>
          </Card>

          <Card title="Identifying the person" icon={Fingerprint}>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Identifier"><Input value={form.identifier_label} onChange={(e) => set('identifier_label', e.target.value)} /></Field>
              <Field label="Second check (optional)">
                <Input value={form.second_factor_label} onChange={(e) => set('second_factor_label', e.target.value)} />
              </Field>
              <Field label="Attempts allowed">
                <Input type="number" min={1} value={form.max_attempts} onChange={(e) => set('max_attempts', Number(e.target.value))} />
              </Field>
              <Field label="Case opened after identification">
                <Select value={form.default_goal} onChange={(e) => set('default_goal', e.target.value)}>
                  <option value="">Ask what they need</option>
                  {documents.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </Select>
              </Field>
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card title="Built-in tools" icon={Wrench} flush
            action={<span className="text-xs text-muted">{form.enabled_tools.length} of {tools.data.builtin.length} on</span>}>
            <p className="border-b border-line bg-slate-50/70 px-5 py-2.5 text-xs text-muted">
              Tools can read records, propose and take notes. No tool can record a staff decision.
            </p>
            <ul className="divide-y divide-line">
              {tools.data.builtin.map((tool: any) => (
                <li key={tool.name} className="flex items-start justify-between gap-4 px-5 py-3">
                  <span>
                    <span className="font-mono text-xs font-semibold text-ink">{tool.name}</span>
                    <span className="block text-sm text-muted">{tool.description}</span>
                  </span>
                  <Switch label={tool.name} checked={form.enabled_tools.includes(tool.name)} onChange={() => toggleTool(tool.name)} />
                </li>
              ))}
            </ul>
          </Card>

          <Card title="What the agent receives at session start" icon={Eye}
            action={
              <Select value={channel} onChange={(e) => setChannel(e.target.value)} className="!w-28 !py-1">
                <option value="web">Web</option>
                <option value="phone">Phone</option>
              </Select>
            }>
            {preview.data && (
              <>
                <pre className="max-h-64 overflow-auto rounded-lg bg-side p-4 font-mono text-xs leading-relaxed whitespace-pre-wrap text-slate-200">{preview.data.instructions}</pre>
                <p className="mt-3 text-xs text-muted">
                  Tools: {preview.data.tools.map((t: any) => t.name).join(', ') || 'none'}
                  {preview.data.mcp_servers.length > 0 && <> · MCP: {preview.data.mcp_servers.join(', ')}</>}
                </p>
              </>
            )}
          </Card>
        </div>
      </div>
    </>
  )
}
