/** Auth API domain module. */
import { api } from './client';

export function login(email, password) {
  return api.post('/auth/login', { email, password });
}

export function me() {
  return api.get('/auth/me');
}
