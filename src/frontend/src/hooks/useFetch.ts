import { useCallback, useEffect, useState } from 'react';

type UseFetchResult<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
};

/**
 * Generic data-fetching hook.
 *
 * - Pass a stable `fetcher` function (wrap in `useCallback` if defined inline).
 *   The effect re-runs whenever the fetcher reference changes, so wrapping in
 *   useCallback with the correct deps is the standard way to trigger a refetch.
 * - Call the returned `refresh()` to manually re-trigger without changing deps.
 */
export function useFetch<T>(fetcher: () => Promise<T>): UseFetchResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetcher()
      .then(result => {
        if (!cancelled) {
          setData(result);
          setLoading(false);
        }
      })
      .catch(err => {
        if (!cancelled) {
          setError((err as Error).message || 'Error loading data');
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
    // Re-run when the fetcher itself changes (i.e. activeQuery changed and
    // the caller's useCallback produced a new reference) OR when refresh() is
    // called (tick bump).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetcher, tick]);

  const refresh = useCallback(() => setTick(t => t + 1), []);

  return { data, loading, error, refresh };
}
