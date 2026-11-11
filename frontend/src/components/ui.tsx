import type { LucideIcon } from 'lucide-react'
import { AlertCircle, Inbox } from 'lucide-react'
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react'
import { STATUS, type Tone } from '../lib/labels'

const TONES: Record<Tone, { badge: string; dot: string; icon: string }> = {
  gray: { badge: 'bg-slate-100 text-slate-700 ring-slate-200', dot: 'bg-slate-400', icon: 'bg-slate-100 text-slate-600' },
  green: { badge: 'bg-emerald-50 text-emerald-700 ring-emerald-200', dot: 'bg-emerald-500', icon: 'bg-emerald-50 text-emerald-600' },
  amber: { badge: 'bg-amber-50 text-amber-800 ring-amber-200', dot: 'bg-amber-500', icon: 'bg-amber-50 text-amber-600' },
  red: { badge: 'bg-red-50 text-red-700 ring-red-200', dot: 'bg-red-500', icon: 'bg-red-50 text-red-600' },
  blue: { badge: 'bg-brand-soft text-brand-dark ring-blue-200', dot: 'bg-brand', icon: 'bg-brand-soft text-brand' },
}

export function Badge({ tone = 'gray', dot, children }: { tone?: Tone; dot?: boolean; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${TONES[tone].badge}`}>
      {dot && <span className={`h-1.5 w-1.5 rounded-full ${TONES[tone].dot}`} />}
      {children}
    </span>
  )
}

export function StatusBadge({ status }: { status: string }) {
  const known = STATUS[status]
  return <Badge tone={known?.tone} dot>{known?.label ?? status}</Badge>
}

type CardProps = { title?: string; icon?: LucideIcon; action?: ReactNode; children: ReactNode; className?: string; flush?: boolean }

export function Card({ title, icon: Icon, action, children, className = '', flush }: CardProps) {
  return (
    <section className={`min-w-0 rounded-xl border border-line bg-white shadow-card ${className}`}>
      {title && (
        <header className="flex min-h-13 flex-wrap items-center justify-between gap-x-3 gap-y-2 border-b border-line px-4 py-3 sm:px-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold">
            {Icon && <Icon size={16} className="text-muted" />}
            {title}
          </h2>
          {action}
        </header>
      )}
      <div className={flush ? '' : 'p-4 sm:p-5'}>{children}</div>
    </section>
  )
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'plain' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  icon?: LucideIcon
}

export function Button({ variant = 'primary', size = 'md', icon: Icon, className = '', children, ...props }: ButtonProps) {
  const variants = {
    primary: 'bg-brand text-white shadow-card hover:bg-brand-dark',
    plain: 'border border-line bg-white text-body shadow-card hover:bg-slate-50',
    danger: 'border border-red-200 bg-white text-red-700 shadow-card hover:bg-red-50',
    ghost: 'text-muted hover:bg-slate-100 hover:text-ink',
  }
  const sizes = { sm: 'h-8 px-2.5 text-xs', md: 'h-9 px-3.5 text-sm', lg: 'h-12 px-6 text-base' }
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {Icon && <Icon size={size === 'lg' ? 20 : 16} />}
      {children}
    </button>
  )
}

const FIELD =
  'w-full rounded-lg border border-line bg-white px-3 py-2 text-sm text-ink shadow-card outline-none placeholder:text-slate-400 focus:border-brand focus:ring-3 focus:ring-brand/15'

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-body">{label}</span>
      {children}
      {hint && <span className="mt-1.5 block text-xs text-muted">{hint}</span>}
    </label>
  )
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`${FIELD} ${props.className ?? ''}`} />
}

export function TextArea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={`${FIELD} ${props.className ?? ''}`} />
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={`${FIELD} ${props.className ?? ''}`} />
}

export function Switch({ checked, onChange, label }: { checked: boolean; onChange: () => void; label: string }) {
  return (
    <button type="button" role="switch" aria-checked={checked} aria-label={label} onClick={onChange}
      className={`relative h-5 w-9 shrink-0 rounded-full transition-colors ${checked ? 'bg-brand' : 'bg-slate-300'}`}>
      <span className={`absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white shadow-card transition-transform ${checked ? 'translate-x-4' : ''}`} />
    </button>
  )
}

export function PageTitle({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-muted">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

export function Table({ head, children }: { head: string[]; children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-line bg-slate-50/70 text-xs text-muted">
            {head.map((h) => <th key={h} className="px-5 py-2.5 font-medium whitespace-nowrap">{h}</th>)}
          </tr>
        </thead>
        <tbody className="[&>tr]:border-b [&>tr]:border-line [&>tr:hover]:bg-slate-50/60 [&>tr:last-child]:border-0 [&_td]:px-5 [&_td]:py-3 [&_td]:whitespace-nowrap">
          {children}
        </tbody>
      </table>
    </div>
  )
}

export function Empty({ icon: Icon = Inbox, children }: { icon?: LucideIcon; children: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 px-4 py-8 text-center text-muted">
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100"><Icon size={18} /></span>
      <p className="max-w-sm">{children}</p>
    </div>
  )
}

export function ErrorText({ children }: { children: ReactNode }) {
  if (!children) return null
  return (
    <p className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
      <AlertCircle size={16} className="mt-0.5 shrink-0" />
      <span className="whitespace-pre-wrap">{children}</span>
    </p>
  )
}

export function StatTile({ icon: Icon, label, value, tone = 'blue' }: { icon: LucideIcon; label: string; value: number; tone?: Tone }) {
  return (
    <div className="flex min-w-0 flex-col gap-3 rounded-xl border border-line bg-white p-4 shadow-card sm:flex-row sm:items-center sm:gap-4 sm:p-5">
      <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg sm:h-11 sm:w-11 ${TONES[tone].icon}`}><Icon size={18} /></span>
      <div className="min-w-0">
        <div className="text-2xl font-semibold tracking-tight text-ink">{value}</div>
        <div className="text-xs leading-snug text-muted">{label}</div>
      </div>
    </div>
  )
}

export function Avatar({ name, size = 'md' }: { name: string; size?: 'sm' | 'md' }) {
  const initials = name.split(' ').filter((w) => /^[A-Za-z]/.test(w) && !w.endsWith('.')).slice(0, 2).map((w) => w[0]).join('')
  const sizes = { sm: 'h-7 w-7 text-[11px]', md: 'h-9 w-9 text-xs' }
  return (
    <span className={`flex shrink-0 items-center justify-center rounded-full bg-brand-soft font-semibold text-brand-dark ${sizes[size]}`}>
      {initials.toUpperCase()}
    </span>
  )
}

type TabsProps<T extends string> = { tabs: { id: T; label: string; count?: number }[]; value: T; onChange: (id: T) => void }

export function Tabs<T extends string>({ tabs, value, onChange }: TabsProps<T>) {
  return (
    <div className="mb-5 flex gap-1 border-b border-line">
      {tabs.map((tab) => (
        <button key={tab.id} onClick={() => onChange(tab.id)}
          className={`-mb-px flex items-center gap-2 border-b-2 px-3 py-2.5 text-sm font-medium ${
            value === tab.id ? 'border-brand text-brand-dark' : 'border-transparent text-muted hover:text-ink'
          }`}>
          {tab.label}
          {tab.count !== undefined && (
            <span className="rounded-full bg-slate-100 px-1.5 text-xs text-muted">{tab.count}</span>
          )}
        </button>
      ))}
    </div>
  )
}
