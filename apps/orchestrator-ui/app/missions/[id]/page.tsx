'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

interface Mission {
    id: string;
    title: string;
    status: string;
    created_at: string;
    updated_at: string;
}

interface TaskGroup {
    id: string;
    title: string;
    status: string;
    kind: string;
    order: number;
}

interface Task {
    id: string;
    group_id: string;
    title: string;
    status: string;
    error?: string;
    output?: any;
}

interface Artifact {
    id: string;
    type: string;
    path: string;
    sha256: string;
}

export default function MissionDetailPage() {
    const params = useParams();
    const missionId = params.id as string;

    const [mission, setMission] = useState<Mission | null>(null);
    const [groups, setGroups] = useState<TaskGroup[]>([]);
    const [tasks, setTasks] = useState<Task[]>([]);
    const [artifacts, setArtifacts] = useState<Artifact[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            try {
                const [missionRes, groupsRes, tasksRes, artifactsRes] = await Promise.all([
                    fetch(`http://127.0.0.1:8765/api/missions/${missionId}`),
                    fetch(`http://127.0.0.1:8765/api/missions/${missionId}/groups`),
                    fetch(`http://127.0.0.1:8765/api/missions/${missionId}/tasks`),
                    fetch(`http://127.0.0.1:8765/api/missions/${missionId}/artifacts`),
                ]);

                if (missionRes.ok) setMission(await missionRes.json());
                if (groupsRes.ok) setGroups(await groupsRes.json());
                if (tasksRes.ok) setTasks(await tasksRes.json());
                if (artifactsRes.ok) setArtifacts(await artifactsRes.json());
            } catch (error) {
                console.error('Error fetching mission details:', error);
            } finally {
                setLoading(false);
            }
        }
        if (missionId) {
            fetchData();
        }
    }, [missionId]);

    if (loading) return <div className="p-8">Loading mission details...</div>;
    if (!mission) return <div className="p-8">Mission not found</div>;

    return (
        <div className="p-8 max-w-6xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2">{mission.title}</h1>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>ID: {mission.id}</span>
                    <span>Created: {new Date(mission.created_at).toLocaleString()}</span>
                    <span
                        className={`px-3 py-1 rounded-full text-sm font-medium ${mission.status === 'completed'
                                ? 'bg-green-100 text-green-800'
                                : mission.status === 'failed'
                                    ? 'bg-red-100 text-red-800'
                                    : mission.status === 'running'
                                        ? 'bg-blue-100 text-blue-800'
                                        : 'bg-gray-100 text-gray-800'
                            }`}
                    >
                        {mission.status}
                    </span>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-6">
                    <h2 className="text-xl font-semibold">Workflow Timeline</h2>
                    {groups.map((group) => (
                        <div key={group.id} className="border rounded-lg p-4 bg-white shadow-sm">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="font-medium text-lg">{group.title}</h3>
                                <span className="text-xs bg-gray-100 px-2 py-1 rounded uppercase">{group.kind}</span>
                            </div>
                            <div className="space-y-3">
                                {tasks
                                    .filter((t) => t.group_id === group.id)
                                    .map((task) => (
                                        <div
                                            key={task.id}
                                            className={`p-3 rounded border-l-4 ${task.status === 'completed'
                                                    ? 'border-green-500 bg-green-50'
                                                    : task.status === 'failed'
                                                        ? 'border-red-500 bg-red-50'
                                                        : 'border-gray-300 bg-gray-50'
                                                }`}
                                        >
                                            <div className="flex justify-between">
                                                <span className="font-medium">{task.title}</span>
                                                <span className="text-xs uppercase">{task.status}</span>
                                            </div>
                                            {task.error && <div className="text-red-600 text-sm mt-1">{task.error}</div>}
                                        </div>
                                    ))}
                            </div>
                        </div>
                    ))}
                </div>

                <div className="space-y-6">
                    <h2 className="text-xl font-semibold">Artifacts</h2>
                    {artifacts.length === 0 ? (
                        <p className="text-gray-500 italic">No artifacts produced yet.</p>
                    ) : (
                        <div className="space-y-3">
                            {artifacts.map((artifact) => (
                                <div key={artifact.id} className="p-4 border rounded-lg bg-white shadow-sm">
                                    <div className="font-medium mb-1">{artifact.type}</div>
                                    <div className="text-sm text-gray-600 break-all font-mono bg-gray-50 p-2 rounded">
                                        {artifact.path}
                                    </div>
                                    <div className="mt-2 text-xs text-gray-400">SHA256: {artifact.sha256.substring(0, 12)}...</div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
