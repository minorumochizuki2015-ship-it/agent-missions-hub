"use client";

import { useEffect, useState } from "react";

type Mission = {
  id: string;
  title: string;
  status?: string;
  priority?: string;
  updated_at?: string;
  owner?: string;
  open_tasks?: number;
  open_task_groups?: number;
  summary?: string;
  tags?: string[];
};

const formatDate = (iso?: string) => {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toISOString().replace("T", " ").replace("Z", " UTC");
};

const fallbackMissions: Mission[] = [
  {
    id: "fallback-1",
    title: "Sample mission (fallback)",
    status: "pending",
    priority: "normal",
    updated_at: new Date().toISOString(),
    owner: "n/a",
    open_tasks: 0,
    open_task_groups: 0,
    summary: "APIが空の場合に表示されるサンプル",
  },
];

export default function MissionsPage() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<"api" | "fallback">("fallback");

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_MISSIONS_API_BASE || "http://127.0.0.1:8000";
    const controller = new AbortController();
    const fetchMissions = async () => {
      setLoading(true);
      setError(null);
      try {
        const resp = await fetch(`${base}/api/missions`, { signal: controller.signal });
        if (!resp.ok) throw new Error(`status ${resp.status}`);
        const data = (await resp.json()) as Mission[];
        if (Array.isArray(data) && data.length > 0) {
          setMissions(
            data.map((m) => ({
              id: m.id,
              title: m.title || "(no title)",
              status: m.status || "pending",
              priority: m.priority || "normal",
              updated_at: m.updated_at,
              owner: m.owner || "n/a",
              open_tasks: m.open_tasks ?? 0,
              open_task_groups: m.open_task_groups ?? 0,
              summary: m.summary,
              tags: m.tags ?? [],
            })),
          );
          setSource("api");
        } else {
          setMissions(fallbackMissions);
          setSource("fallback");
        }
      } catch (e) {
        setError((e as Error).message);
        setMissions(fallbackMissions);
        setSource("fallback");
      } finally {
        setLoading(false);
      }
    };
    fetchMissions();
    return () => controller.abort();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <header className="mb-4 flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-slate-900">Missions</h1>
        <p className="text-sm text-slate-600">
          {loading ? "Loading…" : `Data source: ${source}`}
          {error ? ` / Error: ${error}` : ""}
        </p>
      </header>

      <section aria-label="Mission list" className="space-y-2">
        {missions.map((m) => (
          <article key={m.id} className="rounded border border-slate-200 bg-white p-3 shadow-sm" data-testid="mission-card">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-lg font-semibold text-slate-900">{m.title}</div>
                <div className="text-xs text-slate-600">
                  status: {m.status || "pending"} / priority: {m.priority || "normal"}
                </div>
                <div className="text-xs text-slate-600">
                  owner: {m.owner || "n/a"} / updated: {formatDate(m.updated_at)}
                </div>
              </div>
              <div className="text-right text-xs text-slate-600">
                <div>open tasks: {m.open_tasks ?? 0}</div>
                <div>open groups: {m.open_task_groups ?? 0}</div>
              </div>
            </div>
            {m.summary ? <p className="mt-2 text-sm text-slate-700">{m.summary}</p> : null}
            {m.tags && m.tags.length > 0 ? (
              <div className="mt-2 flex flex-wrap gap-1">
                {m.tags.map((tag) => (
                  <span key={tag} className="rounded bg-slate-100 px-2 py-1 text-[11px] text-slate-700">
                    {tag}
                  </span>
                ))}
              </div>
            ) : null}
          </article>
        ))}
      </section>
    </div>
  );
}
