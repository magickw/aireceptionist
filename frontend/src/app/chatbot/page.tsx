'use client';
import * as React from 'react';
import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Button, TextField,
  Paper, Chip, Alert, CircularProgress, IconButton, Divider, List,
  ListItemButton, ListItemText, ListItemAvatar, Avatar, Tooltip,
} from '@mui/material';
import {
  Chat, Send, Add, Stop, SmartToy, Person, Info,
} from '@mui/icons-material';
import { chatbotApi } from '@/services/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ChatSession {
  id: number;
  customer_name: string | null;
  start_time: string | null;
  end_time: string | null;
  status: string;
}

interface ChatMessage {
  id: string;
  role: 'customer' | 'ai' | 'system';
  text: string;
  timestamp: Date;
  intent?: string;
  confidence?: number;
  sentiment?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const statusColor = (status: string): 'success' | 'error' | 'default' | 'warning' => {
  switch (status) {
    case 'active': return 'success';
    case 'completed': return 'default';
    case 'missed': return 'error';
    default: return 'default';
  }
};

const fmtTime = (iso: string | null): string => {
  if (!iso) return '-';
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
};

const fmtMessageTime = (d: Date): string =>
  d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });

let msgSeq = 0;
const nextMsgId = (): string => `msg-${Date.now()}-${++msgSeq}`;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ChatbotPage() {
  // Session list state
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);

  // Active chat state
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [activeStatus, setActiveStatus] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const [starting, setStarting] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // -----------------------------------------------------------------------
  // Fetch session history
  // -----------------------------------------------------------------------

  const fetchHistory = useCallback(async () => {
    try {
      setSessionsLoading(true);
      const res = await chatbotApi.getHistory(50);
      setSessions(res.data.sessions || []);
    } catch (err) {
      console.error('Failed to fetch chat history', err);
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  // -----------------------------------------------------------------------
  // Auto-scroll to bottom when messages change
  // -----------------------------------------------------------------------

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // -----------------------------------------------------------------------
  // Select an existing session
  // -----------------------------------------------------------------------

  const handleSelectSession = (session: ChatSession) => {
    setActiveSessionId(session.id);
    setActiveStatus(session.status);
    // For an existing session we only have metadata; we display a system
    // message indicating the session was loaded. A production version would
    // call a getMessages(sessionId) endpoint; for now we show the metadata.
    setMessages([
      {
        id: nextMsgId(),
        role: 'system',
        text: `Session #${session.id} loaded -- ${session.status === 'active' ? 'this session is still active.' : `session ended at ${fmtTime(session.end_time)}.`}`,
        timestamp: session.start_time ? new Date(session.start_time) : new Date(),
      },
    ]);
    setInputText('');
  };

  // -----------------------------------------------------------------------
  // Start a new chat session
  // -----------------------------------------------------------------------

  const handleNewChat = async () => {
    try {
      setStarting(true);
      const res = await chatbotApi.start({});
      const { session_id, greeting } = res.data;

      setActiveSessionId(session_id);
      setActiveStatus('active');
      setMessages([
        {
          id: nextMsgId(),
          role: 'ai',
          text: greeting ?? 'Hello! How can I help you today?',
          timestamp: new Date(),
        },
      ]);
      setInputText('');

      // Refresh session list so the new session appears
      fetchHistory();

      // Focus input after a short delay to allow render
      setTimeout(() => inputRef.current?.focus(), 150);
    } catch (err) {
      console.error('Failed to start chat session', err);
    } finally {
      setStarting(false);
    }
  };

  // -----------------------------------------------------------------------
  // Send a message
  // -----------------------------------------------------------------------

  const handleSend = async () => {
    const text = inputText.trim();
    if (!text || !activeSessionId || sending) return;

    const userMsg: ChatMessage = {
      id: nextMsgId(),
      role: 'customer',
      text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setSending(true);

    try {
      const res = await chatbotApi.sendMessage({
        session_id: activeSessionId,
        message: text,
      });
      const { response, intent, confidence, sentiment } = res.data;
      const aiMsg: ChatMessage = {
        id: nextMsgId(),
        role: 'ai',
        text: response,
        timestamp: new Date(),
        intent,
        confidence,
        sentiment,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error('Failed to send message', err);
      setMessages((prev) => [
        ...prev,
        { id: nextMsgId(), role: 'system', text: 'Failed to send message. Please try again.', timestamp: new Date() },
      ]);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  // -----------------------------------------------------------------------
  // End the active session
  // -----------------------------------------------------------------------

  const handleEndSession = async () => {
    if (!activeSessionId) return;
    try {
      await chatbotApi.endSession(activeSessionId);
      setActiveStatus('completed');
      setMessages((prev) => [
        ...prev,
        { id: nextMsgId(), role: 'system', text: 'Session ended.', timestamp: new Date() },
      ]);
      fetchHistory();
    } catch (err) {
      console.error('Failed to end session', err);
    }
  };

  // -----------------------------------------------------------------------
  // Key handler for Enter to send
  // -----------------------------------------------------------------------

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // -----------------------------------------------------------------------
  // Render helpers
  // -----------------------------------------------------------------------

  const renderMessageBubble = (msg: ChatMessage) => {
    if (msg.role === 'system') {
      return (
        <Box key={msg.id} sx={{ display: 'flex', justifyContent: 'center', my: 1 }}>
          <Typography variant="caption" sx={{ fontStyle: 'italic', color: 'text.secondary', bgcolor: 'grey.100', px: 2, py: 0.5, borderRadius: 2 }}>
            {msg.text}
          </Typography>
        </Box>
      );
    }

    const isCustomer = msg.role === 'customer';

    return (
      <Box
        key={msg.id}
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: isCustomer ? 'flex-end' : 'flex-start',
          my: 1,
          px: 1,
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: 1,
            flexDirection: isCustomer ? 'row-reverse' : 'row',
            maxWidth: '75%',
          }}
        >
          <Avatar
            sx={{
              width: 28,
              height: 28,
              bgcolor: isCustomer ? 'primary.main' : 'grey.400',
              flexShrink: 0,
            }}
          >
            {isCustomer ? <Person sx={{ fontSize: 16 }} /> : <SmartToy sx={{ fontSize: 16 }} />}
          </Avatar>

          <Paper
            elevation={0}
            sx={{
              px: 2,
              py: 1,
              borderRadius: 2,
              bgcolor: isCustomer ? 'primary.main' : 'grey.100',
              color: isCustomer ? 'primary.contrastText' : 'text.primary',
              wordBreak: 'break-word',
            }}
          >
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
              {msg.text}
            </Typography>
          </Paper>
        </Box>

        <Typography
          variant="caption"
          sx={{
            mt: 0.3,
            px: 5,
            color: 'text.disabled',
            fontSize: '0.65rem',
          }}
        >
          {fmtMessageTime(msg.timestamp)}
          {msg.intent && (
            <Tooltip title={`Intent: ${msg.intent} | Confidence: ${((msg.confidence ?? 0) * 100).toFixed(0)}%${msg.sentiment ? ` | Sentiment: ${msg.sentiment}` : ''}`}>
              <Info sx={{ fontSize: 12, ml: 0.5, verticalAlign: 'middle', cursor: 'pointer', color: 'text.disabled' }} />
            </Tooltip>
          )}
        </Typography>
      </Box>
    );
  };

  // -----------------------------------------------------------------------
  // JSX
  // -----------------------------------------------------------------------

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>Chat Sessions</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        View and manage web chat conversations with customers.
      </Typography>

      {/* Web Widget Info Card */}
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

      {/* Split-panel layout */}
      <Box sx={{ display: 'flex', gap: 2, height: 'calc(100vh - 340px)', minHeight: 480 }}>
        {/* ---- LEFT PANEL: Session list (40%) ---- */}
        <Paper
          variant="outlined"
          sx={{
            width: '40%',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: 1, borderColor: 'divider' }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              Session History
            </Typography>
            <Button
              variant="contained"
              size="small"
              startIcon={<Add />}
              onClick={handleNewChat}
              disabled={starting}
            >
              {starting ? 'Starting...' : 'New Chat'}
            </Button>
          </Box>

          {/* Session list */}
          <Box sx={{ flex: 1, overflow: 'auto' }}>
            {sessionsLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress size={28} />
              </Box>
            ) : sessions.length === 0 ? (
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <Chat sx={{ fontSize: 48, color: 'grey.300', mb: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  No chat sessions yet.
                </Typography>
                <Typography variant="caption" color="text.disabled">
                  Click "New Chat" to start a conversation.
                </Typography>
              </Box>
            ) : (
              <List disablePadding>
                {sessions.map((session) => (
                  <React.Fragment key={session.id}>
                    <ListItemButton
                      selected={activeSessionId === session.id}
                      onClick={() => handleSelectSession(session)}
                      sx={{ py: 1.5, px: 2 }}
                    >
                      <ListItemAvatar sx={{ minWidth: 40 }}>
                        <Avatar sx={{ width: 32, height: 32, bgcolor: activeSessionId === session.id ? 'primary.main' : 'grey.300' }}>
                          <Chat sx={{ fontSize: 16 }} />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body2" sx={{ fontWeight: 500, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {session.customer_name || 'Anonymous'}
                            </Typography>
                            <Chip label={session.status} color={statusColor(session.status)} size="small" sx={{ height: 20, fontSize: '0.65rem' }} />
                          </Box>
                        }
                        secondary={
                          <Typography variant="caption" color="text.secondary">
                            #{session.id} -- {fmtTime(session.start_time)}
                          </Typography>
                        }
                      />
                    </ListItemButton>
                    <Divider component="li" />
                  </React.Fragment>
                ))}
              </List>
            )}
          </Box>
        </Paper>

        {/* ---- RIGHT PANEL: Chat interface (60%) ---- */}
        <Paper
          variant="outlined"
          sx={{
            width: '60%',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {activeSessionId === null ? (
            /* Empty state */
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 4, color: 'text.secondary' }}>
              <SmartToy sx={{ fontSize: 64, color: 'grey.300', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">No conversation selected</Typography>
              <Typography variant="body2" color="text.disabled" sx={{ mt: 0.5 }}>
                Select a session from the list or start a new chat.
              </Typography>
              <Button variant="outlined" startIcon={<Add />} sx={{ mt: 3 }} onClick={handleNewChat} disabled={starting}>
                {starting ? 'Starting...' : 'New Chat'}
              </Button>
            </Box>
          ) : (
            <>
              {/* Chat header */}
              <Box
                sx={{
                  p: 1.5,
                  px: 2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  borderBottom: 1,
                  borderColor: 'divider',
                  bgcolor: 'grey.50',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    Session #{activeSessionId}
                  </Typography>
                  <Chip
                    label={activeStatus}
                    color={statusColor(activeStatus)}
                    size="small"
                    sx={{ height: 20, fontSize: '0.65rem' }}
                  />
                </Box>
                {activeStatus === 'active' && (
                  <Button
                    variant="outlined"
                    color="error"
                    size="small"
                    startIcon={<Stop />}
                    onClick={handleEndSession}
                  >
                    End Session
                  </Button>
                )}
              </Box>

              {/* Messages area */}
              <Box sx={{ flex: 1, overflow: 'auto', py: 2 }}>
                {messages.map(renderMessageBubble)}
                {sending && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 1 }}>
                    <Avatar sx={{ width: 28, height: 28, bgcolor: 'grey.400' }}>
                      <SmartToy sx={{ fontSize: 16 }} />
                    </Avatar>
                    <Paper elevation={0} sx={{ px: 2, py: 1, borderRadius: 2, bgcolor: 'grey.100' }}>
                      <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                        <CircularProgress size={14} />
                        <Typography variant="body2" color="text.secondary" sx={{ ml: 0.5 }}>
                          Typing...
                        </Typography>
                      </Box>
                    </Paper>
                  </Box>
                )}
                <div ref={messagesEndRef} />
              </Box>

              {/* Input area */}
              <Box
                sx={{
                  p: 1.5,
                  borderTop: 1,
                  borderColor: 'divider',
                  display: 'flex',
                  gap: 1,
                  alignItems: 'flex-end',
                  bgcolor: 'grey.50',
                }}
              >
                <TextField
                  inputRef={inputRef}
                  fullWidth
                  size="small"
                  multiline
                  maxRows={4}
                  placeholder={activeStatus === 'active' ? 'Type a message...' : 'Session has ended.'}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={activeStatus !== 'active' || sending}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                      bgcolor: 'background.paper',
                    },
                  }}
                />
                <IconButton
                  color="primary"
                  onClick={handleSend}
                  disabled={!inputText.trim() || activeStatus !== 'active' || sending}
                  sx={{
                    bgcolor: 'primary.main',
                    color: 'white',
                    '&:hover': { bgcolor: 'primary.dark' },
                    '&.Mui-disabled': { bgcolor: 'grey.200', color: 'grey.400' },
                    borderRadius: 2,
                    width: 40,
                    height: 40,
                  }}
                >
                  <Send sx={{ fontSize: 20 }} />
                </IconButton>
              </Box>
            </>
          )}
        </Paper>
      </Box>
    </Container>
  );
}
