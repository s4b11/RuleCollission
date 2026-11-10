import { Globe, Plug, Plus, ServerCog, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Badge, Button, Card, Empty, ErrorText, Field, Input, PageTitle, Select, TextArea } from '../components/ui'
import { api, useLoad } from '../lib/api'

const EMPTY_TOOL = { name: '', description: '', url: '', method: 'POST', parameters: '{\n  "type": "object",\n  "properties": {}\n}' }

export default function Tools() {
  const tools = useLoad('/studio/tools')
  const servers = useLoad<any[]>('/studio/mcp-servers')
  const [tool, setTool] = useState(EMPTY_TOOL)
  const [server, setServer] = useState({ name: '', url: '' })
  const [error, setError] = useState('')

  async function run(action: () => Promise<unknown>) {
    try {
      await action()
      setError('')
      tools.reload()
      servers.reload()
    } catch (e) {
      setError(e instanceof SyntaxError ? 'The inputs must be valid JSON' : (e as Error).message)
    }
  }

  const addTool = () => run(async () => {
    await api('/studio/tools', { body: { ...tool, parameters: JSON.parse(tool.parameters) } })
    setTool(EMPTY_TOOL)
  })
  const addServer = () => run(async () => {
    await api('/studio/mcp-servers', { body: server })
    setServer({ name: '', url: '' })
  })

  return (
    <>
      <PageTitle title="Tools and MCP" subtitle="Connect the agent to outside systems. External tools are treated as untrusted and can never record a decision." />
      <ErrorText>{error}</ErrorText>
      <div className="mt-4 grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card title="Your web tools" icon={Globe}>
            {tools.data?.custom.length === 0 && <Empty icon={Globe}>No web tools yet. Add one to let the agent call your own system.</Empty>}
            {tools.data?.custom.map((t: any) => (
              <div key={t.id} className="mb-3 flex items-start justify-between gap-3">
                <div>
                  <span className="font-mono text-xs font-semibold">{t.name}</span> <Badge>{t.method}</Badge>
                  <p className="text-muted">{t.description}</p>
                  <p className="break-all text-xs text-muted">{t.url}</p>
                </div>
                <Button variant="ghost" size="sm" icon={Trash2} aria-label="Delete tool" onClick={() => run(() => api(`/studio/tools/${t.id}`, { method: 'DELETE' }))} />
              </div>
            ))}
          </Card>
          <Card title="Add a web tool" icon={Plus}>
            <div className="space-y-3">
              <Field label="Name" hint="Letters, numbers and underscores."><Input value={tool.name} onChange={(e) => setTool({ ...tool, name: e.target.value })} /></Field>
              <Field label="When should the agent use it?"><Input value={tool.description} onChange={(e) => setTool({ ...tool, description: e.target.value })} /></Field>
              <div className="grid grid-cols-4 gap-3">
                <Field label="Method">
                  <Select value={tool.method} onChange={(e) => setTool({ ...tool, method: e.target.value })}>
                    <option>POST</option>
                    <option>GET</option>
                  </Select>
                </Field>
                <div className="col-span-3">
                  <Field label="Address (https only)"><Input value={tool.url} onChange={(e) => setTool({ ...tool, url: e.target.value })} /></Field>
                </div>
              </div>
              <Field label="Inputs (JSON Schema)">
                <TextArea rows={5} className="font-mono text-xs" value={tool.parameters} onChange={(e) => setTool({ ...tool, parameters: e.target.value })} />
              </Field>
              <Button icon={Plus} disabled={!tool.name || !tool.url} onClick={addTool}>Add tool</Button>
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card title="MCP servers" icon={ServerCog}>
            {servers.data?.length === 0 && <Empty icon={ServerCog}>No MCP servers connected.</Empty>}
            {servers.data?.map((s) => (
              <div key={s.id} className="mb-3 flex items-start justify-between gap-3">
                <div>
                  <b>{s.name}</b>
                  <p className="break-all text-xs text-muted">{s.url}</p>
                </div>
                <Button variant="ghost" size="sm" icon={Trash2} aria-label="Remove server" onClick={() => run(() => api(`/studio/mcp-servers/${s.id}`, { method: 'DELETE' }))} />
              </div>
            ))}
          </Card>
          <Card title="Connect an MCP server" icon={Plug}>
            <div className="space-y-3">
              <Field label="Name"><Input value={server.name} onChange={(e) => setServer({ ...server, name: e.target.value })} /></Field>
              <Field label="Address (https only)" hint="The agent loads this server's tools at the start of each conversation.">
                <Input value={server.url} onChange={(e) => setServer({ ...server, url: e.target.value })} />
              </Field>
              <Button icon={Plug} disabled={!server.name || !server.url} onClick={addServer}>Connect</Button>
            </div>
          </Card>
        </div>
      </div>
    </>
  )
}
