import './MapExplorer.css'

export default function MapExplorer() {
  return (
    <div className="map-placeholder">
      <div className="map-message">
        <div className="map-icon">◎</div>
        <div className="map-title">Map View</div>
        <div className="map-sub">Deck.gl + PostGIS pattern-of-life clusters</div>
        <div className="map-sub" style={{ marginTop: 8, fontSize: 11 }}>
          Requires Mordecai3 + location events in database
        </div>
      </div>
    </div>
  )
}
