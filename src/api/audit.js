import { api } from './client';
import { qs } from './query';

export const listAudit = (params) => api.get(`/audit${qs(params)}`);
