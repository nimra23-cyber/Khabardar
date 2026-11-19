/**
 * Sidebar: premium sidebar navigation (cybersecurity SaaS style).
 *
 * Preserves the NAV_ITEMS list and testid conventions from the original NavBar
 * so existing tests pass. On desktop: fixed left sidebar with brand + nav +
 * toggles. On mobile: hamburger opens a drawer.
 */
import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { LanguageToggle } from "./LanguageToggle";
import { ThemeToggle } from "./ThemeToggle";

export const NAV_ITEMS: { to: string; key: string; icon: string }[] = [
  { to: "/dashboard", key: "nav.dashboard", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" },
  { to: "/detector", key: "nav.detector", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" },
  { to: "/url", key: "nav.url", icon: "M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" },
  { to: "/scanner", key: "nav.scanner", icon: "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14M8 8h.01M21 12V5a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-5" },
  { to: "/intelligence", key: "nav.intelligence", icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" },
  { to: "/reports", key: "nav.reports", icon: "M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" },
  { to: "/history", key: "nav.history", icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" },
  { to: "/honeypot", key: "nav.honeypot", icon: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" },
  { to: "/family", key: "nav.family", icon: "M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-5.13a4 4 0 11-8 0 4 4 0 018 0z" },
  { to: "/settings", key: "nav.settings", icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" },
  { to: "/about", key: "nav.about", icon: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" },
];

export function Sidebar() {
  const { t } = useTranslation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navLinks = (
    <nav aria-label={t("nav.ariaLabel")} className="flex flex-1 flex-col gap-0.5 overflow-y-auto px-3 py-2">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          data-testid={`nav-${item.to.slice(1)}`}
          onClick={() => setMobileOpen(false)}
          className={({ isActive }) =>
            [
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-base",
              isActive
                ? "active-nav bg-accent/10 font-medium text-accent"
                : "text-fg/70 hover:bg-surface-hover hover:text-fg",
            ].join(" ")
          }
        >
          <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
          </svg>
          {t(item.key)}
        </NavLink>
      ))}
    </nav>
  );

  const brandAndToggles = (
    <div className="border-border-subtle border-b px-4 py-4">
      <bdi dir="ltr" className="text-lg font-bold tracking-tight text-fg">
        {t("app.name")}
      </bdi>
      <p className="mt-0.5 text-[10px] font-medium uppercase tracking-wider text-accent/60">
        {t("app.tagline")}
      </p>
      <div className="mt-3 flex items-center gap-2">
        <ThemeToggle />
        <LanguageToggle />
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        type="button"
        onClick={() => setMobileOpen(true)}
        className="fixed left-4 top-3 z-50 rounded-md bg-surface p-2 shadow-card desktop:hidden"
        aria-label="Open navigation"
        data-testid="sidebar-toggle"
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 desktop:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={`
          fixed left-0 top-0 z-50 h-full w-64 bg-surface shadow-elevated transition-base desktop:hidden
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
        `}
        data-testid="mobile-sidebar"
      >
        {brandAndToggles}
        {navLinks}
      </aside>

      {/* Desktop sidebar */}
      <aside
        className="fixed left-0 top-0 z-30 hidden h-full w-60 flex-col border-r border-border-subtle bg-surface desktop:flex"
        data-testid="desktop-sidebar"
      >
        {brandAndToggles}
        {navLinks}
      </aside>
    </>
  );
}
