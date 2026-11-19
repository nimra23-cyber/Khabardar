/**
 * Tailwind configuration for KHABARDAR — premium cybersecurity SaaS aesthetic.
 *
 * Colors reference CSS variables from tokens.css (single source of truth).
 * Breakpoints: mobile <=767px (base), tablet 768-1023px, desktop >=1024px.
 */
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    screens: {
      tablet: "768px",
      desktop: "1024px",
    },
    extend: {
      colors: {
        // Brand / surface palette -> CSS variables.
        "deep-navy": "var(--color-deep-navy)",
        "midnight-blue": "var(--color-midnight-blue)",
        "metallic-silver": "var(--color-metallic-silver)",
        "electric-blue": "var(--color-electric-blue)",
        "surface-light": "var(--color-surface-light)",
        "surface-dark": "var(--color-surface-dark)",
        // Risk severity colors.
        danger: "var(--color-danger)",
        warning: "var(--color-warning)",
        safe: "var(--color-safe)",
        // Semantic, theme-aware tokens.
        bg: "var(--color-bg)",
        surface: "var(--color-surface)",
        "surface-elevated": "var(--color-surface-elevated)",
        "surface-hover": "var(--color-surface-hover)",
        fg: "var(--color-fg)",
        accent: "var(--color-accent)",
        // Border tokens.
        "border-subtle": "var(--color-border-subtle)",
        "border-default": "var(--color-border-default)",
        "border-accent": "var(--color-border-accent)",
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
      },
      boxShadow: {
        card: "var(--shadow-card)",
        elevated: "var(--shadow-elevated)",
        glow: "var(--glow-accent)",
      },
      transitionDuration: {
        fast: "150ms",
        base: "200ms",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [],
};
