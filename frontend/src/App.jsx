import React from 'react';
import { Routes, Route, Link, NavLink } from 'react-router-dom';
import ClientDashboard from './pages/ClientDashboard';
import SequencesPage from './pages/SequencesPage';
import InboxPage from './pages/InboxPage';
import DeliverabilityPage from './pages/DeliverabilityPage';
import AdminLayout from './pages/admin/AdminLayout';
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminPersonas from './pages/admin/AdminPersonas';
import AdminSuppressions from './pages/admin/AdminSuppressions';
import AdminMailboxes from './pages/admin/AdminMailboxes';
import AdminModels from './pages/admin/AdminModels';

export default function App() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{
        height: 64,
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 28px',
        background: 'rgba(16, 23, 38, 0.85)',
        backdropFilter: 'blur(12px)',
        position: 'sticky',
        top: 0,
        zIndex: 50
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 10, fontWeight: 700, fontSize: 17 }}>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 32,
              height: 32,
              borderRadius: 8,
              background: 'linear-gradient(135deg, #06b6d4, #3b82f6)',
              color: '#fff',
              fontSize: 16
            }}>📡</span>
            <span>Pulse<span style={{ color: 'var(--accent)' }}>Pipe</span> <span style={{ fontSize: 12, padding: '2px 6px', borderRadius: 4, background: 'rgba(6,182,212,0.15)', color: 'var(--accent)' }}>V2 SDR</span></span>
          </Link>
          <nav style={{ display: 'flex', gap: 20, fontSize: 13, fontWeight: 500 }}>
            <NavLink to="/" end style={({ isActive }) => ({ color: isActive ? 'var(--accent)' : 'var(--muted)', display: 'flex', alignItems: 'center', gap: 6 })}>
              <span>📊</span> Campaigns & Pipeline
            </NavLink>
            <NavLink to="/sequences" style={({ isActive }) => ({ color: isActive ? 'var(--accent)' : 'var(--muted)', display: 'flex', alignItems: 'center', gap: 6 })}>
              <span>⚡</span> Step Sequences
            </NavLink>
            <NavLink to="/inbox" style={({ isActive }) => ({ color: isActive ? 'var(--accent)' : 'var(--muted)', display: 'flex', alignItems: 'center', gap: 6 })}>
              <span>📥</span> Reply Triage <span style={{ fontSize: 10, padding: '1px 5px', borderRadius: 10, background: 'rgba(16,185,129,0.2)', color: 'var(--success)' }}>AI Live</span>
            </NavLink>
            <NavLink to="/deliverability" style={({ isActive }) => ({ color: isActive ? 'var(--accent)' : 'var(--muted)', display: 'flex', alignItems: 'center', gap: 6 })}>
              <span>🛡️</span> Deliverability Health
            </NavLink>
          </nav>
        </div>
        <div>
          <Link to="/admin" style={{
            fontSize: 12,
            fontWeight: 600,
            padding: '7px 14px',
            borderRadius: 8,
            background: 'rgba(6, 182, 212, 0.12)',
            border: '1px solid rgba(6, 182, 212, 0.3)',
            color: 'var(--accent)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6
          }}>
            <span>⚙️</span> SHIVAM SDR Admin
          </Link>
        </div>
      </header>

      <div style={{ flex: 1 }}>
        <Routes>
          <Route path="/" element={<ClientDashboard />} />
          <Route path="/sequences" element={<SequencesPage />} />
          <Route path="/inbox" element={<InboxPage />} />
          <Route path="/deliverability" element={<DeliverabilityPage />} />

          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<AdminDashboard />} />
            <Route path="personas" element={<AdminPersonas />} />
            <Route path="suppressions" element={<AdminSuppressions />} />
            <Route path="mailboxes" element={<AdminMailboxes />} />
            <Route path="models" element={<AdminModels />} />
          </Route>
        </Routes>
      </div>
    </div>
  );
}
