import { useEffect, useState } from 'react';
import { listLocations } from '../api/locations';
import { listDevices } from '../api/equipment';

/** Load locations as {value,label} options (optionally filtered by type). */
export function useLocationOptions(type) {
  const [options, setOptions] = useState([]);
  useEffect(() => {
    let cancelled = false;
    listLocations({ page_size: 100, type })
      .then(res => {
        if (!cancelled) setOptions(res.items.map(l => ({ value: l.id, label: `${l.name} (${l.city || l.type})` })));
      })
      .catch(() => { if (!cancelled) setOptions([]); });
    return () => { cancelled = true; };
  }, [type]);
  return options;
}

/** Load telematics devices as {value,label} options. */
export function useDeviceOptions() {
  const [options, setOptions] = useState([]);
  useEffect(() => {
    let cancelled = false;
    listDevices({ page_size: 100 })
      .then(res => {
        if (!cancelled) setOptions(res.items.map(d => ({ value: d.id, label: `${d.device_serial} (${d.provider})` })));
      })
      .catch(() => { if (!cancelled) setOptions([]); });
    return () => { cancelled = true; };
  }, []);
  return options;
}
