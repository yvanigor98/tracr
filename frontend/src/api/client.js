import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Entities
export const searchEntities = (q, entityType, limit = 20, offset = 0) =>
  api.get('/entities/search', { params: { q, entity_type: entityType, limit, offset } })

export const getEntity = (entityId) =>
  api.get(`/entities/${entityId}`)

export const getEntityMentions = (entityId, limit = 20, offset = 0) =>
  api.get(`/entities/${entityId}/mentions`, { params: { limit, offset } })

// Graph
export const getNeighbours = (entityId, limit = 20) =>
  api.get(`/graph/neighbours/${entityId}`, { params: { limit } })

export const getShortestPath = (fromId, toId) =>
  api.get('/graph/path', { params: { from_id: fromId, to_id: toId } })

// Sources
export const getSources = () => api.get('/sources')
export const createSource = (data) => api.post('/sources', data)
export const deleteSource = (sourceId) => api.delete(`/sources/${sourceId}`)

// Jobs
export const triggerJob = (sourceId) => api.post('/jobs/trigger', { source_id: sourceId })
export const getJobStatus = (jobId) => api.get(`/jobs/${jobId}`)

// Health
export const getHealth = () => api.get('/health')
