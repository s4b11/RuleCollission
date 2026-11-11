import type { LucideIcon } from 'lucide-react'
import {
  BookOpen, Bot, FolderOpen, Inbox, LayoutDashboard, LogOut, Menu, MessagesSquare, QrCode, Scale, Users, Wrench, X,
} from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { setToken } from '../lib/api'
import { Avatar } from './ui'

export type Staff = {
  name: string; email: string; role: string; office: string; is_admin: boolean
  organization: string; subject_label: string
}

export function Logo({ light }: { light?: boolean }) {
  return (
    <span className="flex items-center gap-2.5">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-white">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
          <path d="M5 7h9a4 4 0 0 1 0 8H8m0 0 3-3m-3 3 3 3" />
        </svg>
      </span>
      <span className={`text-[15px] font-semibold tracking-tight ${light ? 'text-white' : 'text-ink'}`}>RuleCollision</span>
    </span>
  )
}

function Item({ to, icon: Icon, label, end, onClick }: { to: string; icon: LucideIcon; label: string; end?: boolean; onClick: () => void }) {
  return (
    <NavLink to={to} end={end} onClick={onClick}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
          isActive ? 'bg-white/10 text-white' : 'text-slate-400 hover:bg-white/5 hover:text-white'
        }`}>
      <Icon size={17} />
      {label}
    </NavLink>
  )
}

export default function Layout({ staff }: { staff: Staff }) {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const close = () => setOpen(false)
  const signOut = () => {
    setToken('')
    navigate('/login')
  }
  const heading = 'px-3 pt-5 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500'

  return (
    <div className="min-h-screen lg:flex">
      <div className="flex items-center justify-between bg-side px-4 py-3 lg:hidden">
        <Logo light />
        <button onClick={() => setOpen(!open)} aria-label="Menu" className="text-white">{open ? <X /> : <Menu />}</button>
      </div>

      <aside className={`${open ? 'block' : 'hidden'} bg-side lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-64 lg:shrink-0 lg:flex-col`}>
        <div className="hidden px-5 pt-5 pb-2 lg:block">
          <Logo light />
          <p className="mt-3 truncate text-xs text-slate-400">{staff.organization}</p>
        </div>
        <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 pb-4">
          <p className={heading}>Operations</p>
          <Item to="/ops" end icon={LayoutDashboard} label="Overview" onClick={close} />
          <Item to="/ops/people" icon={Users} label={`${staff.subject_label}s`} onClick={close} />
          <Item to="/ops/cases" icon={FolderOpen} label="Cases" onClick={close} />
          <Item to="/ops/reviews" icon={Inbox} label="Review inbox" onClick={close} />
          <Item to="/ops/sessions" icon={MessagesSquare} label="Conversations" onClick={close} />
          {staff.is_admin && (
            <>
              <p className={heading}>Agent Studio</p>
              <Item to="/studio/agent" icon={Bot} label="Agent" onClick={close} />
              <Item to="/studio/tools" icon={Wrench} label="Tools and MCP" onClick={close} />
              <Item to="/studio/knowledge" icon={BookOpen} label="Knowledge" onClick={close} />
              <Item to="/studio/rules" icon={Scale} label="Rules" onClick={close} />
              <Item to="/studio/channels" icon={QrCode} label="QR codes and phone" onClick={close} />
            </>
          )}
        </nav>
        <div className="flex items-center gap-3 border-t border-white/10 p-4">
          <Avatar name={staff.name} />
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium text-white">{staff.name}</div>
            <div className="truncate text-xs text-slate-400">{staff.role.replace('_', ' ')} · {staff.office.replace('_', ' ')}</div>
          </div>
          <button onClick={signOut} aria-label="Sign out" title="Sign out" className="text-slate-400 hover:text-white">
            <LogOut size={17} />
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1 px-4 py-6 sm:px-8 sm:py-8">
        <div className="mx-auto max-w-6xl min-w-0"><Outlet context={staff} /></div>
      </main>
    </div>
  )
}
