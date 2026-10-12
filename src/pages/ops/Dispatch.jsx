import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import * as ops from '../../api/operations';

const TRIP_STATUSES = ['planned', 'dispatched', 'in_progress', 'completed', 'cancelled'];

export default function Dispatch() {
  const navigate = useNavigate();
  const [pickups, setPickups] = useState([]);
  const [trips, setTrips] = useState([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [pk, tr] = await Promise.all([
        ops.listPickups({ page_size: 100 }),
        ops.listTrips({ page_size: 100 }),
      ]);
      setPickups(pk.items);
      setTrips(tr.items);
      setError('');
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => { await null; if (!cancelled) load(); })();
    return () => { cancelled = true; };
  }, [load]);

  const act = async (fn) => {
    setBusy(true);
    try { await fn(); await load(); } catch (err) { setError(err.message); } finally { setBusy(false); }
  };

  // Group pickups by terminal (location_id).
  const byTerminal = {};
  for (const p of pickups) {
    const k = p.location_id ?? 'unassigned';
    (byTerminal[k] = byTerminal[k] || []).push(p);
  }

  const tripsByStatus = {};
  for (const t of trips) (tripsByStatus[t.status] = tripsByStatus[t.status] || []).push(t);

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="s-tag">Operations</div>
          <h2>Dispatch board</h2>
        </div>
        <button className="btn secondary" onClick={() => navigate('/dock')}>Go to dock →</button>
      </div>

      {error && <div className="auth-error" style={{ marginBottom: 12 }}>{error}</div>}

      <h3 style={{ margin: '8px 0 12px' }}>Pickups</h3>
      {pickups.length === 0 ? (
        <p style={{ color: 'var(--muted)' }}>No pickup requests.</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14, marginBottom: 24 }}>
          {Object.entries(byTerminal).map(([term, list]) => (
            <div key={term} className="glass-card">
              <div className="kv-label" style={{ marginBottom: 8 }}>Terminal {term}</div>
              {list.map(p => (
                <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>Pickup #{p.id}</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)' }}>{p.requested_date || 'no date'} · {p.expected_pieces} pcs</div>
                  </div>
                  <span className={`badge ${p.status === 'completed' ? 'green' : p.status === 'cancelled' ? 'red' : 'amber'}`}>{p.status}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      <h3 style={{ margin: '8px 0 12px' }}>Trips</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 14 }}>
        {TRIP_STATUSES.filter(s => tripsByStatus[s]?.length).map(status => (
          <div key={status} className="glass-card">
            <div className="kv-label" style={{ marginBottom: 8 }}>{status.replace(/_/g, ' ')}</div>
            {tripsByStatus[status].map(t => (
              <div key={t.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <button className="link-btn" onClick={() => navigate(`/trips/${t.id}`)} style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontWeight: 600, padding: 0 }}>
                    {t.trip_number}
                  </button>
                  <span style={{ fontSize: 11, color: 'var(--muted)' }}>{t.type}</span>
                </div>
                <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
                  {(t.status === 'planned' || t.status === 'dispatched') && (
                    <button className="btn" style={{ padding: '4px 10px', fontSize: 11 }} disabled={busy} onClick={() => act(() => ops.dispatchTrip(t.id))}>Dispatch</button>
                  )}
                  {t.status === 'in_progress' && (
                    <button className="btn" style={{ padding: '4px 10px', fontSize: 11 }} disabled={busy} onClick={() => act(() => ops.arriveTrip(t.id))}>Arrive</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ))}
        {trips.length === 0 && <p style={{ color: 'var(--muted)' }}>No trips.</p>}
      </div>
    </div>
  );
}
