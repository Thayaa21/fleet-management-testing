import { useCallback, useEffect, useState } from 'react';
import * as ops from '../../api/operations';
import { ApiError } from '../../api/client';

export default function Dock() {
  const [manifests, setManifests] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [items, setItems] = useState([]);
  const [probill, setProbill] = useState('');
  const [msg, setMsg] = useState(null); // { type: 'error'|'ok', text }
  const [candidates, setCandidates] = useState([]);
  const [busy, setBusy] = useState(false);

  const loadManifests = useCallback(async () => {
    const res = await ops.listManifests({ status: 'open', page_size: 100 });
    setManifests(res.items);
    if (res.items.length && selectedId == null) setSelectedId(res.items[0].id);
  }, [selectedId]);

  useEffect(() => {
    let cancelled = false;
    (async () => { await null; if (!cancelled) loadManifests(); })();
    return () => { cancelled = true; };
  }, [loadManifests]);

  const loadItems = useCallback(async () => {
    if (selectedId == null) { setItems([]); return; }
    const res = await ops.manifestItems(selectedId);
    setItems(res.filter(i => !i.unloaded_at));
  }, [selectedId]);

  useEffect(() => {
    let cancelled = false;
    (async () => { await null; if (!cancelled) loadItems(); })();
    return () => { cancelled = true; };
  }, [loadItems]);

  const doLoad = async (e) => {
    e.preventDefault();
    if (!probill.trim() || selectedId == null) return;
    setBusy(true);
    setMsg(null);
    setCandidates([]);
    try {
      await ops.loadShipment(selectedId, { probill_number: probill.trim() });
      setMsg({ type: 'ok', text: `Loaded ${probill.trim().toUpperCase()}.` });
      setProbill('');
      await loadItems();
    } catch (err) {
      if (err instanceof ApiError && err.code === 'UNKNOWN_EQUIPMENT_ID') {
        setCandidates(err.details?.candidates || []);
        setMsg({ type: 'error', text: err.message });
      } else {
        setMsg({ type: 'error', text: err.message });
      }
    } finally {
      setBusy(false);
    }
  };

  const doUnload = async (shipmentId) => {
    setBusy(true);
    setMsg(null);
    try {
      await ops.unloadShipment(selectedId, { shipment_id: shipmentId });
      await loadItems();
    } catch (err) {
      setMsg({ type: 'error', text: err.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="s-tag">Operations</div>
          <h2>Dock</h2>
        </div>
      </div>

      <div className="form-field" style={{ maxWidth: 360 }}>
        <label className="form-label">Open manifest</label>
        <select className="form-select" value={selectedId ?? ''} onChange={e => setSelectedId(Number(e.target.value))}>
          {manifests.length === 0 && <option value="">No open manifests</option>}
          {manifests.map(m => (
            <option key={m.id} value={m.id}>Manifest #{m.id} · trailer {m.trailer_id}</option>
          ))}
        </select>
      </div>

      {selectedId != null && (
        <>
          <form onSubmit={doLoad} style={{ display: 'flex', gap: 10, alignItems: 'flex-end', margin: '14px 0', maxWidth: 480 }}>
            <div className="form-field" style={{ flex: 1, marginBottom: 0 }}>
              <label className="form-label">Scan / type probill (Enter to load)</label>
              <input className="form-input" value={probill} onChange={e => setProbill(e.target.value)} placeholder="P0000001" autoFocus />
            </div>
            <button className="btn" type="submit" disabled={busy}>Load</button>
          </form>

          {msg && <div className={msg.type === 'error' ? 'auth-error' : 'auth-hint'} style={{ maxWidth: 480, marginBottom: 10 }}>{msg.text}</div>}

          {candidates.length > 0 && (
            <div style={{ marginBottom: 14 }}>
              <div className="small" style={{ marginBottom: 6 }}>Did you mean:</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {candidates.map(c => (
                  <span key={c} className="badge blue">{c}</span>
                ))}
              </div>
            </div>
          )}

          <h3 style={{ margin: '10px 0' }}>On this trailer</h3>
          {items.length === 0 ? (
            <p style={{ color: 'var(--muted)' }}>Nothing loaded.</p>
          ) : (
            <div className="glass-card" style={{ padding: 0, overflow: 'hidden', maxWidth: 620 }}>
              <table className="lb-table">
                <thead><tr><th>Shipment</th><th>HUs</th><th>Loaded</th><th></th></tr></thead>
                <tbody>
                  {items.map(it => (
                    <tr key={it.id}>
                      <td>#{it.shipment_id}</td>
                      <td>{it.handling_units_loaded}</td>
                      <td>{it.loaded_by || '—'}</td>
                      <td style={{ textAlign: 'right' }}>
                        <button className="btn secondary" style={{ padding: '4px 10px', fontSize: 11 }} disabled={busy} onClick={() => doUnload(it.shipment_id)}>Unload</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
