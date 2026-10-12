import { useCallback, useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as ops from '../../api/operations';

function fmt(dt) {
  return dt ? new Date(dt).toLocaleString() : '—';
}

export default function TripDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [trip, setTrip] = useState(null);
  const [manifests, setManifests] = useState([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const t = await ops.getTrip(id);
      setTrip(t);
      const mf = await ops.listManifests({ trip_id: id, page_size: 100 });
      setManifests(mf.items);
      setError('');
    } catch (err) {
      setError(err.message);
    }
  }, [id]);

  useEffect(() => {
    let cancelled = false;
    (async () => { await null; if (!cancelled) load(); })();
    return () => { cancelled = true; };
  }, [load]);

  const act = async (fn) => {
    setBusy(true);
    try { await fn(); await load(); } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  if (error) return <div className="auth-error">{error}</div>;
  if (!trip) return <p style={{ color: 'var(--muted)' }}>Loading…</p>;

  return (
    <div>
      <button className="btn secondary" style={{ marginBottom: 16 }} onClick={() => navigate('/dispatch')}>← Dispatch</button>

      <div className="page-head">
        <div>
          <div className="s-tag">Trip</div>
          <h2 style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            {trip.trip_number}
            <span className="badge blue">{trip.status.replace(/_/g, ' ')}</span>
          </h2>
          <p style={{ marginTop: 4 }}>{trip.type.replace(/_/g, ' ')}</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {(trip.status === 'planned' || trip.status === 'dispatched') && (
            <button className="btn" disabled={busy} onClick={() => act(() => ops.dispatchTrip(trip.id))}>Dispatch</button>
          )}
          {trip.status === 'in_progress' && (
            <button className="btn" disabled={busy} onClick={() => act(() => ops.arriveTrip(trip.id))}>Arrive</button>
          )}
        </div>
      </div>

      <div className="kv-grid" style={{ marginBottom: 18 }}>
        <div className="kv"><div className="kv-label">Planned departure</div><div className="kv-val">{fmt(trip.planned_departure_at)}</div></div>
        <div className="kv"><div className="kv-label">Actual departure</div><div className="kv-val">{fmt(trip.actual_departure_at)}</div></div>
        <div className="kv"><div className="kv-label">Planned arrival</div><div className="kv-val">{fmt(trip.planned_arrival_at)}</div></div>
        <div className="kv"><div className="kv-label">Actual arrival</div><div className="kv-val">{fmt(trip.actual_arrival_at)}</div></div>
      </div>

      <h3 style={{ margin: '8px 0 10px' }}>Manifests</h3>
      {manifests.length === 0 ? (
        <p style={{ color: 'var(--muted)' }}>No manifests on this trip.</p>
      ) : (
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="lb-table">
            <thead><tr><th>Manifest</th><th>Trailer</th><th>Origin</th><th>Destination</th><th>Status</th></tr></thead>
            <tbody>
              {manifests.map(m => (
                <tr key={m.id}>
                  <td>#{m.id}</td>
                  <td>{m.trailer_id}</td>
                  <td>{m.origin_location_id ?? '—'}</td>
                  <td>{m.destination_location_id ?? '—'}</td>
                  <td><span className="badge blue">{m.status.replace(/_/g, ' ')}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
