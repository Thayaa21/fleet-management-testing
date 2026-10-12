import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as shipmentsApi from '../../api/shipments';
import * as billing from '../../api/billing';
import { listAudit } from '../../api/audit';
import { shipmentPositions } from '../../api/telematics';
import { ShipmentStatusChip } from './Shipments';
import EntityDrawer from '../../components/EntityDrawer';
import ConfirmDialog from '../../components/ConfirmDialog';
import MapView from '../../components/MapView';

const EVENT_CODES = [
  'PICKUP_REQUESTED', 'PICKUP_DISPATCHED', 'ARRIVED_AT_PICKUP', 'PICKED_UP',
  'ARRIVED_AT_TERMINAL', 'LOADED_ON_TRAILER', 'DEPARTED_TERMINAL', 'IN_TRANSIT',
  'ARRIVED_AT_DESTINATION_TERMINAL', 'UNLOADED', 'OUT_FOR_DELIVERY',
  'ARRIVED_AT_DELIVERY', 'DELIVERED', 'DELIVERY_ATTEMPTED', 'APPOINTMENT_SET',
  'DELAYED', 'EXCEPTION', 'CUSTOMS_HOLD', 'CUSTOMS_RELEASED',
].map(c => ({ value: c, label: c.replace(/_/g, ' ') }));

const SOURCES = ['manual', 'dock_scan', 'driver_scan', 'telematics', 'api', 'edi']
  .map(s => ({ value: s, label: s.replace(/_/g, ' ') }));

const MILESTONE_FIELDS = [
  { name: 'event_code', label: 'Event', type: 'select', options: EVENT_CODES, required: true },
  { name: 'source', label: 'Source', type: 'select', options: SOURCES, required: true },
  { name: 'event_at', label: 'Event time (blank = now)', type: 'datetime-local' },
  { name: 'notes', label: 'Notes', type: 'textarea' },
];

function fmt(dt) {
  if (!dt) return '—';
  return new Date(dt).toLocaleString();
}

function delayLabel(eventAt, recordedAt) {
  if (!eventAt || !recordedAt) return null;
  const diffMs = new Date(recordedAt) - new Date(eventAt);
  const mins = Math.round(diffMs / 60000);
  if (mins < 2) return null;
  if (mins < 90) return `recorded ${mins}m after event`;
  return `recorded ${Math.round(mins / 60)}h after event`;
}

