import React from 'react';

export default function AdminMailboxes() {
  const mailboxes = [
    { id: 'mb-01', provider: 'Amazon SES', email: 'alex@outbound.shivam-itcs.com', daily_sent: 5, daily_limit: 50, status: 'Active (Warmup)', warmup_day: 12 },
    { id: 'mb-02', provider: 'Mailgun Dedicated', email: 'sarah@inbound.shivam-itcs.com', daily_sent: 0, daily_limit: 100, status: 'Standby', warmup_day: 28 },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 6px 0' }}>Sending Mailboxes & SMTP Pools</h2>
          <p style={{ color: 'var(--muted)', fontSize: 13, margin: 0 }}>
            Rotational sending pool to maintain domain reputation and prevent spam-trap classification.
          </p>
        </div>
        <button className="btn btn-primary">➕ Connect New Mailbox</button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {mailboxes.map(m => (
          <div key={m.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <h3 style={{ margin: 0, fontSize: 16 }}>{m.email}</h3>
                <span className="badge badge-interested">{m.status}</span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
                Provider: <strong>{m.provider}</strong> · Warmup Stage: Day {m.warmup_day} of 30
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{m.daily_sent} / {m.daily_limit} sent today</div>
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>Domain Throttle: 10% capacity</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
