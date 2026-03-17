import { useState, useEffect, useRef, useCallback } from 'react';
import { BACKEND_URL } from '@/services/api';

interface DashboardEvent {
  type: string;
  session_id?: string;
  business_id?: number;
  timestamp?: string;
  [key: string]: any;
}

interface ActiveSession {
  session_id: string;
  business_id: number;
  customer_phone?: string;
  customer_name?: string;
  started_at?: string;
  transcript?: string[];
  status?: string;
}

interface UseDashboardWebSocketReturn {
  isConnected: boolean;
  activeSessions: Record<string, ActiveSession>;
  events: DashboardEvent[];
  sendCommand: (command: string, sessionId: string, data?: Record<string, any>) => void;
  liveTranscripts: Record<string, string[]>;
}

export function useDashboardWebSocket(businessId: number | null): UseDashboardWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [activeSessions, setActiveSessions] = useState<Record<string, ActiveSession>>({});
  const [events, setEvents] = useState<DashboardEvent[]>([]);
  const [liveTranscripts, setLiveTranscripts] = useState<Record<string, string[]>>({});
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const unmountedRef = useRef(false);

  const connect = useCallback(() => {
    // Guard: don't connect if component is unmounted
    if (!businessId || unmountedRef.current) return;

    const wsProtocol = BACKEND_URL.startsWith('https') ? 'wss' : 'ws';
    const wsHost = BACKEND_URL.replace(/^https?:\/\//, '');
    const wsUrl = `${wsProtocol}://${wsHost}/api/ws/dashboard?business_id=${businessId}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      // Guard: don't proceed if unmounted
      if (unmountedRef.current) {
        ws.close();
        return;
      }
      setIsConnected(true);
      console.log('[Dashboard WS] Connected');
    };

    ws.onmessage = (event) => {
      // Guard: don't process messages if component is unmounted
      if (unmountedRef.current) return;

      try {
        const data: DashboardEvent = JSON.parse(event.data);

        switch (data.type) {
          case 'initial_state':
            setActiveSessions(data.active_sessions || {});
            break;

          case 'call_start':
            setActiveSessions(prev => ({
              ...prev,
              [data.session_id!]: {
                session_id: data.session_id!,
                business_id: data.business_id!,
                customer_phone: data.customer_phone,
                customer_name: data.customer_name,
                started_at: data.timestamp,
                transcript: [],
                status: 'active',
              },
            }));
            break;

          case 'call_end':
            setActiveSessions(prev => {
              const updated = { ...prev };
              if (updated[data.session_id!]) {
                updated[data.session_id!] = { ...updated[data.session_id!], status: 'ended' };
              }
              return updated;
            });
            // Clean up after 5 seconds
            setTimeout(() => {
              // Guard: don't update state if unmounted
              if (unmountedRef.current) return;

              setActiveSessions(prev => {
                const updated = { ...prev };
                delete updated[data.session_id!];
                return updated;
              });
              setLiveTranscripts(prev => {
                const updated = { ...prev };
                delete updated[data.session_id!];
                return updated;
              });
            }, 5000);
            break;

          case 'transcript':
            setLiveTranscripts(prev => ({
              ...prev,
              [data.session_id!]: [
                ...(prev[data.session_id!] || []),
                `Customer: ${data.text}`,
              ],
            }));
            break;

          case 'ai_response':
            setLiveTranscripts(prev => ({
              ...prev,
              [data.session_id!]: [
                ...(prev[data.session_id!] || []),
                `AI: ${data.text}`,
              ],
            }));
            break;

          case 'tool_execution':
            setLiveTranscripts(prev => ({
              ...prev,
              [data.session_id!]: [
                ...(prev[data.session_id!] || []),
                `[Tool: ${data.tool_name}]`,
              ],
            }));
            break;
        }

        setEvents(prev => [data, ...prev].slice(0, 100));
      } catch (e) {
        console.error('[Dashboard WS] Parse error:', e);
      }
    };

    ws.onclose = () => {
      // Guard: don't update state or reconnect if unmounted
      if (unmountedRef.current) return;

      setIsConnected(false);
      console.log('[Dashboard WS] Disconnected, reconnecting in 3s...');
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };

    ws.onerror = (error) => {
      console.error('[Dashboard WS] Error:', error);
    };
  }, [businessId]);

  useEffect(() => {
    unmountedRef.current = false;
    connect();
    return () => {
      unmountedRef.current = true;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        // Clear handlers before closing to prevent reconnection attempts
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.onmessage = null;
        wsRef.current.onopen = null;
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendCommand = useCallback(
    (command: string, sessionId: string, data?: Record<string, any>) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ command, session_id: sessionId, ...data }));
      }
    },
    []
  );

  return { isConnected, activeSessions, events, sendCommand, liveTranscripts };
}
