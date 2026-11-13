/** useIocExtract: extract IOCs from text via /api/iocs/extract (Phase 5). */
import { useCallback, useState } from "react";

import { apiPost, type ApiError } from "../lib/apiClient";
import type { IOCExtractResult } from "../lib/types";

interface State {
  loading: boolean;
  result: IOCExtractResult | null;
  error: ApiError | null;
}

const INITIAL: State = { loading: false, result: null, error: null };

export function useIocExtract() {
  const [state, setState] = useState<State>(INITIAL);

  const extract = useCallback(async (text: string) => {
    setState({ loading: true, result: null, error: null });
    const res = await apiPost<IOCExtractResult>("/api/iocs/extract", { text });
    if (res.ok) setState({ loading: false, result: res.data, error: null });
    else setState({ loading: false, result: null, error: res.error });
    return res;
  }, []);

  return { ...state, extract };
}
