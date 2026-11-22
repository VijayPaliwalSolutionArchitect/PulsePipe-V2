import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

export const pulseApi = {
  // Campaigns
  async listCampaigns(tenantId = 'acme-sales') {
    const { data } = await api.get(`/v1/campaigns/?tenant_id=${tenantId}`);
    return data;
  },
  async createCampaign(payload) {
    const { data } = await api.post('/v1/campaigns/', payload);
    return data;
  },

  // Prospects
  async listProspects(campaignId = 'camp-01') {
    const { data } = await api.get(`/v1/prospects/?campaign_id=${campaignId}`);
    return data;
  },
  async createProspect(payload) {
    const { data } = await api.post('/v1/prospects/', payload);
    return data;
  },

  // Sequences
  async listSequences(campaignId = 'camp-01') {
    const { data } = await api.get(`/v1/sequences/?campaign_id=${campaignId}`);
    return data;
  },
  async generatePersonalizedCopy(payload) {
    const { data } = await api.post('/v1/sequences/generate-copy', payload);
    return data;
  },
  async dispatchStep(payload) {
    const { data } = await api.post('/v1/sequences/dispatch', payload);
    return data;
  },

  // Reply Triage Inbox
  async listReplies(campaignId = 'camp-01') {
    const { data } = await api.get(`/v1/inbox/?campaign_id=${campaignId}`);
    return data;
  },
  async classifyReply(payload) {
    const { data } = await api.post('/v1/inbox/classify', payload);
    return data;
  },

  // Deliverability Health
  async getDeliverabilityHealth(tenantId = 'acme-sales') {
    const { data } = await api.get(`/v1/deliverability/health?tenant_id=${tenantId}`);
    return data;
  },

  // Admin Console
  async getAdminStats() {
    const { data } = await api.get('/v1/admin/stats');
    return data;
  },
  async getAdminSettings() {
    const { data } = await api.get('/v1/admin/settings');
    return data;
  },
  async listPersonas(tenantId = 'acme-sales') {
    const { data } = await api.get(`/v1/admin/personas?tenant_id=${tenantId}`);
    return data;
  },
  async listSuppressions(tenantId = 'acme-sales') {
    const { data } = await api.get(`/v1/admin/suppressions?tenant_id=${tenantId}`);
    return data;
  },
  async addSuppression(payload) {
    const { data } = await api.post('/v1/admin/suppressions', payload);
    return data;
  },
  async getModels() {
    const { data } = await api.get('/v1/admin/models');
    return data;
  }
};

export default api;
