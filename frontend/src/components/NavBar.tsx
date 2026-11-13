/**
 * NavBar: responsive top navigation for the app shell (Req 3).
 *
 * - Uses react-router NavLink so the active destination is visually distinct
 *   (Req 3.5) via the `active-nav` class.
 * - Brand name is a fixed token (never translated), wrapped in <bdi dir="ltr">
 *   so it renders correctly inside an RTL document.
 * - Theme + language toggles live here (preserved Task 1.4/1.5 behavior).
 * - Layout uses symmetric/logical utilities and wraps so there is no horizontal
 *   overflow at mobile/tablet/desktop widths.
 */
import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { LanguageToggle } from "./LanguageToggle";
import { ThemeToggle } from "./ThemeToggle";

/** Navigable destinations (excludes Splash `/`, which is the entry screen). */
export const NAV_ITEMS: { to: string; key: string }[] = [
  { to: "/dashboard", key: "nav.dashboard" },
  { to: "/detector", key: "nav.detector" },
  { to: "/url", key: "nav.url" },
  { to: "/scanner", key: "nav.scanner" },
  { to: "/intelligence", key: "nav.intelligence" },
  { to: "/honeypot", key: "nav.honeypot" },
  { to: "/family", key: "nav.family" },
  { to: "/history", key: "nav.history" },
  { to: "/reports", key: "nav.reports" },
  { to: "/settings", key: "nav.settings" },
  { to: "/about", key: "nav.about" },
];

export function NavBar() {
  const { t } = useTranslation();

  return (
    <header className="border-b border-metallic-silver/20 bg-surface">
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 tablet:px-6 desktop:px-8">
        <bdi dir="ltr" className="text-lg font-semibold">
          {t("app.name")}
        </bdi>
        <div className="flex items-center gap-3">
          <LanguageToggle />
          <ThemeToggle />
        </div>
      </div>

      <nav
        aria-label={t("nav.ariaLabel")}
        className="flex flex-wrap gap-1 px-2 pb-2 tablet:px-4 desktop:px-6"
      >
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            data-testid={`nav-${item.to.slice(1)}`}
            className={({ isActive }) =>
              [
                "rounded px-3 py-1.5 text-sm",
                isActive
                  ? "active-nav bg-accent/15 font-semibold text-fg"
                  : "text-fg/80 hover:bg-bg",
              ].join(" ")
            }
          >
            {t(item.key)}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
