'use client';
import React, { useState, useEffect, useCallback } from 'react';
import {
  Container, Typography, Box, Paper, Button, TextField, Dialog, DialogActions, DialogContent, DialogTitle,
  CircularProgress, Alert, IconButton, Grid, Chip
} from '@mui/material';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { StaticDatePicker } from '@mui/x-date-pickers/StaticDatePicker';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import dayjs, { Dayjs } from 'dayjs';
import api from '@/services/api';
import DeleteIcon from '@mui/icons-material/Delete';
import { useAuth } from '@/context/AuthContext'; // Assuming AuthContext provides user/business info

interface Appointment {
  id: number;
  customer_name: string;
  customer_phone: string;
  appointment_time: string; // Use string for API interaction, convert to Dayjs for UI
  service_type?: string;
  status: string;
  business_id: number;
  source: string;
}

interface AvailableSlot {
  start: string;
  end: string;
  display: string;
}

export default function BuiltInCalendarPage() {
  const { user } = useAuth(); // Get user from auth context
  const businessId = user?.business_id || 1; // Use user's business ID, fallback to 1

  const [selectedDate, setSelectedDate] = useState<Dayjs | null>(dayjs());
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [availableSlots, setAvailableSlots] = useState<AvailableSlot[]>([]);
  const [openAddEditDialog, setOpenAddEditDialog] = useState(false);
  const [currentAppointment, setCurrentAppointment] = useState<Appointment | null>(null);
  const [formValues, setFormValues] = useState({
    customer_name: '',
    customer_phone: '',
    appointment_time: dayjs(),
    service_type: '',
    status: 'scheduled',
    business_id: businessId,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAppointments = useCallback(async () => {
    if (!selectedDate || !businessId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/calendar/builtin/appointments?business_id=${businessId}`);
      // Filter appointments for the selected date
      const filteredAppointments = response.data.filter((app: Appointment) =>
        dayjs(app.appointment_time).isSame(selectedDate, 'day')
      );
      setAppointments(filteredAppointments);
    } catch (err: any) {
      console.error('Failed to fetch appointments:', err);
      setError('Failed to load appointments.');
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
    fetchAppointments();
    fetchAvailableSlots();
  }, [fetchAppointments, fetchAvailableSlots]);

  const handleDateChange = (newDate: Dayjs | null) => {
    setSelectedDate(newDate);
  };

  const handleOpenAddDialog = (slotTime?: Dayjs) => {
    setCurrentAppointment(null);
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

  const handleOpenEditDialog = (appointment: Appointment) => {
    setCurrentAppointment(appointment);
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

  const handleCloseAddEditDialog = () => {
    setOpenAddEditDialog(false);
    setError(null);
  };

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormValues(prev => ({ ...prev, [name]: value }));
  };

  const handleAppointmentTimeChange = (newValue: Dayjs | null) => {
    setFormValues(prev => ({ ...prev, appointment_time: newValue || dayjs() }));
  };

  const handleSaveAppointment = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        ...formValues,
        appointment_time: formValues.appointment_time.toISOString(), // Send ISO string to API
      };

      if (currentAppointment) {
        await api.put(`/calendar/builtin/appointments/${currentAppointment.id}`, payload);
      } else {
        await api.post('/calendar/builtin/appointments', payload);
      }
      handleCloseAddEditDialog();
      fetchAppointments(); // Refresh list
      fetchAvailableSlots(); // Refresh available slots as well
    } catch (err: any) {
      console.error('Failed to save appointment:', err);
      setError(err.response?.data?.detail || 'Failed to save appointment.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAppointment = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this appointment?')) return;
    setLoading(true);
    setError(null);
    try {
      await api.delete(`/calendar/builtin/appointments/${id}`);
      fetchAppointments(); // Refresh list
      fetchAvailableSlots(); // Refresh available slots as well
    } catch (err: any) {
      console.error('Failed to delete appointment:', err);
      setError(err.response?.data?.detail || 'Failed to delete appointment.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>Built-in Calendar</Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Box sx={{ display: 'flex', gap: 3, flexDirection: { xs: 'column', md: 'row' } }}>
        <Paper elevation={3} sx={{ flex: 1, p: 3 }}>
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <StaticDatePicker<Dayjs>
              displayStaticWrapperAs="desktop"
              value={selectedDate}
              onChange={handleDateChange}
              slotProps={{
                day: {
                  sx: (theme) => ({
                    '&.Mui-selected': {
                      backgroundColor: theme.palette.primary.main,
                      color: theme.palette.primary.contrastText,
                    },
                  }),
                },
              }}
            />
          </LocalizationProvider>
        </Paper>

        <Paper elevation={3} sx={{ flex: 2, p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h5">Appointments for {selectedDate?.format('MMMM DD, YYYY')}</Typography>
            <Button variant="contained" onClick={() => handleOpenAddDialog()}>Add Appointment</Button>
          </Box>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>
          ) : (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" sx={{ mb: 1 }}>Scheduled Appointments</Typography>
                {appointments.length === 0 ? (
                  <Typography>No appointments scheduled.</Typography>
                ) : (
                  <Box>
                    {appointments.map((appointment) => (
                      <Paper key={appointment.id} sx={{ p: 2, mb: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box>
                          <Typography variant="subtitle1">{appointment.customer_name} - {appointment.service_type}</Typography>
                          <Typography variant="body2" color="textSecondary">
                            {dayjs(appointment.appointment_time).format('hh:mm A')} - {appointment.customer_phone}
                          </Typography>
                        </Box>
                        <Box>
                          <Button size="small" onClick={() => handleOpenEditDialog(appointment)} sx={{ mr: 1 }}>Edit</Button>
                          <IconButton size="small" color="error" onClick={() => handleDeleteAppointment(appointment.id)}>
                            <DeleteIcon />
                          </IconButton>
                        </Box>
                      </Paper>
                    ))}
                  </Box>
                )}
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" sx={{ mb: 1 }}>Available Slots</Typography>
                {availableSlots.length === 0 ? (
                  <Typography>No available slots.</Typography>
                ) : (
                  <Grid container spacing={1}>
                    {availableSlots.map((slot, index) => (
                      <Grid item key={index}>
                        <Chip
                          label={slot.display}
                          clickable
                          color="primary"
                          variant="outlined"
                          onClick={() => handleOpenAddDialog(dayjs(slot.start))}
                        />
                      </Grid>
                    ))}
                  </Grid>
                )}
              </Grid>
            </Grid>
          )}
        </Paper>
      </Box>

      <Dialog open={openAddEditDialog} onClose={handleCloseAddEditDialog}>
        <DialogTitle>{currentAppointment ? 'Edit Appointment' : 'Add New Appointment'}</DialogTitle>
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
            onChange={handleFormChange}
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
            onChange={handleFormChange}
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
            onChange={handleFormChange}
            sx={{ mb: 2 }}
          />
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DateTimePicker
              label="Appointment Time"
              value={formValues.appointment_time}
              onChange={handleAppointmentTimeChange}
              renderInput={(params) => <TextField {...params} fullWidth variant="standard" sx={{ mb: 2 }} />}
            />
          </LocalizationProvider>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseAddEditDialog} disabled={loading}>Cancel</Button>
          <Button onClick={handleSaveAppointment} disabled={loading}>{loading ? <CircularProgress size={24} /> : (currentAppointment ? 'Update' : 'Add')}</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}