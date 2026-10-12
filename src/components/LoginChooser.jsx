import TpLogo from './TpLogo';

/**
 * LoginChooser — pick Admin (ops) or Customer (portal) sign-in.
 * Mock for now; real auth arrives in Batch 2.
 */
export default function LoginChooser({ onShowView }) {
  return (
    <div className="auth-screen">
      <div style={{ width: '100%', maxWidth: 520, textAlign: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 14 }}>
          <TpLogo size={44} />
        </div>
        <h2 style={{ marginBottom: 6 }}>Sign in</h2>
        <p style={{ marginBottom: 26 }}>Choose how you want to sign in.</p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <button className="auth-card" style={{ textAlign: 'left', cursor: 'pointer' }} onClick={() => onShowView('admin-login')}>
            <div className="auth-title" style={{ fontSize: 16 }}>Staff</div>
            <p style={{ marginBottom: 14 }}>Dispatch, equipment, shipments and operations.</p>
            <span className="btn">Sign in as staff</span>
          </button>

          <button className="auth-card" style={{ textAlign: 'left', cursor: 'pointer' }} onClick={() => onShowView('user-login')}>
            <div className="auth-title" style={{ fontSize: 16 }}>Customer</div>
            <p style={{ marginBottom: 14 }}>Book shipments, request pickups and track freight.</p>
            <span className="btn secondary">Sign in as customer</span>
          </button>
        </div>
      </div>
    </div>
  );
}
