import { useState } from 'react';
import DataTable from '../../components/DataTable';
import EntityDrawer from '../../components/EntityDrawer';
import StatusChip from '../../components/StatusChip';
import * as locationsApi from '../../api/locations';

const TYPE_OPTIONS = [
  { value: 'customer_site', label: 'Customer site' },
  { value: 'terminal', label: 'Terminal' },
  { value: 'cross_dock', label: 'Cross-dock' },
  { value: 'customs_point', label: 'Customs point' },
];

const FIELDS = [
  { name: 'name', label: 'Name', required: true },
  { name: 'type', label: 'Type', type: 'select', options: TYPE_OPTIONS, required: true },
  { name: 'address', label: 'Address' },
  { name: 'city', label: 'City' },
  { name: 'province_state', label: 'Province/State' },
  { name: 'postal_zip', label: 'Postal/ZIP' },
  { name: 'country', label: 'Country (CA/US)' },
  { name: 'lat', label: 'Latitude', type: 'number' },
  { name: 'lng', label: 'Longitude', type: 'number' },
  { name: 'timezone', label: 'Timezone' },
  { name: 'dock_hours', label: 'Dock hours' },
  { name: 'appointment_required', label: 'Appointment', type: 'checkbox', checkboxLabel: 'Appointment required' },
  { name: 'geofence_radius_m', label: 'Geofence radius (m)', type: 'number' },
];

export default function Locations() {
  const [drawer, setDrawer] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const reload = () => setRefreshKey(k => k + 1);

  const columns = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'type', label: 'Type', render: r => r.type.replace(/_/g, ' ') },
    { key: 'city', label: 'City' },
    { key: 'province_state', label: 'Prov/State' },
    { key: 'country', label: 'Country' },
    { key: 'status', label: 'Status', render: r => <StatusChip value={r.status} /> },
  ];

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="s-tag">Master data</div>
          <h2>Locations &amp; terminals</h2>
        </div>
      </div>

      <DataTable
        columns={columns}
        fetchPage={locationsApi.listLocations}
        refreshKey={refreshKey}
        searchPlaceholder="Search name, city, postal…"
        onRowClick={r => setDrawer({ mode: 'edit', initial: r })}
        actions={<button className="btn" onClick={() => setDrawer({ mode: 'create', initial: { geofence_radius_m: 300 } })}>+ New location</button>}
      />

      <EntityDrawer
        open={!!drawer}
        mode={drawer?.mode}
        title={drawer?.mode === 'edit' ? `Edit ${drawer.initial.name}` : 'New location'}
        fields={FIELDS}
        initial={drawer?.initial}
        onClose={() => setDrawer(null)}
        onSubmit={async (values) => {
          if (drawer.mode === 'edit') await locationsApi.updateLocation(drawer.initial.id, values);
          else await locationsApi.createLocation(values);
          reload();
        }}
      />
    </div>
  );
}
