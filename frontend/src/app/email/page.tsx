'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Button, TextField,
  Grid, Alert, CircularProgress, Chip
} from '@mui/material';
import { Email, Send, CheckCircle } from '@mui/icons-material';
import { emailApi } from '@/services/api';

export default function EmailPage() {
  const [status, setStatus] = useState({ enabled: false, provider: '' });
  const [loading, setLoading] = useState(true);
  const [sendDialogOpen, setSendDialogOpen] = useState(false);
  const [formData, setFormData] = useState({ to_email: '', subject: '', body: '' });
  const [sending, setSending] = useState(false);

  useEffect(() => { fetchStatus(); }, []);

  const fetchStatus = async () => {
    try {
      const res = await emailApi.getStatus();
      setStatus(res.data);
    } catch (error) { console.error('Failed to fetch status', error); }
    finally { setLoading(false); }
  };

  const handleSend = async () => {
    if (!formData.to_email || !formData.subject || !formData.body) return;
    setSending(true);
    try {
      await emailApi.send(formData);
      alert('Email sent successfully');
      setSendDialogOpen(false);
      setFormData({ to_email: '', subject: '', body: '' });
    } catch (error) { alert('Failed to send email'); }
    finally { setSending(false); }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Email Notifications</Typography>
        <Button variant="contained" startIcon={<Send />} onClick={() => setSendDialogOpen(true)}>
          Send Email
        </Button>
      </Box>

      <Alert severity={status.enabled ? 'success' : 'warning'} sx={{ mb: 3 }} icon={status.enabled ? <CheckCircle /> : <Email />}>
        SMTP is {status.enabled ? 'configured' : 'not configured'}. {status.provider}
      </Alert>

      {!status.enabled && (
        <Alert severity="info" sx={{ mb: 3 }}>
          To enable email notifications, configure SMTP in your environment variables:
          <br />SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary">Call Notifications</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Receive email notifications for incoming calls with summaries.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary">Appointment Reminders</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Automated email reminders for upcoming appointments.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary">Voicemail Alerts</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Instant email alerts when new voicemails are received.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {sendDialogOpen && (
        <Box sx={{ mt: 4, p: 3, bgcolor: 'background.paper', borderRadius: 1 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>Send Email</Typography>
          <TextField fullWidth label="To Email" value={formData.to_email} onChange={(e) => setFormData({ ...formData, to_email: e.target.value })} sx={{ mb: 2 }} />
          <TextField fullWidth label="Subject" value={formData.subject} onChange={(e) => setFormData({ ...formData, subject: e.target.value })} sx={{ mb: 2 }} />
          <TextField fullWidth multiline rows={4} label="Body" value={formData.body} onChange={(e) => setFormData({ ...formData, body: e.target.value })} sx={{ mb: 2 }} />
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button onClick={() => setSendDialogOpen(false)}>Cancel</Button>
            <Button variant="contained" onClick={handleSend} disabled={sending}>
              {sending ? <CircularProgress size={20} /> : 'Send'}
            </Button>
          </Box>
        </Box>
      )}
    </Container>
  );
}
