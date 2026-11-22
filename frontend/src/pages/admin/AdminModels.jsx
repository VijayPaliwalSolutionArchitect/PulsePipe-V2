import React, { useState, useEffect } from 'react';
import { pulseApi } from '../../api';

export default function AdminModels() {
  const [models, setModels] = useState([]);

  useEffect(() => {
    pulseApi.getModels().then(setModels).catch(console.error);
  }, []);

  const modelData = models.length ? models : [
    { pool_id: 'ultra-fast', model_id: 'groq/llama-3.3-70b-versatile', cost_per_1k_tokens: 0.0005, monthly_cap_usd: 50.0, current_spend_usd: 0.024 },
    { pool_id: 'balanced', model_id: 'openai/gpt-4o-mini', cost_per_1k_tokens: 0.0015, monthly_cap_usd: 80.0, current_spend_usd: 0.048 },
    { pool_id: 'high-reasoning', model_id: 'anthropic/claude-3-5-sonnet-20241022', cost_per_1k_tokens: 0.015, monthly_cap_usd: 100.0, current_spend_usd: 0.010 },
    { pool_id: 'economy', model_id: 'mistral/mistral-small-latest', cost_per_1k_tokens: 0.0002, monthly_cap_usd: 30.0, current_spend_usd: 0.000 },
    { pool_id: 'offline/local', model_id: 'ollama/qwen2.5:latest', cost_per_1k_tokens: 0.0, monthly_cap_usd: 0.0, current_spend_usd: 0.000 }
  ];

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 6px 0' }}>5-Pool AI Model Router & Spend Ledger</h2>
        <p style={{ color: 'var(--muted)', fontSize: 13, margin: 0 }}>
          Dedicated LLM routing: Ultra-fast models for reply triage classification, balanced models for personalized SDR email copy.
        </p>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--muted)' }}>
              <th style={{ padding: '12px 20px' }}>Pool ID</th>
              <th style={{ padding: '12px 20px' }}>Active Model</th>
              <th style={{ padding: '12px 20px' }}>Cost / 1K Tokens</th>
              <th style={{ padding: '12px 20px' }}>Monthly Spend Cap</th>
              <th style={{ padding: '12px 20px' }}>Current Spend</th>
              <th style={{ padding: '12px 20px', textAlign: 'right' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {modelData.map(m => (
              <tr key={m.pool_id} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: '12px 20px', fontWeight: 600, color: 'var(--accent)' }}>{m.pool_id}</td>
                <td style={{ padding: '12px 20px', fontFamily: 'monospace' }}>{m.model_id}</td>
                <td style={{ padding: '12px 20px' }}>${m.cost_per_1k_tokens}</td>
                <td style={{ padding: '12px 20px' }}>${m.monthly_cap_usd}</td>
                <td style={{ padding: '12px 20px', color: 'var(--success)' }}>${m.current_spend_usd}</td>
                <td style={{ padding: '12px 20px', textAlign: 'right' }}>
                  <span className="badge badge-interested">ONLINE</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
