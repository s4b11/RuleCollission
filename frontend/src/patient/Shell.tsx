import type { ReactNode } from 'react'
import { Logo } from '../components/Layout'

export default function Shell({ context, children }: { context?: string; children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-3 px-4 py-3">
          <Logo />
          {context && <span className="truncate text-xs text-muted">{context}</span>}
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-6 sm:py-10">{children}</main>
    </div>
  )
}
