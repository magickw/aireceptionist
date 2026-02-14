'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Button, TextField,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, Alert, CircularProgress, IconButton, Dialog,
  DialogTitle, DialogContent, DialogActions
} from '@mui/material';
import { Add, Delete, Link as LinkIcon, CheckCircle, Error } from '@mui/icons-material';
import { webhooksApi } from '@/services/api';

interface Webhook {
  id: number;
  url: string;
  events: string[];
  status: string;
  created_at: string;
}

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({ url: '', events: ['call.completed'] });

  useEffect(() => { fetchWebhooks(); }, []);

  const fetchWebhooks = async () => {
    try {
      const res = await webhooksApi.list();
      setWebhooks(res.data.webhooks || []);
    } catch (error) { console.error('Failed to fetch webhooks', error); }
    finally { setLoading(false); }
  };

  const handleCreateWebhook = async () => {
    if (!formData.url) return;
    try {
      await webhooksApi.create({ ...formData, name: 'Webhook' });
      setDialogOpen(false);
      setFormData({ url: '', events: ['call.completed'] });
      fetchWebhooks();
    } catch (error) { alert('Failed to create webhook'); }
  };

  const handleDeleteWebhook = async (id: number) => {
    if (!confirm('Are you sure you want to delete this webhook?')) return;
    try {
      await webhooksApi.delete(id);
      fetchWebhooks();
    } catch (error) { alert('Failed to delete webhook'); }
  };

  const getStatusIcon = (status: string) => {
    return status === 'active' ? <CheckCircle color="success" /> : <Error color="error" />;
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>Webhooks</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure webhooks to receive real-time notifications about call events.
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6" color="primary">Webhook Configuration</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Webhooks allow your system to receive HTTP callbacks when specific events occur.
              </Typography>
            </Box>
            <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)}>
              Add Webhook
            </Button>
          </Box>
        </CardContent>
      </Card>

      {loading ? <CircularProgress /> : webhooks.length === 0 ? (
        <Alert severity="info">No webhooks configured. Add a webhook to start receiving notifications.</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>URL</TableCell>
                <TableCell>Events</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {webhooks.map((webhook) => (
                <TableRow key={webhook.id}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinkIcon fontSize="small" color="action" />
                      {webhook.url}
                    </Box>
                  </TableCell>
                  <TableCell>
                    {webhook.events.map((event, idx) => (
                      <Chip key={idx} label={event} size="small" sx={{ mr: 0.5 }} />
                    ))}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getStatusIcon(webhook.status)}
                      <Typography variant="body2">{webhook.status}</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{webhook.created_at ? new Date(webhook.created_at).toLocaleString() : '-'}</TableCell>
                  <TableCell>
                    <IconButton color="error" onClick={() => handleDeleteWebhook(webhook.id)}>
                      <Delete />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Webhook</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Webhook URL"
            placeholder="https://your-server.com/webhook"
            value={formData.url}
            onChange={(e) => setFormData({ ...formData, url: e.target.value })}
            sx={{ mt: 2 }}
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2, mb: 1 }}>
            Events to trigger webhook:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {['call.completed', 'call.missed', 'appointment.created', 'appointment.updated'].map((event) => (
              <Chip
                key={event}
                label={event}
                clickable
                color={formData.events.includes(event) ? 'primary' : 'default'}
                onClick={() => {
                  const newEvents = formData.events.includes(event)
                    ? formData.events.filter(e => e !== event)
                    : [...formData.events, event];
                  setFormData({ ...formData, events: newEvents });
                }}
              />
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateWebhook} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}