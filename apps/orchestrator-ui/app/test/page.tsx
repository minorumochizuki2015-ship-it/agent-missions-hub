'use client'

import { useCallback, useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

interface TestHistoryEntry { ts: string; operation: string; success: boolean }
interface UiAuditSummary { metrics?: any; axe_issues_count?: number; lcp_ms?: number; cls?: number; visual_diff_pct?: number }
interface UiCoverageSummary { total?: { statements?: { pct?: number } } }

export default function TestPage() {
  const base = (process.env.NEXT_PUBLIC_SAFEOPS_API_BASE as string) || 'http://localhost:8787'
  const [items, setItems] = useState<TestHistoryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [auditSummary, setAuditSummary] = useState<UiAuditSummary | null>(null)
  const [coverage, setCoverage] = useState<UiCoverageSummary | null>(null)

  const fetchData = useCallback(async () => {
    try {
      const res = await Promise.allSettled([
        fetch(`${base}/api/test/history`),
        fetch(`${base}/api/ui_audit/summary`),
        fetch(`${base}/api/ui_audit/coverage/ui`),
      ])
      if (res[0].status === 'fulfilled' && res[0].value.ok) {
        const json = await res[0].value.json()
        setItems(Array.isArray(json?.items) ? json.items : [])
      }
      if (res[1].status === 'fulfilled' && res[1].value.ok) {
        setAuditSummary(await res[1].value.json())
      }
      if (res[2].status === 'fulfilled' && res[2].value.ok) {
        setCoverage(await res[2].value.json())
      }
    } finally {
      setLoading(false)
    }
  }, [base])

  useEffect(() => { fetchData() }, [fetchData])

  return (
    <section className="min-h-screen p-10 bg-[#0B1020]">
      <div className="max-w-6xl mx-auto space-y-6">
        <header className="soft-section px-6 py-5 flex items-center justify-between border border-white/50">
          <h1 className="text-2xl font-semibold text-white drop-shadow">TEST</h1>
          <Button onClick={fetchData} className="rounded-full px-5 h-11">Refresh</Button>
        </header>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-sm font-semibold heading-accent">CI Timeline</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {loading && <div className="text-white/70 text-xs">Loading...</div>}
            {!loading && items.length === 0 && <div className="text-white/70 text-xs">No CI events</div>}
            {items.slice(-12).reverse().map((item, idx) => (
              <div key={`${item.ts}-${idx}`} className="flex items-center justify-between text-xs border border-white/40 bg-white/20 rounded-lg p-2">
                <span>{item.operation}</span>
                <Badge variant={item.success ? 'success' : 'danger'}>{item.success ? 'PASS' : 'FAIL'}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-sm font-semibold heading-accent">Nightly UI Gate</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-white/90">
            {loading && <div className="text-white/70 text-xs">Loading...</div>}
            {auditSummary ? (
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>axe: {auditSummary.metrics?.axe_issues_count ?? auditSummary.axe_issues_count ?? 'n/a'}</div>
                <div>LCP: {auditSummary.metrics?.lcp_ms ?? auditSummary.lcp_ms ?? 'n/a'} ms</div>
                <div>TTI: {auditSummary.metrics?.tti_ms ?? auditSummary.metrics?.tti ?? 'n/a'} ms</div>
                <div>CLS: {auditSummary.metrics?.cls ?? auditSummary.cls ?? 'n/a'}</div>
                <div>Visual Diff: {auditSummary.metrics?.visual_diff_pct ?? auditSummary.visual_diff_pct ?? 'n/a'}%</div>
              </div>
            ) : (!loading && <div className="text-white/70 text-xs">Nightly summary not found</div>)}
            <div className="text-xs text-white/70 space-y-1">
              <a className="underline" href={`${base}/api/ui_audit/report`} target="_blank" rel="noopener noreferrer">report.html</a>
              <div className="flex items-center gap-2">
                <a className="underline" href={`${base}/api/ui_audit/screens/current.png`} target="_blank" rel="noopener noreferrer">current.png</a>
                <a className="underline" href={`${base}/api/ui_audit/screens/diff.png`} target="_blank" rel="noopener noreferrer">diff.png</a>
              </div>
              <div>Coverage: {typeof coverage?.total?.statements?.pct === 'number' ? `${coverage.total.statements.pct}%` : 'n/a'}</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  )
}
