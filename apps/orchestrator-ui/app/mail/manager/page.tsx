'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'

import managerEn from '@/locales/manager.en.json'
import managerJa from '@/locales/manager.ja.json'

type Lang = 'en' | 'ja'
type Mission = {
  id: string
  title: string
  status: keyof typeof managerEn.statuses
  owner: string
  run_mode: keyof typeof managerEn.runModes
  updated_at: string
}

type TaskGroup = {
  id: string
  mission_id: string
  title: string
  kind: keyof typeof managerEn.kinds
  status: keyof typeof managerEn.statuses
  order: number
  started_at: string
  finished_at: string
}

type Task = {
  id: string
  group_id: string
  title: string
  status: keyof typeof managerEn.statuses
  agent: string
}

type Artifact = {
  id: string
  task_id: string
  type: keyof typeof managerEn.artifactTypes
  scope: string
  version: string
  sha: string
  tags: string[]
}

const MOCK_MISSIONS: Mission[] = [
  {
    id: 'M-001',
    title: 'Inbox i18n rollout',
    status: 'running',
    owner: 'Hayashi',
    run_mode: 'sequential',
    updated_at: '2025-11-28T07:00:00Z'
  },
  {
    id: 'M-002',
    title: 'Self-heal hardening',
    status: 'pending',
    owner: 'Sato',
    run_mode: 'parallel',
    updated_at: '2025-11-27T15:30:00Z'
  }
]

const MOCK_GROUPS: TaskGroup[] = [
  {
    id: 'G-101',
    mission_id: 'M-001',
    title: 'Gateway',
    kind: 'sequential',
    status: 'completed',
    order: 1,
    started_at: '2025-11-28T06:00:00Z',
    finished_at: '2025-11-28T06:30:00Z'
  },
  {
    id: 'G-102',
    mission_id: 'M-001',
    title: 'UI Gate',
    kind: 'parallel',
    status: 'running',
    order: 2,
    started_at: '2025-11-28T06:40:00Z',
    finished_at: ''
  },
  {
    id: 'G-201',
    mission_id: 'M-002',
    title: 'Plan authoring',
    kind: 'sequential',
    status: 'pending',
    order: 1,
    started_at: '',
    finished_at: ''
  }
]

const MOCK_TASKS: Task[] = [
  { id: 'T-1', group_id: 'G-102', title: 'Run Playwright JA', status: 'running', agent: 'QA-Bot' },
  { id: 'T-2', group_id: 'G-102', title: 'Run Playwright EN', status: 'pending', agent: 'QA-Bot' },
  { id: 'T-3', group_id: 'G-201', title: 'Draft spec', status: 'pending', agent: 'Planner' }
]

const MOCK_ARTIFACTS: Artifact[] = [
  {
    id: 'A-1',
    task_id: 'T-1',
    type: 'test',
    scope: 'project',
    version: 'v1.0',
    sha: 'abc1234',
    tags: ['playwright', 'ui-audit']
  },
  {
    id: 'A-2',
    task_id: 'T-1',
    type: 'screenshot',
    scope: 'project',
    version: 'v1.0',
    sha: 'def5678',
    tags: ['ui', 'manager']
  }
]

type Message = {
  id: string
  title: string
  body: string
  ts: string
}

type Signal = {
  id: string
  type: string
  severity: string
  status: string
  created_at: string
  message?: string
}

function useI18n(lang: Lang) {
  const dict = lang === 'ja' ? managerJa : managerEn
  return dict
}

function formatIso(iso: string) {
  if (!iso) return '—'
  const d = new Date(iso)
  // Render deterministically regardless of server/client locale.
  return d.toISOString().replace('T', ' ').replace('Z', ' UTC')
}

