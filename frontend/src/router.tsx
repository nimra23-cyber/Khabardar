/**
 * Application router (Task 1.7): createBrowserRouter + RouterProvider.
 *
 * Routes:
 *   /            -> Splash (entry screen). Splash stays router-agnostic: it
 *                   calls its `onDone` prop, and the SplashRoute wrapper here
 *                   performs the navigation to /dashboard (Req 3.2).
 *   layout       -> NavBar + <Outlet> wrapping the 11 app pages.
 *     /dashboard, /detector, /url, /scanner, /intelligence, /honeypot,
 *     /family, /history, /reports, /settings, /about
 *
 * Honeypot and Family are Scope B placeholders (disabled controls). The other
 * pages are honest shells that state what is not yet implemented.
 */
import { Suspense } from "react";
import {
  Navigate,
  Outlet,
  RouterProvider,
  createBrowserRouter,
  useNavigate,
} from "react-router-dom";

import { Sidebar } from "./components/Sidebar";
import About from "./pages/About";
import Dashboard from "./pages/Dashboard";
import Detector from "./pages/Detector";
import Family from "./pages/Family";
import History from "./pages/History";
import Honeypot from "./pages/Honeypot";
import Intelligence from "./pages/Intelligence";
import Reports from "./pages/Reports";
import Scanner from "./pages/Scanner";
import Settings from "./pages/Settings";
import Splash from "./pages/Splash";
import UrlAnalyzer from "./pages/UrlAnalyzer";

/** Splash wrapper: keeps Splash router-agnostic; navigates on completion. */
function SplashRoute() {
  const navigate = useNavigate();
  return <Splash onDone={() => navigate("/dashboard", { replace: true })} />;
}

/** App layout: sidebar + main content area. */
function AppLayout() {
  return (
    <div className="min-h-full bg-bg text-fg">
      <Sidebar />
      <main className="min-h-full px-4 py-6 tablet:px-6 desktop:ml-60 desktop:px-8">
        <Suspense fallback={null}>
          <Outlet />
        </Suspense>
      </main>
    </div>
  );
}

import type { RouteObject } from "react-router-dom";

/** Route table (exported so tests can build an equivalent memory router). */
export const routes: RouteObject[] = [
  { path: "/", element: <SplashRoute /> },
  {
    element: <AppLayout />,
    children: [
      { path: "/dashboard", element: <Dashboard /> },
      { path: "/detector", element: <Detector /> },
      { path: "/url", element: <UrlAnalyzer /> },
      { path: "/scanner", element: <Scanner /> },
      { path: "/intelligence", element: <Intelligence /> },
      { path: "/honeypot", element: <Honeypot /> },
      { path: "/family", element: <Family /> },
      { path: "/history", element: <History /> },
      { path: "/reports", element: <Reports /> },
      { path: "/settings", element: <Settings /> },
      { path: "/about", element: <About /> },
    ],
  },
  // Unknown paths fall back to the splash entry.
  { path: "*", element: <Navigate to="/" replace /> },
];

export const router = createBrowserRouter(routes);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
