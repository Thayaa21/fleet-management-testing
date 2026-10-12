import { api } from './client';
import { qs } from './query';

// API clients
export const listClients = () => api.get('/integrations/clients');
export const createClient = (body) => api.post('/integrations/clients', body);

// API keys
export const listKeys = (clientId) => api.get(`/integrations/clients/${clientId}/keys`);
export const createKey = (clientId, body) => api.post(`/integrations/clients/${clientId}/keys`, body);
export const revokeKey = (keyId) => api.post(`/integrations/keys/${keyId}/revoke`, {});

// IP allowlist
export const listAllowlist = (clientId) => api.get(`/integrations/clients/${clientId}/allowlist`);
export const addAllowlist = (clientId, body) => api.post(`/integrations/clients/${clientId}/allowlist`, body);
export const deleteAllowlist = (entryId) => api.del(`/integrations/allowlist/${entryId}`);

// Webhook subscriptions
export const listSubscriptions = (clientId) => api.get(`/integrations/clients/${clientId}/subscriptions`);
export const createSubscription = (clientId, body) => api.post(`/integrations/clients/${clientId}/subscriptions`, body);

// Logs & deliveries
export const apiLogs = (params) => api.get(`/integrations/api-logs${qs(params)}`);
export const webhookDeliveries = (params) => api.get(`/integrations/webhook-deliveries${qs(params)}`);
export const resendDelivery = (id) => api.post(`/integrations/webhook-deliveries/${id}/resend`, {});
export const deliverNow = () => api.post('/integrations/webhook-deliveries/deliver-now', {});
