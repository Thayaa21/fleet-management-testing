import { useState } from 'react';
import TpLogo from './TpLogo';

// Dev credentials seeded by `python -m app.seed_users`.
const DEMO_LOGIN = { email: 'customer@example.com', password: 'customer123' };

function LoginForm({ onLogin, onBack, onSwitchToSignup }) {
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
    } catch (err) {
      setError(err.message || 'Sign in failed.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = () => { setEmail(DEMO_LOGIN.email); setPassword(DEMO_LOGIN.password); setError(''); };

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
          <TpLogo size={40} />
        </div>
        <div className="auth-title">Customer sign in</div>
        <div className="auth-sub">Book and track your shipments.</div>

        <div className="auth-hint">
          Demo: <strong>{DEMO_LOGIN.email}</strong> / <strong>{DEMO_LOGIN.password}</strong>
          <button type="button" onClick={fillDemo} style={{ display: 'block', marginTop: 6, background: 'none', border: 'none', color: 'var(--accent)', fontSize: 12, cursor: 'pointer', padding: 0, fontWeight: 600 }}>
            Fill automatically
          </button>
        </div>

        <form onSubmit={submit}>
          <div className="form-field">
            <label className="form-label">Email</label>
            <input className="form-input" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" required />
          </div>
          <div className="form-field">
            <label className="form-label">Password</label>
            <input className="form-input" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required />
          </div>
          {error && <div className="auth-error">{error}</div>}
          <button className="btn" type="submit" disabled={loading} style={{ width: '100%', marginTop: 4 }}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div style={{ marginTop: 16, fontSize: 12.5, color: 'var(--muted)', textAlign: 'center' }}>
          New here?{' '}
          <button style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: 'inherit', fontWeight: 600 }} onClick={onSwitchToSignup}>
            Create an account
          </button>
        </div>
        <div className="auth-back" onClick={onBack}>← Back</div>
      </div>
    </div>
  );
}

function SignupForm({ onBack }) {
  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
          <TpLogo size={40} />
        </div>
        <div className="auth-title">Create account</div>
        <div className="auth-sub">Customer accounts are provisioned by our team.</div>
        <div className="auth-hint">
          Self-service signup isn’t available yet. Contact your account manager to have a
          customer login created. Account self-registration is planned for a later batch.
        </div>
        <button className="btn" style={{ width: '100%' }} onClick={onBack}>Back to sign in</button>
      </div>
    </div>
  );
}

export default function UserLogin({ mode, onLogin, onBack }) {
  const [localMode, setLocalMode] = useState(mode);

  if (localMode === 'signup') {
    return <SignupForm onBack={() => setLocalMode('login')} />;
  }
  return (
    <LoginForm
      onLogin={onLogin}
      onBack={onBack}
      onSwitchToSignup={() => setLocalMode('signup')}
    />
  );
}
