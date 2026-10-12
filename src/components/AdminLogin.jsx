import { useState } from 'react';
import TpLogo from './TpLogo';

// Dev credentials seeded by `python -m app.seed_users`.
const DEMO = { email: 'admin@example.com', password: 'admin123' };

export default function AdminLogin({ onLogin, onBack, onShowView }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async e => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await onLogin(email, password);
      // On success the app re-renders into the ops dashboard.
    } catch (err) {
      setError(err.message || 'Sign in failed.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = () => { setEmail(DEMO.email); setPassword(DEMO.password); setError(''); };

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
          <TpLogo size={40} />
        </div>
        <div className="auth-title">Staff sign in</div>
        <div className="auth-sub">Access the operations dashboard.</div>

        <div className="auth-hint">
          Demo: <strong>{DEMO.email}</strong> / <strong>{DEMO.password}</strong>
          <button type="button" onClick={fillDemo} style={{ display: 'block', marginTop: 6, background: 'none', border: 'none', color: 'var(--accent)', fontSize: 12, cursor: 'pointer', padding: 0, fontWeight: 600 }}>
            Fill automatically
          </button>
        </div>

        <form onSubmit={submit}>
          <div className="form-field">
            <label className="form-label">Email</label>
            <input className="form-input" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="admin@example.com" autoComplete="email" required />
          </div>
          <div className="form-field">
            <label className="form-label">Password</label>
            <input className="form-input" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" autoComplete="current-password" required />
          </div>
          {error && <div className="auth-error">{error}</div>}
          <button className="btn" type="submit" disabled={loading} style={{ width: '100%', marginTop: 4 }}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div style={{ marginTop: 16, fontSize: 12.5, color: 'var(--muted)', textAlign: 'center' }}>
          Not staff?{' '}
          <button style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: 'inherit', fontWeight: 600 }} onClick={() => onShowView('user-login')}>
            Customer sign in
          </button>
        </div>
        <div className="auth-back" onClick={onBack}>← Back</div>
      </div>
    </div>
  );
}
