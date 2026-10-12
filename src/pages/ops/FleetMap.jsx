import { useEffect, useState } from 'react';
import MapView from '../../components/MapView';
import { listTractors } from '../../api/equipment';
import { tractorPositions } from '../../api/telematics';

// Staleness thresholds (hours) → color.
function staleColor(recordedAt) {
  if (!recordedAt) return '#9CA3AF'; // no signal (gray)
  const ageH = (Date.now() - new Date(recordedAt).getTime()) / 3.6e6;
  if (ageH < 1) return '#15803D';   // fresh (green)
  if (ageH < 3) return '#B45309';   // stale (amber)
  return '#B91C1C';                 // no recent signal (red)
}

export default function FleetMap() {
  const [markers, setMarkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      await null;
      try {
        const res = await listTractors({ page_size: 100 });
        const withDevice = res.items.filter(t => t.telematics_device_id);
        const points = await Promise.all(withDevice.map(async (t) => {
          try {
            const pos = await tractorPositions(t.id);
            const last = pos.positions[pos.positions.length - 1];
            if (!last) return null;
            return {
              id: t.id, lat: last.lat, lng: last.lng, color: staleColor(last.recorded_at),
              label: `${t.unit_number} · ${new Date(last.recorded_at).toLocaleString()}`,
            };
          } catch {
            return null;
          }
        }));
        if (!cancelled) { setMarkers(points.filter(Boolean)); setError(''); }
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const center = markers.length ? [markers[0].lat, markers[0].lng] : [45, -90];

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="s-tag">Telematics</div>
          <h2>Fleet map</h2>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 16, marginBottom: 12, fontSize: 12, color: 'var(--muted)' }}>
        <span><span style={{ color: '#15803D' }}>●</span> fresh (&lt;1h)</span>
        <span><span style={{ color: '#B45309' }}>●</span> stale (&lt;3h)</span>
        <span><span style={{ color: '#B91C1C' }}>●</span> no recent signal</span>
      </div>

      {error && <div className="auth-error" style={{ marginBottom: 12 }}>{error}</div>}
      {loading ? (
        <p style={{ color: 'var(--muted)' }}>Loading positions…</p>
      ) : markers.length === 0 ? (
        <p style={{ color: 'var(--muted)' }}>No tractor positions yet. Ingest telematics pings to populate the map.</p>
      ) : (
        <MapView center={center} zoom={5} markers={markers} height={520} />
      )}
    </div>
  );
}
