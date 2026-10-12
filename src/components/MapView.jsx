import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

// Fix the default marker icon paths under bundlers.
const DefaultIcon = L.icon({ iconUrl: icon, shadowUrl: iconShadow, iconSize: [25, 41], iconAnchor: [12, 41] });
L.Marker.prototype.options.icon = DefaultIcon;

function coloredDot(color) {
  return L.divIcon({
    className: '',
    html: `<span style="display:block;width:14px;height:14px;border-radius:50%;background:${color};border:2px solid #fff;box-shadow:0 0 0 1px rgba(0,0,0,0.3)"></span>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

/**
 * MapView — a thin Leaflet wrapper.
 * Props:
 * - center [lat,lng], zoom
 * - markers: [{ id, lat, lng, color?, label? }]
 * - polyline: [[lat,lng], ...]
 */
export default function MapView({ center = [45, -90], zoom = 4, markers = [], polyline = null, height = 480 }) {
  return (
    <div style={{ height, borderRadius: 'var(--radius)', overflow: 'hidden', border: '1px solid var(--border)' }}>
      <MapContainer center={center} zoom={zoom} style={{ height: '100%', width: '100%' }} scrollWheelZoom>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {markers.map(m => (
          <Marker key={m.id} position={[m.lat, m.lng]} icon={m.color ? coloredDot(m.color) : DefaultIcon}>
            {m.label && <Popup>{m.label}</Popup>}
          </Marker>
        ))}
        {polyline && polyline.length > 1 && <Polyline positions={polyline} color="#2563EB" />}
      </MapContainer>
    </div>
  );
}
