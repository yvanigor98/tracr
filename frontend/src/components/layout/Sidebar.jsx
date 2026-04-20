import { NavLink } from 'react-router-dom'
import './Sidebar.css'

const NAV = [
  { section: 'Intelligence' },
  { to: '/graph',    icon: '◈', label: 'Graph Explorer' },
  { to: '/entities', icon: '⊕', label: 'Entity Search'  },
  { to: '/map',      icon: '◎', label: 'Map View'        },
  { section: 'Collection' },
  { to: '/sources',  icon: '⟳', label: 'Sources'         },
  { to: '/jobs',     icon: '⚡', label: 'Jobs'            },
  { section: 'Reports' },
  { to: '/export',   icon: '▤', label: 'Export'          },
  { to: '/settings', icon: '◧', label: 'Settings'        },
]

export default function Sidebar() {
  return (
    <nav className="sidebar">
      {NAV.map((item, i) =>
        item.section ? (
          <div key={i} className="nav-section">{item.section}</div>
        ) : (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </NavLink>
        )
      )}

      <div className="sidebar-footer">
        <div className="system-status">
          <div className="status-row">
            <span><span className="status-dot dot-green" />API</span>
            <span className="status-val">online</span>
          </div>
          <div className="status-row">
            <span><span className="status-dot dot-green" />Neo4j</span>
            <span className="status-val">connected</span>
          </div>
          <div className="status-row">
            <span><span className="status-dot dot-green" />BentoML</span>
            <span className="status-val">en_trf</span>
          </div>
        </div>
      </div>
    </nav>
  )
}
