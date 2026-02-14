'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Button, TextField,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  Alert, CircularProgress, Grid, FormControl, InputLabel, Select, MenuItem
} from '@mui/material';
import { Add, Send, Sms, CheckCircle } from '@mui/icons-material';
import { smsApi } from '@/services/api';

interface SMSTemplate {
  id: number;
  name: string;
  event_type: string;
  content: string;
}

const EVENT_TYPES = [
  'call.missed', 'call.completed', 'appointment.confirmation',
  'appointment.reminder', 'appointment.cancelled', 'voicemail.received'
];

export default function SMSPage() {
  const [templates, setTemplates] = useState<SMSTemplate[]>([]);
  const [status, setStatus] = useState({ enabled: false, provider: '' });
  const [loading, setLoading] = useState(true);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [sendDialogOpen, setSendDialogOpen] = useState(false);
  const [templateForm, setTemplateForm] = useState({ name: '', event_type: '', content: '' });
  const [sendForm, setSendForm] = useState({ to_number: '', message: '', media_url: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [templatesRes, statusRes] = await Promise.all([smsApi.listTemplates(), smsApi.getStatus()]);
      setTemplates(templatesRes.data.templates || []);
      setStatus(statusRes.data);
    } catch (error) { console.error('Failed to fetch data', error); }
    finally { setLoading(false); }
  };

  const handleCreateTemplate = async () => {
    if (!templateForm.name || !templateForm.event_type || !templateForm.content) return;
    setSaving(true);
    try {
      await smsApi.createTemplate(templateForm);
      setTemplateDialogOpen(false);
      setTemplateForm({ name: '', event_type: '', content: '' });
      fetchData();
    } catch (error) { alert('Failed to create template'); }
    finally { setSaving(false); }
  };

  const handleSendSMS = async () => {
    if (!sendForm.to_number || !sendForm.message) return;
    setSaving(true);
    try {
      await smsApi.send(sendForm);
      setSendDialogOpen(false);
      setSendForm({ to_number: '', message: '', media_url: '' });
      alert('SMS sent successfully');
    } catch (error) { alert('Failed to send SMS'); }
    finally { setSaving(false); }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">SMS Notifications</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button variant="outlined" startIcon={<Send />} onClick={() => setSendDialogOpen(true)}>
            Send SMS
          </Button>
          <Button variant="contained" startIcon={<Add />} onClick={() => setTemplateDialogOpen(true)}>
            Add Template
          </Button>
        </Box>
      </Box>

      <Alert severity={status.enabled ? 'success' : 'warning'} sx={{ mb: 3 }} icon={status.enabled ? <CheckCircle /> : <Sms />}>
        Twilio is {status.enabled ? 'configured' : 'not configured'}. {status.provider}
      </Alert>

      {loading ? <CircularProgress /> : templates.length === 0 ? (
        <Alert severity="info">No SMS templates. Create one to automate notifications.</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Event Type</TableCell>
                <TableCell>Content</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {templates.map((template) => (
                <TableRow key={template.id}>
                  <TableCell>{template.name}</TableCell>
                  <TableCell><Chip label={template.event_type} size="small" /></TableCell>
                  <TableCell sx={{ maxWidth: 400 }}>{template.content}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={templateDialogOpen} onClose={() => setTemplateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add SMS Template</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Name" value={templateForm.name} onChange={(e) => setTemplateForm({ ...templateForm, name: e.target.value })} sx={{ mt: 2, mb: 2 }} />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Event Type</InputLabel>
            <Select value={templateForm.event_type} label="Event Type" onChange={(e) => setTemplateForm({ ...templateForm, event_type: e.target.value })}>
              {EVENT_TYPES.map((e) => <MenuItem key={e} value={e}>{e}</MenuItem>)}
            </Select>
          </FormControl>
          <TextField fullWidth multiline rows={3} label="Content" value={templateForm.content} onChange={(e) => setTemplateForm({ ...templateForm, content: e.target.value })} placeholder="Use {{customer_name}}, {{appointment_time}}, etc." />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTemplateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateTemplate} variant="contained" disabled={saving || !templateForm.name || !templateForm.event_type || !templateForm.content}>
            {saving ? <CircularProgress size={20} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={sendDialogOpen} onClose={() => setSendDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Send SMS</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="To Number" value={sendForm.to_number} onChange={(e) => setSendForm({ ...sendForm, to_number: e.target.value })} placeholder="+1234567890" sx={{ mt: 2, mb: 2 }} />
          <TextField fullWidth multiline rows={3} label="Message" value={sendForm.message} onChange={(e) => setSendForm({ ...sendForm, message: e.target.value })} sx={{ mb: 2 }} />
          <TextField fullWidth label="Media URL (optional)" value={sendForm.media_url} onChange={(e) => setSendForm({ ...sendForm, media_url: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSendDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSendSMS} variant="contained" disabled={saving || !sendForm.to_number || !sendForm.message}>
            {saving ? <CircularProgress size={20} /> : 'Send'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
