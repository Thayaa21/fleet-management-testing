import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DataTable from '../../components/DataTable';
import * as billing from '../../api/billing';

function statusClass(s) {
  return s === 'issued' ? 'green' : s === 'paid' ? 'blue' : s === 'void' ? 'red' : 'amber';
}

export default function Billing() {
  const navigate = useNavigate();
  const [tab, setTab] = useState('draft');
  const [refreshKey, setRefreshKey] = useState(0);

  const issue = async (id) => {
    await billing.issueFreightBill(id);
    setRefreshKey(k => k + 1);
  };

  const columns = [
    { key: 'bill_number', label: 'Bill #', sortable: true },
    { key: 'shipment_id', label: 'Shipment', render: r => <button style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', padding: 0 }} onClick={(e) => { e.stopPropagation(); navigate(`/shipments/${r.shipment_id}`); }}>#{r.shipment_id}</button> },
    { key: 'subtotal', label: 'Subtotal', render: r => `$${r.subtotal.toFixed(2)}` },
    { key: 'fuel_surcharge', label: 'Fuel', render: r => `$${r.fuel_surcharge.toFixed(2)}` },
    { key: 'accessorials_total', label: 'Accessorials', render: r => `$${r.accessorials_total.toFixed(2)}` },
    { key: 'total', label: 'Total', render: r => <strong>${r.total.toFixed(2)}</strong> },
    { key: 'status', label: 'Status', render: r => <span className={`badge ${statusClass(r.status)}`}>{r.status}</span> },
    {
      key: 'id', label: '', render: r => (r.status === 'draft' ?
        <button className="btn" style={{ padding: '3px 10px', fontSize: 11 }} onClick={(e) => { e.stopPropagation(); issue(r.id); }}>Issue</button> : null),
    },
  ];

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="s-tag">Revenue</div>
          <h2>Billing</h2>
        </div>
      </div>

      <div className="tabs">
        {['draft', 'issued', 'paid'].map(t => (
          <button key={t} className={`tab${tab === t ? ' active' : ''}`} onClick={() => setTab(t)} style={{ textTransform: 'capitalize' }}>{t}</button>
        ))}
      </div>

      <DataTable columns={columns} filters={{ status: tab }} refreshKey={refreshKey}
        fetchPage={(p) => billing.listFreightBills({ ...p, status: tab })}
        searchPlaceholder="(search n/a)" />
    </div>
  );
}
