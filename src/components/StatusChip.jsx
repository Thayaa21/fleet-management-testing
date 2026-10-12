/** Small colored status pill. Maps common statuses to badge colors. */
const CLASS_BY_STATUS = {
  active: 'green',
  available: 'green',
  inactive: 'red',
  out_of_service: 'red',
  maintenance: 'amber',
  in_use: 'blue',
  unassigned: 'amber',
};

export default function StatusChip({ value }) {
  if (!value) return null;
  const cls = CLASS_BY_STATUS[value] || 'blue';
  const label = String(value).replace(/_/g, ' ');
  return <span className={`badge ${cls}`}>{label}</span>;
}
