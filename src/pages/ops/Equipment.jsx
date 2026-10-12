import { useState } from 'react';
import DataTable from '../../components/DataTable';
import EntityDrawer from '../../components/EntityDrawer';
import StatusChip from '../../components/StatusChip';
import * as equipmentApi from '../../api/equipment';
import { useLocationOptions, useDeviceOptions } from '../../hooks/useOptions';

const PROVIDER_OPTIONS = [
  { value: 'samsara', label: 'Samsara' },
  { value: 'geotab', label: 'Geotab' },
  { value: 'mock', label: 'Mock' },
  { value: 'other', label: 'Other' },
];

const TRAILER_TYPE_OPTIONS = [
  { value: 'dry_van', label: 'Dry van' },
  { value: 'reefer', label: 'Reefer' },
  { value: 'flatbed', label: 'Flatbed' },
  { value: 'pup', label: 'Pup' },
  { value: 'straight_truck_box', label: 'Straight truck box' },
];

function TractorsTab() {
  const [drawer, setDrawer] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const reload = () => setRefreshKey(k => k + 1);
  const terminals = useLocationOptions('terminal');
  const devices = useDeviceOptions();

  const fields = [
    { name: 'unit_number', label: 'Unit number', required: true, editableOnCreateOnly: true },
    { name: 'vin', label: 'VIN' },
    { name: 'plate', label: 'Plate' },
    { name: 'home_terminal_id', label: 'Home terminal', type: 'select', options: terminals },
    { name: 'telematics_device_id', label: 'Telematics device', type: 'select', options: devices },
  ];
  const columns = [
    { key: 'unit_number', label: 'Unit #', sortable: true },
    { key: 'vin', label: 'VIN' },
    { key: 'plate', label: 'Plate' },
    { key: 'telematics_device_id', label: 'Device', render: r => r.telematics_device_id ?? '—' },
    { key: 'status', label: 'Status', render: r => <StatusChip value={r.status} /> },
  ];
  return (
    <>
      <DataTable
        columns={columns} fetchPage={equipmentApi.listTractors} refreshKey={refreshKey}
        searchPlaceholder="Search unit, VIN, plate…"
        onRowClick={r => setDrawer({ mode: 'edit', initial: r })}
        actions={<button className="btn" onClick={() => setDrawer({ mode: 'create', initial: {} })}>+ New tractor</button>}
      />
      <EntityDrawer
        open={!!drawer} mode={drawer?.mode}
        title={drawer?.mode === 'edit' ? `Edit ${drawer.initial.unit_number}` : 'New tractor'}
        fields={fields} initial={drawer?.initial} onClose={() => setDrawer(null)}
        onSubmit={async (values) => {
          if (drawer.mode === 'edit') await equipmentApi.updateTractor(drawer.initial.id, values);
          else await equipmentApi.createTractor(values);
          reload();
        }}
      />
    </>
  );
}

function TrailersTab() {
  const [drawer, setDrawer] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const reload = () => setRefreshKey(k => k + 1);
  const terminals = useLocationOptions('terminal');
  const devices = useDeviceOptions();

  const fields = [
    { name: 'trailer_number', label: 'Trailer number', required: true, editableOnCreateOnly: true },
    { name: 'type', label: 'Type', type: 'select', options: TRAILER_TYPE_OPTIONS, required: true },
    { name: 'length_ft', label: 'Length (ft)', type: 'number' },
    { name: 'capacity_lbs', label: 'Capacity (lbs)', type: 'number' },
    { name: 'capacity_cuft', label: 'Capacity (cu ft)', type: 'number' },
    { name: 'home_terminal_id', label: 'Home terminal', type: 'select', options: terminals },
    { name: 'telematics_device_id', label: 'Telematics device', type: 'select', options: devices },
  ];
  const columns = [
    { key: 'trailer_number', label: 'Trailer #', sortable: true },
    { key: 'type', label: 'Type', render: r => r.type.replace(/_/g, ' ') },
    { key: 'capacity_lbs', label: 'Cap (lbs)' },
    { key: 'telematics_device_id', label: 'Device', render: r => r.telematics_device_id ?? '—' },
    { key: 'status', label: 'Status', render: r => <StatusChip value={r.status} /> },
  ];
  return (
    <>
      <DataTable
        columns={columns} fetchPage={equipmentApi.listTrailers} refreshKey={refreshKey}
        searchPlaceholder="Search trailer #…"
        onRowClick={r => setDrawer({ mode: 'edit', initial: r })}
        actions={<button className="btn" onClick={() => setDrawer({ mode: 'create', initial: { type: 'dry_van' } })}>+ New trailer</button>}
      />
      <EntityDrawer
        open={!!drawer} mode={drawer?.mode}
        title={drawer?.mode === 'edit' ? `Edit ${drawer.initial.trailer_number}` : 'New trailer'}
        fields={fields} initial={drawer?.initial} onClose={() => setDrawer(null)}
        onSubmit={async (values) => {
          if (drawer.mode === 'edit') await equipmentApi.updateTrailer(drawer.initial.id, values);
          else await equipmentApi.createTrailer(values);
          reload();
        }}
      />
    </>
  );
}

function DevicesTab() {
  const [drawer, setDrawer] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const reload = () => setRefreshKey(k => k + 1);

  const fields = [
    { name: 'device_serial', label: 'Device serial', required: true, editableOnCreateOnly: true },
    { name: 'provider', label: 'Provider', type: 'select', options: PROVIDER_OPTIONS, required: true },
  ];
  const columns = [
    { key: 'device_serial', label: 'Serial', sortable: true },
    { key: 'provider', label: 'Provider' },
    { key: 'attached_to_type', label: 'Attached to', render: r => (r.attached_to_type === 'none' ? '—' : `${r.attached_to_type} #${r.attached_to_id}`) },
    { key: 'status', label: 'Status', render: r => <StatusChip value={r.status} /> },
  ];
  return (
    <>
      <DataTable
        columns={columns} fetchPage={equipmentApi.listDevices} refreshKey={refreshKey}
        searchPlaceholder="Search serial…"
        onRowClick={r => setDrawer({ mode: 'edit', initial: r })}
        actions={<button className="btn" onClick={() => setDrawer({ mode: 'create', initial: { provider: 'mock' } })}>+ New device</button>}
      />
      <EntityDrawer
        open={!!drawer} mode={drawer?.mode}
        title={drawer?.mode === 'edit' ? `Edit ${drawer.initial.device_serial}` : 'New device'}
        fields={fields} initial={drawer?.initial} onClose={() => setDrawer(null)}
        onSubmit={async (values) => {
          if (drawer.mode === 'edit') await equipmentApi.updateDevice(drawer.initial.id, values);
          else await equipmentApi.createDevice(values);
          reload();
        }}
      />
    </>
  );
}

const TABS = [
  { id: 'tractors', label: 'Tractors', el: <TractorsTab /> },
  { id: 'trailers', label: 'Trailers', el: <TrailersTab /> },
  { id: 'devices', label: 'Devices', el: <DevicesTab /> },
];

export default function Equipment() {
  const [tab, setTab] = useState('tractors');
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="s-tag">Master data</div>
          <h2>Equipment</h2>
        </div>
      </div>
      <div className="tabs">
        {TABS.map(t => (
          <button key={t.id} className={`tab${tab === t.id ? ' active' : ''}`} onClick={() => setTab(t.id)}>{t.label}</button>
        ))}
      </div>
      {TABS.find(t => t.id === tab).el}
    </div>
  );
}
