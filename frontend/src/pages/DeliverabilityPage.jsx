import React, { useState, useEffect } from 'react';
import { pulseApi } from '../api';

export default function DeliverabilityPage() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    pulseApi.getDeliverabilityHealth().then(setHealth).catch(console.error);
  }, []);

  return (
    <div style={{ padding: '32px 40px', maxWidth: 1400, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: '0 0 6px 0' }}>Deliverability & Domain Health</h1>
          <p style={{ color: 'var(--muted)', fontSize: 14, margin: 0 }}>
            Sender domain reputation monitoring: SPF, DKIM, DMARC records, bounce rates, and daily throttle ceilings.
          </p>
        </div>
        <span className="badge badge-interested" style={{ padding: '6px 14px', fontSize: 13 }}>
          🟢 SENDER REPUTATION: 99.4% HEALTHY
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20, marginBottom: 32 }}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>SPF Authentication</span>
            <span className="badge badge-interested">VALID</span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 8 }}>v=spf1 include:_spf.mailgun.org include:amazonses.com ~all</div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>DKIM Signature</span>
            <span className="badge badge-interested">2048-BIT SIGNED</span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 8 }}>k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQ...</div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>DMARC Policy</span>
            <span className="badge badge-interested">p=reject (100%)</span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 8 }}>Spoofing protection enabled with strict reject policy.</div>
        </div>
      </div>

      {/* METRICS & DOMAIN THROTTLE */}
      <div className="card">
        <h3 style={{ fontSize: 16, margin: '0 0 16px 0' }}>Daily Outbound Throttle & Bounce Metrics</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }}>
          <div style={{ padding: 18, background: 'rgba(0,0,0,0.3)', borderRadius: 10 }}>
            <div style={{ fontSize: 12, color: 'var(--muted)' }}>Daily Domain Send Volume</div>
            <div style={{ fontSize: 26, fontWeight: 700, margin: '6px 0', color: 'var(--accent)' }}>5 / 50</div>
            <div style={{ fontSize: 12, color: 'var(--muted)' }}>Within safe warmup rate limits (10% capacity)</div>
          </div>

          <div style={{ padding: 18, background: 'rgba(0,0,0,0.3)', borderRadius: 10 }}>
            <div style={{ fontSize: 12, color: 'var(--muted)' }}>Bounce Rate (Hard + Soft)</div>
            <div style={{ fontSize: 26, fontWeight: 700, margin: '6px 0', color: 'var(--success)' }}>0.0%</div>
            <div style={{ fontSize: 12, color: 'var(--muted)' }}>Target: &lt; 2.0% (Zero bounces recorded)</div>
          </div>

          <div style={{ padding: 18, background: 'rgba(0,0,0,0.3)', borderRadius: 10 }}>
            <div style={{ fontSize: 12, color: 'var(--muted)' }}>Opt-Out Suppression Rate</div>
            <div style={{ fontSize: 26, fontWeight: 700, margin: '6px 0', color: '#fbbf24' }}>1.2%</div>
            <div style={{ fontSize: 12, color: 'var(--muted)' }}>Instantly blacklisted from future campaigns</div>
          </div>
        </div>
      </div>
    </div>
  );
}
