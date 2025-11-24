"use client";import { useEffect,useState } from 'react'
const base=process.env.NEXT_PUBLIC_SAFEOPS_API_BASE||'http://localhost:8787'
type Instance={instance_id:string,role:string,port:number,pid:number,started_at:string}
export default function Page(){
  const [instances,setInstances]=useState<Instance[]>([]);const [loading,setLoading]=useState(true);const [role,setRole]=useState('work')
  const fetchList=async()=>{try{const r=await fetch(`${base}/api/codex/instances`);if(r.ok){const j=await r.json();setInstances(j.instances||[])}}finally{setLoading(false)}}
  useEffect(()=>{fetchList()},[])
  const createInstance=async()=>{const r=await fetch(`${base}/api/codex/instances/create`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({role})});if(r.ok){await fetchList()}}
  const terminate=async(id:string)=>{const r=await fetch(`${base}/api/codex/instances/terminate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({instance_id:id})});if(r.ok){await fetchList()}}
  const health=async(id:string)=>{const r=await fetch(`${base}/api/codex/instances/${id}/health`);const j=r.ok?await r.json():null;window.alert(j?`alive=${j.alive} port=${j.port}`:'health check failed')}
  return (
    <main className="min-h-screen bg-gray-50 p-6" aria-label="Codex Instances">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Codex Instances</h1>
        <div className="p-4 border rounded mb-4">
          <div className="text-sm font-medium mb-2">Create Instance</div>
          <div className="flex items-center gap-2">
            <select aria-label="Role" value={role} onChange={(e)=>setRole(e.target.value)} className="border rounded px-2 py-1">
              <option value="work">work</option><option value="planner">planner</option><option value="auditor">auditor</option>
            </select>
            <button className="border rounded px-3 py-1 text-sm" onClick={createInstance}>Create</button>
          </div>
        </div>
        <div className="p-4 border rounded">
          <div className="text-sm font-medium mb-2">Instances</div>
          {loading? <div className="text-sm text-gray-600">Loading...</div> : (instances.length===0? <div className="text-sm text-gray-600">No instances</div> : (
            <div className="space-y-2">
              {instances.map(it=> (
                <div key={it.instance_id} className="flex items-center justify-between p-2 border rounded">
                  <div className="text-sm">{it.role} • {it.instance_id.slice(0,8)} • port {it.port}</div>
                  <div className="flex items-center gap-2">
                    <button className="border rounded px-3 py-1 text-sm" onClick={()=>health(it.instance_id)}>Health</button>
                    <button className="border rounded px-3 py-1 text-sm" onClick={()=>terminate(it.instance_id)}>Terminate</button>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
