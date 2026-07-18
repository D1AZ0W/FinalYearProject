import { useEffect } from 'react';
import { toast } from 'react-toastify';
import { getNotificationStream } from '../lib/api';

/**
 * Connects to the SSE notification stream and shows a toast for every
 * new fine case detected. Cleans up the EventSource on unmount.
 */
export function useNotifications(): void {
  useEffect(() => {
    const evtSource = new EventSource(getNotificationStream());

    evtSource.onmessage = event => {
      try {
        const data = JSON.parse(event.data as string) as { case_id: number };
        toast.success(`Case #${data.case_id} added to the fine list.`);
      } catch {
        // Ignore malformed SSE payloads
      }
    };

    evtSource.onerror = () => {
      evtSource.close();
    };

    return () => {
      evtSource.close();
    };
  }, []);
}
