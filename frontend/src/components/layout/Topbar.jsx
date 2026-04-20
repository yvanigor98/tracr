import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Topbar.css'

export default function Topbar({ onSearch }) {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  const handleSearch = (e) => {
    e.preventDefault()
    if (query.trim()) onSearch?.(query.trim())
  }

  return (
    <header className="topbar">
      <div className="logo">
        <div className="logo-dot" />
        TRACR
      </div>

      <form className="search-bar" onSubmit={handleSearch}>
        <span className="search-icon">⌕</span>
        <input
          type="text"
          placeholder="Search entities, IPs, domains, locations..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </form>

      <div className="topbar-actions">
        <span className="badge badge-green">● live</span>
        <div className="avatar">IH</div>
      </div>
    </header>
  )
}
