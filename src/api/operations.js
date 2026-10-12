import { api } from './client';
import { qs } from './query';

// Pickups
export const listPickups = (params) => api.get(`/pickups${qs(params)}`);
export const createPickup = (body) => api.post('/pickups', body);
export const updatePickup = (id, body) => api.patch(`/pickups/${id}`, body);
export const cancelPickup = (id) => api.post(`/pickups/${id}/cancel`, {});

// Trips
export const listTrips = (params) => api.get(`/trips${qs(params)}`);
export const getTrip = (id) => api.get(`/trips/${id}`);
export const createTrip = (body) => api.post('/trips', body);
export const hookTrailer = (id, body) => api.post(`/trips/${id}/trailers`, body);
export const dispatchTrip = (id) => api.post(`/trips/${id}/dispatch`, {});
export const arriveTrip = (id) => api.post(`/trips/${id}/arrive`, {});

// Manifests
export const listManifests = (params) => api.get(`/manifests${qs(params)}`);
export const getManifest = (id) => api.get(`/manifests/${id}`);
export const createManifest = (body) => api.post('/manifests', body);
export const manifestItems = (id) => api.get(`/manifests/${id}/items`);
export const loadShipment = (id, body) => api.post(`/manifests/${id}/load`, body);
export const unloadShipment = (id, body) => api.post(`/manifests/${id}/unload`, body);
export const closeManifest = (id) => api.post(`/manifests/${id}/close`, {});

// Equipment cross-views
export const trailerContents = (id) => api.get(`/equipment/trailers/${id}/contents`);
export const tractorCurrentTrip = (id) => api.get(`/equipment/tractors/${id}/current-trip`);
