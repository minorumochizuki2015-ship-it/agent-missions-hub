"use client"

import { useCallback, useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

const backgroundClass = "bg-[#0B1020] bg-[radial-gradient(circle_at_20%_20%,rgba(120,140,255,0.18),transparent_30%),radial-gradient(circle_at_80%_10%,rgba(34,197,235,0.16),transparent_26%)]"

export default function SettingsPage() {
  const base = (process.env.NEXT_PUBLIC_SAFEOPS_API_BASE as string) || 'http://localhost:8787'
  const [health, setHealth] = useState<any>(null)
  const [status, setStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [h, s] = await Promise.allSettled([
        fetch(`${base}/api/health/ui`),
        fetch(`${base}/api/orchestrator/status`),
      ])
      if (h.status === 'fulfilled' && h.value.ok) setHealth(await h.value.json())
      if (s.status === 'fulfilled' && s.value.ok) setStatus(await s.value.json())
    } catch {}
    setLoading(false)
  }, [base])

  useEffect(() => { fetchData() }, [fetchData])

  return (
    <section className={`min-h-screen p-10 ${backgroundClass}`} aria-label="SETTINGS canvas">
      <div className="max-w-6xl mx-auto space-y-6 text-slate-200">
        <div className="text-sm text-slate-300/90">Route: /settings</div>
        <h1 className="text-3xl font-semibold tracking-tight text-white drop-shadow-[0_2px_6px_rgba(0,0,0,0.45)]">Settings / Health</h1>
        <p className="text-slate-300/90 leading-relaxed">
          APIベース: {base}
        </p>
        <Button size="sm" className="rounded-full px-4" onClick={fetchData}>Refresh</Button>

        <Card className="glass-card shadow-[0_18px_80px_rgba(0,0,0,0.70)]">
          <CardHeader>
            <CardTitle className="heading-accent text-sm font-semibold">Health Gate</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {loading && <div className="text-white/70 text-xs">Loading...</div>}
            {health && (
              <>
                <div>ok: {String(health.ok)}</div>
                <div>timestamp: {health.timestamp}</div>
                <div>static_exists: {String(health.static_exists)}</div>
              </>
            )}
            {!loading && !health && <div className="text-white/70 text-xs">/api/health/ui から応答がありません</div>}
          </CardContent>
        </Card>

        <Card className="glass-card shadow-[0_18px_80px_rgba(0,0,0,0.70)]">
          <CardHeader>
            <CardTitle className="heading-accent text-sm font-semibold">Orchestrator Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {loading && <div className="text-white/70 text-xs">Loading...</div>}
            {status && (
              <>
                <div>version: {status.server_version || 'n/a'}</div>
                <div>uptime: {status.uptime_seconds ?? 'n/a'} seconds</div>
                <div>agents online: {Array.isArray(status.cli_sessions) ? status.cli_sessions.length : (status.agents_online ?? 'n/a')}</div>
              </>
            )}
            {!loading && !status && <div className="text-white/70 text-xs">/api/orchestrator/status から応答がありません</div>}
          </CardContent>
        </Card>
      </div>
    </section>
  )
}
