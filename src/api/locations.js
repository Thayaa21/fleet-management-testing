import { api } from './client';
import { qs } from './query';

export const listLocations = (params) => api.get(`/locations${qs(params)}`);
export const getLocation = (id) => api.get(`/locations/${id}`);
export const createLocation = (body) => api.post('/locations', body);
export const updateLocation = (id, body) => api.patch(`/locations/${id}`, body);
export const deactivateLocation = (id) => api.del(`/locations/${id}`);
