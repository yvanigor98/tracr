import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Topbar from './components/layout/Topbar'
import Sidebar from './components/layout/Sidebar'
import GraphPage from './pages/GraphPage'
import MapPage from './pages/MapPage'
import EntitiesPage from './pages/EntitiesPage'
import SourcesPage from './pages/SourcesPage'
import './styles/globals.css'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30000 } }
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="scanlines" />
        <div style={{ display:'flex', flexDirection:'column', height:'100vh' }}>
          <Topbar />
          <div style={{ display:'flex', flex:1, overflow:'hidden' }}>
            <Sidebar />
            <main style={{ flex:1, overflow:'hidden', position:'relative' }}>
              <Routes>
                <Route path="/" element={<Navigate to="/graph" replace />} />
                <Route path="/graph" element={<GraphPage />} />
                <Route path="/map" element={<MapPage />} />
                <Route path="/entities" element={<EntitiesPage />} />
                <Route path="/sources" element={<SourcesPage />} />
                <Route path="*" element={<Navigate to="/graph" replace />} />
              </Routes>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
