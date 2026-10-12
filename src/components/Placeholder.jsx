/**
 * Placeholder — shown for sections whose real implementation lands in a later
 * batch of the build plan. Keeps the app shell navigable without faking data.
 */
export default function Placeholder({ title, note }) {
  return (
    <div className="placeholder">
      <span className="badge amber">Coming in a later batch</span>
      <h2>{title}</h2>
      <p style={{ maxWidth: 440 }}>
        {note || 'This section is part of the app shell for now. Its real functionality is built in a later batch of the build plan.'}
      </p>
    </div>
  );
}
