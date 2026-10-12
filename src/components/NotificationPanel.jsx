import { useState, useRef, useEffect } from 'react';
import { Bell, X, CheckCheck, AlertTriangle, CheckCircle, Info, Zap } from 'lucide-react';
import { useFleetState } from '../hooks/fleetContext';

const TYPE_CONFIG = {
  critical: { icon: AlertTriangle, color: 'var(--red)',   bg: 'rgba(236,111,142,0.12)',  border: 'rgba(236,111,142,0.25)' },
  warning:  { icon: AlertTriangle, color: 'var(--amber)', bg: 'rgba(255,146,56,0.10)',   border: 'rgba(255,146,56,0.25)' },
  success:  { icon: CheckCircle,   color: 'var(--green)', bg: 'rgba(88,176,156,0.10)',   border: 'rgba(88,176,156,0.25)' },
  info:     { icon: Info,          color: 'var(--blue)',  bg: 'rgba(46,202,220,0.10)',   border: 'rgba(46,202,220,0.25)' },
};

export default function NotificationPanel() {
  const { notifications, markAllRead, dismissNotification, clearAllNotifications } = useFleetState();
  const [open, setOpen] = useState(false);
  const panelRef = useRef(null);

  const unreadCount = notifications.filter(n => !n.read).length;

  // Close when clicking outside
  useEffect(() => {
    const handleClick = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) setOpen(false);
    };
    if (open) document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  const handleOpen = () => {
    setOpen(prev => !prev);
  };

  return (
    <div ref={panelRef} style={{ position: 'relative' }}>
      {/* Bell button */}
      <button
        onClick={handleOpen}
        style={{
          width: '40px', height: '40px', borderRadius: '12px',
          background: open ? 'rgba(46,202,220,0.15)' : 'var(--card)',
          border: open ? '1px solid var(--blue)' : '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: open ? 'var(--blue)' : 'var(--text)',
          cursor: 'pointer', position: 'relative', transition: 'all 0.2s',
        }}
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span style={{
            position: 'absolute', top: '-4px', right: '-4px',
            background: 'var(--red)', color: '#fff',
            fontSize: '9px', fontWeight: '800',
            width: '16px', height: '16px', borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            border: '1.5px solid var(--bg)',
          }}>
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown panel */}
      {open && (
        <div
          className="animate-fade"
          style={{
            position: 'absolute', top: 'calc(100% + 10px)', right: 0,
            width: '360px', zIndex: 500,
            background: 'var(--surface)',
            border: '1px solid var(--border)', borderRadius: '12px',
            boxShadow: '0 16px 48px rgba(0,0,0,0.25)',
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Zap size={15} color="var(--blue)" />
              <span style={{ fontWeight: '700', fontSize: '13px' }}>Notifications</span>
              {unreadCount > 0 && (
                <span className="badge red" style={{ fontSize: '9px', padding: '2px 6px' }}>{unreadCount} NEW</span>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                onClick={markAllRead}
                style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--blue)', background: 'none', border: 'none', cursor: 'pointer', padding: '4px 8px', borderRadius: '6px' }}
              >
                <CheckCheck size={13} />
                Mark all read
              </button>
            )}
          </div>

          {/* List */}
          <div style={{ maxHeight: '420px', overflowY: 'auto' }}>
            {notifications.length === 0 ? (
              <div style={{ padding: '48px 20px', textAlign: 'center' }}>
                <Bell size={28} color="var(--muted)" style={{ marginBottom: '12px', opacity: 0.4 }} />
                <p className="small" style={{ color: 'var(--muted)' }}>No notifications</p>
              </div>
            ) : (
              notifications.map(n => {
                const cfg = TYPE_CONFIG[n.type] || TYPE_CONFIG.info;
                const Icon = cfg.icon;
                return (
                  <div
                    key={n.id}
                    style={{
                      padding: '14px 20px',
                      borderBottom: '1px solid rgba(0,0,0,0.04)',
                      background: n.read ? 'transparent' : 'rgba(46,202,220,0.04)',
                      display: 'flex', gap: '12px', alignItems: 'flex-start',
                      transition: 'background 0.2s',
                    }}
                  >
                    {/* Icon badge */}
                    <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: cfg.bg, border: `1px solid ${cfg.border}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: '1px' }}>
                      <Icon size={14} color={cfg.color} />
                    </div>

                    {/* Content */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '3px' }}>
                        <span style={{ fontWeight: n.read ? '600' : '700', fontSize: '13px', lineHeight: '1.3' }}>{n.title}</span>
                        {!n.read && <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--blue)', flexShrink: 0, marginTop: '4px' }} />}
                      </div>
                      <p style={{ fontSize: '12px', color: 'var(--muted)', lineHeight: '1.5', marginBottom: '4px' }}>{n.message}</p>
                      <span style={{ fontSize: '10px', color: 'rgba(208,221,231,0.4)', fontWeight: '600' }}>{n.time}</span>
                    </div>

                    {/* Dismiss */}
                    <button
                      onClick={() => dismissNotification(n.id)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', padding: '2px', borderRadius: '4px', flexShrink: 0, opacity: 0.5, transition: 'opacity 0.2s' }}
                      onMouseEnter={e => e.currentTarget.style.opacity = 1}
                      onMouseLeave={e => e.currentTarget.style.opacity = 0.5}
                    >
                      <X size={13} />
                    </button>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border)', textAlign: 'center' }}>
              <button
                onClick={clearAllNotifications}
                style={{ fontSize: '11px', color: 'var(--muted)', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                Clear all notifications
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}