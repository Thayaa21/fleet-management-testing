import { useState } from 'react';
import FormField from './FormField';
import { toFormErrors } from '../api/formErrors';

/**
 * Generic create/edit drawer driven by a field schema.
 *
 * Props:
 * - open, mode ('create' | 'edit'), title
 * - fields: [{ name, label, type ('text'|'number'|'date'|'checkbox'|'select'|'textarea'),
 *             options?: [{value,label}], required?, editableOnCreateOnly? }]
 * - initial: initial values object (for edit)
 * - onSubmit(values) -> Promise (throws ApiError on failure)
 * - onClose()
 */
function DrawerForm({ mode, title, fields, initial, onSubmit, onClose }) {
  // Initialized once per mount; the parent gives a fresh `key` each time it
  // opens, so state resets naturally without a sync effect.
  const [values, setValues] = useState(() => ({ ...initial }));
  const [fieldErrors, setFieldErrors] = useState({});
  const [message, setMessage] = useState('');
  const [saving, setSaving] = useState(false);

  const set = (name, value) => setValues(v => ({ ...v, [name]: value }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setFieldErrors({});
    setMessage('');
    try {
      // Drop empty strings so optional fields stay unset.
      const payload = {};
      for (const [k, v] of Object.entries(values)) {
        if (v === '' || v === undefined) continue;
        payload[k] = v;
      }
      await onSubmit(payload);
      onClose();
    } catch (err) {
      const { fieldErrors: fe, message: msg } = toFormErrors(err);
      setFieldErrors(fe);
      setMessage(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer" onClick={e => e.stopPropagation()}>
        <div className="drawer-header">
          <h3>{title}</h3>
          <button className="btn secondary" onClick={onClose} style={{ padding: '6px 12px' }}>✕</button>
        </div>
        <form onSubmit={submit} style={{ display: 'contents' }}>
          <div className="drawer-body">
            {message && <div className="auth-error" style={{ marginBottom: 14 }}>{message}</div>}
            {fields.map(f => {
              if (f.editableOnCreateOnly && mode === 'edit') return null;
              const err = fieldErrors[f.name];
              const val = values[f.name] ?? (f.type === 'checkbox' ? false : '');
              return (
                <FormField key={f.name} label={f.label} error={err} required={f.required}>
                  {f.type === 'select' ? (
                    <select className="form-select" value={val} onChange={e => set(f.name, e.target.value)}>
                      <option value="">Select…</option>
                      {f.options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                  ) : f.type === 'textarea' ? (
                    <textarea className="form-input" rows={3} value={val} onChange={e => set(f.name, e.target.value)} />
                  ) : f.type === 'checkbox' ? (
                    <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                      <input type="checkbox" checked={!!val} onChange={e => set(f.name, e.target.checked)} />
                      {f.checkboxLabel || 'Yes'}
                    </label>
                  ) : (
                    <input
                      className="form-input"
                      type={f.type || 'text'}
                      value={val}
                      onChange={e => set(f.name, f.type === 'number' ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value)}
                    />
                  )}
                </FormField>
              );
            })}
          </div>
          <div className="drawer-footer">
            <button type="button" className="btn secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn" disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function EntityDrawer({ open, mode, title, fields, initial = {}, onSubmit, onClose }) {
  if (!open) return null;
  // Remount per open (and per entity) so form state initializes fresh from `initial`.
  const formKey = `${mode}:${initial?.id ?? 'new'}`;
  return (
    <DrawerForm
      key={formKey}
      mode={mode}
      title={title}
      fields={fields}
      initial={initial}
      onSubmit={onSubmit}
      onClose={onClose}
    />
  );
}
