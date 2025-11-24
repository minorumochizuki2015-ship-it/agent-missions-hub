'use client'

import { useCallback, useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function PlanPage() {
  const base = (process.env.NEXT_PUBLIC_SAFEOPS_API_BASE as string) || 'http://localhost:8787'
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${base}/api/plan/summary`)
      if (res.ok) setSummary(await res.json())
    } finally {
      setLoading(false)
    }
  }, [base])

  useEffect(() => { fetchData() }, [fetchData])

  return (
    <section className="min-h-screen p-10 bg-[#0B1020]">
      <div className="max-w-6xl mx-auto space-y-6">
        <header className="soft-section px-6 py-5 flex items-center justify-between border border-white/50">
          <h1 className="text-2xl font-semibold text-white drop-shadow">PLAN</h1>
          <Button onClick={fetchData} className="rounded-full px-5 h-11">Refresh</Button>
        </header>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-sm font-semibold heading-accent">Diff</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs whitespace-pre-wrap break-words bg-white/10 border border-white/30 rounded-xl p-3 min-h-[160px]">
              {(() => {
                if (loading) return 'Loading...'
                const diff = Array.isArray(summary?.diff) ? summary.diff : []
                if (!diff.length) return '差分はまだ記録されていません。'
                return diff
                  .map((step: any) => {
                    const entries = Array.isArray(step.entries) ? step.entries : []
                    return [`# ${step.id || 'step'}`, `status: ${step.status || 'n/a'}`, step.description || '', ...entries.map((e: string) => `+ ${e}`)]
                      .filter(Boolean)
                      .join('\n')
                  })
                  .join('\n\n')
              })()}
            </pre>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-sm font-semibold heading-accent">Signals</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {Array.isArray(summary?.signals) && summary.signals.length ? (
              summary.signals.map((sig: any) => (
                <div key={`${sig.source}-${sig.path}`} className="text-xs">
                  <div className="font-semibold text-white drop-shadow">{sig.source}</div>
                  <div className="text-white/90 break-words leading-relaxed">{sig.summary}</div>
                  <div className="text-[11px] text-white/70 break-all">{sig.path}</div>
                </div>
              ))
            ) : (
              <div className="text-white/70 text-xs">Signals は未検出です</div>
            )}
          </CardContent>
        </Card>
      </div>
    </section>
  )
}
