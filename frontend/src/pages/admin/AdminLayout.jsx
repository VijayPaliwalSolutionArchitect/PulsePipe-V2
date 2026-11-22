import React from 'react';
import { NavLink, Outlet, Link } from 'react-router-dom';

class AdminErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error('[PulsePipe Admin Error]', error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 40, color: 'var(--text)' }}>
          <div className="card" style={{ maxWidth: 600, margin: '40px auto', borderColor: 'var(--danger)' }}>
            <h2 style={{ color: 'var(--danger)', margin: '0 0 12px 0' }}>SDR Console Error</h2>
            <p style={{ color: 'var(--muted)', fontSize: 14 }}>{this.state.error?.message || 'An unexpected rendering error occurred.'}</p>
            <button className="btn btn-primary" onClick={() => window.location.reload()} style={{ marginTop: 16 }}>
              🔄 Reload Console
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function AdminLayout() {
  const navItems = [
    { to: '/admin', label: 'SDR Overview', icon: '📊', end: true },
    { to: '/admin/personas', label: 'Sender Personas', icon: '👤' },
    { to: '/admin/suppressions', label: 'Suppressions & Opt-Outs', icon: '🚫' },
    { to: '/admin/mailboxes', label: 'Mailbox Pools & SMTP', icon: '📬' },
    { to: '/admin/models', label: 'Model Router & Spend', icon: '⚡' },
  ];

  return (
    <AdminErrorBoundary>
      <div style={{ display: 'flex', minHeight: 'calc(100vh - 64px)' }}>
        <aside style={{
          width: 260,
          borderRight: '1px solid var(--border)',
          padding: '24px 16px',
          background: 'rgba(16, 23, 38, 0.4)',
          display: 'flex',
          flexDirection: 'column',
          gap: 6
        }}>
          <div style={{ padding: '0 12px 16px', borderBottom: '1px solid var(--border)', marginBottom: 12 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: 0.8 }}>
              SDR System Administration
            </div>
          </div>
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 14px',
                borderRadius: 8,
                fontSize: 13,
                fontWeight: 600,
                color: isActive ? 'var(--accent)' : 'var(--muted)',
                background: isActive ? 'rgba(6, 182, 212, 0.12)' : 'transparent',
                border: isActive ? '1px solid rgba(6, 182, 212, 0.25)' : '1px solid transparent'
              })}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
          <div style={{ marginTop: 'auto', paddingTop: 16, borderTop: '1px solid var(--border)' }}>
            <Link to="/" style={{ fontSize: 12, color: 'var(--muted)', display: 'block', textAlign: 'center' }}>
              ← Back to Campaign Hub
            </Link>
          </div>
        </aside>

        <main style={{ flex: 1, padding: '32px 40px', overflowY: 'auto' }}>
          <Outlet />
        </main>
      </div>
    </AdminErrorBoundary>
  );
}
