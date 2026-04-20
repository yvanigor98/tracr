import { useEffect, useRef, useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import Graph from 'graphology'
import { Sigma } from 'sigma'
import { searchEntities, getNeighbours } from '../../api/client'
import EntityPanel from './EntityPanel'
import './GraphExplorer.css'

const TYPE_COLORS = {
  person: '#ff4d6d',
  org: '#00e5ff',
  gpe: '#39ff14',
  loc: '#ffb347',
  date: '#888',
}

export default function GraphExplorer() {
  const containerRef = useRef(null)
  const sigmaRef = useRef(null)
  const graphRef = useRef(null)
  const [selectedEntity, setSelectedEntity] = useState(null)
  const [nodeCount, setNodeCount] = useState(0)
  const [edgeCount, setEdgeCount] = useState(0)

  // Load initial entities
  const { data: entities } = useQuery({
    queryKey: ['entities-graph'],
    queryFn: () => searchEntities(undefined, undefined, 50).then(r => r.data),
  })

  // Init Sigma
  useEffect(() => {
    if (!containerRef.current) return

    const graph = new Graph({ multi: false })
    graphRef.current = graph

    const sigma = new Sigma(graph, containerRef.current, {
      renderEdgeLabels: false,
      defaultEdgeColor: 'rgba(30,45,61,0.8)',
      defaultNodeColor: '#00e5ff',
      labelColor: { color: '#c9d5e0' },
      labelSize: 10,
      labelFont: 'Space Mono, monospace',
      minCameraRatio: 0.1,
      maxCameraRatio: 10,
    })

    sigmaRef.current = sigma

    sigma.on('clickNode', ({ node }) => {
      const attrs = graph.getNodeAttributes(node)
      setSelectedEntity(attrs.entity)
      loadNeighbours(node, attrs.entity)
    })

    return () => { sigma.kill(); sigmaRef.current = null }
  }, [])

  // Populate graph from entities
  useEffect(() => {
    if (!entities?.items || !graphRef.current) return
    const graph = graphRef.current

    entities.items.forEach((entity, i) => {
      const angle = (i / entities.items.length) * 2 * Math.PI
      const r = 3 + Math.random() * 2
      const x = r * Math.cos(angle)
      const y = r * Math.sin(angle)
      const color = TYPE_COLORS[entity.entity_type] || '#888'
      const size = 4 + entity.confidence * 8

      if (!graph.hasNode(entity.id)) {
        graph.addNode(entity.id, {
          x, y, size, color,
          label: entity.canonical_name,
          entity,
        })
      }
    })

    setNodeCount(graph.order)
    setEdgeCount(graph.size)
    sigmaRef.current?.refresh()
  }, [entities])

  const loadNeighbours = useCallback(async (nodeId, entity) => {
    if (!graphRef.current) return
    const graph = graphRef.current

    try {
      const res = await getNeighbours(nodeId, 10)
      const neighbours = res.data?.neighbours || []

      neighbours.forEach((n, i) => {
        const color = TYPE_COLORS[n.entity_type] || '#888'
        if (!graph.hasNode(n.entity_id)) {
          const baseNode = graph.getNodeAttributes(nodeId)
          const angle = (i / neighbours.length) * 2 * Math.PI
          graph.addNode(n.entity_id, {
            x: baseNode.x + 1.5 * Math.cos(angle),
            y: baseNode.y + 1.5 * Math.sin(angle),
            size: 4,
            color,
            label: n.canonical_name,
            entity: n,
          })
        }
        if (!graph.hasEdge(nodeId, n.entity_id) && !graph.hasEdge(n.entity_id, nodeId)) {
          graph.addEdge(nodeId, n.entity_id, {
            size: Math.min(1 + n.weight * 0.1, 4),
            color: 'rgba(0,229,255,0.2)',
          })
        }
      })

      setNodeCount(graph.order)
      setEdgeCount(graph.size)
      sigmaRef.current?.refresh()
    } catch (e) {
      console.warn('Graph neighbours error:', e)
    }
  }, [])

  return (
    <div className="graph-explorer">
      {/* Stats */}
      <div className="graph-stats">
        <div className="stat-chip"><span>{nodeCount}</span> nodes</div>
        <div className="stat-chip"><span>{edgeCount}</span> edges</div>
      </div>

      {/* View tabs */}
      <div className="view-tabs">
        <div className="view-tab active">Graph</div>
        <div className="view-tab" onClick={() => window.location.href='/map'}>Map</div>
        <div className="view-tab" onClick={() => window.location.href='/entities'}>Table</div>
      </div>

      {/* Legend */}
      <div className="graph-legend">
        <div className="legend-title">Entity Types</div>
        {Object.entries(TYPE_COLORS).slice(0,4).map(([type, color]) => (
          <div key={type} className="legend-item">
            <div className="legend-dot" style={{ background: color }} />
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </div>
        ))}
      </div>

      {/* Sigma container */}
      <div ref={containerRef} className="sigma-container" />

      {/* Entity panel */}
      {selectedEntity && (
        <EntityPanel
          entity={selectedEntity}
          onClose={() => setSelectedEntity(null)}
        />
      )}
    </div>
  )
}
