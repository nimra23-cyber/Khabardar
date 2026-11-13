/**
 * Canonical palette values (single source of truth for TS/tests).
 *
 * These MUST match the fixed brand values in `tokens.css`. Tests assert both
 * (a) that this object holds the exact approved values and (b) that the CSS
 * tokens resolve to them, guarding against drift between TS and CSS.
 */
export const PALETTE = {
  deepNavy: "#101D31",
  midnightBlue: "#172A45",
  metallicSilver: "#C5D0DC",
  electricBlue: "#3987FF",
  surfaceLight: "#F4F7FB",
  surfaceDark: "#0B1423",
  danger: "#E5484D",
  warning: "#E5A323",
  safe: "#1C9B70",
} as const;

/** Map of CSS custom-property name -> expected hex (brand/palette tokens). */
export const CSS_TOKEN_EXPECTED: Record<string, string> = {
  "--color-deep-navy": PALETTE.deepNavy,
  "--color-midnight-blue": PALETTE.midnightBlue,
  "--color-metallic-silver": PALETTE.metallicSilver,
  "--color-electric-blue": PALETTE.electricBlue,
  "--color-surface-light": PALETTE.surfaceLight,
  "--color-surface-dark": PALETTE.surfaceDark,
  "--color-danger": PALETTE.danger,
  "--color-warning": PALETTE.warning,
  "--color-safe": PALETTE.safe,
};

export type ThemeName = "dark" | "light";
