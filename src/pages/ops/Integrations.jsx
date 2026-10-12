import { useEffect, useState } from 'react';
import DataTable from '../../components/DataTable';
import { ingestLogs } from '../../api/telematics';
import * as integrationsApi from '../../api/integrations';
import { listCustomers } from '../../api/customers';

const INGEST_ERROR_CODES = ['UNKNOWN_DEVICE', 'DEVICE_UNASSIGNED', 'MALFORMED_PAYLOAD', 'AUTH_FAILED', 'DUPLICATE'];
const API_ERROR_CODES = [
  'MISSING_API_KEY', 'INVALID_API_KEY', 'EXPIRED_API_KEY', 'REVOKED_API_KEY', 'INSUFFICIENT_SCOPE',
  'IP_NOT_ALLOWED', 'RATE_LIMITED', 'VALIDATION_ERROR', 'UNKNOWN_PROBILL', 'DUPLICATE_REQUEST', 'INTERNAL_ERROR',
];
const SCOPES = ['tracking:read', 'shipments:write', 'pickups:write', 'documents:read'];

function fmt(dt) {
  return dt ? new Date(dt).toLocaleString() : '—';
}

// ── Telematics ingest log ──
function TelematicsTab() {
  const [errorCode, setErrorCode] = useState('');
  const columns = [
    { key: 'received_at', label: 'Received', render: r => fmt(r.received_at) },
    { key: 'provider', label: 'Provider' },
    { key: 'device_serial', label: 'Device', render: r => r.device_serial || '—' },
    { key: 'http_status_returned', label: 'HTTP' },
    { key: 'error_code', label: 'Result', render: r => (r.error_code ? <span className="badge red">{r.error_code}</span> : <span className="badge green">OK</span>) },
  ];
  return (
    <>
      <div style={{ display: 'flex', gap: 10, marginBottom: 12, alignItems: 'center' }}>
        <label className="form-label" style={{ margin: 0 }}>Error code</label>
        <select className="form-select" style={{ width: 220 }} value={errorCode} onChange={e => setErrorCode(e.target.value)}>
          <option value="">All</option>
          {INGEST_ERROR_CODES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      <DataTable columns={columns} filters={{ error_code: errorCode }}
        fetchPage={(p) => ingestLogs({ ...p, error_code: errorCode || undefined })}
        searchPlaceholder="(search n/a)" />
    </>
  );
}

// ── API clients + keys + allowlist + subscriptions ──
function ClientsTab() {
  const [clients, setClients] = useState([]);
  const [selected, setSelected] = useState(null);
  const [keys, setKeys] = useState([]);
  const [allowlist, setAllowlist] = useState([]);
  const [subs, setSubs] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [newKey, setNewKey] = useState(null); // full key shown once
  const [msg, setMsg] = useState('');
  const [scopes, setScopes] = useState(['tracking:read']);
  const [cidr, setCidr] = useState('');
  const [targetUrl, setTargetUrl] = useState('');
  const [subSecret, setSubSecret] = useState('');

  const loadClients = () => integrationsApi.listClients().then(setClients).catch(e => setMsg(e.message));
  useEffect(() => {
    let cancelled = false;
    (async () => { await null; if (!cancelled) { loadClients(); listCustomers({ page_size: 100 }).then(r => setCustomers(r.items)).catch(() => {}); } })();
    return () => { cancelled = true; };
  }, []);

  const openClient = async (c) => {
    setSelected(c); setNewKey(null); setMsg('');
    setKeys(await integrationsApi.listKeys(c.id));
    setAllowlist(await integrationsApi.listAllowlist(c.id));
    setSubs(await integrationsApi.listSubscriptions(c.id));
  };

  const addClient = async () => {
    if (!customers.length) { setMsg('Create a customer first.'); return; }
    const name = prompt('Client name?');
    if (!name) return;
    try {
      await integrationsApi.createClient({ customer_id: customers[0].id, name });
      loadClients();
    } catch (e) { setMsg(e.message); }
  };

  const genKey = async () => {
    try {
      const created = await integrationsApi.createKey(selected.id, { scopes });
      setNewKey(created.api_key);
      setKeys(await integrationsApi.listKeys(selected.id));
    } catch (e) { setMsg(e.message); }
  };

  const addIp = async () => {
    if (!cidr) return;
    await integrationsApi.addAllowlist(selected.id, { cidr, label: '' });
    setCidr('');
    setAllowlist(await integrationsApi.listAllowlist(selected.id));
  };

  const addSub = async () => {
    if (!targetUrl) return;
    await integrationsApi.createSubscription(selected.id, { target_url: targetUrl, secret: subSecret, event_types: [] });
    setTargetUrl(''); setSubSecret('');
    setSubs(await integrationsApi.listSubscriptions(selected.id));
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 20 }}>
      <div>
        <button className="btn" style={{ marginBottom: 10 }} onClick={addClient}>+ New client</button>
        {msg && <div className="auth-error" style={{ marginBottom: 8 }}>{msg}</div>}
        <div className="glass-card" style={{ padding: 8 }}>
          {clients.length === 0 ? <p style={{ color: 'var(--muted)', padding: 8 }}>No clients.</p> : clients.map(c => (
            <button key={c.id} onClick={() => openClient(c)}
              style={{ display: 'block', width: '100%', textAlign: 'left', background: selected?.id === c.id ? 'var(--accent-dim)' : 'none', border: 'none', padding: '8px 10px', borderRadius: 6, cursor: 'pointer', color: 'var(--text)' }}>
              {c.name} <span className="badge blue" style={{ marginLeft: 6 }}>{c.status}</span>
            </button>
          ))}
        </div>
      </div>

      <div>
        {!selected ? (
          <p style={{ color: 'var(--muted)' }}>Select a client to manage keys, allowlist and webhooks.</p>
        ) : (
          <>
            <h3 style={{ marginBottom: 10 }}>{selected.name}</h3>

            {/* Keys */}
            <div className="glass-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <strong>API keys</strong>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  {SCOPES.map(s => (
                    <label key={s} style={{ fontSize: 11, display: 'flex', gap: 3, alignItems: 'center' }}>
                      <input type="checkbox" checked={scopes.includes(s)}
                        onChange={e => setScopes(v => e.target.checked ? [...v, s] : v.filter(x => x !== s))} />
                      {s}
                    </label>
                  ))}
                  <button className="btn" style={{ padding: '4px 10px', fontSize: 11 }} onClick={genKey}>Generate</button>
                </div>
              </div>
              {newKey && (
                <div className="auth-hint" style={{ marginBottom: 10 }}>
                  Copy this key now — it will not be shown again:<br />
                  <code style={{ wordBreak: 'break-all' }}>{newKey}</code>
                </div>
              )}
              <table className="lb-table">
                <thead><tr><th>Prefix</th><th>Scopes</th><th>Expires</th><th>Last used</th><th></th></tr></thead>
                <tbody>
                  {keys.length === 0 ? <tr><td colSpan={5} style={{ color: 'var(--muted)' }}>No keys.</td></tr> : keys.map(k => (
                    <tr key={k.id}>
                      <td><code>{k.key_prefix}</code></td>
                      <td style={{ fontSize: 12 }}>{(k.scopes || []).join(', ')}</td>
                      <td>{fmt(k.expires_at)}</td>
                      <td>{fmt(k.last_used_at)}</td>
                      <td style={{ textAlign: 'right' }}>
                        {k.revoked_at ? <span className="badge red">revoked</span> :
                          <button className="btn secondary" style={{ padding: '3px 8px', fontSize: 11 }}
                            onClick={async () => { await integrationsApi.revokeKey(k.id); setKeys(await integrationsApi.listKeys(selected.id)); }}>Revoke</button>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* IP allowlist */}
            <div className="glass-card">
              <strong>IP allowlist</strong>
              <div style={{ display: 'flex', gap: 8, margin: '10px 0' }}>
                <input className="form-input" style={{ maxWidth: 220 }} placeholder="e.g. 203.0.113.0/24" value={cidr} onChange={e => setCidr(e.target.value)} />
                <button className="btn secondary" onClick={addIp}>Add CIDR</button>
              </div>
              {allowlist.length === 0 ? <p style={{ color: 'var(--muted)', fontSize: 13 }}>No allowlist — all IPs allowed.</p> : allowlist.map(a => (
                <div key={a.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                  <code>{a.cidr}</code>
                  <button className="btn secondary" style={{ padding: '2px 8px', fontSize: 11 }}
                    onClick={async () => { await integrationsApi.deleteAllowlist(a.id); setAllowlist(await integrationsApi.listAllowlist(selected.id)); }}>Remove</button>
                </div>
              ))}
            </div>

            {/* Webhook subscriptions */}
            <div className="glass-card">
              <strong>Webhook subscriptions</strong>
              <div style={{ display: 'flex', gap: 8, margin: '10px 0', flexWrap: 'wrap' }}>
                <input className="form-input" style={{ flex: 1, minWidth: 220 }} placeholder="https://customer.example/hook" value={targetUrl} onChange={e => setTargetUrl(e.target.value)} />
                <input className="form-input" style={{ maxWidth: 160 }} placeholder="signing secret" value={subSecret} onChange={e => setSubSecret(e.target.value)} />
                <button className="btn secondary" onClick={addSub}>Add</button>
              </div>
              {subs.length === 0 ? <p style={{ color: 'var(--muted)', fontSize: 13 }}>No subscriptions.</p> : subs.map(s => (
                <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 13 }}>
                  <code style={{ wordBreak: 'break-all' }}>{s.target_url}</code>
                  <span className={`badge ${s.status === 'failing' ? 'red' : s.status === 'paused' ? 'amber' : 'green'}`}>{s.status}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── API request log ──
function ApiLogsTab() {
  const [errorCode, setErrorCode] = useState('');
  const columns = [
    { key: 'received_at', label: 'When', render: r => fmt(r.received_at) },
    { key: 'method', label: 'Method' },
    { key: 'path', label: 'Path' },
    { key: 'key_prefix', label: 'Key', render: r => r.key_prefix ? <code>{r.key_prefix}</code> : '—' },
    { key: 'source_ip', label: 'IP' },
    { key: 'response_status', label: 'Status' },
    { key: 'error_code', label: 'Error', render: r => (r.error_code ? <span className="badge red">{r.error_code}</span> : <span className="badge green">OK</span>) },
    { key: 'latency_ms', label: 'ms' },
  ];
  return (
    <>
      <div style={{ display: 'flex', gap: 10, marginBottom: 12, alignItems: 'center' }}>
        <label className="form-label" style={{ margin: 0 }}>Error code</label>
        <select className="form-select" style={{ width: 240 }} value={errorCode} onChange={e => setErrorCode(e.target.value)}>
          <option value="">All</option>
          {API_ERROR_CODES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      <DataTable columns={columns} filters={{ error_code: errorCode }}
        fetchPage={(p) => integrationsApi.apiLogs({ ...p, error_code: errorCode || undefined })}
        searchPlaceholder="(search n/a)" />
    </>
  );
}

// ── Webhook deliveries ──
function WebhooksTab() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [onlyFailed, setOnlyFailed] = useState(false);
  const columns = [
    { key: 'created_at', label: 'Shipment', render: r => `#${r.shipment_id ?? '—'}` },
    { key: 'attempt_number', label: 'Attempt' },
    { key: 'response_status', label: 'HTTP', render: r => r.response_status ?? '—' },
    { key: 'error', label: 'Error', render: r => (r.error ? <span className="badge red">{r.error}</span> : null) },
    { key: 'delivered', label: 'Delivered', render: r => (r.delivered ? <span className="badge green">yes</span> : <span className="badge amber">no</span>) },
    { key: 'next_retry_at', label: 'Next retry', render: r => fmt(r.next_retry_at) },
    {
      key: 'id', label: '', render: r => (
        <button className="btn secondary" style={{ padding: '3px 8px', fontSize: 11 }}
          onClick={async (e) => { e.stopPropagation(); await integrationsApi.resendDelivery(r.id); setRefreshKey(k => k + 1); }}>Resend</button>
      ),
    },
  ];
  return (
    <>
      <div style={{ display: 'flex', gap: 12, marginBottom: 12, alignItems: 'center' }}>
        <label style={{ display: 'flex', gap: 6, alignItems: 'center', fontSize: 13, color: 'var(--muted)' }}>
          <input type="checkbox" checked={onlyFailed} onChange={e => setOnlyFailed(e.target.checked)} /> Only failed
        </label>
        <button className="btn secondary" style={{ marginLeft: 'auto' }}
          onClick={async () => { await integrationsApi.deliverNow(); setRefreshKey(k => k + 1); }}>Deliver now</button>
      </div>
      <DataTable columns={columns} refreshKey={refreshKey} filters={{ delivered: onlyFailed ? false : undefined }}
        fetchPage={(p) => integrationsApi.webhookDeliveries({ ...p, delivered: onlyFailed ? false : undefined })}
        searchPlaceholder="(search n/a)" />
    </>
  );
}

const TABS = [
  { id: 'telematics', label: 'Telematics', el: <TelematicsTab /> },
  { id: 'clients', label: 'API Clients', el: <ClientsTab /> },
  { id: 'logs', label: 'API Logs', el: <ApiLogsTab /> },
  { id: 'webhooks', label: 'Webhooks', el: <WebhooksTab /> },
];

export default function Integrations() {
  const [tab, setTab] = useState('telematics');
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="s-tag">Integrations</div>
          <h2>Integrations</h2>
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
