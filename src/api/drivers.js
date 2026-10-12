import { api } from './client';
import { qs } from './query';

export const listDrivers = (params) => api.get(`/drivers${qs(params)}`);
export const getDriver = (id) => api.get(`/drivers/${id}`);
export const createDriver = (body) => api.post('/drivers', body);
export const updateDriver = (id, body) => api.patch(`/drivers/${id}`, body);
export const deactivateDriver = (id) => api.del(`/drivers/${id}`);
