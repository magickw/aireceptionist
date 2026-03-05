'use client';

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  TextField,
  Button,
  Stack,
  Divider,
  Tooltip,
  Paper,
} from '@mui/material';
import PhoneIcon from '@mui/icons-material/Phone';
import PhoneDisabledIcon from '@mui/icons-material/PhoneDisabled';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import CampaignIcon from '@mui/icons-material/Campaign';

interface ActiveSession {
  session_id: string;
  business_id: number;
  customer_phone?: string;
  customer_name?: string;
  started_at?: string;
  status?: string;
}

interface LiveCallPanelProps {
  activeSessions: Record<string, ActiveSession>;
  liveTranscripts: Record<string, string[]>;
  isConnected: boolean;
  onWhisper: (sessionId: string, text: string) => void;
  onBargeIn: (sessionId: string, text: string) => void;
  onEndCall: (sessionId: string) => void;
}

export default function LiveCallPanel({
  activeSessions,
  liveTranscripts,
  isConnected,
  onWhisper,
  onBargeIn,
  onEndCall,
}: LiveCallPanelProps) {
  const [whisperText, setWhisperText] = useState<Record<string, string>>({});
  const [bargeInText, setBargeInText] = useState<Record<string, string>>({});

  const sessionEntries = Object.entries(activeSessions);

  if (sessionEntries.length === 0) {
    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
            <PhoneIcon color="action" />
            <Typography variant="h6">Live Calls</Typography>
            <Chip
              label={isConnected ? 'Connected' : 'Disconnected'}
              color={isConnected ? 'success' : 'error'}
              size="small"
            />
          </Stack>
          <Typography variant="body2" color="text.secondary">
            No active calls at this time.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
          <PhoneIcon color="success" />
          <Typography variant="h6">Live Calls ({sessionEntries.length})</Typography>
          <Chip
            label={isConnected ? 'Live' : 'Reconnecting...'}
            color={isConnected ? 'success' : 'warning'}
            size="small"
          />
        </Stack>

        {sessionEntries.map(([sessionId, session]) => {
          const transcript = liveTranscripts[sessionId] || [];
          return (
            <Paper key={sessionId} variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography variant="subtitle2">
                    {session.customer_name || session.customer_phone || 'Unknown'}
                  </Typography>
                  <Chip
                    label={session.status || 'active'}
                    color={session.status === 'active' ? 'success' : 'default'}
                    size="small"
                  />
                </Stack>
                <Tooltip title="End Call">
                  <IconButton
                    color="error"
                    size="small"
                    onClick={() => onEndCall(sessionId)}
                  >
                    <PhoneDisabledIcon />
                  </IconButton>
                </Tooltip>
              </Stack>

              {/* Live Transcript */}
              <Box
                sx={{
                  maxHeight: 200,
                  overflowY: 'auto',
                  bgcolor: 'grey.50',
                  borderRadius: 1,
                  p: 1,
                  mb: 1,
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                }}
              >
                {transcript.length === 0 ? (
                  <Typography variant="caption" color="text.secondary">
                    Waiting for conversation...
                  </Typography>
                ) : (
                  transcript.map((line, i) => (
                    <Typography
                      key={i}
                      variant="caption"
                      display="block"
                      sx={{
                        color: line.startsWith('AI:')
                          ? 'primary.main'
                          : line.startsWith('[Tool')
                          ? 'warning.main'
                          : 'text.primary',
                      }}
                    >
                      {line}
                    </Typography>
                  ))
                )}
              </Box>

              <Divider sx={{ my: 1 }} />

              {/* Supervisor Controls */}
              <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                <TextField
                  size="small"
                  placeholder="Whisper to AI..."
                  value={whisperText[sessionId] || ''}
                  onChange={(e) =>
                    setWhisperText((prev) => ({ ...prev, [sessionId]: e.target.value }))
                  }
                  sx={{ flex: 1 }}
                />
                <Tooltip title="Whisper (only AI hears)">
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<RecordVoiceOverIcon />}
                    onClick={() => {
                      if (whisperText[sessionId]) {
                        onWhisper(sessionId, whisperText[sessionId]);
                        setWhisperText((prev) => ({ ...prev, [sessionId]: '' }));
                      }
                    }}
                  >
                    Whisper
                  </Button>
                </Tooltip>
              </Stack>

              <Stack direction="row" spacing={1}>
                <TextField
                  size="small"
                  placeholder="Barge-in message..."
                  value={bargeInText[sessionId] || ''}
                  onChange={(e) =>
                    setBargeInText((prev) => ({ ...prev, [sessionId]: e.target.value }))
                  }
                  sx={{ flex: 1 }}
                />
                <Tooltip title="Barge-in (caller hears)">
                  <Button
                    variant="contained"
                    size="small"
                    color="warning"
                    startIcon={<CampaignIcon />}
                    onClick={() => {
                      if (bargeInText[sessionId]) {
                        onBargeIn(sessionId, bargeInText[sessionId]);
                        setBargeInText((prev) => ({ ...prev, [sessionId]: '' }));
                      }
                    }}
                  >
                    Barge In
                  </Button>
                </Tooltip>
              </Stack>
            </Paper>
          );
        })}
      </CardContent>
    </Card>
  );
}
