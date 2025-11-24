interface Props {
  params: { id: string };
}

const sampleArtifact = {
  id: "artifact-1",
  type: "plan",
  version: "v1",
  sha256: "deadbeef",
  tags: ["plan", "self-heal"],
  summary: "Recovery plan for failing task",
};

export default function ArtifactDetail({ params }: Props) {
  const { id } = params;
  return (
    <main className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Artifact: {id}</h1>
      <div className="border rounded p-4 bg-white/50 space-y-1">
        <div>Type: {sampleArtifact.type}</div>
        <div>Version: {sampleArtifact.version}</div>
        <div>SHA256: {sampleArtifact.sha256}</div>
        <div>Tags: {sampleArtifact.tags.join(", ")}</div>
        <div className="text-sm text-gray-600">Summary: {sampleArtifact.summary}</div>
      </div>
    </main>
  );
}
