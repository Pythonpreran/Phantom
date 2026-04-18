/**
 * PHANTOM — WebSocket Hook
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { getWsUrl } from '../utils/api';

export function useWebSocket() {
  const [events, setEvents] = useState([]);
  const [stats, setStats] = useState({
    total_requests: 0,
    total_attacks: 0,
    total_blocked: 0,
    active_users: 0,
    rpm: 0,
  });
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(getWsUrl());

      ws.onopen = () => {
        setConnected(true);
        if (reconnectTimer.current) {
          clearTimeout(reconnectTimer.current);
          reconnectTimer.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'event') {
            setEvents((prev) => {
              const next = [msg.data, ...prev];
              return next.slice(0, 100);
            });
            if (msg.stats) {
              setStats(msg.stats);
            }
          }
        } catch (e) {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        setConnected(false);
        reconnectTimer.current = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch (e) {
      reconnectTimer.current = setTimeout(connect, 3000);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    };
  }, [connect]);

  return { events, stats, connected };
}
