import React, { useState, useEffect } from 'react';
import { pulseApi } from '../api';

export default function SequencesPage() {
  const [sequences, setSequences] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    pulseApi.listSequences().then(s => {
      setSequences(s);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  return (
    <div style={{ padding: '32px 40px', maxWidth: 1400, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: '0 0 6px 0' }}>Multi-Step Drip Sequences</h1>
          <p style={{ color: 'var(--muted)', fontSize: 14, margin: 0 }}>
            Automated cadence triggers: introductory email, architecture follow-up, and graceful breakup.
          </p>
        </div>
        <button className="btn btn-primary">➕ Add Step to Cadence</button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {sequences.map((step, idx) => (
          <div key={step.id} className="card" style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              width: 48,
              height: 48,
              borderRadius: 10,
              background: 'rgba(6, 182, 212, 0.15)',
              color: 'var(--accent)',
              fontWeight: 700,
              fontSize: 16
            }}>
              #{step.step_number}
            </div>

            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <h3 style={{ margin: 0, fontSize: 17 }}>
                  {step.step_type === 'initial_email' ? 'Step 1: Signal-Personalized Introduction' :
                   step.step_type === 'follow_up' ? 'Step 2: Technical Value & Latency Proof' :
                   'Step 3: Polite Breakup & Opt-Out Notice'}
                </h3>
                <span className="badge badge-more_info">Delay: {step.delay_days} Days after previous</span>
              </div>

              <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
                <strong>Subject Template:</strong> <code style={{ color: '#e2e8f0' }}>{step.subject_template}</code>
              </div>

              <div style={{
                background: 'rgba(0,0,0,0.3)',
                padding: 14,
                borderRadius: 8,
                fontSize: 13,
                color: '#cbd5e1',
                lineHeight: 1.6
              }}>
                {step.body_template}
              </div>

              <div style={{ marginTop: 12, display: 'flex', gap: 16, fontSize: 12, color: 'var(--muted)' }}>
                <span>🎯 Persona: <strong>Technical SDR</strong></span>
                <span>📬 Channel: <strong>Work Email (SMTP/SES)</strong></span>
                <span>🛡️ Stop condition: <strong>Reply received or Opt-out</strong></span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
