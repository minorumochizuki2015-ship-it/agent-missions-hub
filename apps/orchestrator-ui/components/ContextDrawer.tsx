'use client'

import { useEffect, useState } from 'react'

export default function ContextDrawer() {
  const base = (process.env.NEXT_PUBLIC_SAFEOPS_API_BASE as string) || 'http://localhost:8787'
  const [status, setStatus] = useState<any>(null)
  const [kpi, setKpi] = useState<any>(null)
  const [approvalsStats, setApprovalsStats] = useState<any>({})
  const [signals, setSignals] = useState<Array<{ source: string; summary: string }>>([])

  useEffect(() => {
    const load = async () => {
      try {
        const s = await fetch(`${base}/api/orchestrator/status`).then(r => r.ok ? r.json() : null)
        const k = await fetch(`${base}/api/safeops/kpi`).then(r => r.ok ? r.json() : null)
        const a = await fetch(`${base}/api/approvals`).then(r => r.ok ? r.json() : null)
        const d = await fetch(`${base}/api/safeops/events`).then(r => r.ok ? r.json() : [])
        const plan = await fetch(`${base}/api/plan/summary`).then(r => r.ok ? r.json() : null)
        setStatus(s)
        setKpi(k)
        setApprovalsStats(a || {})
        setEvents(Array.isArray(d) ? d : [])
        setSignals(Array.isArray(plan?.signals) ? plan.signals : [])
      } catch {}
    }
    load()
  }, [base])

  const [events, setEvents] = useState<Array<{ ts: string; id?: string; note?: string }>>([])
  const items = events.slice(0, 5)

  return (
    <div className="p-4">
      <section aria-label="SafeOps Timeline" className="mb-4">
        <h2 className="text-sm font-semibold mb-2">Dangerous Commands Timeline</h2>
        <div className="space-y-1 text-xs text-gray-700">
          {items.map((ev: any, i: number) => (
            <div key={i} className="flex items-center justify-between">
              <span>{ev.ts}</span>
              <span className="text-gray-500">{ev.id || ev.note || ''}</span>
            </div>
          ))}
          {items.length === 0 && <div className="text-gray-500">No recent events</div>}
        </div>
      </section>
      <section aria-label="Approvals Ledger" className="mb-4">
        <h2 className="text-sm font-semibold mb-2">Approvals</h2>
        <div className="text-xs text-gray-700 grid grid-cols-2 gap-2">
          <div>pending: {approvalsStats?.pending ?? 0}</div>
          <div>approved: {approvalsStats?.approved ?? 0}</div>
          <div>rejected: {approvalsStats?.rejected ?? 0}</div>
          <div>expired: {approvalsStats?.expired ?? 0}</div>
        </div>
      </section>
      <section aria-label="External Signals">
        <h2 className="text-sm font-semibold mb-2">External Signals</h2>
        <div className="text-xs text-gray-700 space-y-1">
          {signals.length === 0 && (
            <div>No recent signals</div>
          )}
          {signals.map((sig, idx) => (
            <div key={`${sig.source}-${idx}`}>
              <div className="font-medium">{sig.source}</div>
              <div className="text-gray-500">{sig.summary}</div>
            </div>
          ))}
          <div className="pt-2 border-t border-gray-100 text-[11px] text-gray-500">
            Server {status?.server_version ?? 'n/a'} • Uptime {status?.uptime_seconds != null ? `${status.uptime_seconds}s` : 'n/a'} • Self-Heal {kpi?.health_score ?? 0}
          </div>
        </div>
      </section>
    </div>
  )
}
