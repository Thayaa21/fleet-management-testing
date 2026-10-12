import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DataTable from '../../components/DataTable';
import * as shipmentsApi from '../../api/shipments';

const STATUSES = [
  'BOOKED', 'PICKUP_DISPATCHED', 'PICKED_UP', 'AT_ORIGIN_TERMINAL', 'IN_LINEHAUL',
  'AT_DESTINATION_TERMINAL', 'OUT_FOR_DELIVERY', 'DELIVERED', 'EXCEPTION', 'CANCELLED',
];

// Color class per shipment status.
function statusClass(s) {
  if (s === 'DELIVERED') return 'green';
  if (s === 'EXCEPTION') return 'red';
  if (s === 'CANCELLED') return 'red';
  if (s === 'BOOKED') return 'amber';
  return 'blue';
}

export function ShipmentStatusChip({ value }) {
  if (!value) return null;
  return <span className={`badge ${statusClass(value)}`}>{value.replace(/_/g, ' ')}</span>;
}

export default function Shipments() {
  const navigate = useNavigate();
  const [status, setStatus] = useState('');
  const [stale, setStale] = useState(false);
  const [dqOnly, setDqOnly] = useState(false);

  const filters = {
    status: status || undefined,
    stale_for_hours: stale ? 6 : undefined,
    has_data_quality_flags: dqOnly ? true : undefined,
  };

  const columns = [
    { key: 'probill_number', label: 'Probill', sortable: true },
    { key: 'bol_number', label: 'BOL' },
    { key: 'current_status', label: 'Status', render: r => <ShipmentStatusChip value={r.current_status} /> },
    { key: 'total_weight_lbs', label: 'Weight (lbs)', render: r => (r.total_weight_lbs || 0).toLocaleString() },
    { key: 'freight_class', label: 'Class' },
    { key: 'is_cross_border', label: 'Cross-border', render: r => (r.is_cross_border ? 'Yes' : '—') },
    {
      key: 'data_quality_flags', label: 'DQ',
      render: r => (r.data_quality_flags?.length ? <span className="badge amber">{r.data_quality_flags.length}</span> : '—'),
    },
  ];

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="s-tag">Operations</div>
          <h2>Shipments</h2>
        </div>
      </div>

      {/* Status chips */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
        <button className={`btn ${status === '' ? '' : 'secondary'}`} style={{ padding: '5px 12px', fontSize: 11 }} onClick={() => setStatus('')}>All</button>
        {STATUSES.map(s => (
          <button key={s} className={`btn ${status === s ? '' : 'secondary'}`} style={{ padding: '5px 12px', fontSize: 11 }} onClick={() => setStatus(s)}>
            {s.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {/* Toggles */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 14, fontSize: 13, color: 'var(--muted)' }}>
        <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <input type="checkbox" checked={stale} onChange={e => setStale(e.target.checked)} />
          Stale (&gt; 6h, not delivered)
        </label>
        <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <input type="checkbox" checked={dqOnly} onChange={e => setDqOnly(e.target.checked)} />
          Has data-quality flags
        </label>
      </div>

      <DataTable
        columns={columns}
        fetchPage={shipmentsApi.listShipments}
        filters={filters}
        searchPlaceholder="Search probill, BOL, reference…"
        onRowClick={r => navigate(`/shipments/${r.id}`)}
      />
    </div>
  );
}
