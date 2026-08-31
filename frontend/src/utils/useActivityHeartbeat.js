import { useEffect, useRef } from 'react';
import api from './api';

const HEARTBEAT_INTERVAL_MS = 20000; // keep in sync with backend HEARTBEAT_INTERVAL_SECONDS

/**
 * Pings /api/activity/heartbeat while the page is open and visible, so the backend can
 * accumulate active time spent on a task submission or exercise attempt (see
 * backend/models/activity_session.py). Fires immediately on mount, then on an interval,
 * paused via the Page Visibility API while the tab is hidden. No explicit start/stop calls
 * needed - the backend session is created on the first heartbeat and closed server-side
 * when the student actually submits.
 *
 * @param {'task'|'exercise'} activityType
 * @param {number|string} targetId - task id or exercise id
 * @param {boolean} enabled - set false to skip tracking (e.g. while still loading)
 */
export default function useActivityHeartbeat(activityType, targetId, enabled = true) {
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!enabled || !targetId) return undefined;

    const sendHeartbeat = () => {
      if (document.visibilityState !== 'visible') return;
      api.post('/activity/heartbeat', { activity_type: activityType, target_id: targetId })
        .catch(() => {
          // Non-critical: if a heartbeat is missed, the backend just under-counts active
          // time for this stretch. Don't surface an error to the student for this.
        });
    };

    sendHeartbeat();
    intervalRef.current = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL_MS);

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') sendHeartbeat();
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      clearInterval(intervalRef.current);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [activityType, targetId, enabled]);
}
