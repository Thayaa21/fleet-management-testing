import logo from '../assets/qubi-logo.png';

// qubi "by qBotica" lockup; `size` is the rendered height.
export default function TpLogo({ size = 36 }) {
  return (
    <img
      src={logo}
      alt="qubi by qBotica"
      style={{ height: size, width: 'auto', display: 'block', flexShrink: 0 }}
    />
  );
}
