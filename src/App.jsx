import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import LoginChooser from './components/LoginChooser';
import AdminLogin from './components/AdminLogin';
import UserLogin from './components/UserLogin';
import UserDashboard from './pages/UserDashboard';
import Sidebar from './components/Sidebar';
import NotificationPanel from './components/NotificationPanel';
import Placeholder from './components/Placeholder';
import TpLogo from './components/TpLogo';
import Customers from './pages/ops/Customers';
import Locations from './pages/ops/Locations';
import Drivers from './pages/ops/Drivers';
import Equipment from './pages/ops/Equipment';
import Shipments from './pages/ops/Shipments';
import ShipmentDetail from './pages/ops/ShipmentDetail';
import Dispatch from './pages/ops/Dispatch';
import Dock from './pages/ops/Dock';
import TripDetail from './pages/ops/TripDetail';
import FleetMap from './pages/ops/FleetMap';
import Integrations from './pages/ops/Integrations';
import Exceptions from './pages/ops/Exceptions';
import Billing from './pages/ops/Billing';
import { useTheme } from './hooks/useTheme';
import { useAuth, isStaff } from './auth';

const APP_NAME = 'TMS';

function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button className="theme-toggle" onClick={toggle} title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} aria-label="Toggle theme">
      {theme === 'dark' ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z" /></svg>
      )}
    </button>
  );
}

/** Login flow shown when there is no authenticated user. */
function LoginFlow() {
  const { login } = useAuth();
  const [screen, setScreen] = useState('chooser'); // chooser | admin-login | user-login | user-signup

  if (screen === 'admin-login') {
    return <AdminLogin onLogin={login} onBack={() => setScreen('chooser')} onShowView={setScreen} />;
  }
  if (screen === 'user-login') {
    return <UserLogin mode="login" onLogin={login} onBack={() => setScreen('chooser')} onShowView={setScreen} />;
  }
  if (screen === 'user-signup') {
    return <UserLogin mode="signup" onLogin={login} onBack={() => setScreen('chooser')} onShowView={setScreen} />;
  }
  return <LoginChooser onShowView={setScreen} />;
}

/** Internal operations dashboard (staff roles only). */
function OpsDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (location.pathname === '/') navigate('/shipments', { replace: true });
  }, [location.pathname, navigate]);

  return (
    <div id="db-panel" className="open">
      <div id="db-topbar">
        <div className="brand-mark">
          <TpLogo size={34} />
          <span>{APP_NAME}</span>
        </div>
        <div className="db-topbar-spacer" />
        <div className="db-search">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
          <input type="text" placeholder="Search…" />
        </div>
        <ThemeToggle />
        <NotificationPanel />
        <div style={{ fontSize: 13, color: 'var(--muted)' }}>{user.full_name}</div>
        <button className="db-tbtn" onClick={logout}>Sign Out</button>
      </div>

      <div id="db-body">
        <Sidebar />
        <div id="db-content">
          <Routes>
            <Route path="/" element={<Navigate to="/shipments" replace />} />
            <Route path="/shipments" element={<Shipments />} />
            <Route path="/shipments/:id" element={<ShipmentDetail />} />
            <Route path="/dispatch" element={<Dispatch />} />
            <Route path="/dock" element={<Dock />} />
            <Route path="/trips/:id" element={<TripDetail />} />
            <Route path="/equipment" element={<Equipment />} />
            <Route path="/drivers" element={<Drivers />} />
            <Route path="/customers" element={<Customers />} />
            <Route path="/locations" element={<Locations />} />
            <Route path="/map" element={<FleetMap />} />
            <Route path="/exceptions" element={<Exceptions />} />
            <Route path="/billing" element={<Billing />} />
            <Route path="/integrations" element={<Integrations />} />
            <Route path="/settings" element={<Placeholder title="Settings" note="Configuration lands in a later batch." />} />
            <Route path="*" element={<Navigate to="/shipments" replace />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const { user, loading, logout } = useAuth();

  if (loading) {
    return (
      <div className="auth-screen">
        <p>Loading…</p>
      </div>
    );
  }

  if (!user) return <LoginFlow />;

  if (isStaff(user.role)) return <OpsDashboard />;

  // customer_user → portal
  return <UserDashboard onLogout={logout} />;
}
