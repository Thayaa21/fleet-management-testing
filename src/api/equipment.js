import { api } from './client';
import { qs } from './query';

// Tractors
export const listTractors = (params) => api.get(`/equipment/tractors${qs(params)}`);
export const getTractor = (id) => api.get(`/equipment/tractors/${id}`);
export const createTractor = (body) => api.post('/equipment/tractors', body);
export const updateTractor = (id, body) => api.patch(`/equipment/tractors/${id}`, body);
export const retireTractor = (id) => api.del(`/equipment/tractors/${id}`);

// Trailers
export const listTrailers = (params) => api.get(`/equipment/trailers${qs(params)}`);
export const getTrailer = (id) => api.get(`/equipment/trailers/${id}`);
export const createTrailer = (body) => api.post('/equipment/trailers', body);
export const updateTrailer = (id, body) => api.patch(`/equipment/trailers/${id}`, body);
export const retireTrailer = (id) => api.del(`/equipment/trailers/${id}`);

// Devices
export const listDevices = (params) => api.get(`/equipment/devices${qs(params)}`);
export const getDevice = (id) => api.get(`/equipment/devices/${id}`);
export const createDevice = (body) => api.post('/equipment/devices', body);
export const updateDevice = (id, body) => api.patch(`/equipment/devices/${id}`, body);
export const deactivateDevice = (id) => api.del(`/equipment/devices/${id}`);
