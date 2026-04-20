import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchEntities } from '../api/client'
import EntityPanel from '../components/graph/EntityPanel'

export default function EntitiesPage() {
  const [q, setQ] = useState('')
  const [selected, setSelected] = useState(null)

  const { data } = useQuery({
    queryKey: ['entities', q],
    queryFn: () => searchEntities(q || undefined).then(r => r.data),
    enabled: true,
  })

  return (
    <div style={{ display:'flex', height:'100%', background:'var(--bg)' }}>
      <div style={{ flex:1, padding:'20px', overflowY:'auto' }}>
        <input
          style={{ width:'100%', background:'var(--surface2)', border:'1px solid var(--border)', color:'var(--text-bright)', fontFamily:'var(--font-mono)', fontSize:'12px', padding:'10px 16px', borderRadius:'4px', outline:'none', marginBottom:'16px' }}
          placeholder="Search entities..."
          value={q}
          onChange={e => setQ(e.target.value)}
        />
        {data?.items?.map(entity => (
          <div key={entity.id}
            onClick={() => setSelected(entity)}
            style={{ padding:'12px 16px', background:'var(--surface)', border:'1px solid var(--border)', borderRadius:'4px', marginBottom:'8px', cursor:'pointer', borderLeft:`3px solid ${entity.entity_type === 'person' ? 'var(--node-person)' : entity.entity_type === 'org' ? 'var(--node-org)' : 'var(--node-gpe)'}` }}>
            <div style={{ fontSize:'14px', fontWeight:700, color:'var(--text-bright)' }}>{entity.canonical_name}</div>
            <div style={{ fontFamily:'var(--font-mono)', fontSize:'10px', color:'var(--text-dim)', marginTop:'4px' }}>{entity.entity_type} · confidence {entity.confidence?.toFixed(2)} · {entity.aliases?.length} aliases</div>
          </div>
        ))}
      </div>
      {selected && (
        <EntityPanel entity={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  )
}
