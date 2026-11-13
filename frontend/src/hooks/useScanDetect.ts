/** useScanDetect: submit text to /api/scam/detect (Task 2.14). */
import { useCallback, useState } from "react";

import { apiPost, type ApiError } from "../lib/apiClient";
import type { DetectResult } from "../lib/types";

interface State {
  loading: boolean;
  result: DetectResult | null;
  error: ApiError | null;
}

const INITIAL: State = { loading: false, result: null, error: null };

export function useScanDetect() {
  const [state, setState] = useState<State>(INITIAL);

  const detect = useCallback(async (text: string) => {
    setState({ loading: true, result: null, error: null });
    const res = await apiPost<DetectResult>("/api/scam/detect", { text });
    if (res.ok) {
      setState({ loading: false, result: res.data, error: null });
    } else {
      // Keep previous input in the component; just surface the error.
      setState({ loading: false, result: null, error: res.error });
    }
    return res;
  }, []);

  const reset = useCallback(() => setState(INITIAL), []);

  return { ...state, detect, reset };
}