export default function ShipmentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState('overview');
  const [shipment, setShipment] = useState(null);
  const [audit, setAudit] = useState([]);
  const [positions, setPositions] = useState(null);
  const [documents, setDocuments] = useState(null);
  const [excList, setExcList] = useState(null);
  const [bills, setBills] = useState(null);
  const [error, setError] = useState('');
  const [addOpen, setAddOpen] = useState(false);
  const [voidTarget, setVoidTarget] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    shipmentsApi.getShipment(id)
      .then(s => { if (!cancelled) { setShipment(s); setError(''); } })
      .catch(err => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
  }, [id, refreshKey]);

  useEffect(() => {
    if (tab !== 'audit') return;
    let cancelled = false;
    listAudit({ entity_type: 'shipments', entity_id: id, page_size: 100 })
      .then(res => { if (!cancelled) setAudit(res.items); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [tab, id, refreshKey]);

  useEffect(() => {
    if (tab !== 'map') return;
    let cancelled = false;
    shipmentPositions(id)
      .then(res => { if (!cancelled) setPositions(res); })
      .catch(() => { if (!cancelled) setPositions({ positions: [] }); });
    return () => { cancelled = true; };
  }, [tab, id, refreshKey]);

  useEffect(() => {
    if (tab !== 'documents') return;
    let cancelled = false;
    billing.listDocuments(id).then(d => { if (!cancelled) setDocuments(d); }).catch(() => setDocuments([]));
    return () => { cancelled = true; };
  }, [tab, id, refreshKey]);

  useEffect(() => {
    if (tab !== 'exceptions') return;
    let cancelled = false;
    billing.listExceptions({ shipment_id: id, page_size: 100 }).then(r => { if (!cancelled) setExcList(r.items); }).catch(() => setExcList([]));
    return () => { cancelled = true; };
  }, [tab, id, refreshKey]);

  useEffect(() => {
    if (tab !== 'charges') return;
    let cancelled = false;
    billing.listFreightBills({ page_size: 100 }).then(r => { if (!cancelled) setBills(r.items.filter(b => b.shipment_id === Number(id))); }).catch(() => setBills([]));
    return () => { cancelled = true; };
  }, [tab, id, refreshKey]);

  const uploadDoc = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const type = prompt('Document type (BOL, POD, customs, photo, other):', 'BOL') || 'other';
    await billing.uploadDocument(id, type, file);
    reload();
  };

  if (error) return <div className="auth-error">{error}</div>;
  if (!shipment) return <p style={{ color: 'var(--muted)' }}>Loading…</p>;

  const activeMilestones = (shipment.milestones || []).filter(m => !m.is_voided);
  const reload = () => setRefreshKey(k => k + 1);

  const doVoid = async () => {
    await shipmentsApi.voidMilestone(voidTarget.id, 'voided from UI');
    setVoidTarget(null);
    reload();
  };

  return (
    <div>
      <button className="btn secondary" style={{ marginBottom: 16 }} onClick={() => navigate('/shipments')}>← Shipments</button>

      <div className="page-head">
        <div>
          <div className="s-tag">Shipment</div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {shipment.probill_number}
            <ShipmentStatusChip value={shipment.current_status} />
          </h2>
          <p style={{ marginTop: 4 }}>
            BOL {shipment.bol_number || '—'} · {shipment.total_weight_lbs?.toLocaleString()} lbs · class {shipment.freight_class || '—'}
            {shipment.is_cross_border ? ' · cross-border' : ''}
          </p>
        </div>
        <button className="btn" onClick={() => setAddOpen(true)}>+ Add milestone</button>
      </div>

      <div className="tabs">
        {['overview', 'timeline', 'map', 'documents', 'exceptions', 'charges', 'audit'].map(t => (
          <button key={t} className={`tab${tab === t ? ' active' : ''}`} onClick={() => setTab(t)} style={{ textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      {tab === 'overview' && (
        <div>
          <div className="kv-grid" style={{ marginBottom: 18 }}>
            <div className="kv"><div className="kv-label">Service level</div><div className="kv-val">{shipment.service_level}</div></div>
            <div className="kv"><div className="kv-label">Pieces</div><div className="kv-val">{shipment.total_pieces}</div></div>
            <div className="kv"><div className="kv-label">Pickup date</div><div className="kv-val">{shipment.pickup_date || '—'}</div></div>
            <div className="kv"><div className="kv-label">Est. delivery</div><div className="kv-val">{fmt(shipment.estimated_delivery_at)}</div></div>
            <div className="kv"><div className="kv-label">Source</div><div className="kv-val">{shipment.source}</div></div>
            <div className="kv"><div className="kv-label">Reference</div><div className="kv-val">{shipment.customer_reference || '—'}</div></div>
          </div>

          <h3 style={{ margin: '18px 0 10px' }}>Handling units</h3>
          {shipment.handling_units?.length ? (
            <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
              <table className="lb-table">
                <thead><tr><th>Type</th><th>Qty</th><th>Dims (in)</th><th>Weight</th><th>Barcode</th></tr></thead>
                <tbody>
                  {shipment.handling_units.map(u => (
                    <tr key={u.id}>
                      <td>{u.type}</td>
                      <td>{u.quantity}</td>
                      <td>{[u.length_in, u.width_in, u.height_in].some(Boolean) ? `${u.length_in ?? '?'}×${u.width_in ?? '?'}×${u.height_in ?? '?'}` : '—'}</td>
                      <td>{u.weight_lbs ?? '—'}</td>
                      <td>{u.label_barcode || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p style={{ color: 'var(--muted)' }}>No handling units.</p>}

          {shipment.data_quality_flags?.length > 0 && (
            <>
              <h3 style={{ margin: '18px 0 10px' }}>Data-quality flags</h3>
              {shipment.data_quality_flags.map((f, i) => (
                <div key={i} className="auth-error" style={{ marginBottom: 8 }}>
                  <strong>{f.code}</strong> — {f.detail}
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {tab === 'timeline' && (
        <div>
          {activeMilestones.length === 0 ? (
            <p style={{ color: 'var(--muted)' }}>No milestones yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {activeMilestones.map(m => {
                const delay = delayLabel(m.event_at, m.recorded_at);
                return (
                  <div key={m.id} className="glass-card" style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--accent)', marginTop: 5, flexShrink: 0 }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, color: 'var(--text)' }}>{m.event_code.replace(/_/g, ' ')}</div>
                      <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                        {fmt(m.event_at)} · source: {m.source}{m.edi_214_code ? ` · EDI ${m.edi_214_code}` : ''}
                      </div>
                      {delay && <div style={{ fontSize: 12, color: 'var(--amber)' }}>{delay}</div>}
                      {m.notes && <div style={{ fontSize: 13, marginTop: 4 }}>{m.notes}</div>}
                    </div>
                    <button className="btn secondary" style={{ padding: '5px 10px', fontSize: 11 }} onClick={() => setVoidTarget(m)}>Void</button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {tab === 'map' && (
        <div>
          {positions == null ? (
            <p style={{ color: 'var(--muted)' }}>Loading positions…</p>
          ) : positions.positions.length === 0 ? (
            <p style={{ color: 'var(--muted)' }}>No positions recorded for this shipment yet.</p>
          ) : (
            <MapView
              center={[positions.positions[0].lat, positions.positions[0].lng]}
              zoom={6}
              polyline={positions.positions.map(p => [p.lat, p.lng])}
              markers={[
                { id: 'start', ...positions.positions[0], color: '#15803D', label: 'Start' },
                { id: 'latest', ...positions.positions[positions.positions.length - 1], color: '#2563EB', label: 'Latest' },
              ]}
            />
          )}
        </div>
      )}

      {tab === 'documents' && (
        <div>
          <div style={{ marginBottom: 12 }}>
            <label className="btn" style={{ cursor: 'pointer' }}>
              Upload document
              <input type="file" style={{ display: 'none' }} onChange={uploadDoc} />
            </label>
          </div>
          {documents == null ? <p style={{ color: 'var(--muted)' }}>Loading…</p> : documents.length === 0 ? (
            <p style={{ color: 'var(--muted)' }}>No documents.</p>
          ) : (
            <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
              <table className="lb-table">
                <thead><tr><th>Type</th><th>Filename</th><th>Uploaded by</th><th>When</th></tr></thead>
                <tbody>
                  {documents.map(d => (
                    <tr key={d.id}>
                      <td><span className="badge blue">{d.type}</span></td>
                      <td>{d.filename}</td>
                      <td>{d.uploaded_by || '—'}</td>
                      <td>{fmt(d.uploaded_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'exceptions' && (
        <div>
          {excList == null ? <p style={{ color: 'var(--muted)' }}>Loading…</p> : excList.length === 0 ? (
            <p style={{ color: 'var(--muted)' }}>No exceptions.</p>
          ) : (
            <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
              <table className="lb-table">
                <thead><tr><th>Type</th><th>Severity</th><th>Status</th><th>Description</th><th>Source</th></tr></thead>
                <tbody>
                  {excList.map(e => (
                    <tr key={e.id}>
                      <td>{e.type.replace(/_/g, ' ')}</td>
                      <td><span className={`badge ${e.severity === 'high' ? 'red' : e.severity === 'medium' ? 'amber' : 'blue'}`}>{e.severity}</span></td>
                      <td><span className={`badge ${e.status === 'resolved' ? 'green' : e.status === 'investigating' ? 'amber' : 'red'}`}>{e.status}</span></td>
                      <td>{e.description}</td>
                      <td>{e.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'charges' && (
        <div>
          {bills == null ? <p style={{ color: 'var(--muted)' }}>Loading…</p> : bills.length === 0 ? (
            <p style={{ color: 'var(--muted)' }}>No freight bill yet (a draft is generated on delivery).</p>
          ) : bills.map(b => (
            <div key={b.id} className="glass-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <strong>{b.bill_number}</strong>
                <span className={`badge ${b.status === 'issued' ? 'green' : b.status === 'draft' ? 'amber' : 'blue'}`}>{b.status}</span>
              </div>
              <table className="lb-table">
                <thead><tr><th>Code</th><th>Description</th><th style={{ textAlign: 'right' }}>Amount</th></tr></thead>
                <tbody>
                  {(b.line_items || []).map((li, i) => (
                    <tr key={i}><td>{li.code}</td><td>{li.description}</td><td style={{ textAlign: 'right' }}>${(li.amount || 0).toFixed(2)}</td></tr>
                  ))}
                </tbody>
              </table>
              <div style={{ textAlign: 'right', marginTop: 10, fontWeight: 700 }}>Total: ${b.total.toFixed(2)}</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'audit' && (
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="lb-table">
            <thead><tr><th>When</th><th>Action</th><th>Actor</th><th>Changed / reason</th></tr></thead>
            <tbody>
              {audit.length === 0 ? (
                <tr><td colSpan={4} style={{ textAlign: 'center', padding: 24, color: 'var(--muted)' }}>No audit entries.</td></tr>
              ) : audit.map(a => (
                <tr key={a.id}>
                  <td>{fmt(a.created_at)}</td>
                  <td><span className="badge blue">{a.action}</span></td>
                  <td>{a.actor_type}{a.actor_id ? ` #${a.actor_id}` : ''}</td>
                  <td style={{ fontSize: 12 }}>
                    {a.reason || (a.changed_fields ? Object.keys(a.changed_fields).join(', ') : '—')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <EntityDrawer
        open={addOpen}
        mode="create"
        title="Add milestone"
        fields={MILESTONE_FIELDS}
        initial={{ source: 'manual' }}
        onClose={() => setAddOpen(false)}
        onSubmit={async (values) => {
          const body = { ...values };
          if (body.event_at) body.event_at = new Date(body.event_at).toISOString();
          await shipmentsApi.addMilestone(id, body);
          reload();
        }}
      />

      <ConfirmDialog
        open={!!voidTarget}
        title="Void milestone"
        message={voidTarget ? `Void the "${voidTarget.event_code.replace(/_/g, ' ')}" milestone? Status will be recomputed.` : ''}
        confirmLabel="Void"
        onCancel={() => setVoidTarget(null)}
        onConfirm={doVoid}
      />
    </div>
  );
}
