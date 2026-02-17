'use client';
import * as React from 'react';
import { useState, useEffect, useRef } from 'react';
import { Container, Typography, Box, Grid, Card, CardHeader, CardContent, TextField, IconButton, Button, List, ListItem, Paper, Alert, Chip } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AgentThoughts from '@/components/AgentThoughts';
import VoiceVisualizer from '@/components/VoiceVisualizer';
import { getWebSocketUrl } from '@/services/api';
import api from '@/services/api';

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
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sessionIdRef = useRef<string>('');
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

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
            // Only add if full_text is provided to avoid duplicate with agent_response
            if (event.full_text) {
              addMessage(event.full_text, 'ai');
            }
            setStreamingText('');
          }
        } else if (event.type === 'agent_response') {
          setIsProcessing(false);
          setIsSpeaking(false);
          // Only add if streaming didn't already add the message
          const msgs = currentCall?.messages || [];
          const lastAiMsg = msgs.filter((m: any) => m.sender === 'ai').pop();
          if (!lastAiMsg || lastAiMsg.content !== event.text) {
            addMessage(event.text, 'ai');
          }
          if (event.reasoning) setReasoningData(event.reasoning);
        } else if (event.type === 'reasoning_chain' || event.type === 'reasoning_complete') {
          // Handle reasoning data
          if (event.data) setReasoningData(event.data);
        } else if (event.type === 'human_intervention_request') {
          setAutonomyMode('GUARDED');
        } else if (event.type === 'error') {
          console.error('Backend poll error:', event.message);
          addMessage(`Error: ${event.message}`, 'ai');
          setIsProcessing(false);
        }
      }
    } catch (error) {
      console.error('Poll error:', error);
    }
  };

  // Send message via HTTP
  const sendHttpMessage = async (text: string) => {
    if (!sessionIdRef.current) {
      console.error('No session ID');
      return;
    }
    try {
      console.log('[CallSim] Sending message:', text, 'to session:', sessionIdRef.current);
      const response = await api.post(`/voice/session/${sessionIdRef.current}/message`, { text });
      console.log('[CallSim] Message sent, response:', response);
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

  useEffect(() => {
    const connect = async () => {
      console.log('🔌 Connecting to WebSocket:', getWebSocketUrl().replace(/\?token=.*$/, '?token=REDACTED'));
      
      try {
        const ws = new WebSocket(getWebSocketUrl());
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('🔌 WebSocket connection established');
          setConnectionStatus('connected');
        };
        
        ws.onclose = () => {
          console.log('🔌 WebSocket connection closed');
          setConnectionStatus('disconnected');
        };
        
        ws.onerror = () => {
          console.error('WebSocket error');
          setConnectionStatus('disconnected');
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.type === 'thought') {
            setThoughts(prev => [...prev, { step: data.step, message: data.message, timestamp: new Date() }]);
          } else if (data.type === 'text_chunk') {
            setStreamingText(prev => prev + data.chunk);
            setIsSpeaking(true);
            if (data.is_last) {
              setIsProcessing(false);
              setIsSpeaking(false);
              // Only add if full_text is provided
              if (data.full_text) {
                addMessage(data.full_text, 'ai');
              }
              setStreamingText('');
            }
          } else if (data.type === 'agent_response') {
            setIsProcessing(false);
            setIsSpeaking(false);
            // Only add if not already added via text_chunk
            const msgs = currentCall?.messages || [];
            const lastAiMsg = msgs.filter((m: any) => m.sender === 'ai').pop();
            if (!lastAiMsg || lastAiMsg.content !== data.text) {
              addMessage(data.text, 'ai');
            }
            if (data.reasoning) setReasoningData(data.reasoning);
            setStreamingText('');
          } else if (data.type === 'human_intervention_request') {
            setAutonomyMode('GUARDED');
          } else if (data.type === 'error') {
            console.error('WebSocket backend error:', data.message);
            addMessage(`Error: ${data.message}`, 'ai');
            setIsProcessing(false);
          }
        };
        
        // Fallback to HTTP if WebSocket fails within 5 seconds
        setTimeout(() => {
          if (connectionStatus === 'connecting') {
            console.log('🔄 WebSocket timed out, switching to HTTP fallback');
            ws.close();
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

  const addMessage = (content: string, sender: 'customer' | 'ai') => {
    const message = { id: Date.now(), sender, content };
    setCurrentCall((prev: any) => ({ ...prev, messages: [...(prev?.messages || []), message] }));
  };

  const startCall = () => {
    setCurrentCall({ messages: [] });
    setThoughts([]);
    setStreamingText('');
    setAutonomyMode('AUTONOMOUS');
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
      console.warn("Connection not ready, message queued");
      return;
    }
    
    setMessageInput('');
    setIsProcessing(true);
  };

  const endCall = () => {
    setCurrentCall(null);
    setThoughts([]);
    setStreamingText('');
    setIsSpeaking(false);
    
    if (connectionStatus === 'http_fallback') {
      endHttpSession();
    } else if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'end_call' }));
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h4">AI Call Simulator</Typography>
          <Chip 
            label={connectionStatus === 'connected' ? 'WebSocket' : connectionStatus === 'http_fallback' ? 'HTTP Polling' : 'Connecting...'} 
            color={connectionStatus === 'connected' ? 'success' : connectionStatus === 'http_fallback' ? 'warning' : 'default'}
            size="small"
          />
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
        </Box>
        {currentCall && (
          <Button variant="outlined" color="error" onClick={endCall}>
            End Call
          </Button>
        )}
      </Box>
      
      {/* Voice Visualizer */}
      <Box sx={{ mb: 3 }}>
        <VoiceVisualizer 
          isActive={!!currentCall} 
          isSpeaking={isSpeaking} 
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
                    <Paper sx={{ p: 1.5, bgcolor: m.sender === 'ai' ? '#f1f5f9' : 'primary.main', color: m.sender === 'ai' ? 'inherit' : 'white' }}>{m.content}</Paper>
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
              <Box sx={{ p: 2, display: 'flex' }} component="form" onSubmit={(e) => { e.preventDefault(); sendMessage(); }}>
                <TextField 
                  fullWidth 
                  value={messageInput} 
                  onChange={(e) => setMessageInput(e.target.value)} 
                  placeholder="Type message..."
                  disabled={isProcessing}
                />
                <IconButton type="submit" disabled={Boolean(!messageInput.trim())}><SendIcon /></IconButton>
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
