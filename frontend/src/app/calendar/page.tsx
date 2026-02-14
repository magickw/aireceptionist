'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Button, Grid,
  Alert, CircularProgress, Chip, IconButton, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Paper, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField
} from '@mui/material';
import { Add, Delete, CalendarMonth, Google, Microsoft } from '@mui/icons-material';
import { calendarApi } from '@/services/api';

interface CalendarIntegration {
  id: number;
  provider: string;
  calendar_id: string;
  status: string;
  last_sync_at: string | null;
}

interface CalendarEvent {
  id: string;
  summary: string;
  description: string;
  start: string;
  end: string;
  attendees: string[];
}

export default function CalendarPage() {
  const [integrations, setIntegrations] = useState<CalendarIntegration[]>([]);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [eventDialogOpen, setEventDialogOpen] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<number | null>(null);
  const [formData, setFormData] = useState({ summary: '', description: '', start_time: '', end_time: '' });

  useEffect(() => { fetchIntegrations(); }, []);

  const fetchIntegrations = async () => {
    try {
      const res = await calendarApi.list();
      setIntegrations(res.data.integrations || []);
      if (res.data.integrations?.length > 0) {
        setSelectedIntegration(res.data.integrations[0].id);
        fetchEvents(res.data.integrations[0].id);
      }
    } catch (error) { console.error('Failed to fetch integrations', error); }
    finally { setLoading(false); }
  };

  const fetchEvents = async (integrationId: number) => {
    try {
      const res = await calendarApi.getEvents(integrationId);
      setEvents(res.data.events || []);
    } catch (error) { console.error('Failed to fetch events', error); }
  };

  const handleConnectGoogle = async () => {
    try {
      const res = await calendarApi.connectGoogle();
      window.location.href = res.data.auth_url;
    } catch (error) { alert('Failed to initiate Google connection'); }
  };

  const handleConnectMicrosoft = async () => {
    try {
      const res = await calendarApi.connectMicrosoft();
      window.location.href = res.data.auth_url;
    } catch (error) { alert('Failed to initiate Microsoft connection'); }
  };

  const handleCreateEvent = async () => {
    if (!selectedIntegration || !formData.summary || !formData.start_time || !formData.end_time) return;
    try {
      await calendarApi.createEvent(selectedIntegration, formData);
      setEventDialogOpen(false);
      setFormData({ summary: '', description: '', start_time: '', end_time: '' });
      fetchEvents(selectedIntegration);
    } catch (error) { alert('Failed to create event'); }
  };

  const handleIntegrationSelect = (id: number) => { setSelectedIntegration(id); fetchEvents(id); };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>Calendar Integrations</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Connect your calendar to sync appointments automatically.
      </Typography>

      {loading ? <CircularProgress /> : (
        <>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Google color="primary" />
                    <Typography variant="h6">Google Calendar</Typography>
                  </Box>
                  <Button variant="outlined" fullWidth onClick={handleConnectGoogle} startIcon={<Add />}>
                    Connect Google
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Microsoft color="primary" />
                    <Typography variant="h6">Outlook Calendar</Typography>
                  </Box>
                  <Button variant="outlined" fullWidth onClick={handleConnectMicrosoft} startIcon={<Add />}>
                    Connect Outlook
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {integrations.length > 0 ? (
            <>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Connected Calendars</Typography>
                <Button variant="contained" startIcon={<Add />} onClick={() => setEventDialogOpen(true)}>
                  Add Event
                </Button>
              </Box>
              <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
                {integrations.map((int) => (
                  <Chip key={int.id} label={`${int.provider} - ${int.status}`}
                    color={int.status === 'active' ? 'success' : 'default'}
                    onClick={() => handleIntegrationSelect(int.id)}
                    variant={selectedIntegration === int.id ? 'filled' : 'outlined'} />
                ))}
              </Box>

              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Event</TableCell>
                      <TableCell>Start</TableCell>
                      <TableCell>End</TableCell>
                      <TableCell>Attendees</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {events.length === 0 ? (
                      <TableRow><TableCell colSpan={4} align="center">No events found</TableCell></TableRow>
                    ) : events.map((event) => (
                      <TableRow key={event.id}>
                        <TableCell>{event.summary}</TableCell>
                        <TableCell>{event.start ? new Date(event.start).toLocaleString() : '-'}</TableCell>
                        <TableCell>{event.end ? new Date(event.end).toLocaleString() : '-'}</TableCell>
                        <TableCell>{event.attendees?.join(', ') || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          ) : (
            <Alert severity="info">No calendars connected. Connect a calendar to sync appointments.</Alert>
          )}
        </>
      )}

      <Dialog open={eventDialogOpen} onClose={() => setEventDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Calendar Event</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Title" value={formData.summary} onChange={(e) => setFormData({ ...formData, summary: e.target.value })} sx={{ mt: 2, mb: 2 }} />
          <TextField fullWidth label="Description" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} sx={{ mb: 2 }} />
          <TextField fullWidth type="datetime-local" label="Start Time" InputLabelProps={{ shrink: true }} value={formData.start_time} onChange={(e) => setFormData({ ...formData, start_time: e.target.value })} sx={{ mb: 2 }} />
          <TextField fullWidth type="datetime-local" label="End Time" InputLabelProps={{ shrink: true }} value={formData.end_time} onChange={(e) => setFormData({ ...formData, end_time: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEventDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateEvent} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
