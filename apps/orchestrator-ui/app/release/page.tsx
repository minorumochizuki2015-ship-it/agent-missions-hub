"use client"

import { useCallback, useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

interface ReleaseStatus { kpi?: any; signoffs?: Array<{ reviewer: string; notes: string; timestamp: string }>; promotions?: Array<{ ts?: string; stage?: string; status?: string; note?: string }> }

const backgroundClass = "bg-[#0B1020] bg-[radial-gradient(circle_at_20%_20%,rgba(120,140,255,0.18),transparent_30%),radial-gradient(circle_at_80%_10%,rgba(34,197,235,0.16),transparent_26%)]"

export default function ReleasePage() {
  const base = (process.env.NEXT_PUBLIC_SAFEOPS_API_BASE as string) || 'http://localhost:8787'
  const [status, setStatus] = useState<ReleaseStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<string>('')

  const fetchStatus = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${base}/api/release/status`)
      if (res.ok) setStatus(await res.json())
    } catch (e: any) {
      setMessage(e?.message || 'failed to fetch status')
    } finally {
      setLoading(false)
    }
  }, [base])

  const doPromotion = useCallback(async (dry: boolean) => {
    setMessage('')
    try {
      const payload = { task_id: `release_${Date.now()}`, stage: 'production', dry_run: dry }
      const res = await fetch(`${base}/api/orchestrator/promotion`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      if (!res.ok) throw new Error('promotion failed')
      const json = await res.json()
      setMessage(json?.session_id ? `Started: ${json.session_id}` : 'Promotion triggered')
      fetchStatus()
    } catch (e: any) {
      setMessage(e?.message || 'promotion failed')
    }
  }, [base, fetchStatus])

  useEffect(() => { fetchStatus() }, [fetchStatus])

  return (
    <section className={`min-h-screen p-10 ${backgroundClass}`} aria-label="RELEASE canvas">
      <div className="max-w-6xl mx-auto space-y-6 text-slate-200">
        <div className="text-sm text-slate-300/90">Route: /release</div>
        <h1 className="text-3xl font-semibold tracking-tight text-white drop-shadow-[0_2px_6px_rgba(0,0,0,0.45)]">RELEASE</h1>

        <Card className="glass-card shadow-[0_18px_80px_rgba(0,0,0,0.70)]">
          <CardHeader>
            <CardTitle className="heading-accent text-sm font-semibold">Release KPI</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {loading && <div className="text-white/70 text-xs">Loading...</div>}
            <div>Hash Drift Alerts: {status?.kpi?.hash_drift_alert ?? 'n/a'}</div>
            <div>Dangerous w/o Approval: {status?.kpi?.dangerous_without_approval ?? 'n/a'}</div>
            <div>Override Alerts: {status?.kpi?.override_alerts ?? 'n/a'}</div>
            <a className="underline text-white/80 text-xs" href="/docs/operations/runbooks/20251102_release_runbook.md" target="_blank" rel="noreferrer">Release Runbook</a>
          </CardContent>
        </Card>

        <Card className="glass-card shadow-[0_18px_80px_rgba(0,0,0,0.70)]">
          <CardHeader>
            <CardTitle className="heading-accent text-sm font-semibold">Promotion</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex flex-wrap gap-2">
              <Button size="sm" className="rounded-full px-4" onClick={() => doPromotion(true)}>Release (Dry-Run)</Button>
              <Button size="sm" className="rounded-full px-4" onClick={() => doPromotion(false)}>Release to Production</Button>
            </div>
            {message && <div className="text-white/80 text-xs">{message}</div>}
            <div className="text-xs text-white/70 space-y-1">
              <div className="font-semibold">Recent Sign-offs</div>
              {(status?.signoffs || []).slice(-5).map((s, i) => (
                <div key={`${s.timestamp}-${i}`}>{s.reviewer || 'reviewer'}: {s.notes || 'n/a'}</div>
              ))}
              {(status?.signoffs || []).length === 0 && <div>No sign-off entries</div>}
            </div>
            <div className="text-xs text-white/70 space-y-1">
              <div className="font-semibold">Promotion Log</div>
              {(status?.promotions || []).slice(-6).map((p, idx) => (
                <div key={`${p.ts}-${idx}`} className="flex items-center justify-between glass-subcard-sm">
                  <span>{p.ts || 'n/a'}</span>
                  <Badge variant={p.status === 'success' ? 'success' : 'secondary'}>{p.stage || 'n/a'} · {p.status || 'n/a'}</Badge>
                </div>
              ))}
              {(status?.promotions || []).length === 0 && <div className="text-white/70">No promotion entries</div>}
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  )
}
