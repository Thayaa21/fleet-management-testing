import { useState } from 'react';
import DataTable from '../../components/DataTable';
import EntityDrawer from '../../components/EntityDrawer';
import StatusChip from '../../components/StatusChip';
import * as customersApi from '../../api/customers';

const TYPE_OPTIONS = [
  { value: 'shipper', label: 'Shipper' },
  { value: 'consignee', label: 'Consignee' },
  { value: 'both', label: 'Both' },
  { value: 'third_party_payer', label: 'Third-party payer' },
];

const FIELDS = [
  { name: 'account_number', label: 'Account number', required: true, editableOnCreateOnly: true },
  { name: 'name', label: 'Name', required: true },
  { name: 'type', label: 'Type', type: 'select', options: TYPE_OPTIONS, required: true },
  { name: 'contact_name', label: 'Contact name' },
  { name: 'contact_email', label: 'Contact email' },
  { name: 'contact_phone', label: 'Contact phone' },
  { name: 'billing_city', label: 'Billing city' },
  { name: 'billing_province_state', label: 'Billing prov/state' },
  { name: 'billing_country', label: 'Billing country (CA/US)' },
  { name: 'payment_terms', label: 'Payment terms' },
  { name: 'credit_hold', label: 'Credit hold', type: 'checkbox', checkboxLabel: 'On credit hold' },
  { name: 'notes', label: 'Notes', type: 'textarea' },
];

export default function Customers() {
  const [drawer, setDrawer] = useState(null); // {mode, initial}
  const [refreshKey, setRefreshKey] = useState(0);
  const reload = () => setRefreshKey(k => k + 1);

  const columns = [
    { key: 'account_number', label: 'Account', sortable: true },
    { key: 'name', label: 'Name', sortable: true },
    { key: 'type', label: 'Type', render: r => r.type.replace(/_/g, ' ') },
    { key: 'contact_name', label: 'Contact' },
    { key: 'credit_hold', label: 'Credit hold', render: r => (r.credit_hold ? 'Yes' : '—') },
    { key: 'status', label: 'Status', render: r => <StatusChip value={r.status} /> },
  ];

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="s-tag">Master data</div>
          <h2>Customers</h2>
        </div>
      </div>

      <DataTable
        columns={columns}
        fetchPage={customersApi.listCustomers}
        refreshKey={refreshKey}
        searchPlaceholder="Search account, name, contact…"
        onRowClick={r => setDrawer({ mode: 'edit', initial: r })}
        actions={<button className="btn" onClick={() => setDrawer({ mode: 'create', initial: {} })}>+ New customer</button>}
      />

      <EntityDrawer
        open={!!drawer}
        mode={drawer?.mode}
        title={drawer?.mode === 'edit' ? `Edit ${drawer.initial.account_number}` : 'New customer'}
        fields={FIELDS}
        initial={drawer?.initial}
        onClose={() => setDrawer(null)}
        onSubmit={async (values) => {
          if (drawer.mode === 'edit') await customersApi.updateCustomer(drawer.initial.id, values);
          else await customersApi.createCustomer(values);
          reload();
        }}
      />
    </div>
  );
}
