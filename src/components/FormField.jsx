/**
 * FormField — a labeled input/select/textarea that renders an inline error.
 * `error` is a string (already resolved for this field by the form).
 */
export default function FormField({ label, error, required, children }) {
  return (
    <div className="form-field">
      {label && (
        <label className="form-label">
          {label}{required && <span style={{ color: 'var(--red)' }}> *</span>}
        </label>
      )}
      {children}
      {error && <div style={{ color: 'var(--red)', fontSize: 12, marginTop: 4 }}>{error}</div>}
    </div>
  );
}
