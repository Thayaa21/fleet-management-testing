import { api } from './client';
import { qs } from './query';

export const ingestLogs = (params) => api.get(`/integrations/telematics/logs${qs(params)}`);
export const telematicsHealth = (params) => api.get(`/telematics/health${qs(params)}`);

export const tractorPositions = (id, params) => api.get(`/equipment/tractors/${id}/positions${qs(params)}`);
export const trailerPositions = (id, params) => api.get(`/equipment/trailers/${id}/positions${qs(params)}`);
export const shipmentPositions = (id) => api.get(`/shipments/${id}/positions`);
