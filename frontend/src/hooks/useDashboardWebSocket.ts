import { useState, useEffect, useRef, useCallback } from 'react';

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

  const connect = useCallback(() => {
    if (!businessId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:\/\//, '') || window.location.host;
    const wsUrl = `${protocol}//${host}/api/ws/dashboard?business_id=${businessId}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      console.log('[Dashboard WS] Connected');
    };

    ws.onmessage = (event) => {
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
      setIsConnected(false);
      console.log('[Dashboard WS] Disconnected, reconnecting in 3s...');
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };

    ws.onerror = (error) => {
      console.error('[Dashboard WS] Error:', error);
    };
  }, [businessId]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
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
