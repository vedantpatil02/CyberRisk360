import { useQuery } from '@tanstack/react-query';
import { listNotifications } from '../api/endpoints/notifications';

export function useNotifications() {
  return useQuery({
    queryKey: ['notifications'],
    queryFn: listNotifications,
    // Light poll - no WebSocket/push infra exists in this codebase, and
    // notifications are computed live server-side anyway (see
    // analytics/notifications.py), so a periodic refetch is enough to
    // keep the bell reasonably current without new infrastructure.
    refetchInterval: 60_000,
  });
}
