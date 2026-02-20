'use client';
import * as React from 'react';
import { useState, useEffect, useCallback } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Button, Grid,
  Alert, CircularProgress, Chip, IconButton, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, Paper, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, MenuItem,
  Tooltip
} from '@mui/material';
import { Add, Delete, CalendarMonth, Google, Microsoft, Edit, CloudDownload } from '@mui/icons-material';
import dynamic from 'next/dynamic'; // Import dynamic for date pickers in dialogs

// Dynamically import date-related components for dialogs as well
const LocalizationProvider = dynamic(() => import('@mui/x-date-pickers/LocalizationProvider').then(mod => mod.LocalizationProvider), { ssr: false });
const AdapterDayjs = dynamic(() => import('@mui/x-date-pickers/AdapterDayjs').then(mod => mod.AdapterDayjs), { ssr: false });
const DateTimePicker = dynamic(() => import('@mui/x-date-pickers/DateTimePicker').then(mod => mod.DateTimePicker), { ssr: false });


import dayjs, { Dayjs } from 'dayjs';
import api, { calendarApi } from '@/services/api';
import { useAuth } from '@/context/AuthContext'; // Assuming AuthContext provides user/business info

interface CalendarIntegration {
  id: number;
  provider: string;
  calendar_id: string;
  status: string;
  last_sync_at: string | null;
}

interface ExternalCalendarEvent {
  id: string;
  summary: string;
  description: string;
  start: string;
  end: string;
  attendees: string[];
  integration_id: number; // To link to its integration
}

interface BuiltInAppointment {
  id: number;
  customer_name: string;
  customer_phone: string;
  appointment_time: string; // ISO string
  service_type?: string;
  status: string;
  business_id: number;
  source: string; // "internal"
}

interface AvailableSlot {
  start: string;
  end: string;
  display: string;
}

