/** useDashboardStats: fetch real SOC dashboard metrics (Phase 6). */
import { useEffect, useState } from "react";

import { apiGet, type ApiError } from "../lib/apiClient";
import type { DashboardStats } from "../lib/types";

export function useDashboardStats() {
  const [data, setData] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      const res = await apiGet<DashboardStats>("/api/dashboard/stats");
      if (!active) return;
      if (res.ok) setData(res.data);
      else setError(res.error);
      setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, []);

  return { data, loading, error };
}
