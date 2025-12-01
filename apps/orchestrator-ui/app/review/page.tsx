"use client"

import { useCallback, useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface ApprovalItem { task_id: string; status: string }
interface AuditItem { ts: string; op: string; success: boolean }
interface DangerousEvent { ts: string; id?: string; note?: string; approvals_id?: string; override?: boolean }

const backgroundClass = "bg-[#0B1020] bg-[radial-gradient(circle_at_20%_20%,rgba(120,140,255,0.18),transparent_30%),radial-gradient(circle_at_80%_10%,rgba(34,197,235,0.16),transparent_26%)]"

export default function ReviewPage() {
  const base = (process.env.NEXT_PUBLIC_SAFEOPS_API_BASE as string) || 'http://localhost:8787'
  const [approvals, setApprovals] = useState<ApprovalItem[]>([])
  const [audit, setAudit] = useState<AuditItem[]>([])
  const [dangerous, setDangerous] = useState<DangerousEvent[]>([])
  const [loading, setLoading] = useState(true)

  const parseApprovals = (content: string): ApprovalItem[] => {
    const list: ApprovalItem[] = []
    const lines = content.split('\n')
    for (const line of lines) {
      if (line.includes('|') && !line.includes('---')) {
        const parts = line.split('|').map(p => p.trim())
        if (parts.length >= 3 && parts[0] !== 'appr_id') {
          list.push({ task_id: parts[1], status: parts[2] })
        }
      }
    }
    return list
  }

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await Promise.allSettled([
        fetch(`${base}/api/approvals`),
        fetch(`${base}/api/safeops/audit_summary`),
        fetch(`${base}/api/safeops/events`),
      ])
      if (res[0].status === 'fulfilled' && res[0].value.ok) {
        const txt = await res[0].value.json()
        setApprovals(parseApprovals(txt.content || ''))
      }
      if (res[1].status === 'fulfilled' && res[1].value.ok) {
        const data = await res[1].value.json()
        setAudit(Array.isArray(data?.items) ? data.items : [])
      }
      if (res[2].status === 'fulfilled' && res[2].value.ok) {
        const data = await res[2].value.json()
        setDangerous(Array.isArray(data) ? data : [])
      }
    } catch {}
    setLoading(false)
  }, [base])

  useEffect(() => { fetchData() }, [fetchData])

  const hasOverride = dangerous.some(ev => ev.override)

  return (
    <section className={`min-h-screen p-10 ${backgroundClass}`} aria-label="REVIEW canvas">
      <div className="max-w-6xl mx-auto space-y-6 text-slate-200">
        <div className="text-sm text-slate-300/90">Route: /review</div>
        <h1 className="text-3xl font-semibold tracking-tight text-white drop-shadow-[0_2px_6px_rgba(0,0,0,0.45)]">REVIEW</h1>

        {hasOverride && (
          <Card className="glass-card shadow-[0_18px_80px_rgba(0,0,0,0.70)] border border-red-300/60">
            <CardHeader>
              <CardTitle className="heading-accent text-sm font-semibold text-red-200">Override Alert</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-white/90">
              <div className="text-white/80 text-xs">Override=true の危険コマンドがあります。APPROVALS.md と dangerous_command_events の突合を確認してください。</div>
            </CardContent>
          </Card>
        )}

        <Card className="glass-card shadow-[0_18px_80px_rgba(0,0,0,0.70)]">
          <CardHeader>
            <CardTitle className="heading-accent text-sm font-semibold">Approvals</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {loading && <div className="text-white/70 text-xs">Loading...</div>}
            {!loading && approvals.length === 0 && <div className="text-white/70 text-xs">No approval entries</div>}
            {approvals.slice(0, 12).map((a, idx) => (
              <div key={`${a.task_id}-${idx}`} className="flex items-center justify-between glass-subcard-sm">
                <span className="text-slate-200/90">{a.task_id}</span>
                <Badge variant={a.status === 'approved' ? 'success' : a.status === 'pending' ? 'warning' : 'danger'}>{a.status}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="glass-card shadow-[0_18px_80px_rgba(0,0,0,0.70)]">
          <CardHeader>
            <CardTitle className="heading-accent text-sm font-semibold">Audit Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {loading && <div className="text-white/70 text-xs">Loading...</div>}
            {!loading && audit.length === 0 && <div className="text-white/70 text-xs">No audit entries</div>}
            {audit.slice(0, 12).map((it, idx) => (
              <div key={`${it.op}-${idx}`} className="flex items-center justify-between glass-subcard-sm">
                <span>{it.op}</span>
                <Badge variant={it.success ? 'success' : 'danger'}>{it.success ? 'PASS' : 'FAIL'}</Badge>
              </div>
            ))}
            <div className="text-[11px] text-white/70 space-y-1">
              <a className="underline" href={`${base}/api/ui_audit/sarif`} target="_blank" rel="noopener noreferrer">axe SARIF</a>
              <a className="underline block" href={`${base}/observability/policy/ci_evidence.jsonl`} target="_blank" rel="noopener noreferrer">CI Evidence</a>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card shadow-[0_18px_80px_rgba(0,0,0,0.70)]">
          <CardHeader>
            <CardTitle className="heading-accent text-sm font-semibold">Dangerous Commands</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {loading && <div className="text-white/70 text-xs">Loading...</div>}
            {!loading && dangerous.length === 0 && <div className="text-white/70 text-xs">No events</div>}
            {dangerous.slice(0, 10).map((ev, idx) => (
              <div key={`${ev.ts}-${idx}`} className="glass-subcard-sm space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-white/80 text-xs">{ev.ts}</span>
                  {ev.override && <Badge variant="danger">Override</Badge>}
                </div>
                <div className="text-white/90 break-words">{ev.note || ev.id || 'n/a'}</div>
                <div className="body-muted">Approval: {ev.approvals_id || 'n/a'}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </section>
  )
}
