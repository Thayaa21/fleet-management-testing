import { useState } from 'react';
import TpLogo from '../components/TpLogo';
import { useFleetState } from '../hooks/fleetContext';

const STATUS_CLASS = { 'In Transit': 'blue', Delivered: 'green', Pending: 'amber' };

const COMMODITIES = ['General', 'Reefer', 'Industrial', 'Pharma', 'Automotive', 'Agriculture', 'Hazmat', 'Retail'];
const TRAILERS = ['Dry Van', 'Reefer', 'Flatbed', 'Pup', 'Straight truck'];

function BookPane() {
  const { bookShipment } = useFleetState();
  const [form, setForm] = useState({
    pickupCity: '', pickupState: '', pickupZip: '', pickupDate: '',
    destCity: '', destState: '', destZip: '',
    commodity: 'General', weight: '', trailer: 'Dry Van',
    name: '', company: '', email: '',
  });
  const [confirmation, setConfirmation] = useState(null);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = e => {
    e.preventDefault();
    const id = bookShipment(form);
    setConfirmation(id);
  };

  if (confirmation) {
    return (
      <div className="glass-card" style={{ maxWidth: 520 }}>
        <span className="badge green">Booked</span>
        <h2 style={{ margin: '12px 0 6px' }}>Shipment booked</h2>
        <p>A dispatcher will confirm and schedule your pickup. Reference:</p>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 15, fontWeight: 700, color: 'var(--accent)', margin: '10px 0 18px' }}>{confirmation}</div>
        <button className="btn" onClick={() => setConfirmation(null)}>Book another shipment</button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 720 }}>
      <h2 style={{ marginBottom: 4 }}>Book a shipment</h2>
      <p style={{ marginBottom: 20 }}>Enter pickup, delivery and freight details.</p>
      <form onSubmit={submit}>
        <div className="glass-card">
          <h3 style={{ marginBottom: 14 }}>Pickup</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: 12 }}>
            <div className="form-field"><label className="form-label">City</label><input className="form-input" value={form.pickupCity} onChange={e => set('pickupCity', e.target.value)} required /></div>
            <div className="form-field"><label className="form-label">Prov/State</label><input className="form-input" value={form.pickupState} onChange={e => set('pickupState', e.target.value)} required /></div>
            <div className="form-field"><label className="form-label">Postal/ZIP</label><input className="form-input" value={form.pickupZip} onChange={e => set('pickupZip', e.target.value)} /></div>
          </div>
          <div className="form-field"><label className="form-label">Pickup date</label><input className="form-input" type="date" value={form.pickupDate} onChange={e => set('pickupDate', e.target.value)} required /></div>
        </div>

        <div className="glass-card">
          <h3 style={{ marginBottom: 14 }}>Delivery</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: 12 }}>
            <div className="form-field"><label className="form-label">City</label><input className="form-input" value={form.destCity} onChange={e => set('destCity', e.target.value)} required /></div>
            <div className="form-field"><label className="form-label">Prov/State</label><input className="form-input" value={form.destState} onChange={e => set('destState', e.target.value)} required /></div>
            <div className="form-field"><label className="form-label">Postal/ZIP</label><input className="form-input" value={form.destZip} onChange={e => set('destZip', e.target.value)} /></div>
          </div>
        </div>

        <div className="glass-card">
          <h3 style={{ marginBottom: 14 }}>Freight</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
            <div className="form-field"><label className="form-label">Weight (lbs)</label><input className="form-input" type="number" value={form.weight} onChange={e => set('weight', e.target.value)} required /></div>
            <div className="form-field">
              <label className="form-label">Commodity</label>
              <select className="form-select" value={form.commodity} onChange={e => set('commodity', e.target.value)}>
                {COMMODITIES.map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-field">
              <label className="form-label">Trailer</label>
              <select className="form-select" value={form.trailer} onChange={e => set('trailer', e.target.value)}>
                {TRAILERS.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
          </div>
        </div>

        <div className="glass-card">
          <h3 style={{ marginBottom: 14 }}>Contact</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
            <div className="form-field"><label className="form-label">Name</label><input className="form-input" value={form.name} onChange={e => set('name', e.target.value)} required /></div>
            <div className="form-field"><label className="form-label">Company</label><input className="form-input" value={form.company} onChange={e => set('company', e.target.value)} required /></div>
            <div className="form-field"><label className="form-label">Email</label><input className="form-input" type="email" value={form.email} onChange={e => set('email', e.target.value)} required /></div>
          </div>
        </div>

        <button className="btn" type="submit">Request booking</button>
      </form>
    </div>
  );
}

function TrackPane() {
  const { userShipments } = useFleetState();
  const [openId, setOpenId] = useState(null);

  if (userShipments.length === 0) {
    return (
      <div className="placeholder">
        <h2>No shipments yet</h2>
        <p>Book a shipment and it will show up here.</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 760 }}>
      <h2 style={{ marginBottom: 4 }}>My shipments</h2>
      <p style={{ marginBottom: 20 }}>{userShipments.length} shipment(s).</p>
      {userShipments.map(s => {
        const open = openId === s.id;
        return (
          <div key={s.id} className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
            <button
              onClick={() => setOpenId(open ? null : s.id)}
              style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none', padding: 18, display: 'flex', alignItems: 'center', gap: 14 }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, color: 'var(--text)' }}>{s.id}</div>
                <div style={{ fontSize: 13, color: 'var(--muted)' }}>{s.origin} → {s.dest}</div>
                <div style={{ fontSize: 12, color: 'var(--faint)' }}>{s.commodity} · {s.weight} · {s.trailer}</div>
              </div>
              <span className={`badge ${STATUS_CLASS[s.status] || 'amber'}`}>{s.status}</span>
            </button>
            {open && (
              <div style={{ padding: '0 18px 18px' }}>
                <div className="divider" />
                {s.events.map((ev, i) => (
                  <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'center', padding: '6px 0' }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: ev.done ? 'var(--green)' : 'var(--border2)', flexShrink: 0 }} />
                    <span style={{ fontSize: 13, color: ev.done ? 'var(--text)' : 'var(--faint)' }}>{ev.label}</span>
                    <span style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--faint)' }}>{ev.time}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

const TABS = [
  { id: 'book', label: 'Book shipment' },
  { id: 'track', label: 'My shipments' },
];

export default function UserDashboard({ onLogout }) {
  const [tab, setTab] = useState('book');

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'var(--bg)', display: 'flex', flexDirection: 'column', zIndex: 100 }}>
      <div id="db-topbar">
        <div className="brand-mark">
          <TpLogo size={34} />
          <span>Customer Portal</span>
        </div>
        <div className="db-topbar-spacer" />
        <button className="db-tbtn" onClick={onLogout}>Sign Out</button>
      </div>

      <div style={{ display: 'flex', gap: 4, padding: '10px 20px', borderBottom: '1px solid var(--border)', background: 'var(--surface)' }}>
        {TABS.map(t => (
          <button
            key={t.id}
            className={`btn ${tab === t.id ? '' : 'secondary'}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 28px', background: 'var(--bg)' }}>
        {tab === 'book' && <BookPane />}
        {tab === 'track' && <TrackPane />}
      </div>
    </div>
  );
}
