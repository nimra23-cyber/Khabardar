/**
 * useMediaScan: POST to /api/media/scan using FormData (Task 4.x).
 *
 * Uses direct fetch with FormData — NOT apiPost (which is JSON-only).
 * Never auto-opens QR URLs. Input file is preserved on server error.
 */
import { useCallback, useState } from "react";

import { API_BASE, type ApiError } from "../lib/apiClient";
import type { MediaScanResult } from "../lib/types";

interface State {
  loading: boolean;
  result: MediaScanResult | null;
  error: ApiError | null;
}

const INITIAL: State = { loading: false, result: null, error: null };

export function useMediaScan() {
  const [state, setState] = useState<State>(INITIAL);

  const scan = useCallback(async (file: File) => {
    setState({ loading: true, result: null, error: null });

    const formData = new FormData();
    formData.append("image", file);

    try {
      const resp = await fetch(`${API_BASE}/api/media/scan`, {
        method: "POST",
        body: formData,
        // Do NOT set Content-Type — browser sets it with the correct boundary.
      });

      let body: unknown;
      try {
        body = await resp.json();
      } catch {
        setState({
          loading: false,
          result: null,
          error: {
            code: "BAD_RESPONSE",
            message: "The server returned an unreadable response.",
            operation: "/api/media/scan",
          },
        });
        return { ok: false as const };
      }

      const b = body as Record<string, unknown>;

      if (b && b.ok === true) {
        setState({ loading: false, result: b.data as MediaScanResult, error: null });
        return { ok: true as const, data: b.data as MediaScanResult };
      }

      if (b && b.ok === false && b.error) {
        const err = b.error as ApiError;
        setState({ loading: false, result: null, error: err });
        return { ok: false as const, error: err };
      }

      setState({
        loading: false,
        result: null,
        error: {
          code: "UNEXPECTED",
          message: "The server returned an unexpected response.",
          operation: "/api/media/scan",
        },
      });
      return { ok: false as const };
    } catch {
      setState({
        loading: false,
        result: null,
        error: {
          code: "NETWORK_ERROR",
          message: "Could not reach the server. Check your connection and try again.",
          operation: "network",
        },
      });
      return { ok: false as const };
    }
  }, []);

  const reset = useCallback(() => setState(INITIAL), []);

  return { ...state, scan, reset };
}
