import Link from "next/link";

interface Props {
  params: { id: string };
}

const taskGroups = [
  { id: "tg-1", title: "Plan", status: "completed" },
  { id: "tg-2", title: "Execute", status: "running" },
];

export default function MissionDetail({ params }: Props) {
  const { id } = params;
  return (
    <main className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Mission: {id}</h1>
      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Task Groups</h2>
        <ul className="space-y-2">
          {taskGroups.map((tg) => (
            <li key={tg.id} className="border rounded p-3 bg-white/50 flex justify-between">
              <div>
                <div className="font-semibold">{tg.title}</div>
                <div className="text-sm text-gray-500">Status: {tg.status}</div>
              </div>
              <Link className="text-blue-600 underline" href={`/missions/${id}/timeline`}>
                Timeline
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
