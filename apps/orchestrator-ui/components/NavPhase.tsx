'use client'

import { useEffect, useState } from 'react'

type Props = { location?: 'sidebar' | 'header' }

export default function NavPhase({ location = 'sidebar' }: Props) {
  const phases = [
    { key: 'plan', label: 'PLAN' },
    { key: 'test', label: 'TEST' },
    { key: 'review', label: 'REVIEW' },
    { key: 'release', label: 'RELEASE' },
  ] as const
  const [active, setActive] = useState<string>('plan')

  useEffect(() => {
    const handler = (ev: Event) => {
      const phase = (ev as CustomEvent).detail
      if (typeof phase === 'string') {
        setActive(phase.toLowerCase())
      }
    }
    window.addEventListener('safeops-phase', handler as EventListener)
    return () => window.removeEventListener('safeops-phase', handler as EventListener)
  }, [])

  const send = (p: (typeof phases)[number]) => {
    const phase = p.key
    setActive(phase)
    try { window.dispatchEvent(new CustomEvent('safeops-phase', { detail: phase })) } catch {}
  }

  const baseCls = location === 'sidebar' ? 'block px-3 py-2 rounded hover:bg-gray-100' : 'px-3 py-1 rounded hover:bg-gray-100'
  const ariaLabel = location === 'header' ? 'Navigation phases header' : 'Navigation phases sidebar'

  const idPrefix = location === 'header' ? 'hdr' : 'sbar'

  return (
    <div>
      <nav
        className={location === 'header' ? 'flex items-center gap-2' : 'space-y-1'}
        aria-label={ariaLabel}
        role="tablist"
      >
        {phases.map(p => {
          const current = active === p.key
          const tabId = `${idPrefix}-tab-${p.key}`
          const panelId = `${idPrefix}-panel-${p.key}`
          return (
            <button
              key={p.key}
              id={tabId}
              role="tab"
              aria-label={p.label}
              aria-selected={current}
              aria-controls={panelId}
              tabIndex={current ? 0 : -1}
              type="button"
              className={`${baseCls} ${current ? 'bg-gray-900 text-white' : ''}`}
              onClick={() => send(p)}
            >
              {p.label}
            </button>
          )
        })}
      </nav>
      <div className="sr-only">
        {phases.map(p => {
          const tabId = `${idPrefix}-tab-${p.key}`
          const panelId = `${idPrefix}-panel-${p.key}`
          return (
            <div
              key={panelId}
              id={panelId}
              role="tabpanel"
              aria-labelledby={tabId}
              hidden={active !== p.key}
            >
              {p.label} panel
            </div>
          )
        })}
      </div>
    </div>
  )
}
