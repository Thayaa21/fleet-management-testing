import { api } from './client';
import { qs } from './query';

export const listCustomers = (params) => api.get(`/customers${qs(params)}`);
export const getCustomer = (id) => api.get(`/customers/${id}`);
export const createCustomer = (body) => api.post('/customers', body);
export const updateCustomer = (id, body) => api.patch(`/customers/${id}`, body);
export const deactivateCustomer = (id) => api.del(`/customers/${id}`);
