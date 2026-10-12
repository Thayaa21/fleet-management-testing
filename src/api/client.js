/**
 * Shared fetch wrapper for the TMS API.
 *
 * - Prefixes requests with the API base URL (VITE_API_BASE_URL, default '/api'
 *   which the Vite dev server proxies to the backend).
 * - Attaches the bearer token when one is set.
 * - Parses the standard error envelope {"error": {code, message, details}} and
 *   throws an ApiError that carries code, status, details and the request id.
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api';

let authToken = null;

export function setAuthToken(token) {
  authToken = token;
}

export function getAuthToken() {
  return authToken;
}

export class ApiError extends Error {
  constructor({ code, message, details, status, requestId }) {
    super(message || code || 'Request failed');
    this.name = 'ApiError';
    this.code = code || 'UNKNOWN';
    this.details = details ?? null;
    this.status = status ?? 0;
    this.requestId = requestId ?? null;
  }
}

async function request(method, path, { body, headers } = {}) {
  const opts = { method, headers: { ...(headers || {}) } };
  if (authToken) opts.headers.Authorization = `Bearer ${authToken}`;
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }

  let resp;
  try {
    resp = await fetch(`${BASE_URL}${path}`, opts);
  } catch {
    throw new ApiError({ code: 'NETWORK_ERROR', message: 'Could not reach the server.', status: 0 });
  }

  const requestId = resp.headers.get('X-Request-ID');

  // 204 / empty body
  if (resp.status === 204) return null;

  let data = null;
  const text = await resp.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!resp.ok) {
    const err = data?.error ?? {};
    throw new ApiError({
      code: err.code,
      message: err.message || `Request failed (${resp.status})`,
      details: err.details,
      status: resp.status,
      requestId,
    });
  }

  return data;
}

/** Upload multipart/form-data (e.g. a file). `form` is a FormData instance. */
async function upload(path, form) {
  const headers = {};
  if (authToken) headers.Authorization = `Bearer ${authToken}`;
  let resp;
  try {
    resp = await fetch(`${BASE_URL}${path}`, { method: 'POST', headers, body: form });
  } catch {
    throw new ApiError({ code: 'NETWORK_ERROR', message: 'Could not reach the server.', status: 0 });
  }
  const requestId = resp.headers.get('X-Request-ID');
  const text = await resp.text();
  const data = text ? JSON.parse(text) : null;
  if (!resp.ok) {
    const err = data?.error ?? {};
    throw new ApiError({ code: err.code, message: err.message || `Upload failed (${resp.status})`, details: err.details, status: resp.status, requestId });
  }
  return data;
}

export const api = {
  get: (path, opts) => request('GET', path, opts),
  post: (path, body, opts) => request('POST', path, { ...opts, body }),
  put: (path, body, opts) => request('PUT', path, { ...opts, body }),
  patch: (path, body, opts) => request('PATCH', path, { ...opts, body }),
  del: (path, opts) => request('DELETE', path, opts),
  upload,
};
