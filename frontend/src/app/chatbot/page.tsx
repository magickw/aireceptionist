'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Button, TextField,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, Alert, CircularProgress
} from '@mui/material';
import { Chat, History, Send } from '@mui/icons-material';
import { chatbotApi } from '@/services/api';

interface ChatSession {
  id: number;
  customer_name: string | null;
  start_time: string | null;
  end_time: string | null;
  status: string;
}

export default function ChatbotPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchHistory(); }, []);

  const fetchHistory = async () => {
    try {
      const res = await chatbotApi.getHistory(20);
      setSessions(res.data.sessions || []);
    } catch (error) { console.error('Failed to fetch chat history', error); }
    finally { setLoading(false); }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'completed': return 'default';
      case 'missed': return 'error';
      default: return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>Chat Sessions</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        View and manage web chat conversations with customers.
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" color="primary">Web Chat Widget</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Integrate the chat widget into your website to enable customers to chat with your AI receptionist.
          </Typography>
          <Alert severity="info" sx={{ mt: 2 }}>
            Add this script to your website:
            <Box component="code" sx={{ display: 'block', mt: 1, p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
              {`<script src="${typeof window !== 'undefined' ? window.location.origin : ''}/chat-widget.js" data-business-id="YOUR_BUSINESS_ID"></script>`}
            </Box>
          </Alert>
        </CardContent>
      </Card>

      {loading ? <CircularProgress /> : sessions.length === 0 ? (
        <Alert severity="info">No chat sessions yet.</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Session ID</TableCell>
                <TableCell>Customer</TableCell>
                <TableCell>Start Time</TableCell>
                <TableCell>End Time</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sessions.map((session) => (
                <TableRow key={session.id}>
                  <TableCell>#{session.id}</TableCell>
                  <TableCell>{session.customer_name || 'Anonymous'}</TableCell>
                  <TableCell>{session.start_time ? new Date(session.start_time).toLocaleString() : '-'}</TableCell>
                  <TableCell>{session.end_time ? new Date(session.end_time).toLocaleString() : '-'}</TableCell>
                  <TableCell>
                    <Chip label={session.status} color={getStatusColor(session.status)} size="small" />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Container>
  );
}
