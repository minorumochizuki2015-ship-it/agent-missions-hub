interface Props {
  params: { id: string };
}

const timeline = [
  { id: "t1", title: "Draft plan", status: "completed", ts: "08:00" },
  { id: "t2", title: "Run workflow", status: "running", ts: "09:00" },
  { id: "t3", title: "Self-heal retry", status: "queued", ts: "09:30" },
];

export default function MissionTimeline({ params }: Props) {
  const { id } = params;
  return (
    <main className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Timeline: {id}</h1>
      <ol className="space-y-2">
        {timeline.map((item) => (
          <li key={item.id} className="border rounded p-3 bg-white/50">
            <div className="flex justify-between">
              <div className="font-semibold">{item.title}</div>
              <div className="text-sm text-gray-500">{item.ts}</div>
            </div>
            <div className="text-sm text-gray-600">Status: {item.status}</div>
          </li>
        ))}
      </ol>
    </main>
  );
}
