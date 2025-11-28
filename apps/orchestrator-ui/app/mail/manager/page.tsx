'use client'

import Link from 'next/link'
import { useMemo } from 'react'

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

function useI18n(lang: Lang) {
  const dict = lang === 'ja' ? managerJa : managerEn
  return dict
}

function formatIso(iso: string) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString()
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

  const missions = MOCK_MISSIONS
  const [selectedMission] = missions
  const groups = useMemo(
    () => MOCK_GROUPS.filter((g) => g.mission_id === selectedMission.id).sort((a, b) => a.order - b.order),
    [selectedMission.id]
  )
  const tasks = MOCK_TASKS.filter((t) => groups.some((g) => g.id === t.group_id))
  const artifacts = MOCK_ARTIFACTS.filter((a) => tasks.some((t) => t.id === a.task_id))

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

  return (
    <main className="min-h-screen bg-slate-50 p-4 lg:p-6">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-semibold" data-testid="manager-title">
          {t.pageTitle}
        </h1>
        <Link
          href={toggleHref}
          className="text-sm text-blue-600 underline"
          data-testid="language-toggle"
        >
          {t.langToggle}: {toggleLang.toUpperCase()}
        </Link>
      </header>

      <div className="grid gap-4 lg:grid-cols-3">
        <section className="rounded-lg bg-white p-4 shadow-sm" aria-label={t.missions}>
          <h2 className="mb-2 text-lg font-semibold">{t.missions}</h2>
          <ul className="divide-y divide-slate-200">
            {missions.map((m) => (
              <li key={m.id} className="py-2" data-testid="mission-row">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{m.title}</p>
                    <p className="text-xs text-slate-500">
                      {t.owner}: {m.owner} · {t.runMode}: {t.runModes[m.run_mode]}
                    </p>
                  </div>
                  <span className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-700">
                    {t.statuses[m.status]}
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  {t.updatedAt}: {formatIso(m.updated_at)}
                </p>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-lg bg-white p-4 shadow-sm" aria-label={t.taskGroups}>
          <h2 className="mb-2 text-lg font-semibold">{t.taskGroups}</h2>
          <div className="space-y-2">
            {groups.map((g) => (
              <article
                key={g.id}
                className="rounded border border-slate-200 p-3"
                data-testid="taskgroup-card"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{g.title}</p>
                    <p className="text-xs text-slate-500">
                      {t.kind}: {t.kinds[g.kind]} · {t.status}: {t.statuses[g.status]}
                    </p>
                  </div>
                  <span className="rounded bg-indigo-50 px-2 py-1 text-[11px] text-indigo-700">
                    {t.runModes[g.kind] || g.kind}
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  {t.startedAt}: {formatIso(g.started_at)} / {t.finishedAt}: {formatIso(g.finished_at)}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="rounded-lg bg-white p-4 shadow-sm" aria-label={t.tasksArtifacts}>
          <h2 className="mb-2 text-lg font-semibold">{t.tasksArtifacts}</h2>
          <div className="space-y-2">
            {tasks.map((task) => (
              <article
                key={task.id}
                className="rounded border border-slate-200 p-3"
                data-testid="task-card"
              >
                <p className="font-medium">{task.title}</p>
                <p className="text-xs text-slate-500">
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
                          <span className="text-[10px] uppercase text-slate-500">{a.scope}</span>
                        </div>
                        <div className="text-[11px] text-slate-500">
                          {t.version}: {a.version} · {t.sha}: {a.sha}
                        </div>
                        <div className="text-[11px] text-slate-500">
                          {t.tags}: {a.tags.join(', ')}
                        </div>
                      </div>
                    ))}
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  )
}
