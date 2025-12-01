'use client'

import { useEffect, useState } from 'react'

export default function FooterStatus() {
  const base = (process.env.NEXT_PUBLIC_SAFEOPS_API_BASE as string) || 'http://localhost:8787'
  const [ts, setTs] = useState<string>('n/a')
  const [heal, setHeal] = useState<string>('n/a')
  const [sessions, setSessions] = useState<number>(0)
  useEffect(() => {
    const load = async () => {
      try {
        const s = await fetch(`${base}/api/orchestrator/status`).then(r => r.ok ? r.json() : null)
        const k = await fetch(`${base}/api/safeops/kpi`).then(r => r.ok ? r.json() : null)
        setTs(s?.timestamp || 'n/a')
        setHeal(String(k?.health_score ?? 'n/a'))
        setSessions(Array.isArray(s?.cli_sessions) ? s.cli_sessions.length : 0)
      } catch {}
    }
    load()
    const id = setInterval(load, 60000)
    return () => clearInterval(id)
  }, [base])
  return (
    <div className="max-w-7xl mx-auto px-4 py-3 text-sm text-gray-600 flex items-center justify-between">
      <div>
        <span className="font-medium">Activity:</span> {ts}
      </div>
      <div>
        <span className="font-medium">Self-Heal:</span> {heal}
      </div>
      <div>
        <span className="font-medium">Sessions:</span> {sessions}
      </div>
    </div>
  )
}