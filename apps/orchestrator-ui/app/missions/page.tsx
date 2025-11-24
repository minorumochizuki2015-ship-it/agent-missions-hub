'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface Mission {
  id: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export default function MissionsPage() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 2000);
    let mounted = true;
    async function fetchMissions() {
      try {
        const res = await fetch('http://127.0.0.1:8765/api/missions/', { signal: controller.signal });
        if (res.ok) {
          const data = await res.json();
          if (mounted) setMissions(data);
        } else {
          console.error('Failed to fetch missions');
        }
      } catch (error) {
        console.error('Error fetching missions:', error);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    fetchMissions();
    return () => {
      mounted = false;
      clearTimeout(timeout);
      controller.abort();
    };
  }, []);

  if (loading) {
    return <div className="p-8">Loading missions...</div>;
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Missions</h1>
      <div className="grid gap-4">
        {missions.length === 0 ? (
          <p>No missions found.</p>
        ) : (
          missions.map((mission) => (
            <Link
              key={mission.id}
              href={`/missions/${mission.id}`}
              className="block p-6 bg-white rounded-lg border border-gray-200 shadow-sm hover:bg-gray-50 transition-colors"
            >
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">{mission.title}</h2>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    mission.status === 'completed'
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
              <div className="mt-2 text-sm text-gray-500">
                ID: {mission.id} • Updated: {new Date(mission.updated_at).toLocaleString()}
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
