import Link from "next/link";

const missions = [
  { id: "mission-1", title: "Mission 1", status: "running" },
  { id: "mission-2", title: "Mission 2", status: "pending" },
];

export default function MissionsPage() {
  return (
    <div className="p-6 space-y-4">
      <header>
        <h1 className="text-2xl font-bold">Missions</h1>
      </header>
      <section aria-label="Mission list">
        <ul className="space-y-2">
          {missions.map((m) => (
            <li key={m.id} className="border rounded p-3 bg-white/50">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold">{m.title}</div>
                  <div className="text-sm text-gray-500">Status: {m.status}</div>
                </div>
                <div className="space-x-2">
                  <Link className="text-blue-600 underline" href={`/missions/${m.id}`}>
                    View
                  </Link>
                  <Link className="text-blue-600 underline" href={`/missions/${m.id}/timeline`}>
                    Timeline
                  </Link>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