export default function ManagerPage({
  searchParams
}: {
  searchParams?: { lang?: string }
}) {
  const langParam = (searchParams?.lang || 'en').toLowerCase()
  const lang: Lang = langParam === 'ja' ? 'ja' : 'en'
  const t = useI18n(lang)
  const featureOn = (process.env.NEXT_PUBLIC_FEATURE_MANAGER_UI || 'true').toLowerCase() === 'true'

  const [missions, setMissions] = useState<Mission[]>([])
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [fromApi, setFromApi] = useState(false)
  const [fetched, setFetched] = useState(false)
  const [query, setQuery] = useState('')
  const [signals, setSignals] = useState<Signal[]>([])

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_MISSIONS_API_BASE || 'http://127.0.0.1:8000'
    const controller = new AbortController()
    const fetchMissions = async () => {
      setLoading(true)
      setApiError(null)
      try {
        const resp = await fetch(`${base}/api/missions`, { signal: controller.signal })
        if (!resp.ok) throw new Error(`status ${resp.status}`)
        const data = (await resp.json()) as Mission[]
        if (Array.isArray(data) && data.length > 0) {
          setFromApi(true)
          setMissions(
            data.map((m) => ({
              ...m,
              owner: (m as any).owner || 'n/a',
              run_mode: (m as any).run_mode || 'sequential',
              updated_at: m.updated_at || new Date().toISOString()
            }))
          )
        } else {
          setFromApi(false)
          setApiError('empty')
        }
      } catch (e) {
        setFromApi(false)
        setApiError((e as Error).message)
      } finally {
        setFetched(true)
        setLoading(false)
      }
    }
    fetchMissions()
    const fetchSignals = async () => {
      try {
        const resp = await fetch(`${base}/api/signals?limit=20`, { signal: controller.signal })
        if (!resp.ok) return
        const data = (await resp.json()) as { signals?: Signal[] }
        if (data.signals) setSignals(data.signals)
      } catch (e) {
        /* noop */
      }
    }
    fetchSignals()
    return () => controller.abort()
  }, [])

  const [selectedMission] = missions
  const groups = useMemo(
    () =>
      selectedMission
        ? MOCK_GROUPS.filter((g) => g.mission_id === selectedMission.id).sort((a, b) => a.order - b.order)
        : [],
    [selectedMission?.id]
  )
  const tasks = selectedMission ? MOCK_TASKS.filter((t) => groups.some((g) => g.id === t.group_id)) : []
  const artifacts = selectedMission
    ? MOCK_ARTIFACTS.filter((a) => tasks.some((t) => t.id === a.task_id))
    : []

  const messages: Message[] = missions.slice(0, 3).map((m, i) => ({
    id: `msg-${m.id}-${i}`,
    title: `${m.title} - update`,
    body: `${t.statuses[m.status]} @ ${formatIso(m.updated_at)}`,
    ts: m.updated_at
  }))

  if (!featureOn) {
    return (
      <section className="min-h-screen bg-slate-50 p-6">
        <div className="mx-auto max-w-4xl space-y-4">
          <h1 className="text-2xl font-semibold" data-testid="manager-disabled-title">
            {t.disabledTitle}
          </h1>
          <p className="text-sm text-slate-600">{t.disabledBody}</p>
          <Link className="text-blue-600 underline" href="/mail/unified-inbox">
            {t.backToInbox}
          </Link>
        </div>
      </section>
    )
  }

  const toggleLang = lang === 'en' ? 'ja' : 'en'
  const toggleHref = `/mail/manager?lang=${toggleLang}`
  const filteredMissions = missions.filter((m) =>
    m.title.toLowerCase().includes(query.toLowerCase())
  )
  const showApiAlert = fetched && (!fromApi || apiError !== null || missions.length === 0)
  const alertDetail = apiError && apiError !== 'empty' ? ` (${apiError})` : ''
  const navItems = [
    { key: 'plan', label: t.navPlan },
    { key: 'test', label: t.navTest },
    { key: 'review', label: t.navReview },
    { key: 'release', label: t.navRelease }
  ]
  const runningCount = missions.filter((m) => m.status === 'running').length
  const pendingCount = missions.filter((m) => m.status === 'pending').length
  const completedCount = missions.filter((m) => m.status === 'completed').length

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <div className="mx-auto max-w-7xl p-4 lg:p-6">
      <div className="flex flex-col gap-4 xl:flex-row">
        <aside className="hidden w-52 flex-shrink-0 flex-col gap-2 border-r border-slate-800 bg-slate-900/80 p-3 xl:flex">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{t.navSection}</div>
          {navItems.map((item) => (
            <button
              key={item.key}
              type="button"
              className="w-full rounded border border-slate-800 bg-slate-900 px-3 py-2 text-left text-sm font-medium text-slate-100 hover:border-indigo-500"
            >
              {item.label}
            </button>
          ))}
        </aside>
        <main className="flex-1 space-y-4">
      <header className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-50" data-testid="manager-title">
            {t.pageTitle}
          </h1>
          <p className="text-xs text-slate-300">
            {loading
              ? 'Loading…'
              : showApiAlert
                ? `${t.apiAlertTitle}${alertDetail}`
                : `${missions.length} missions`}
          </p>
          <div className="text-[11px] font-medium uppercase tracking-wide text-slate-300">
            Data:{' '}
            <span className="rounded-full bg-slate-800 px-2 py-1 text-[10px] font-semibold text-slate-100 ring-1 ring-slate-700">
              {fromApi ? 'API' : 'mock'}
            </span>
          </div>
        </div>
        <Link
          href={toggleHref}
          className="text-sm text-blue-700 underline"
          data-testid="language-toggle"
        >
          {t.langToggle}: {toggleLang.toUpperCase()}
        </Link>
      </header>
      <div className="mb-4 flex flex-wrap gap-2">
        {navItems.map((item) => (
          <button
            key={item.key}
            type="button"
            className="rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-slate-50 shadow-sm ring-1 ring-slate-700"
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg bg-slate-900/80 px-3 py-2 text-sm shadow-sm ring-1 ring-slate-800">
          <div className="text-xs font-semibold uppercase text-slate-300">Running</div>
          <div className="text-base font-semibold text-emerald-100">{runningCount}</div>
        </div>
        <div className="rounded-lg bg-slate-900/80 px-3 py-2 text-sm shadow-sm ring-1 ring-slate-800">
          <div className="text-xs font-semibold uppercase text-slate-300">Pending</div>
          <div className="text-base font-semibold text-amber-100">{pendingCount}</div>
        </div>
        <div className="rounded-lg bg-slate-900/80 px-3 py-2 text-sm shadow-sm ring-1 ring-slate-800">
          <div className="text-xs font-semibold uppercase text-slate-300">Completed</div>
          <div className="text-base font-semibold text-slate-50">{completedCount}</div>
        </div>
        <div className="rounded-lg bg-slate-900/80 px-3 py-2 text-sm shadow-sm ring-1 ring-slate-800">
          <div className="text-xs font-semibold uppercase text-slate-300">Signals</div>
          <div className="text-base font-semibold text-sky-100">{signals.length}</div>
        </div>
      </div>
      {showApiAlert && (
        <div className="mb-4 rounded-md border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-50" role="alert">
          <div className="font-semibold text-rose-50">{t.apiAlertTitle}</div>
          <div>
            {t.apiAlertBody}
            {alertDetail}
          </div>
          <div className="text-xs text-rose-100/80">{t.apiAlertHint}</div>
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-4">
        <section className="rounded-lg bg-white p-4 shadow-sm ring-1 ring-slate-100 xl:col-span-1" aria-label={t.liveMissions}>
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">{t.liveMissions}</h2>
            <span className="text-[11px] text-slate-600">{fromApi ? 'API' : 'mock'}</span>
          </div>
          <div className="space-y-2">
            {missions.length === 0 && <p className="text-sm text-slate-600">{t.liveMissionsEmpty}</p>}
            {missions.slice(0, 5).map((m) => (
              <article key={m.id} className="rounded border border-slate-200 p-3" data-testid="live-mission-card">
                <p className="font-medium text-slate-900">{m.title}</p>
                <p className="text-xs text-slate-600">
                  {t.status}: {t.statuses[m.status]} · {t.owner}: {m.owner}
                </p>
                <p className="text-[11px] text-slate-600">
                  {t.liveMissionsUpdated}: {formatIso(m.updated_at)}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="rounded-lg bg-white p-4 shadow-sm ring-1 ring-slate-100 xl:col-span-1" aria-label={t.missions}>
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">{t.missions}</h2>
          </div>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t.searchPlaceholder}
            className="mb-3 w-full rounded border border-slate-200 px-3 py-2 text-sm"
          />
          <ul className="divide-y divide-slate-200">
            {filteredMissions.map((m) => (
              <li key={m.id} className="py-2" data-testid="mission-row">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-900">{m.title}</p>
                    <p className="text-xs text-slate-600">
                      {t.owner}: {m.owner} · {t.runMode}: {t.runModes[m.run_mode]}
                    </p>
                  </div>
                  <span className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-800">
                    {t.statuses[m.status]}
                  </span>
                </div>
                <p className="text-xs text-slate-600">
                  {t.updatedAt}: {formatIso(m.updated_at)}
                </p>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-lg bg-white p-4 shadow-sm xl:col-span-2" aria-label={t.taskGroups}>
          <div className="mb-4 grid gap-3 lg:grid-cols-2">
            <div className="rounded border border-slate-200 p-3">
              <div className="mb-2 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">{t.taskGroups}</h2>
                <span className="text-[11px] text-slate-600">{groups.length} items</span>
              </div>
              <div className="space-y-2">
                {groups.map((g) => (
                  <article
                    key={g.id}
                    className="rounded border border-slate-200 p-3"
                    data-testid="taskgroup-card"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-slate-900">{g.title}</p>
                        <p className="text-xs text-slate-800">
                          {t.kind}: {t.kinds[g.kind]} · {t.status}: {t.statuses[g.status]}
                        </p>
                      </div>
                      <span className="rounded bg-indigo-50 px-2 py-1 text-[11px] text-indigo-800">
                        {t.runModes[g.kind] || g.kind}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700">
                      {t.startedAt}: {formatIso(g.started_at)} / {t.finishedAt}: {formatIso(g.finished_at)}
                    </p>
                  </article>
                ))}
              </div>
            </div>

            <div className="rounded border border-slate-200 p-3 space-y-2" data-testid="smoke-card">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900">Smoke Test</h3>
                <span className="rounded bg-emerald-50 px-2 py-1 text-[11px] text-emerald-800">beta</span>
              </div>
              <p className="text-sm text-slate-900">
                Latest runs derive from missions; replace with real smoke-test API when available.
              </p>
              <div className="text-sm text-slate-800">
                <div>Running: {missions.filter((m) => m.status === 'running').length}</div>
                <div>Pending: {missions.filter((m) => m.status === 'pending').length}</div>
                <div>Completed: {missions.filter((m) => m.status === 'completed').length}</div>
              </div>
            </div>
          </div>

          <section className="rounded border border-slate-200 p-3" aria-label={t.tasksArtifacts}>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">{t.tasksArtifacts}</h2>
            <div className="grid gap-2 md:grid-cols-2">
              {tasks.map((task) => (
                <article
                  key={task.id}
                  className="rounded border border-slate-200 p-3"
                  data-testid="task-card"
                >
                  <p className="font-medium text-slate-900">{task.title}</p>
                  <p className="text-xs text-slate-700">
                    {t.status}: {t.statuses[task.status]} · Agent: {task.agent}
                  </p>

                  <div className="mt-2 space-y-1">
                    {artifacts
                      .filter((a) => a.task_id === task.id)
                      .map((a) => (
                        <div
                          key={a.id}
                          className="rounded bg-slate-50 px-2 py-1 text-xs text-slate-700"
                          data-testid="artifact-card"
                        >
                          <div className="flex items-center justify-between">
                            <span>{t.artifactTypes[a.type]}</span>
                            <span className="text-[10px] uppercase text-slate-700">{a.scope}</span>
                          </div>
                          <div className="text-[11px] text-slate-700">
                            {t.version}: {a.version} · {t.sha}: {a.sha}
                          </div>
                          <div className="text-[11px] text-slate-700">
                            {t.tags}: {a.tags.join(', ')}
                          </div>
                        </div>
                      ))}
                  </div>
                </article>
              ))}
            </div>
          </section>
        </section>

        <section className="rounded-lg bg-white p-4 shadow-sm xl:col-span-1" aria-label="Messages">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Messages</h2>
            <span className="text-[11px] text-slate-600">{messages.length} latest</span>
          </div>
          <div className="space-y-2">
            {messages.map((msg) => (
              <article key={msg.id} className="rounded border border-slate-200 p-3" data-testid="message-card">
                <p className="font-medium text-slate-900">{msg.title}</p>
                <p className="text-xs text-slate-600">{formatIso(msg.ts)}</p>
                <p className="text-sm text-slate-700">{msg.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="rounded-lg bg-white p-4 shadow-sm xl:col-span-1" aria-label="Signals">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Signals</h2>
            <span className="text-[11px] text-slate-600">{signals.length} latest</span>
          </div>
          <div className="space-y-2">
            {signals.map((s) => (
              <article key={s.id} className="rounded border border-slate-200 p-3" data-testid="signal-card">
                <div className="flex items-center justify-between text-sm font-medium text-slate-900">
                  <span>{s.type}</span>
                  <span className="text-xs uppercase text-slate-600">{s.severity}</span>
                </div>
                <p className="text-xs text-slate-600">{formatIso(s.created_at)}</p>
                <p className="text-sm text-slate-700">{s.message || '—'}</p>
                <p className="text-[11px] text-slate-600">status: {s.status}</p>
              </article>
            ))}
            {signals.length === 0 && <p className="text-sm text-slate-600">No signals yet</p>}
          </div>
        </section>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        <section className="rounded-lg bg-white p-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wide text-amber-600">{t.dangerousCommands}</div>
          <p className="text-sm text-slate-700">{t.noRecent}</p>
        </section>
        <section className="rounded-lg bg-white p-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wide text-emerald-600">{t.approvals}</div>
          <p className="text-sm text-slate-700">{t.noApprovals}</p>
        </section>
        <section className="rounded-lg bg-white p-4 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wide text-sky-600">{t.externalSignals}</div>
          <p className="text-sm text-slate-700">
            {signals.length === 0 ? t.noSignals : `${signals.length} ${t.latest}`}
          </p>
        </section>
      </div>
        </main>
        <aside className="hidden w-72 flex-shrink-0 flex-col gap-3 border-l border-slate-800 bg-slate-900/70 p-3 xl:flex">
          <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3">
            <div className="text-xs font-semibold uppercase tracking-wide text-amber-100">{t.dangerousCommands}</div>
            <p className="text-sm text-amber-50/90">{t.noRecent}</p>
            <p className="text-xs text-amber-100/80">{t.rightDangerNote}</p>
          </div>
          <div className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-3">
            <div className="text-xs font-semibold uppercase tracking-wide text-emerald-100">{t.approvals}</div>
            <p className="text-sm text-emerald-50/90">{t.noApprovals}</p>
            <p className="text-xs text-emerald-100/80">{t.rightApprovalsNote}</p>
          </div>
          <div className="rounded-lg border border-sky-500/40 bg-sky-500/10 p-3">
            <div className="text-xs font-semibold uppercase tracking-wide text-sky-100">{t.externalSignals}</div>
            <p className="text-sm text-sky-50/90">
              {signals.length === 0 ? t.noSignals : `${signals.length} ${t.latest}`}
            </p>
            <p className="text-xs text-sky-100/80">{t.rightSignalsNote}</p>
          </div>
        </aside>
      </div>
      </div>
    </div>
  )
}
