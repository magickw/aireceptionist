'use client';
import * as React from 'react';
import { useState, useEffect, useRef } from 'react';
import { Container, Typography, Box, Grid, Card, CardHeader, CardContent, TextField, IconButton, Button, List, ListItem, Paper } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AgentThoughts from '@/components/AgentThoughts';
import VoiceVisualizer from '@/components/VoiceVisualizer';
import { getWebSocketUrl } from '@/services/api';

export default function CallSimulator() {
  const [currentCall, setCurrentCall] = useState<any>(null);
  const [messageInput, setMessageInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [thoughts, setThoughts] = useState<any[]>([]);
  const [reasoningData, setReasoningData] = useState<any>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const connect = () => {
      console.log('🔌 Connecting to WebSocket:', getWebSocketUrl().replace(/\?token=.*$/, '?token=REDACTED'));
      const ws = new WebSocket(getWebSocketUrl());
      wsRef.current = ws;

      ws.onopen = () => console.log('🔌 WebSocket connection established');
      ws.onclose = () => console.log('🔌 WebSocket connection closed');
      ws.onerror = (err) => console.error('WebSocket error:', err);

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'thought') {
          setThoughts(prev => [...prev, { step: data.step, message: data.message, timestamp: new Date() }]);
        } else if (data.type === 'text_chunk') {
          // Handle streaming text chunks
          setStreamingText(prev => prev + data.chunk);
          setIsSpeaking(true);
          
          // If this is the last chunk, finalize the message
          if (data.is_last) {
            setIsProcessing(false);
            setIsSpeaking(false);
            addMessage(data.full_text || streamingText + data.chunk, 'ai');
            if (data.full_text) setStreamingText('');
          }
        } else if (data.type === 'agent_response') {
          // Handle complete response (backwards compatibility)
          setIsProcessing(false);
          setIsSpeaking(false);
          // Only add if not already added via streaming
          const currentMessages = currentCall?.messages || [];
          const lastMessage = currentMessages[currentMessages.length - 1];
          if (!lastMessage || lastMessage.sender !== 'ai' || lastMessage.content !== data.text) {
            addMessage(data.text, 'ai');
          }
          if (data.reasoning) setReasoningData(data.reasoning);
          setStreamingText('');
        }
      };
    };
    
    if (typeof window !== 'undefined') {
        connect();
    }

    return () => {
      wsRef.current?.close();
    };
  }, []);

  // Auto-scroll to bottom when messages change
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
    setTimeout(() => addMessage("Hello! How can I help you today?", 'ai'), 500);
  };
  
  const sendMessage = () => {
    if (!messageInput.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.error("Cannot send message, WebSocket is not open.");
        return;
    };
    addMessage(messageInput, 'customer');
    wsRef.current.send(JSON.stringify({ type: 'user_input', text: messageInput }));
    setMessageInput('');
    setIsProcessing(true);
  };

  const endCall = () => {
    setCurrentCall(null);
    setThoughts([]);
    setStreamingText('');
    setIsSpeaking(false);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'end_call' }));
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">AI Call Simulator</Typography>
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
      `}</style>
    </Container>
  );
}
