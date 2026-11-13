/** useUrlAnalyze: submit a URL to /api/url/analyze (Phase 3). */
import { useCallback, useState } from "react";

import { apiPost, type ApiError } from "../lib/apiClient";
import type { URLAnalysisResult } from "../lib/types";

interface State {
  loading: boolean;
  result: URLAnalysisResult | null;
  error: ApiError | null;
}

const INITIAL: State = { loading: false, result: null, error: null };

export function useUrlAnalyze() {
  const [state, setState] = useState<State>(INITIAL);

  const analyze = useCallback(async (url: string) => {
    setState({ loading: true, result: null, error: null });
    const res = await apiPost<URLAnalysisResult>("/api/url/analyze", { url });
    if (res.ok) {
      setState({ loading: false, result: res.data, error: null });
    } else {
      setState({ loading: false, result: null, error: res.error });
    }
    return res;
  }, []);

  return { ...state, analyze };
}