export default function CalendarPage() {
  const { user } = useAuth();
  const businessId = user?.business_id || 1; // Fallback for now

  const [integrations, setIntegrations] = useState<CalendarIntegration[]>([]);
  const [externalEvents, setExternalEvents] = useState<ExternalCalendarEvent[]>([]);
  const [builtInAppointments, setBuiltInAppointments] = useState<BuiltInAppointment[]>([]);
  const [availableSlots, setAvailableSlots] = useState<AvailableSlot[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs());

  // Dialog for adding/editing built-in appointments
  const [openAddEditDialog, setOpenAddEditDialog] = useState(false);
  const [currentBuiltInAppointment, setCurrentBuiltInAppointment] = useState<BuiltInAppointment | null>(null);
  const [formValues, setFormValues] = useState({
    customer_name: '',
    customer_phone: '',
    appointment_time: dayjs(),
    service_type: '',
    status: 'scheduled',
    business_id: businessId,
  });

  // Dialog for creating external events
  const [externalEventDialogOpen, setExternalEventDialogOpen] = useState(false);
  const [externalEventFormData, setExternalEventFormData] = useState({ summary: '', description: '', start_time: '', end_time: '' });

  // Dialog for importing events
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [selectedIntegrationForImport, setSelectedIntegrationForImport] = useState<number | null>(null);
  const [importDateRange, setImportDateRange] = useState({ start: dayjs(), end: dayjs().add(1, 'month') });


  const fetchIntegrations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await calendarApi.list();
      setIntegrations(res.data.integrations || []);
    } catch (err: any) {
      console.error('Failed to fetch integrations', err);
      setError('Failed to load calendar integrations.');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchExternalEvents = useCallback(async () => {
    if (!selectedDate || integrations.length === 0) {
      setExternalEvents([]); // Clear external events if no integrations or no date
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const eventsPromises = integrations.map(async (integration) => {
        const res = await calendarApi.getEvents(integration.id, selectedDate.startOf('day').toISOString(), selectedDate.endOf('day').toISOString());
        return res.data.events ? res.data.events.map((event: any) => ({ ...event, integration_id: integration.id })) : [];
      });
      const allEvents = await Promise.all(eventsPromises);
      setExternalEvents(allEvents.flat());
    } catch (err: any) {
      console.error('Failed to fetch external events', err);
      setError('Failed to load external calendar events.');
    } finally {
      setLoading(false);
    }
  }, [selectedDate, integrations]);

  const fetchBuiltInAppointments = useCallback(async () => {
    if (!selectedDate || !businessId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/calendar/builtin/appointments?business_id=${businessId}`);
      const filteredAppointments = response.data.filter((app: BuiltInAppointment) =>
        dayjs(app.appointment_time).isSame(selectedDate, 'day')
      );
      setBuiltInAppointments(filteredAppointments);
    } catch (err: any) {
      console.error('Failed to fetch built-in appointments:', err);
      setError('Failed to load built-in appointments.');
    } finally {
      setLoading(false);
    }
  }, [selectedDate, businessId]);

  const fetchAvailableSlots = useCallback(async () => {
    if (!selectedDate || !businessId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/calendar/builtin/availability?business_id=${businessId}&date_str=${selectedDate.format('YYYY-MM-DD')}`);
      setAvailableSlots(response.data);
    } catch (err: any) {
      console.error('Failed to fetch available slots:', err);
      setError('Failed to load available slots.');
    } finally {
      setLoading(false);
    }
  }, [selectedDate, businessId]);


  useEffect(() => {
    fetchIntegrations();
  }, [fetchIntegrations]);

  useEffect(() => {
    if (integrations.length > 0 || !loading) {
      fetchExternalEvents();
    }
  }, [integrations, fetchExternalEvents, loading]);

  useEffect(() => {
    fetchBuiltInAppointments();
    fetchAvailableSlots();
  }, [selectedDate, fetchBuiltInAppointments, fetchAvailableSlots]);

  // Handlers for External Calendar Integrations
  const handleConnectGoogle = async () => {
    try {
      const res = await calendarApi.connectGoogle();
      window.location.href = res.data.auth_url;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initiate Google connection');
    }
  };

  const handleConnectMicrosoft = async () => {
    try {
      const res = await calendarApi.connectMicrosoft();
      window.location.href = res.data.auth_url;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initiate Microsoft connection');
    }
  };

  const handleCreateExternalEvent = async () => {
    if (integrations.length === 0) {
      setError('Please connect a calendar integration first.');
      return;
    }
    const firstIntegrationId = integrations[0].id; // Use the first active integration for simplicity
    if (!firstIntegrationId || !externalEventFormData.summary || !externalEventFormData.start_time || !externalEventFormData.end_time) return;

    setLoading(true);
    setError(null);
    try {
      await calendarApi.createEvent(firstIntegrationId, externalEventFormData);
      setExternalEventDialogOpen(false);
      setExternalEventFormData({ summary: '', description: '', start_time: '', end_time: '' });
      fetchExternalEvents(); // Refresh external events
    } catch (err: any) {
      console.error('Failed to create external event', err);
      setError(err.response?.data?.detail || 'Failed to create event in external calendar');
    } finally {
      setLoading(false);
    }
  };

  const handleImportEvents = async () => {
    if (!selectedIntegrationForImport) {
      setError('Please select an integration to import from.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.post(`/calendar/import-events?integration_id=${selectedIntegrationForImport}&start_date=${importDateRange.start.toISOString()}&end_date=${importDateRange.end.toISOString()}`);
      alert(`Import complete: ${response.data.imported_count} imported, ${response.data.failed_count} failed.`);
      setImportDialogOpen(false);
      fetchBuiltInAppointments(); // Refresh built-in appointments
      fetchAvailableSlots(); // Refresh available slots
    } catch (err: any) {
      console.error('Failed to import events:', err);
      setError(err.response?.data?.detail || 'Failed to import events.');
    } finally {
      setLoading(false);
    }
  };

  // Handlers for Built-in Appointments
  const handleDateChange = (newDate: Dayjs | null) => {
    if (newDate) setSelectedDate(newDate);
  };

  const handleOpenAddBuiltInDialog = (slotTime?: Dayjs) => {
    setCurrentBuiltInAppointment(null);
    setFormValues({
      customer_name: '',
      customer_phone: '',
      appointment_time: slotTime || (selectedDate ? selectedDate.hour(9).minute(0).second(0) : dayjs().hour(9).minute(0).second(0)),
      service_type: '',
      status: 'scheduled',
      business_id: businessId,
    });
    setOpenAddEditDialog(true);
  };

  const handleOpenEditBuiltInDialog = (appointment: BuiltInAppointment) => {
    setCurrentBuiltInAppointment(appointment);
    setFormValues({
      customer_name: appointment.customer_name,
      customer_phone: appointment.customer_phone,
      appointment_time: dayjs(appointment.appointment_time),
      service_type: appointment.service_type || '',
      status: appointment.status,
      business_id: appointment.business_id,
    });
    setOpenAddEditDialog(true);
  };

  const handleCloseAddEditBuiltInDialog = () => {
    setOpenAddEditDialog(false);
    setError(null);
  };

  const handleBuiltInFormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormValues(prev => ({ ...prev, [name]: value }));
  };

  const handleBuiltInAppointmentTimeChange = (newValue: Dayjs | null) => {
    setFormValues(prev => ({ ...prev, appointment_time: newValue || dayjs() }));
  };

  const handleSaveBuiltInAppointment = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        ...formValues,
        appointment_time: formValues.appointment_time.toISOString(),
      };

      if (currentBuiltInAppointment) {
        await api.put(`/calendar/builtin/appointments/${currentBuiltInAppointment.id}`, payload);
      } else {
        await api.post('/calendar/builtin/appointments', payload);
      }
      handleCloseAddEditBuiltInDialog();
      fetchBuiltInAppointments();
      fetchAvailableSlots();
    } catch (err: any) {
      console.error('Failed to save built-in appointment:', err);
      setError(err.response?.data?.detail || 'Failed to save appointment.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBuiltInAppointment = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this appointment?')) return;
    setLoading(true);
    setError(null);
    try {
      await api.delete(`/calendar/builtin/appointments/${id}`);
      fetchBuiltInAppointments();
      fetchAvailableSlots();
    } catch (err: any) {
      console.error('Failed to delete built-in appointment:', err);
      setError(err.response?.data?.detail || 'Failed to delete appointment.');
    } finally {
      setLoading(false);
    }
  };

  // Combine and sort all events for display
  const allEvents = React.useMemo(() => {
    const combined = [
      ...builtInAppointments.map(app => ({
        id: app.id,
        summary: `${app.customer_name} (${app.service_type || 'Appointment'})`,
        description: `Phone: ${app.customer_phone}`,
        start: app.appointment_time,
        end: dayjs(app.appointment_time).add(1, 'hour').toISOString(), // Assume 1hr duration
        attendees: [],
        type: 'Built-in',
        source: app.source,
        original: app, // Keep original object for editing
      })),
      ...externalEvents.map(event => ({
        id: event.id,
        summary: event.summary,
        description: event.description,
        start: event.start,
        end: event.end,
        attendees: event.attendees,
        type: 'External',
        source: integrations.find(int => int.id === event.integration_id)?.provider || 'Unknown',
        original: event,
      })),
    ];
    return combined.sort((a, b) => dayjs(a.start).diff(dayjs(b.start)));
  }, [builtInAppointments, externalEvents, integrations]);

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>Calendar Management</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Manage your built-in calendar and integrate with external providers.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Date Selector</Typography>
            {/* Direct usage of dynamically imported DateTimePicker for main date selector */}
            {typeof window !== 'undefined' && (
              <LocalizationProvider dateAdapter={AdapterDayjs}>
                <DateTimePicker
                  label="Select Date"
                  value={selectedDate}
                  onChange={handleDateChange}
                  renderInput={(params) => <TextField {...params} fullWidth />}
                  slotProps={{
                    actionBar: {
                      actions: ['clear', 'today'],
                    },
                  }}
                />
              </LocalizationProvider>
            )}

            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>Available Slots</Typography>
              {loading ? (
                <CircularProgress size={20} />
              ) : availableSlots.length === 0 ? (
                <Typography variant="body2">No available slots for this date.</Typography>
              ) : (
                <Grid container spacing={1}>
                  {availableSlots.map((slot, index) => (
                    <Grid item key={index}>
                      <Chip
                        label={slot.display}
                        clickable
                        color="primary"
                        variant="outlined"
                        onClick={() => handleOpenAddBuiltInDialog(dayjs(slot.start))}
                      />
                    </Grid>
                  ))}
                </Grid>
              )}
            </Box>

            <Box sx={{ mt: 4 }}>
              <Typography variant="h6" gutterBottom>External Integrations</Typography>
              <Grid container spacing={1} sx={{ mb: 2 }}>
                <Grid item xs={12}>
                  <Button variant="outlined" fullWidth onClick={handleConnectGoogle} startIcon={<Google />}>
                    Connect Google
                  </Button>
                </Grid>
                <Grid item xs={12}>
                  <Button variant="outlined" fullWidth onClick={handleConnectMicrosoft} startIcon={<Microsoft />}>
                    Connect Outlook
                  </Button>
                </Grid>
              </Grid>

              {integrations.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>Active Integrations:</Typography>
                  {integrations.map((int) => (
                    <Chip key={int.id} label={`${int.provider} (${int.status})`} size="small" sx={{ mr: 1, mb: 1 }} />
                  ))}
                  <Button variant="contained" fullWidth startIcon={<CloudDownload />} sx={{ mt: 2 }} onClick={() => setImportDialogOpen(true)}>
                    Import External Events
                  </Button>
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={8}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h5">All Appointments & Events ({selectedDate.format('MMMM DD, YYYY')})</Typography>
              <Box>
                <Button variant="contained" onClick={() => handleOpenAddBuiltInDialog()} startIcon={<Add />} sx={{ mr: 1 }}>
                  Add Built-in
                </Button>
                {integrations.length > 0 && (
                  <Button variant="contained" onClick={() => setExternalEventDialogOpen(true)} startIcon={<Add />}>
                    Add External
                  </Button>
                )}
              </Box>
            </Box>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>
            ) : allEvents.length === 0 ? (
              <Typography>No appointments or events scheduled for this date.</Typography>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Time</TableCell>
                      <TableCell>Summary</TableCell>
                      <TableCell>Source</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {allEvents.map((event: any) => (
                      <TableRow key={event.id}>
                        <TableCell>{dayjs(event.start).format('hh:mm A')}</TableCell>
                        <TableCell>
                          <Tooltip title={event.description}>
                            <span>{event.summary}</span>
                          </Tooltip>
                        </TableCell>
                        <TableCell>
                          <Chip label={event.source} size="small" />
                        </TableCell>
                        <TableCell>
                          {event.type === 'Built-in' && (
                            <>
                              <IconButton size="small" onClick={() => handleOpenEditBuiltInDialog(event.original)}>
                                <Edit fontSize="small" />
                              </IconButton>
                              <IconButton size="small" color="error" onClick={() => handleDeleteBuiltInAppointment(event.id)}>
                                <Delete fontSize="small" />
                              </IconButton>
                            </>
                          )}
                          {/* Add actions for external events if editable via API */}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Built-in Appointment Add/Edit Dialog */}
      <Dialog open={openAddEditDialog} onClose={handleCloseAddEditBuiltInDialog}>
        <DialogTitle>{currentBuiltInAppointment ? 'Edit Built-in Appointment' : 'Add New Built-in Appointment'}</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField
            autoFocus
            margin="dense"
            name="customer_name"
            label="Customer Name"
            type="text"
            fullWidth
            variant="standard"
            value={formValues.customer_name}
            onChange={handleBuiltInFormChange}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            name="customer_phone"
            label="Customer Phone"
            type="text"
            fullWidth
            variant="standard"
            value={formValues.customer_phone}
            onChange={handleBuiltInFormChange}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            name="service_type"
            label="Service Type"
            type="text"
            fullWidth
            variant="standard"
            value={formValues.service_type}
            onChange={handleBuiltInFormChange}
            sx={{ mb: 2 }}
          />
          {/* Direct import here as this is a client-side only form */}
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DateTimePicker
              label="Appointment Time"
              value={formValues.appointment_time}
              onChange={handleBuiltInAppointmentTimeChange}
              renderInput={(params) => <TextField {...params} fullWidth variant="standard" sx={{ mb: 2 }} />}
            />
          </LocalizationProvider>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseAddEditBuiltInDialog} disabled={loading}>Cancel</Button>
          <Button onClick={handleSaveBuiltInAppointment} disabled={loading}>{loading ? <CircularProgress size={24} /> : (currentBuiltInAppointment ? 'Update' : 'Add')}</Button>
        </DialogActions>
      </Dialog>

      {/* External Event Add Dialog */}
      <Dialog open={externalEventDialogOpen} onClose={() => setExternalEventDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add External Calendar Event</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField fullWidth label="Title" value={externalEventFormData.summary} onChange={(e) => setExternalEventFormData({ ...externalEventFormData, summary: e.target.value })} sx={{ mt: 2, mb: 2 }} />
          <TextField fullWidth label="Description" value={externalEventFormData.description} onChange={(e) => setExternalEventFormData({ ...externalEventFormData, description: e.target.value })} sx={{ mb: 2 }} />
          {/* Direct import here as this is a client-side only form */}
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DateTimePicker
              label="Start Time"
              value={dayjs(externalEventFormData.start_time)}
              onChange={(newValue) => setExternalEventFormData({ ...externalEventFormData, start_time: newValue ? newValue.toISOString() : '' })}
              renderInput={(params) => <TextField {...params} fullWidth sx={{ mb: 2 }} />}
            />
            <DateTimePicker
              label="End Time"
              value={dayjs(externalEventFormData.end_time)}
              onChange={(newValue) => setExternalEventFormData({ ...externalEventFormData, end_time: newValue ? newValue.toISOString() : '' })}
              renderInput={(params) => <TextField {...params} fullWidth />}
            />
          </LocalizationProvider>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExternalEventDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateExternalEvent} variant="contained" disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Create'}</Button>
        </DialogActions>
      </Dialog>

      {/* Import Events Dialog */}
      <Dialog open={importDialogOpen} onClose={() => setImportDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Import Events from External Calendar</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField
            select
            fullWidth
            label="Select Calendar Integration"
            value={selectedIntegrationForImport || ''}
            onChange={(e) => setSelectedIntegrationForImport(Number(e.target.value))}
            variant="standard"
            sx={{ mt: 2, mb: 2 }}
          >
            {integrations.map((integration) => (
              <MenuItem key={integration.id} value={integration.id}>
                {integration.provider} - {integration.calendar_id || 'Primary'} ({integration.status})
              </MenuItem>
            ))}
          </TextField>
          {/* Direct import here as this is a client-side only form */}
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DateTimePicker
              label="Import Start Date"
              value={importDateRange.start}
              onChange={(newValue) => setImportDateRange(prev => ({ ...prev, start: newValue || dayjs() }))}
              renderInput={(params) => <TextField {...params} fullWidth variant="standard" sx={{ mb: 2 }} />}
            />
            <DateTimePicker
              label="Import End Date"
              value={importDateRange.end}
              onChange={(newValue) => setImportDateRange(prev => ({ ...prev, end: newValue || dayjs() }))}
              renderInput={(params) => <TextField {...params} fullWidth variant="standard" />}
            />
          </LocalizationProvider>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleImportEvents} variant="contained" disabled={loading}>{loading ? <CircularProgress size={24} /> : 'Import'}</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}