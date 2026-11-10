import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { setToken } from '../lib/api'

export type Staff = {
  name: string; email: string; role: string; office: string; is_admin: boolean
  organization: string; subject_label: string
}

const link = ({ isActive }: { isActive: boolean }) =>
  `block rounded-md px-3 py-2 ${isActive ? 'bg-brand-soft font-medium text-brand-dark' : 'text-ink hover:bg-slate-50'}`

export default function Layout({ staff }: { staff: Staff }) {
  const navigate = useNavigate()
  const signOut = () => {
    setToken('')
    navigate('/login')
  }
  return (
    <div className="flex min-h-screen">
      <aside className="flex w-60 shrink-0 flex-col border-r border-line bg-white">
        <div className="border-b border-line px-5 py-4">
          <div className="font-semibold">RuleCollision</div>
          <div className="mt-0.5 text-xs text-muted">{staff.organization}</div>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          <p className="px-3 pt-2 pb-1 text-xs font-semibold uppercase tracking-wide text-muted">Operations</p>
          <NavLink to="/ops" end className={link}>Overview</NavLink>
          <NavLink to="/ops/people" className={link}>{staff.subject_label}s</NavLink>
          <NavLink to="/ops/cases" className={link}>Cases</NavLink>
          <NavLink to="/ops/reviews" className={link}>Review inbox</NavLink>
          <NavLink to="/ops/sessions" className={link}>Conversations</NavLink>
          {staff.is_admin && (
            <>
              <p className="px-3 pt-5 pb-1 text-xs font-semibold uppercase tracking-wide text-muted">Agent Studio</p>
              <NavLink to="/studio/agent" className={link}>Agent</NavLink>
              <NavLink to="/studio/tools" className={link}>Tools and MCP</NavLink>
              <NavLink to="/studio/knowledge" className={link}>Knowledge</NavLink>
              <NavLink to="/studio/rules" className={link}>Rules</NavLink>
              <NavLink to="/studio/channels" className={link}>QR codes and phone</NavLink>
            </>
          )}
        </nav>
        <div className="border-t border-line p-4 text-xs">
          <div className="font-medium">{staff.name}</div>
          <div className="text-muted">{staff.role.replace('_', ' ')} · {staff.office}</div>
          <button onClick={signOut} className="mt-2 text-brand hover:underline">Sign out</button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 p-8">
        <div className="mx-auto max-w-6xl"><Outlet context={staff} /></div>
      </main>
    </div>
  )
}
