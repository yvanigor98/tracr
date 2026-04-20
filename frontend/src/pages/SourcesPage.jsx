import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getSources, createSource, triggerJob } from '../api/client'

export default function SourcesPage() {
  const qc = useQueryClient()
  const [form, setForm] = useState({ name:'', type:'rss', url:'' })
  const { data } = useQuery({ queryKey:['sources'], queryFn: () => getSources().then(r => r.data) })
  const create = useMutation({ mutationFn: createSource, onSuccess: () => qc.invalidateQueries(['sources']) })
  const trigger = useMutation({ mutationFn: (id) => triggerJob(id) })

  return (
    <div style={{ padding:'20px', overflowY:'auto', height:'100%', background:'var(--bg)' }}>
      <div style={{ fontFamily:'var(--font-mono)', fontSize:'11px', color:'var(--text-dim)', letterSpacing:'0.1em', textTransform:'uppercase', marginBottom:'16px' }}>Sources</div>

      <div style={{ display:'flex', gap:'8px', marginBottom:'20px' }}>
        <input style={{ flex:2, background:'var(--surface2)', border:'1px solid var(--border)', color:'var(--text-bright)', fontFamily:'var(--font-mono)', fontSize:'12px', padding:'8px 12px', borderRadius:'4px', outline:'none' }}
          placeholder="Name" value={form.name} onChange={e => setForm(f=>({...f,name:e.target.value}))} />
        <select style={{ background:'var(--surface2)', border:'1px solid var(--border)', color:'var(--text)', fontFamily:'var(--font-mono)', fontSize:'12px', padding:'8px', borderRadius:'4px', outline:'none' }}
          value={form.type} onChange={e => setForm(f=>({...f,type:e.target.value}))}>
          <option>rss</option><option>whois</option><option>shodan</option>
        </select>
        <input style={{ flex:3, background:'var(--surface2)', border:'1px solid var(--border)', color:'var(--text-bright)', fontFamily:'var(--font-mono)', fontSize:'12px', padding:'8px 12px', borderRadius:'4px', outline:'none' }}
          placeholder="URL / domain / IP" value={form.url} onChange={e => setForm(f=>({...f,url:e.target.value}))} />
        <button onClick={() => create.mutate(form)}
          style={{ background:'var(--accent)', color:'#000', fontFamily:'var(--font-mono)', fontSize:'11px', fontWeight:700, padding:'8px 16px', border:'none', borderRadius:'4px', cursor:'pointer' }}>
          + ADD
        </button>
      </div>

      {data?.map(src => (
        <div key={src.id} style={{ display:'flex', alignItems:'center', gap:'12px', padding:'12px 16px', background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'4px', marginBottom:'8px' }}>
          <div style={{ flex:1 }}>
            <div style={{ fontSize:'13px', fontWeight:600, color:'var(--text-bright)' }}>{src.name}</div>
            <div style={{ fontFamily:'var(--font-mono)', fontSize:'10px', color:'var(--text-dim)', marginTop:'3px' }}>{src.type} · {src.url}</div>
          </div>
          <span style={{ fontFamily:'var(--font-mono)', fontSize:'9px', padding:'2px 8px', borderRadius:'2px', color: src.active ? 'var(--accent3)' : 'var(--text-dim)', border:`1px solid ${src.active ? 'var(--accent3)' : 'var(--border)'}` }}>
            {src.active ? 'active' : 'inactive'}
          </span>
          <button onClick={() => trigger.mutate(src.id)}
            style={{ background:'transparent', border:'1px solid var(--border)', color:'var(--accent)', fontFamily:'var(--font-mono)', fontSize:'10px', padding:'4px 12px', borderRadius:'3px', cursor:'pointer' }}>
            ⟳ run
          </button>
        </div>
      ))}
    </div>
  )
}
