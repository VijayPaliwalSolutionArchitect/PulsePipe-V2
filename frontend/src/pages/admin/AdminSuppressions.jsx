import React, { useState, useEffect } from 'react';
import { pulseApi } from '../../api';

export default function AdminSuppressions() {
  const [suppressions, setSuppressions] = useState([]);
  const [newEmail, setNewEmail] = useState('');

  const load = () => {
    pulseApi.listSuppressions().then(setSuppressions).catch(console.error);
  };

  useEffect(load, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newEmail.trim()) return;
    await pulseApi.addSuppression({ email: newEmail.trim(), reason: 'Manual administrative block' });
    setNewEmail('');
    load();
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 6px 0' }}>Suppressions & Opt-Out Blacklist</h2>
          <p style={{ color: 'var(--muted)', fontSize: 13, margin: 0 }}>
            CAN-SPAM & GDPR compliance engine: suppressed contacts are strictly blocked from all outbound sequence dispatches.
          </p>
        </div>
      </div>

      <form onSubmit={handleAdd} className="card" style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <input
          type="email"
          placeholder="Enter email to suppress (e.g. prospect@example.com)..."
          value={newEmail}
          onChange={e => setNewEmail(e.target.value)}
          style={{
            flex: 1,
            background: 'rgba(0,0,0,0.3)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            padding: '10px 14px',
            color: 'var(--text)',
            fontSize: 13
          }}
          required
        />
        <button type="submit" className="btn btn-primary">🚫 Add to Blacklist</button>
      </form>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--muted)' }}>
              <th style={{ padding: '12px 20px' }}>Suppressed Email</th>
              <th style={{ padding: '12px 20px' }}>Reason</th>
              <th style={{ padding: '12px 20px' }}>Suppressed Date</th>
              <th style={{ padding: '12px 20px', textAlign: 'right' }}>Compliance</th>
            </tr>
          </thead>
          <tbody>
            {suppressions.map(s => (
              <tr key={s.id} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: '12px 20px', fontWeight: 600 }}>{s.email}</td>
                <td style={{ padding: '12px 20px', color: 'var(--muted)' }}>{s.reason}</td>
                <td style={{ padding: '12px 20px', color: 'var(--muted)' }}>{s.created_at || '2026-11-22'}</td>
                <td style={{ padding: '12px 20px', textAlign: 'right' }}>
                  <span className="badge badge-unsubscribe">HARD SUPPRESSION</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
