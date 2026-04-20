import { useQuery } from '@tanstack/react-query'
import { getEntityMentions, getNeighbours } from '../../api/client'
import './EntityPanel.css'

const TYPE_COLORS = {
  person: 'var(--node-person)',
  org: 'var(--node-org)',
  gpe: 'var(--node-gpe)',
  loc: 'var(--node-loc)',
}

export default function EntityPanel({ entity, onClose }) {
  const entityId = entity?.id || entity?.entity_id

  const { data: mentions } = useQuery({
    queryKey: ['mentions', entityId],
    queryFn: () => getEntityMentions(entityId, 5).then(r => r.data),
    enabled: !!entityId,
  })

  const { data: neighbours } = useQuery({
    queryKey: ['neighbours', entityId],
    queryFn: () => getNeighbours(entityId, 8).then(r => r.data),
    enabled: !!entityId,
  })

  if (!entity) return null
  const name = entity.canonical_name || entity.canonical_name
  const type = entity.entity_type
  const color = TYPE_COLORS[type] || 'var(--text-dim)'
  const confidence = entity.confidence ?? 0

  return (
    <div className="entity-panel">
      <div className="panel-header">
        <span className="panel-title">Entity Detail</span>
        <span className="panel-close" onClick={onClose}>×</span>
      </div>

      <div className="panel-scroll">
        <div className="entity-card">
          <div className="entity-type-badge" style={{ color, borderColor: color, background: `${color}18` }}>
            {type}
          </div>
          <div className="entity-name">{name}</div>
          <div className="entity-meta">
            <div className="meta-item">
              <span className="meta-label">Confidence</span>
              <span className="meta-value">{confidence.toFixed(2)}</span>
            </div>
            <div className="meta-item">
              <span className="meta-label">Aliases</span>
              <span className="meta-value">{entity.aliases?.length ?? 0}</span>
            </div>
          </div>
        </div>

        {/* Confidence bar */}
        <div className="conf-row">
          <div className="conf-bar">
            <div className="conf-fill" style={{ width: `${confidence * 100}%` }} />
          </div>
        </div>

        {/* Aliases */}
        {entity.aliases?.length > 0 && (
          <div className="panel-section">
            <div className="section-label">Aliases</div>
            <div className="aliases-list">
              {entity.aliases.map((a, i) => (
                <span key={i} className="alias-tag">{a}</span>
              ))}
            </div>
          </div>
        )}

        {/* Neighbours */}
        {neighbours?.neighbours?.length > 0 && (
          <div className="panel-section">
            <div className="section-label">Top Connections</div>
            {neighbours.neighbours.map((n) => (
              <div key={n.entity_id} className="connection-item">
                <div className="conn-dot" style={{ background: TYPE_COLORS[n.entity_type] || '#888' }} />
                <span className="conn-name">{n.canonical_name}</span>
                <span className="conn-weight">×{n.weight}</span>
              </div>
            ))}
          </div>
        )}

        {/* Mentions */}
        {mentions?.items?.length > 0 && (
          <div className="panel-section">
            <div className="section-label">Recent Mentions ({mentions.total})</div>
            {mentions.items.map((m) => (
              <div key={m.id} className="mention-item">
                <div className="mention-score">score {m.score?.toFixed(2)}</div>
                <div className="mention-text">{m.snippet}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
