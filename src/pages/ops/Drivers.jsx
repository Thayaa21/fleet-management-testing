import { useState } from 'react';
import DataTable from '../../components/DataTable';
import EntityDrawer from '../../components/EntityDrawer';
import StatusChip from '../../components/StatusChip';
import * as driversApi from '../../api/drivers';
import { useLocationOptions } from '../../hooks/useOptions';

const TYPE_OPTIONS = [
  { value: 'city_pd', label: 'City P&D' },
  { value: 'linehaul', label: 'Linehaul' },
];

export default function Drivers() {
  const [drawer, setDrawer] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const reload = () => setRefreshKey(k => k + 1);
  const terminalOptions = useLocationOptions('terminal');

  const fields = [
    { name: 'employee_number', label: 'Employee number', required: true, editableOnCreateOnly: true },
    { name: 'full_name', label: 'Full name', required: true },
    { name: 'type', label: 'Type', type: 'select', options: TYPE_OPTIONS, required: true },
    { name: 'phone', label: 'Phone' },
    { name: 'license_number', label: 'License number' },
    { name: 'license_province_state', label: 'License prov/state' },
    { name: 'license_expiry', label: 'License expiry', type: 'date' },
    { name: 'home_terminal_id', label: 'Home terminal', type: 'select', options: terminalOptions },
    { name: 'hos_hours_remaining', label: 'HOS hours remaining', type: 'number' },
  ];

  const columns = [
    { key: 'employee_number', label: 'Emp #', sortable: true },
    { key: 'full_name', label: 'Name', sortable: true },
    { key: 'type', label: 'Type', render: r => r.type.replace(/_/g, ' ') },
    { key: 'phone', label: 'Phone' },
    { key: 'hos_hours_remaining', label: 'HOS (h)' },
    { key: 'status', label: 'Status', render: r => <StatusChip value={r.status} /> },
  ];

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="s-tag">Master data</div>
          <h2>Drivers</h2>
        </div>
      </div>

      <DataTable
        columns={columns}
        fetchPage={driversApi.listDrivers}
        refreshKey={refreshKey}
        searchPlaceholder="Search emp #, name, license…"
        onRowClick={r => setDrawer({ mode: 'edit', initial: r })}
        actions={<button className="btn" onClick={() => setDrawer({ mode: 'create', initial: {} })}>+ New driver</button>}
      />

      <EntityDrawer
        open={!!drawer}
        mode={drawer?.mode}
        title={drawer?.mode === 'edit' ? `Edit ${drawer.initial.full_name}` : 'New driver'}
        fields={fields}
        initial={drawer?.initial}
        onClose={() => setDrawer(null)}
        onSubmit={async (values) => {
          if (drawer.mode === 'edit') await driversApi.updateDriver(drawer.initial.id, values);
          else await driversApi.createDriver(values);
          reload();
        }}
      />
    </div>
  );
}
