/**
 * Ghost CFO SVG logo — can be rendered at any size.
 * Usage: <GhostLogo size={32} /> or <GhostLogo size={48} showText />
 */
export default function GhostLogo({
  size = 32,
  showText = false,
  textSize = "text-lg",
}: {
  size?: number;
  showText?: boolean;
  textSize?: string;
}) {
  const id = `grad-${size}`;
  return (
    <span className="inline-flex items-center gap-2.5">
      <svg
        width={size}
        height={size}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Ghost CFO logo"
      >
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#2DD4BF" />
            <stop offset="100%" stopColor="#06B6D4" />
          </linearGradient>
        </defs>

        {/* Gradient circle background */}
        <circle cx="32" cy="32" r="30" fill={`url(#${id})`} />

        {/* Ghost body */}
        {/* Head (top arc) */}
        <ellipse cx="32" cy="24" rx="13" ry="13" fill="white" />
        {/* Body rectangle */}
        <rect x="19" y="24" width="26" height="18" fill="white" />
        {/* Scalloped bottom — 3 bumps */}
        <circle cx="23.3" cy="42" r="4.3" fill="white" />
        <circle cx="32" cy="42" r="4.3" fill="white" />
        <circle cx="40.7" cy="42" r="4.3" fill="white" />

        {/* Eyes */}
        <circle cx="27" cy="23" r="3" fill="#0D1117" />
        <circle cx="37" cy="23" r="3" fill="#0D1117" />

        {/* Subtle border */}
        <circle cx="32" cy="32" r="30" stroke="white" strokeOpacity="0.15" strokeWidth="1.5" />
      </svg>

      {showText && (
        <span className={`font-heading font-bold text-white ${textSize}`}>
          Ghost CFO
        </span>
      )}
    </span>
  );
}
