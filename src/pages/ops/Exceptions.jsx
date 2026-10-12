import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DataTable from '../../components/DataTable';
import * as billing from '../../api/billing';

const TYPES = ['overage', 'shortage', 'damage', 'refused', 'missed_pickup', 'missed_delivery', 'delay', 'customs_hold', 'data_quality'];
const SEVERITIES = ['low', 'medium', 'high'];
const STATUSES = ['open', 'investigating', 'resolved'];

function sevClass(s) { return s === 'high' ? 'red' : s === 'medium' ? 'amber' : 'blue'; }
function statusClass(s) { return s === 'resolved' ? 'green' : s === 'investigating' ? 'amber' : 'red'; }

export default function Exceptions() {
  const navigate = useNavigate();
  const [type, setType] = useState('');
  const [severity, setSeverity] = useState('');
  const [status, setStatus] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  const filters = { type: type || undefined, severity: severity || undefined, status: status || undefined };

  const resolve = async (id) => {
    await billing.updateException(id, { status: 'resolved', resolution_notes: 'resolved from queue' });
    setRefreshKey(k => k + 1);
  };

  const columns = [
    { key: 'opened_at', label: 'Opened', render: r => new Date(r.opened_at).toLocaleString() },
    { key: 'shipment_id', label: 'Shipment', render: r => <button className="link" style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', padding: 0 }} onClick={(e) => { e.stopPropagation(); navigate(`/shipments/${r.shipment_id}`); }}>#{r.shipment_id}</button> },
    { key: 'type', label: 'Type', render: r => r.type.replace(/_/g, ' ') },
    { key: 'severity', label: 'Severity', render: r => <span className={`badge ${sevClass(r.severity)}`}>{r.severity}</span> },
    { key: 'status', label: 'Status', render: r => <span className={`badge ${statusClass(r.status)}`}>{r.status}</span> },
    { key: 'description', label: 'Description' },
    { key: 'source', label: 'Source' },
    {
      key: 'id', label: '', render: r => (r.status !== 'resolved' ?
        <button className="btn secondary" style={{ padding: '3px 8px', fontSize: 11 }} onClick={(e) => { e.stopPropagation(); resolve(r.id); }}>Resolve</button> : null),
    },
  ];

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="s-tag">Operations</div>
          <h2>Exceptions</h2>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
        <select className="form-select" style={{ width: 170 }} value={type} onChange={e => setType(e.target.value)}>
          <option value="">All types</option>
          {TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
        </select>
        <select className="form-select" style={{ width: 140 }} value={severity} onChange={e => setSeverity(e.target.value)}>
          <option value="">All severities</option>
          {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className="form-select" style={{ width: 150 }} value={status} onChange={e => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <DataTable columns={columns} filters={filters} refreshKey={refreshKey}
        fetchPage={(p) => billing.listExceptions({ ...p, ...filters })}
        searchPlaceholder="(search n/a)" />
    </div>
  );
}
