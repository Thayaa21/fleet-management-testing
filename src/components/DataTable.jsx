import { useEffect, useMemo, useState } from 'react';

/**
 * DataTable — searchable, sortable, paginated table backed by a list API.
 *
 * Props:
 * - columns: [{ key, label, sortable?, render?(row) }]
 * - fetchPage(params) -> Promise<{items,total,page,page_size}>
 *   params = { page, page_size, q, sort, ...filters }
 * - filters: extra query params object (re-fetches when it changes)
 * - onRowClick(row)
 * - actions: node rendered in the toolbar (e.g. a "New" button)
 * - refreshKey: change to force a reload
 * - searchPlaceholder
 */
export default function DataTable({
  columns,
  fetchPage,
  filters = {},
  onRowClick,
  actions,
  refreshKey = 0,
  searchPlaceholder = 'Search…',
}) {
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [sort, setSort] = useState(null); // { key, dir }
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: 20 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const filtersKey = JSON.stringify(filters);

  // Reset to page 1 when the query or filters change — done during render
  // (React's "adjust state while rendering" pattern) rather than in an effect.
  const [prevKey, setPrevKey] = useState(`${q}|${filtersKey}`);
  const currentKey = `${q}|${filtersKey}`;
  if (currentKey !== prevKey) {
    setPrevKey(currentKey);
    if (page !== 1) setPage(1);
  }

  useEffect(() => {
    let cancelled = false;

    async function run() {
      // `await null` first so state updates happen in an async continuation
      // rather than synchronously in the effect body.
      await null;
      if (cancelled) return;
      setLoading(true);
      setError(null);
      try {
        const params = { page, page_size: pageSize, q: q || undefined, ...filters };
        if (sort) params.sort = `${sort.dir === 'desc' ? '-' : ''}${sort.key}`;
        const res = await fetchPage(params);
        if (!cancelled) setData(res);
      } catch (err) {
        if (!cancelled) setError(err.message || 'Failed to load.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    run();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize, q, sort, filtersKey, refreshKey]);

  const totalPages = Math.max(1, Math.ceil(data.total / pageSize));

  const toggleSort = (col) => {
    if (!col.sortable) return;
    setSort(prev => {
      if (!prev || prev.key !== col.key) return { key: col.key, dir: 'asc' };
      if (prev.dir === 'asc') return { key: col.key, dir: 'desc' };
      return null;
    });
  };

  // Client-side sort when a sortable column is active (backend sort is optional).
  const rows = useMemo(() => {
    if (!sort) return data.items;
    const sorted = [...data.items].sort((a, b) => {
      const av = a[sort.key];
      const bv = b[sort.key];
      if (av == null) return 1;
      if (bv == null) return -1;
      if (av < bv) return sort.dir === 'asc' ? -1 : 1;
      if (av > bv) return sort.dir === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [data.items, sort]);

  return (
    <div>
      <div style={{ display: 'flex', gap: 10, marginBottom: 14, alignItems: 'center', flexWrap: 'wrap' }}>
        <div className="db-search" style={{ width: 260 }}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
          <input value={q} onChange={e => setQ(e.target.value)} placeholder={searchPlaceholder} />
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 10, alignItems: 'center' }}>{actions}</div>
      </div>

      {error && <div className="auth-error" style={{ marginBottom: 12 }}>{error}</div>}

      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="lb-table">
          <thead>
            <tr>
              {columns.map(col => (
                <th
                  key={col.key}
                  onClick={() => toggleSort(col)}
                  style={{ cursor: col.sortable ? 'pointer' : 'default', userSelect: 'none' }}
                >
                  {col.label}
                  {sort?.key === col.key && (sort.dir === 'asc' ? ' ▲' : ' ▼')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={columns.length} style={{ textAlign: 'center', padding: 32, color: 'var(--muted)' }}>Loading…</td></tr>
            ) : rows.length === 0 ? (
              <tr><td colSpan={columns.length} style={{ textAlign: 'center', padding: 32, color: 'var(--muted)' }}>No records found.</td></tr>
            ) : (
              rows.map(row => (
                <tr
                  key={row.id}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  style={{ cursor: onRowClick ? 'pointer' : 'default' }}
                >
                  {columns.map(col => (
                    <td key={col.key}>{col.render ? col.render(row) : row[col.key]}</td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12 }}>
        <span className="small">{data.total} record(s)</span>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className="btn secondary" disabled={page <= 1} onClick={() => setPage(p => Math.max(1, p - 1))}>Prev</button>
          <span className="small">Page {data.page} of {totalPages}</span>
          <button className="btn secondary" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next</button>
        </div>
      </div>
    </div>
  );
}
