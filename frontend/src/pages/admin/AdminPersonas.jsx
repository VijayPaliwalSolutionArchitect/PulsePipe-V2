import React, { useState, useEffect } from 'react';
import { pulseApi } from '../../api';

export default function AdminPersonas() {
  const [personas, setPersonas] = useState([]);

  useEffect(() => {
    pulseApi.listPersonas().then(setPersonas).catch(console.error);
  }, []);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 6px 0' }}>SDR Sender Personas & Voice Profiles</h2>
          <p style={{ color: 'var(--muted)', fontSize: 13, margin: 0 }}>
            Configure consultative AI SDR writing styles, tone, and peer-to-peer positioning.
          </p>
        </div>
        <button className="btn btn-primary">➕ Create Persona</button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
        {personas.map(p => (
          <div key={p.id} className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 16 }}>{p.name.toUpperCase()} PERSONA</h3>
                <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>Tone: {p.tone}</div>
              </div>
              {p.is_default && <span className="badge badge-interested">DEFAULT SENDER</span>}
            </div>

            <div style={{ background: 'rgba(0,0,0,0.3)', padding: 14, borderRadius: 8, fontSize: 13, color: '#cbd5e1', lineHeight: 1.6 }}>
              <strong>System Instruction:</strong> {p.system_prompt}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
