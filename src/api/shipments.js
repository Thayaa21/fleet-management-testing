import { api } from './client';
import { qs } from './query';

export const listShipments = (params) => api.get(`/shipments${qs(params)}`);
export const getShipment = (id) => api.get(`/shipments/${id}`);
export const createShipment = (body) => api.post('/shipments', body);
export const updateShipment = (id, body) => api.patch(`/shipments/${id}`, body);
export const cancelShipment = (id, reason) => api.post(`/shipments/${id}/cancel`, { reason });

export const listHandlingUnits = (id) => api.get(`/shipments/${id}/handling-units`);
export const addHandlingUnit = (id, body) => api.post(`/shipments/${id}/handling-units`, body);

export const listMilestones = (id, includeVoided) =>
  api.get(`/shipments/${id}/milestones${qs({ include_voided: includeVoided || undefined })}`);
export const addMilestone = (id, body) => api.post(`/shipments/${id}/milestones`, body);
export const voidMilestone = (milestoneId, reason) => api.post(`/milestones/${milestoneId}/void`, { reason });

export const getTimeline = (id) => api.get(`/shipments/${id}/timeline`);
