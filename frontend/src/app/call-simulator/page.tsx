'use client';
import * as React from 'react';
import { useState, useEffect, useRef, useCallback } from 'react';
import { Container, Typography, Box, Grid, Card, CardHeader, CardContent, TextField, IconButton, Button, List, ListItem, Paper, Chip, ToggleButtonGroup, ToggleButton, Tooltip, Snackbar, Alert, useTheme, useMediaQuery } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import KeyboardIcon from '@mui/icons-material/Keyboard';
import GraphicEqIcon from '@mui/icons-material/GraphicEq';
import AgentThoughts from '@/components/AgentThoughts';
import VoiceVisualizer from '@/components/VoiceVisualizer';
import { getWebSocketUrl } from '@/services/api';
import api from '@/services/api';
import { useVoiceStreaming } from '@/hooks/useVoiceStreaming';

interface SnackbarState {
  open: boolean;
  message: string;
  severity: 'success' | 'error' | 'info' | 'warning';
}

export default function CallSimulator() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [currentCall, setCurrentCall] = useState<any>(null);
  const [messageInput, setMessageInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [thoughts, setThoughts] = useState<any[]>([]);
  const [reasoningData, setReasoningData] = useState<any>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'http_fallback'>('connecting');
  const [autonomyMode, setAutonomyMode] = useState<'AUTONOMOUS' | 'GUARDED'>('AUTONOMOUS');
  const [inputMode, setInputMode] = useState<'text' | 'voice'>('text');
  const [isStreamingReady, setIsStreamingReady] = useState(false);
  const [latencyMetrics, setLatencyMetrics] = useState<any>(null);
  const [sttPreview, setSttPreview] = useState('');
  const [snackbar, setSnackbar] = useState<SnackbarState>({ open: false, message: '', severity: 'info' });

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sessionIdRef = useRef<string>('');
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const connectionStatusRef = useRef<'connecting' | 'connected' | 'disconnected' | 'http_fallback'>('connecting');
  const lastEventIdRef = useRef<number>(0);

  // Reconnect state
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const userEndedCallRef = useRef(false);
  const unmountedRef = useRef(false);
  const MAX_RECONNECT_ATTEMPTS = 5;

  const showSnackbar = useCallback((message: string, severity: SnackbarState['severity'] = 'info') => {
    setSnackbar({ open: true, message, severity });
  }, []);

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  // Stable addMessage using ref to avoid stale closure
  const addMessageRef = useRef<(content: string, sender: 'customer' | 'ai') => void>(() => {});
  const addMessage = useCallback((content: string, sender: 'customer' | 'ai') => {
    if (!content || !content.trim()) return;
    const message = { id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`, sender, content };
    setCurrentCall((prev: any) => prev ? { ...prev, messages: [...(prev.messages || []), message] } : prev);
  }, []);
  addMessageRef.current = addMessage;

  // Refs for auto-start recording (phone-like UX)
  const startRecordingRef = useRef<(() => Promise<void>) | null>(null);
  const stopRecordingRef = useRef<(() => void) | null>(null);
  const stopPlaybackRef = useRef<(() => void) | null>(null);
  const autoStartEnabledRef = useRef(false);
  const autoStartTimerRef = useRef<NodeJS.Timeout | null>(null);
  const wsFallbackTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Voice streaming hook
  const {
    isRecording,
    isPlaying,
    startRecording,
    stopRecording,
    playAudioChunk,
    stopPlayback,
    micLevel,
    browserCompatibility,
  } = useVoiceStreaming({
    wsRef,
    onPlaybackStart: () => {
      if (unmountedRef.current) return;
      setIsSpeaking(true);
    },
    onPlaybackEnd: () => {
      if (unmountedRef.current) return;
      setIsSpeaking(false);
      // Auto-start recording after AI finishes speaking (phone-like UX)
      if (autoStartEnabledRef.current) {
        // Clear any existing timer first to prevent race conditions
        if (autoStartTimerRef.current) {
          clearTimeout(autoStartTimerRef.current);
          autoStartTimerRef.current = null;
        }
        // Small delay to let echo cancellation settle
        autoStartTimerRef.current = setTimeout(() => {
          // Guard: don't proceed if component is unmounted
          if (unmountedRef.current) return;

          if (autoStartEnabledRef.current && !isRecording) {
            console.log('[CallSim] Auto-starting recording after playback ended');
            startRecordingRef.current?.();
          }
          autoStartTimerRef.current = null;
        }, 300);
      }
    },
    onError: (msg) => showSnackbar(msg, 'error'),
  });

  // Check browser compatibility when switching to voice mode
  useEffect(() => {
    if (inputMode === 'voice' && browserCompatibility) {
      if (!browserCompatibility.supported) {
        showSnackbar('Voice features are not supported in this browser. Please use Chrome, Firefox, Edge, or Safari.', 'error');
        setInputMode('text');
      } else if (browserCompatibility.warnings.length > 0) {
        showSnackbar(browserCompatibility.warnings[0], 'warning');
      }
    }
  }, [inputMode, browserCompatibility, showSnackbar]);

  // Keep refs in sync with latest values
  startRecordingRef.current = startRecording;
  stopRecordingRef.current = stopRecording;
  stopPlaybackRef.current = stopPlayback;
  autoStartEnabledRef.current = !!currentCall && inputMode === 'voice' && !userEndedCallRef.current;

  // Create HTTP session
  const createHttpSession = async () => {
    try {
      const response = await api.post('/voice/session', {
        customer_phone: '+15551234567',
        call_type: 'simulator'
      });
      sessionIdRef.current = response.data.session_id;
      lastEventIdRef.current = 0;
      return response.data.session_id;
    } catch (error) {
      console.error('Failed to create HTTP session:', error);
      showSnackbar('Failed to create session', 'error');
      return null;
    }
  };

  // Poll for HTTP events (cursor-based)
  const pollHttpEvents = async () => {
    if (!sessionIdRef.current) return;

    try {
      const params = lastEventIdRef.current > 0 ? `?last_event_id=${lastEventIdRef.current}` : '';
      const response = await api.get(`/voice/session/${sessionIdRef.current}/events${params}`);
      const events = response.data.events || [];

      for (const event of events) {
        // Track cursor
        if (event._event_id) {
          lastEventIdRef.current = Math.max(lastEventIdRef.current, event._event_id);
        }

        if (event.type === 'thought') {
          setThoughts(prev => [...prev, { step: event.step, message: event.message, timestamp: new Date() }]);
        } else if (event.type === 'text_chunk') {
          setStreamingText(prev => prev + event.chunk);
          setIsSpeaking(true);
          if (event.is_last) {
            setIsProcessing(false);
            setIsSpeaking(false);
            if (event.full_text) {
              addMessageRef.current(event.full_text, 'ai');
            }
            setStreamingText('');
          }
        } else if (event.type === 'agent_response') {
          setIsProcessing(false);
          setIsSpeaking(false);
          addMessageRef.current(event.text, 'ai');
          if (event.reasoning) setReasoningData(event.reasoning);
        } else if (event.type === 'reasoning_chain' || event.type === 'reasoning_complete') {
          if (event.data) setReasoningData(event.data);
        } else if (event.type === 'human_intervention_request') {
          setAutonomyMode('GUARDED');
        } else if (event.type === 'error') {
          console.error('Backend poll error:', event.message);
          showSnackbar(`Backend error: ${event.message}`, 'error');
          setIsProcessing(false);
        }
      }
    } catch (error) {
      console.error('Poll error:', error);
    }
  };

  // Send message via HTTP
  const sendHttpMessage = async (text: string) => {
    if (!sessionIdRef.current) return;
    try {
      await api.post(`/voice/session/${sessionIdRef.current}/message`, { text });
    } catch (error: any) {
      console.error('[CallSim] Failed to send HTTP message:', error?.response?.data || error?.message || error);
      showSnackbar('Failed to send message', 'error');
    }
  };

  // End HTTP session
  const endHttpSession = async () => {
    if (!sessionIdRef.current) return;
    try {
      await api.post(`/voice/session/${sessionIdRef.current}/end`);
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    } catch (error) {
      console.error('Failed to end HTTP session:', error);
    }
  };

  // Ref for playAudioChunk to use inside WS handler without stale closure
  const playAudioChunkRef = useRef(playAudioChunk);
  playAudioChunkRef.current = playAudioChunk;

  // Ref for showSnackbar inside WS handler
  const showSnackbarRef = useRef(showSnackbar);
  showSnackbarRef.current = showSnackbar;

  // Switch to HTTP fallback
  const switchToHttpFallback = useCallback(() => {
    connectionStatusRef.current = 'http_fallback';
    setConnectionStatus('http_fallback');
    createHttpSession().then(sessionId => {
      if (sessionId) {
        pollIntervalRef.current = setInterval(pollHttpEvents, 2000);
      }
    });
  }, []);

  // Connect WebSocket with optional reconnect support
  const connectWs = useCallback((isReconnect = false) => {
    if (unmountedRef.current) return;

    console.log(`[CallSim] ${isReconnect ? 'Reconnecting' : 'Connecting'} to WebSocket...`);
    if (!isReconnect) {
      connectionStatusRef.current = 'connecting';
      setConnectionStatus('connecting');
    }

    try {
      const ws = new WebSocket(getWebSocketUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        // Guard: don't proceed if unmounted
        if (unmountedRef.current) {
          console.log('[CallSim] WebSocket opened but component unmounted, closing');
          ws.close();
          return;
        }
        console.log('[CallSim] WebSocket connected');
        const token = localStorage.getItem('token');
        if (token) {
          ws.send(JSON.stringify({ type: 'auth', token }));
        }
        connectionStatusRef.current = 'connected';
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        if (isReconnect) {
          showSnackbarRef.current('Reconnected to server', 'success');
        }
      };

      ws.onclose = () => {
        console.log('[CallSim] WebSocket closed');

        // Guard: don't update state if component is unmounted
        if (unmountedRef.current || userEndedCallRef.current) return;

        setIsStreamingReady(false);

        // Attempt reconnect
        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          const attempt = reconnectAttemptsRef.current;
          reconnectAttemptsRef.current += 1;
          const delay = Math.min(1000 * Math.pow(2, attempt), 16000);
          console.log(`[CallSim] Reconnecting in ${delay}ms (attempt ${attempt + 1}/${MAX_RECONNECT_ATTEMPTS})`);
          setConnectionStatus('disconnected');
          showSnackbarRef.current(`Connection lost. Reconnecting (${attempt + 1}/${MAX_RECONNECT_ATTEMPTS})...`, 'warning');
          reconnectTimerRef.current = setTimeout(() => connectWs(true), delay);
        } else {
          console.log('[CallSim] Max reconnect attempts reached, falling back to HTTP');
          showSnackbarRef.current('Connection lost. Switched to HTTP fallback.', 'error');
          switchToHttpFallback();
        }
      };

      ws.onerror = () => {
        console.error('[CallSim] WebSocket error');
        // onclose will fire after onerror, reconnect handled there
      };

      ws.onmessage = (event) => {
        // Guard: don't process messages if component is unmounted
        if (unmountedRef.current) return;

        const data = JSON.parse(event.data);
        console.log('[CallSim] WS message type:', data.type, data);

        if (data.type === 'connected') {
          console.log('[CallSim] Server connected:', data.session_id);
        } else if (data.type === 'streaming_ready') {
          setIsStreamingReady(true);
          console.log('[CallSim] Streaming ready');
        } else if (data.type === 'thought') {
          setThoughts(prev => [...prev, { step: data.step, message: data.message, timestamp: new Date() }]);
        } else if (data.type === 'transcript') {
          // User speech transcript from streaming STT
          console.log('[CallSim] Transcript received:', data.text, 'is_partial:', data.is_partial);

          if (data.is_partial) {
            // Partial transcript — only update preview, don't touch messages
            setSttPreview(data.text);
          } else {
            // Final transcript — add to messages, clear preview
            setSttPreview('');
            addMessageRef.current(data.text, 'customer');
          }
          setIsProcessing(true);
        } else if (data.type === 'text_chunk') {
          setStreamingText(prev => prev + data.chunk);
          setIsSpeaking(true);
          if (data.is_last) {
            setIsProcessing(false);
            setIsSpeaking(false);
            if (data.full_text) {
              addMessageRef.current(data.full_text, 'ai');
            }
            setStreamingText('');
          }
        } else if (data.type === 'thinking') {
          setThoughts(prev => [...prev, { step: 'Reasoning', message: data.thinking || data, timestamp: new Date() }]);
        } else if (data.type === 'agent_response') {
          setIsProcessing(false);
          setIsSpeaking(false);
          setSttPreview('');
          addMessageRef.current(data.text, 'ai');
          if (data.reasoning) setReasoningData(data.reasoning);
          setStreamingText('');
        } else if (data.type === 'audio') {
          const sampleRate = data.sample_rate || 16000;
          playAudioChunkRef.current(data.audio, sampleRate);
        } else if (data.type === 'reasoning_chain' || data.type === 'reasoning_complete') {
          if (data.data) setReasoningData(data.data);
        } else if (data.type === 'human_intervention_request') {
          setAutonomyMode('GUARDED');
          addMessageRef.current(`[Transfer requested: ${data.reason || 'Human agent needed'}]`, 'ai');
        } else if (data.type === 'streaming_failed') {
          setIsStreamingReady(false);
          setInputMode('text');
          console.warn('[CallSim] Streaming failed:', data.message);
          showSnackbarRef.current('Voice streaming failed. Switched to text mode.', 'warning');
        } else if (data.type === 'latency' || data.type === 'latency_metrics') {
          setLatencyMetrics(data.metrics);
          console.log('[CallSim] Latency:', data.metrics);
        } else if (data.type === 'call_ended') {
          console.log('[CallSim] Call ended by server');
          // Clean up call state when server ends the call
          if (isRecording) stopRecordingRef.current?.();
          stopPlaybackRef.current?.();
          setCurrentCall(null);
          setThoughts([]);
          setStreamingText('');
          setIsSpeaking(false);
          setIsStreamingReady(false);
          setSttPreview('');
          setIsProcessing(false);
          // Close WebSocket - server ended the call
          if (wsRef.current) {
            wsRef.current.onclose = null; // Prevent reconnection attempt
            wsRef.current.close();
            wsRef.current = null;
          }
        } else if (data.type === 'error') {
          console.error('[CallSim] Backend error:', data.message);
          showSnackbarRef.current(`Error: ${data.message}`, 'error');
          setIsProcessing(false);
        }
      };

      // Fallback to HTTP if WebSocket fails within 15 seconds
      wsFallbackTimerRef.current = setTimeout(() => {
        // Guard: don't proceed if component is unmounted
        if (unmountedRef.current) return;

        if (connectionStatusRef.current === 'connecting') {
          console.log('[CallSim] WebSocket timed out, switching to HTTP fallback');
          ws.close();
          showSnackbarRef.current('WebSocket timed out. Using HTTP fallback.', 'warning');
          switchToHttpFallback();
        }
      }, 15000);

    } catch (error) {
      console.error('WebSocket failed, using HTTP fallback:', error);
      showSnackbarRef.current('WebSocket connection failed. Using HTTP fallback.', 'error');
      switchToHttpFallback();
    }
  }, [switchToHttpFallback]);

  // Reset unmounted flag on mount
  useEffect(() => {
    unmountedRef.current = false;
    userEndedCallRef.current = false;
  }, []);

  // Initial connection
  useEffect(() => {
    if (typeof window !== 'undefined') {
      connectWs();
    }

    return () => {
      // Mark as unmounted to prevent state updates and reconnects
      unmountedRef.current = true;
      userEndedCallRef.current = true;

      // Clear any pending timers
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (autoStartTimerRef.current) {
        clearTimeout(autoStartTimerRef.current);
        autoStartTimerRef.current = null;
      }
      if (wsFallbackTimerRef.current) {
        clearTimeout(wsFallbackTimerRef.current);
        wsFallbackTimerRef.current = null;
      }
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }

      // Stop any active audio/recording
      stopRecordingRef.current?.();
      stopPlaybackRef.current?.();

      // Close WebSocket - clear handlers first to prevent reconnection attempts
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.onmessage = null;
        wsRef.current.onopen = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connectWs]);

  // Tab visibility: warn if disconnected when user returns
  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        if (wsRef.current && wsRef.current.readyState !== WebSocket.OPEN && connectionStatusRef.current !== 'http_fallback') {
          showSnackbar('Connection may have been interrupted while tab was inactive.', 'warning');
        }
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => document.removeEventListener('visibilitychange', handleVisibility);
  }, [showSnackbar]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentCall?.messages, streamingText, sttPreview]);

  const startCall = () => {
    userEndedCallRef.current = false;
    setCurrentCall({ messages: [] });
    setThoughts([]);
    setStreamingText('');
    setAutonomyMode('AUTONOMOUS');
    setLatencyMetrics(null);
    setTimeout(() => addMessage("Hello! How can I help you today?", 'ai'), 500);
  };

  const sendMessage = () => {
    if (!messageInput.trim()) return;

    addMessage(messageInput, 'customer');

    if (connectionStatus === 'http_fallback') {
      sendHttpMessage(messageInput);
    } else if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'user_input', text: messageInput }));
    } else {
      showSnackbar('Connection not ready. Please wait or try again.', 'warning');
      return;
    }

    setMessageInput('');
    setIsProcessing(true);
  };

  const toggleRecording = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      // Stop any playback before recording (barge-in)
      stopPlayback();
      // Notify backend to drain pending output
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'barge_in' }));
      }
      await startRecording();
    }
  };

  const endCall = () => {
    userEndedCallRef.current = true;
    // Cancel any pending auto-start timers
    if (autoStartTimerRef.current) {
      clearTimeout(autoStartTimerRef.current);
      autoStartTimerRef.current = null;
    }

    if (isRecording) stopRecording();
    stopPlayback();

    setCurrentCall(null);
    setThoughts([]);
    setStreamingText('');
    setIsSpeaking(false);
    setLatencyMetrics(null);
    setIsStreamingReady(false);
    setSttPreview('');

    if (connectionStatus === 'http_fallback') {
      endHttpSession();
    } else if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'end_call' }));
    }
  };

  const micButtonSize = isMobile ? 72 : 56;

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Typography variant="h4">AI Call Simulator</Typography>
          <Chip
            label={
              connectionStatus === 'connected' ? 'WebSocket' :
              connectionStatus === 'http_fallback' ? 'HTTP Polling' :
              connectionStatus === 'disconnected' ? 'Disconnected' :
              'Connecting...'
            }
            color={
              connectionStatus === 'connected' ? 'success' :
              connectionStatus === 'http_fallback' ? 'warning' :
              connectionStatus === 'disconnected' ? 'error' :
              'default'
            }
            size="small"
          />
          {isStreamingReady && (
            <Chip
              label="Streaming"
              color="info"
              size="small"
              variant="outlined"
              icon={<GraphicEqIcon />}
            />
          )}
          {currentCall && (
            <Chip
              label={`MODE: ${autonomyMode}`}
              color={autonomyMode === 'AUTONOMOUS' ? 'success' : 'error'}
              variant="outlined"
              size="small"
              sx={{
                fontWeight: 'bold',
                borderWidth: 2,
                animation: autonomyMode === 'GUARDED' ? 'blink 1s infinite' : 'none'
              }}
            />
          )}
          {latencyMetrics && latencyMetrics.time_to_first_chunk_ms !== undefined && (
            <Tooltip title={`STT: ${latencyMetrics.stt_ms?.toFixed(0) || '?'}ms | LLM: ${latencyMetrics.llm_first_token_ms?.toFixed(0) || '?'}ms | TTS: ${latencyMetrics.tts_first_audio_ms?.toFixed(0) || '?'}ms | Voice-to-Voice: ${latencyMetrics.voice_to_voice_ms?.toFixed(0) || '?'}ms`}>
              <Chip
                label={`${latencyMetrics.voice_to_voice_ms?.toFixed(0) || latencyMetrics.time_to_first_chunk_ms?.toFixed(0) || '?'}ms`}
                size="small"
                variant="outlined"
                color={(latencyMetrics.voice_to_voice_ms || latencyMetrics.time_to_first_chunk_ms) < 2000 ? 'success' : 'warning'}
              />
            </Tooltip>
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {currentCall && (
            <>
              <ToggleButtonGroup
                value={inputMode}
                exclusive
                onChange={(_e, val) => { if (val) setInputMode(val); }}
                size="small"
              >
                <ToggleButton value="text">
                  <Tooltip title="Text input"><KeyboardIcon fontSize="small" /></Tooltip>
                </ToggleButton>
                <ToggleButton value="voice" disabled={connectionStatus === 'http_fallback'}>
                  <Tooltip title="Voice input (streaming)"><MicIcon fontSize="small" /></Tooltip>
                </ToggleButton>
              </ToggleButtonGroup>
              <Button variant="outlined" color="error" onClick={endCall}>
                End Call
              </Button>
            </>
          )}
        </Box>
      </Box>

      {/* Voice Visualizer */}
      <Box sx={{ mb: 3 }}>
        <VoiceVisualizer
          isActive={!!currentCall}
          isSpeaking={isSpeaking || isPlaying}
          isRecording={isRecording}
          micLevel={micLevel}
        />
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
            <CardHeader
              title={currentCall ? "Call in Progress" : "Ready to Start"}
              action={!currentCall && <Button onClick={startCall}>Start Call</Button>}
            />
            <CardContent sx={{ flexGrow: 1, overflowY: 'auto' }}>
              <List>
                {currentCall?.messages.map((m: any) => (
                  <ListItem key={m.id} sx={{ justifyContent: m.sender === 'ai' ? 'flex-start' : 'flex-end' }}>
                    <Paper sx={{ p: 1.5, maxWidth: '80%', bgcolor: m.sender === 'ai' ? '#f1f5f9' : 'primary.main', color: m.sender === 'ai' ? 'inherit' : 'white' }}>{m.content}</Paper>
                  </ListItem>
                ))}
                {/* Show streaming text */}
                {streamingText && (
                  <ListItem sx={{ justifyContent: 'flex-start' }}>
                    <Paper sx={{ p: 1.5, bgcolor: '#f1f5f9' }}>
                      {streamingText}
                      <Box component="span" sx={{ animation: 'pulse 1s infinite', ml: 0.5 }}>|</Box>
                    </Paper>
                  </ListItem>
                )}
                {/* STT preview bubble — translucent "listening" indicator */}
                {sttPreview && (
                  <ListItem sx={{ justifyContent: 'flex-end' }}>
                    <Paper sx={{ p: 1.5, maxWidth: '80%', bgcolor: 'primary.main', color: 'white', opacity: 0.6, fontStyle: 'italic' }}>
                      {sttPreview}
                      <Typography variant="caption" sx={{ display: 'block', mt: 0.5, opacity: 0.8 }}>listening...</Typography>
                    </Paper>
                  </ListItem>
                )}
                <div ref={messagesEndRef} />
              </List>
            </CardContent>
            {currentCall && (
              <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                {inputMode === 'text' ? (
                  <Box component="form" onSubmit={(e) => { e.preventDefault(); sendMessage(); }} sx={{ display: 'flex', flex: 1, flexDirection: isMobile ? 'column' : 'row', gap: isMobile ? 1 : 0 }}>
                    <TextField
                      fullWidth
                      value={messageInput}
                      onChange={(e) => setMessageInput(e.target.value)}
                      placeholder="Type message..."
                      disabled={isProcessing}
                      size="small"
                    />
                    <IconButton type="submit" disabled={Boolean(!messageInput.trim())}><SendIcon /></IconButton>
                  </Box>
                ) : (
                  <Box sx={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', gap: 2, flexDirection: isMobile ? 'column' : 'row' }}>
                    <IconButton
                      onClick={toggleRecording}
                      sx={{
                        width: micButtonSize,
                        height: micButtonSize,
                        bgcolor: isRecording ? 'success.main' : (isProcessing || isSpeaking) ? 'grey.400' : 'primary.main',
                        color: 'white',
                        '&:hover': { bgcolor: isRecording ? 'success.dark' : 'primary.dark' },
                        animation: isRecording ? 'pulse 1.5s infinite' : 'none',
                      }}
                    >
                      {isRecording ? <MicIcon /> : <MicOffIcon />}
                    </IconButton>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexDirection: 'column' }}>
                      {isRecording && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box
                            sx={{
                              width: 100,
                              height: 8,
                              borderRadius: 4,
                              bgcolor: 'grey.200',
                              overflow: 'hidden',
                            }}
                          >
                            <Box
                              sx={{
                                width: `${micLevel * 100}%`,
                                height: '100%',
                                bgcolor: micLevel > 0.6 ? 'error.main' : micLevel > 0.3 ? 'warning.main' : 'success.main',
                                transition: 'width 0.05s',
                                borderRadius: 4,
                              }}
                            />
                          </Box>
                          <Typography variant="caption" color="text.secondary">
                            Listening...
                          </Typography>
                        </Box>
                      )}
                      {!isRecording && (isProcessing || isSpeaking) && (
                        <Typography variant="caption" color="text.secondary">
                          AI speaking...
                        </Typography>
                      )}
                      {!isRecording && !isProcessing && !isSpeaking && (
                        <Typography variant="caption" color="text.secondary">
                          Mic paused — tap to speak
                        </Typography>
                      )}
                    </Box>
                  </Box>
                )}
              </Box>
            )}
          </Card>
        </Grid>
        <Grid item xs={12} lg={4}>
          <Card>
            <CardHeader title="Agent Reasoning" />
            <CardContent>
                <AgentThoughts thoughts={thoughts} reasoningData={reasoningData} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} variant="filled" sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>

      <style jsx global>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        @keyframes blink {
          0%, 100% { opacity: 1; border-color: #ef4444; }
          50% { opacity: 0.5; border-color: transparent; }
        }
      `}</style>
    </Container>
  );
}
