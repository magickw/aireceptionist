'use client';
import * as React from 'react';
import { useState, useEffect, useRef } from 'react';
import { Container, Typography, Box, Grid, Card, CardHeader, CardContent, TextField, IconButton, Button, List, ListItem, Paper } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AgentThoughts from '@/components/AgentThoughts';
import { getWebSocketUrl } from '@/services/api'; // Use the centralized WS function

export default function CallSimulator() {
  const [currentCall, setCurrentCall] = useState<any>(null);
  const [messageInput, setMessageInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [thoughts, setThoughts] = useState<any[]>([]);
  const [reasoningData, setReasoningData] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // This effect runs only when the component mounts and is the single source of truth for the WebSocket connection.
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
        } else if (data.type === 'agent_response') {
          setIsProcessing(false);
          addMessage(data.text, 'ai');
          if (data.reasoning) setReasoningData(data.reasoning);
        }
      };
    };
    
    // The previous implementation tried to connect on the server, which is not possible for WebSockets.
    // This check ensures we only connect when running in the browser.
    if (typeof window !== 'undefined') {
        connect();
    }

    return () => {
      wsRef.current?.close();
    };
  }, []);

  const addMessage = (content: string, sender: 'customer' | 'ai') => {
    const message = { id: Date.now(), sender, content };
    setCurrentCall((prev: any) => ({ ...prev, messages: [...(prev?.messages || []), message] }));
  };

  const startCall = () => {
    setCurrentCall({ messages: [] });
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

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" sx={{ mb: 4 }}>AI Call Simulator</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
            <CardHeader title={currentCall ? "Call in Progress" : "Ready to Start"} action={!currentCall && <Button onClick={startCall}>Start Call</Button>} />
            <CardContent sx={{ flexGrow: 1, overflowY: 'auto' }}>
              <List>
                {currentCall?.messages.map((m: any) => (
                  <ListItem key={m.id} sx={{ justifyContent: m.sender === 'ai' ? 'flex-start' : 'flex-end' }}>
                    <Paper sx={{ p: 1.5, bgcolor: m.sender === 'ai' ? '#f1f5f9' : 'primary.main', color: m.sender === 'ai' ? 'inherit' : 'white' }}>{m.content}</Paper>
                  </ListItem>
                ))}
              </List>
            </CardContent>
            {currentCall && (
              <Box sx={{ p: 2, display: 'flex' }} component="form" onSubmit={(e) => { e.preventDefault(); sendMessage(); }}>
                <TextField fullWidth value={messageInput} onChange={(e) => setMessageInput(e.target.value)} placeholder="Type message..." />
                <IconButton type="submit"><SendIcon /></IconButton>
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
    </Container>
  );
}
