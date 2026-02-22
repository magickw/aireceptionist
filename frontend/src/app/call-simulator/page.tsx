'use client';
import * as React from 'react';
import { useState, useEffect, useRef, useCallback } from 'react';
import { Container, Typography, Box, Grid, Card, CardHeader, CardContent, TextField, IconButton, Button, List, ListItem, Paper, Chip, ToggleButtonGroup, ToggleButton, Tooltip } from '@mui/material';
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

export default function CallSimulator() {
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
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sessionIdRef = useRef<string>('');
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const connectionStatusRef = useRef<'connecting' | 'connected' | 'disconnected' | 'http_fallback'>('connecting');

  // Stable addMessage using ref to avoid stale closure
  const addMessageRef = useRef<(content: string, sender: 'customer' | 'ai') => void>(() => {});
  const addMessage = useCallback((content: string, sender: 'customer' | 'ai') => {
    const message = { id: Date.now(), sender, content };
    setCurrentCall((prev: any) => prev ? { ...prev, messages: [...(prev.messages || []), message] } : prev);
  }, []);
  addMessageRef.current = addMessage;

  // Voice streaming hook
  const {
    isRecording,
    isPlaying,
    startRecording,
    stopRecording,
    playAudioChunk,
    stopPlayback,
    micLevel,
    interimTranscript,
  } = useVoiceStreaming({
    wsRef,
    onPlaybackStart: () => setIsSpeaking(true),
    onPlaybackEnd: () => setIsSpeaking(false),
    onTranscript: useCallback((text: string, isFinal: boolean) => {
      // When streaming is ready, don't send browser STT - wait for backend STT
      // This callback is only used for HTTP fallback mode
      if (isStreamingReady) return;
      if (!isFinal) return;
      // Browser STT produced final text → send as user_input (HTTP fallback only)
      addMessageRef.current(text, 'customer');
      setIsProcessing(true);

      if (connectionStatus === 'http_fallback') {
        sendHttpMessage(text);
      } else if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'user_input', text }));
      }
    }, [connectionStatus, isStreamingReady]),
    isStreamingReady,
  });

  // Create HTTP session
  const createHttpSession = async () => {
    try {
      const response = await api.post('/voice/session', {
        customer_phone: '+15551234567',
        call_type: 'simulator'
      });
      sessionIdRef.current = response.data.session_id;
      return response.data.session_id;
    } catch (error) {
      console.error('Failed to create HTTP session:', error);
      return null;
    }
  };

  // Poll for HTTP events
  const pollHttpEvents = async () => {
    if (!sessionIdRef.current) return;

    try {
      const response = await api.get(`/voice/session/${sessionIdRef.current}/events`);
      const events = response.data.events || [];

      for (const event of events) {
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
          addMessageRef.current(`Error: ${event.message}`, 'ai');
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

  useEffect(() => {
    const connect = async () => {
      console.log('[CallSim] Connecting to WebSocket...');

      try {
        const ws = new WebSocket(getWebSocketUrl());
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('[CallSim] WebSocket connected');
          // Send auth token as first message
          const token = localStorage.getItem('token');
          if (token) {
            ws.send(JSON.stringify({ type: 'auth', token }));
          }
          connectionStatusRef.current = 'connected';
          setConnectionStatus('connected');
        };

        ws.onclose = () => {
          console.log('[CallSim] WebSocket closed');
          setConnectionStatus('disconnected');
          setIsStreamingReady(false);
        };

        ws.onerror = () => {
          console.error('[CallSim] WebSocket error');
          setConnectionStatus('disconnected');
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);

          if (data.type === 'connected') {
            // Server acknowledged connection
            console.log('[CallSim] Server connected:', data.session_id);
          } else if (data.type === 'streaming_ready') {
            // Nova Sonic bidirectional streaming is active
            setIsStreamingReady(true);
            console.log('[CallSim] Streaming ready');
          } else if (data.type === 'thought') {
            setThoughts(prev => [...prev, { step: data.step, message: data.message, timestamp: new Date() }]);
          } else if (data.type === 'transcript') {
            // User speech transcript from streaming STT
            addMessageRef.current(data.text, 'customer');
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
          } else if (data.type === 'agent_response') {
            setIsProcessing(false);
            setIsSpeaking(false);
            addMessageRef.current(data.text, 'ai');
            if (data.reasoning) setReasoningData(data.reasoning);
            setStreamingText('');
          } else if (data.type === 'audio') {
            // Play audio response (streaming: 24kHz, batch: 16kHz)
            const sampleRate = data.sample_rate || 16000;
            playAudioChunkRef.current(data.audio, sampleRate);
          } else if (data.type === 'reasoning_chain' || data.type === 'reasoning_complete') {
            if (data.data) setReasoningData(data.data);
          } else if (data.type === 'human_intervention_request') {
            setAutonomyMode('GUARDED');
            addMessageRef.current(`[Transfer requested: ${data.reason || 'Human agent needed'}]`, 'ai');
          } else if (data.type === 'streaming_failed') {
            // Stream died mid-session — fall back to text mode
            setIsStreamingReady(false);
            setInputMode('text');
            console.warn('[CallSim] Streaming failed:', data.message);
          } else if (data.type === 'latency_metrics') {
            setLatencyMetrics(data.metrics);
            console.log('[CallSim] Latency:', data.metrics);
          } else if (data.type === 'call_ended') {
            console.log('[CallSim] Call ended by server');
          } else if (data.type === 'error') {
            console.error('[CallSim] Backend error:', data.message);
            addMessageRef.current(`Error: ${data.message}`, 'ai');
            setIsProcessing(false);
          }
        };

        // Fallback to HTTP if WebSocket fails within 5 seconds
        setTimeout(() => {
          if (connectionStatusRef.current === 'connecting') {
            console.log('[CallSim] WebSocket timed out, switching to HTTP fallback');
            ws.close();
            connectionStatusRef.current = 'http_fallback';
            setConnectionStatus('http_fallback');
            createHttpSession().then(sessionId => {
              if (sessionId) {
                pollIntervalRef.current = setInterval(pollHttpEvents, 2000);
              }
            });
          }
        }, 5000);

      } catch (error) {
        console.error('WebSocket failed, using HTTP fallback:', error);
        setConnectionStatus('http_fallback');
        createHttpSession().then(sessionId => {
          if (sessionId) {
            pollIntervalRef.current = setInterval(pollHttpEvents, 2000);
          }
        });
      }
    };

    if (typeof window !== 'undefined') {
      connect();
    }

    return () => {
      wsRef.current?.close();
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentCall?.messages, streamingText]);

  const startCall = () => {
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
      console.warn("Connection not ready");
      return;
    }

    setMessageInput('');
    setIsProcessing(true);
  };

  const toggleRecording = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      // Stop any playback before recording
      stopPlayback();
      await startRecording();
    }
  };

  const endCall = () => {
    // Stop recording/playback
    if (isRecording) stopRecording();
    stopPlayback();

    setCurrentCall(null);
    setThoughts([]);
    setStreamingText('');
    setIsSpeaking(false);
    setLatencyMetrics(null);
    setIsStreamingReady(false);

    if (connectionStatus === 'http_fallback') {
      endHttpSession();
    } else if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'end_call' }));
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Typography variant="h4">AI Call Simulator</Typography>
          <Chip
            label={connectionStatus === 'connected' ? 'WebSocket' : connectionStatus === 'http_fallback' ? 'HTTP Polling' : 'Connecting...'}
            color={connectionStatus === 'connected' ? 'success' : connectionStatus === 'http_fallback' ? 'warning' : 'default'}
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
          {latencyMetrics && latencyMetrics.time_to_first_byte_ms !== undefined && (
            <Tooltip title={`Transcript: ${latencyMetrics.time_to_transcript_ms?.toFixed(0) || '?'}ms | First byte: ${latencyMetrics.time_to_first_byte_ms?.toFixed(0) || '?'}ms | Total: ${latencyMetrics.total_turn_ms?.toFixed(0) || '?'}ms`}>
              <Chip
                label={`${latencyMetrics.time_to_first_byte_ms?.toFixed(0)}ms`}
                size="small"
                variant="outlined"
                color={latencyMetrics.time_to_first_byte_ms < 1000 ? 'success' : 'warning'}
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
                <div ref={messagesEndRef} />
              </List>
            </CardContent>
            {currentCall && (
              <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                {inputMode === 'text' ? (
                  <Box component="form" onSubmit={(e) => { e.preventDefault(); sendMessage(); }} sx={{ display: 'flex', flex: 1 }}>
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
                  <Box sx={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', gap: 2 }}>
                    <IconButton
                      onClick={toggleRecording}
                      sx={{
                        width: 56,
                        height: 56,
                        bgcolor: isRecording ? 'error.main' : 'primary.main',
                        color: 'white',
                        '&:hover': { bgcolor: isRecording ? 'error.dark' : 'primary.dark' },
                        animation: isRecording ? 'pulse 1.5s infinite' : 'none',
                      }}
                    >
                      {isRecording ? <MicOffIcon /> : <MicIcon />}
                    </IconButton>
                    {isRecording && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexDirection: 'column' }}>
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
                        {interimTranscript && (
                          <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic', maxWidth: 300, textAlign: 'center' }}>
                            {interimTranscript}
                          </Typography>
                        )}
                      </Box>
                    )}
                    {!isRecording && (
                      <Typography variant="caption" color="text.secondary">
                        Tap to speak
                      </Typography>
                    )}
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
