/** useHistory: fetch the local user's scan history (Task 6.7). */
import { useCallback, useEffect, useState } from "react";

import { apiGet, type ApiError } from "../lib/apiClient";
import type { HistoryResponse } from "../lib/types";

export function useHistory() {
  const [data, setData] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const res = await apiGet<HistoryResponse>("/api/history");
    if (res.ok) {
      setData(res.data);
    } else {
      setError(res.error);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, reload: load };
}
