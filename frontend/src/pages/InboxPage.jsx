import React, { useState, useEffect } from 'react';
import { pulseApi } from '../api';

export default function InboxPage() {
  const [replies, setReplies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedReply, setSelectedReply] = useState(null);

  useEffect(() => {
    pulseApi.listReplies().then(data => {
      setReplies(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  return (
    <div style={{ padding: '32px 40px', maxWidth: 1400, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: '0 0 6px 0' }}>AI Reply Triage Inbox</h1>
          <p style={{ color: 'var(--muted)', fontSize: 14, margin: 0 }}>
            Inbound prospect email classifier: auto-detects meeting intent, technical inquiries, out-of-office, and CAN-SPAM unsubscribes.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <span className="badge badge-interested">Interested (Demo)</span>
          <span className="badge badge-more_info">More Info</span>
          <span className="badge badge-out_of_office">Out of Office</span>
          <span className="badge badge-unsubscribe">Unsubscribe</span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: 24 }}>
        {/* REPLIES LIST */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', fontWeight: 600, fontSize: 14 }}>
            Inbound Responses ({replies.length})
          </div>
          <div style={{ maxHeight: 650, overflowY: 'auto' }}>
            {replies.map(r => (
              <div
                key={r.id}
                onClick={() => setSelectedReply(r)}
                style={{
                  padding: '16px 20px',
                  borderBottom: '1px solid var(--border)',
                  cursor: 'pointer',
                  background: selectedReply?.id === r.id ? 'var(--surface-hover)' : 'transparent',
                  transition: 'background 0.15s'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontWeight: 600, fontSize: 13 }}>{r.sender_email}</span>
                  <span className={`badge badge-${r.reply_intent}`}>
                    {r.reply_intent}
                  </span>
                </div>
                <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text)', marginBottom: 4 }}>{r.subject}</div>
                <div style={{ fontSize: 12, color: 'var(--muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {r.body_text}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* DETAIL VIEW & SUGGESTED ACTION */}
        <div className="card">
          {selectedReply ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border)', paddingBottom: 16, marginBottom: 20 }}>
                <div>
                  <h3 style={{ margin: '0 0 6px 0', fontSize: 18 }}>{selectedReply.subject}</h3>
                  <div style={{ fontSize: 13, color: 'var(--muted)' }}>From: <strong style={{ color: 'var(--text)' }}>{selectedReply.sender_email}</strong></div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span className={`badge badge-${selectedReply.reply_intent}`} style={{ fontSize: 12, padding: '4px 12px' }}>
                    Intent: {selectedReply.reply_intent} (Confidence: {Math.round(selectedReply.confidence * 100)}%)
                  </span>
                  <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>Status: {selectedReply.status}</div>
                </div>
              </div>

              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>Prospect Email Body</div>
                <div style={{ padding: 18, background: 'rgba(0,0,0,0.3)', borderRadius: 8, fontSize: 14, lineHeight: 1.6, color: '#e2e8f0' }}>
                  {selectedReply.body_text}
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 20 }}>
                <div style={{ fontSize: 12, color: 'var(--accent)', fontWeight: 600, marginBottom: 8, textTransform: 'uppercase' }}>
                  🤖 AI Suggested Action & Response
                </div>
                <div style={{ padding: 16, background: 'rgba(6, 182, 212, 0.08)', border: '1px solid rgba(6, 182, 212, 0.25)', borderRadius: 8, marginBottom: 16 }}>
                  <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--accent)', marginBottom: 4 }}>
                    Recommended Action: {selectedReply.suggested_action}
                  </div>
                  <div style={{ fontSize: 13, color: '#cbd5e1' }}>
                    {selectedReply.suggested_reply}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 12 }}>
                  <button className="btn btn-primary" onClick={() => alert('Action executed: Reply queued!')}>
                    ✓ Approve & Send AI Reply
                  </button>
                  <button className="btn btn-secondary" onClick={() => alert('Snoozed!')}>
                    🕒 Snooze Cadence
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div style={{ padding: 60, textAlign: 'center', color: 'var(--muted)' }}>
              Select an inbound prospect reply from the left panel to review AI classification and recommended response.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
