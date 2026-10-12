/** Build a query string from an object, skipping null/undefined/'' values. */
export function qs(params = {}) {
  const usp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === null || v === undefined || v === '') continue;
    usp.set(k, v);
  }
  const s = usp.toString();
  return s ? `?${s}` : '';
}
