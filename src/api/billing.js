import { api } from './client';
import { qs } from './query';

// Exceptions
export const listExceptions = (params) => api.get(`/exceptions${qs(params)}`);
export const createException = (body) => api.post('/exceptions', body);
export const updateException = (id, body) => api.patch(`/exceptions/${id}`, body);

// Quotes
export const quote = (body) => api.post('/quotes', body);

// Documents
export const listDocuments = (shipmentId) => api.get(`/shipments/${shipmentId}/documents`);
export const uploadDocument = (shipmentId, type, file) => {
  const form = new FormData();
  form.append('type', type);
  form.append('file', file);
  return api.upload(`/shipments/${shipmentId}/documents`, form);
};

// Freight bills
export const listFreightBills = (params) => api.get(`/freight-bills${qs(params)}`);
export const getFreightBill = (id) => api.get(`/freight-bills/${id}`);
export const issueFreightBill = (id) => api.post(`/freight-bills/${id}/issue`, {});
