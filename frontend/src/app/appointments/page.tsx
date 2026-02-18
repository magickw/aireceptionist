'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Container, Typography, Box, Card, CardContent, Grid, Chip,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, IconButton, LinearProgress, TextField, InputAdornment,
  FormControl, InputLabel, Select, MenuItem, Dialog, DialogTitle,
  DialogContent, DialogActions, Button, Tooltip, Alert, Snackbar,
  SelectChangeEvent,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import CancelIcon from '@mui/icons-material/Cancel';
import EventIcon from '@mui/icons-material/Event';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import EventBusyIcon from '@mui/icons-material/EventBusy';
import ScheduleIcon from '@mui/icons-material/Schedule';
import PersonIcon from '@mui/icons-material/Person';
import api from '@/services/api';
import { format, parseISO } from 'date-fns';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Appointment {
  id: number;
  business_id: number;
  customer_name: string;
  customer_phone: string;
  service_type: string;
  appointment_time: string;
  status: string;
  created_at?: string;
}

interface AppointmentFormData {
  customer_name: string;
  customer_phone: string;
  service_type: string;
  appointment_time: string;
  status: string;
}

interface AppointmentStats {
  total: number;
  scheduled: number;
  completed: number;
  cancelled: number;
}

const EMPTY_FORM: AppointmentFormData = {
  customer_name: '',
  customer_phone: '',
  service_type: '',
  appointment_time: '',
  status: 'scheduled',
};

const STATUS_OPTIONS = [
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'no_show', label: 'No Show' },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getStatusChipColor(status: string): 'primary' | 'success' | 'error' | 'warning' | 'default' {
  switch (status.toLowerCase()) {
    case 'scheduled':
      return 'primary';
    case 'completed':
      return 'success';
    case 'cancelled':
      return 'error';
    case 'no_show':
      return 'warning';
    default:
      return 'default';
  }
}

function formatStatusLabel(status: string): string {
  return status
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function formatAppointmentTime(iso: string): string {
  try {
    return format(parseISO(iso), 'MMM d, yyyy h:mm a');
  } catch {
    return iso;
  }
}

/** Convert an ISO datetime string to a value suitable for datetime-local input. */
function toDatetimeLocalValue(iso: string): string {
  try {
    return format(parseISO(iso), "yyyy-MM-dd'T'HH:mm");
  } catch {
    return '';
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function AppointmentsPage() {
  // Data state
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [businessId, setBusinessId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Dialog state
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editingAppointment, setEditingAppointment] = useState<Appointment | null>(null);
  const [formData, setFormData] = useState<AppointmentFormData>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

  // Feedback state
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  // ---------- Data fetching ----------

  const fetchAppointments = useCallback(async () => {
    setLoading(true);
    try {
      const businessRes = await api.get('/businesses');
      if (businessRes.data.length > 0) {
        const bId = businessRes.data[0].id;
        setBusinessId(bId);
        const appointmentsRes = await api.get(`/appointments/business/${bId}`);
        setAppointments(appointmentsRes.data);
      }
    } catch (error) {
      console.error('Failed to fetch appointments', error);
      showSnackbar('Failed to load appointments.', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAppointments();
  }, [fetchAppointments]);

  // ---------- Derived / computed ----------

  const stats: AppointmentStats = useMemo(() => {
    const total = appointments.length;
    const scheduled = appointments.filter((a) => a.status.toLowerCase() === 'scheduled').length;
    const completed = appointments.filter((a) => a.status.toLowerCase() === 'completed').length;
    const cancelled = appointments.filter((a) => a.status.toLowerCase() === 'cancelled').length;
    return { total, scheduled, completed, cancelled };
  }, [appointments]);

  const filteredAppointments = useMemo(() => {
    let filtered = [...appointments];

    if (statusFilter !== 'all') {
      filtered = filtered.filter((a) => a.status.toLowerCase() === statusFilter);
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (a) =>
          a.customer_name.toLowerCase().includes(query) ||
          a.customer_phone.toLowerCase().includes(query) ||
          a.service_type.toLowerCase().includes(query),
      );
    }

    return filtered;
  }, [appointments, statusFilter, searchQuery]);

  // ---------- Snackbar helper ----------

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  // ---------- Form helpers ----------

  const handleTextFieldChange = (field: keyof AppointmentFormData) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleSelectChange = (field: keyof AppointmentFormData) => (e: SelectChangeEvent<string>) => {
    setFormData((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const isFormValid = (): boolean => {
    return (
      formData.customer_name.trim() !== '' &&
      formData.customer_phone.trim() !== '' &&
      formData.service_type.trim() !== '' &&
      formData.appointment_time !== '' &&
      formData.status !== ''
    );
  };

  // ---------- Create ----------

  const openCreateDialog = () => {
    setFormData(EMPTY_FORM);
    setCreateOpen(true);
  };

  const handleCreate = async () => {
    if (!businessId || !isFormValid()) return;
    setSubmitting(true);
    try {
      await api.post('/appointments/', {
        business_id: businessId,
        customer_name: formData.customer_name,
        customer_phone: formData.customer_phone,
        service_type: formData.service_type,
        appointment_time: formData.appointment_time,
        status: formData.status,
      });
      setCreateOpen(false);
      showSnackbar('Appointment created successfully.', 'success');
      await fetchAppointments();
    } catch (error) {
      console.error('Failed to create appointment', error);
      showSnackbar('Failed to create appointment.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  // ---------- Edit ----------

  const openEditDialog = (appointment: Appointment) => {
    setEditingAppointment(appointment);
    setFormData({
      customer_name: appointment.customer_name,
      customer_phone: appointment.customer_phone,
      service_type: appointment.service_type,
      appointment_time: toDatetimeLocalValue(appointment.appointment_time),
      status: appointment.status.toLowerCase(),
    });
    setEditOpen(true);
  };

  const handleEdit = async () => {
    if (!editingAppointment || !isFormValid()) return;
    setSubmitting(true);
    try {
      await api.put(`/appointments/${editingAppointment.id}`, {
        customer_name: formData.customer_name,
        customer_phone: formData.customer_phone,
        service_type: formData.service_type,
        appointment_time: formData.appointment_time,
        status: formData.status,
      });
      setEditOpen(false);
      setEditingAppointment(null);
      showSnackbar('Appointment updated successfully.', 'success');
      await fetchAppointments();
    } catch (error) {
      console.error('Failed to update appointment', error);
      showSnackbar('Failed to update appointment.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  // ---------- Cancel ----------

  const handleCancel = async (appointment: Appointment) => {
    setSubmitting(true);
    try {
      await api.put(`/appointments/${appointment.id}`, {
        customer_name: appointment.customer_name,
        customer_phone: appointment.customer_phone,
        service_type: appointment.service_type,
        appointment_time: appointment.appointment_time,
        status: 'cancelled',
      });
      showSnackbar('Appointment cancelled.', 'success');
      await fetchAppointments();
    } catch (error) {
      console.error('Failed to cancel appointment', error);
      showSnackbar('Failed to cancel appointment.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  // ---------- Render: Loading ----------

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <LinearProgress />
      </Container>
    );
  }

  // ---------- Render: Page ----------

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold">
            Appointments
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage and track all customer appointments.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button startIcon={<RefreshIcon />} onClick={fetchAppointments} variant="outlined">
            Refresh
          </Button>
          <Button startIcon={<AddIcon />} onClick={openCreateDialog} variant="contained">
            New Appointment
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
                <EventIcon color="action" />
              </Box>
              <Typography variant="h4" fontWeight="bold">
                {stats.total}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
                <ScheduleIcon color="primary" />
              </Box>
              <Typography variant="h4" fontWeight="bold" color="primary.main">
                {stats.scheduled}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Scheduled
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
                <CheckCircleIcon color="success" />
              </Box>
              <Typography variant="h4" fontWeight="bold" color="success.main">
                {stats.completed}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Completed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
                <EventBusyIcon color="error" />
              </Box>
              <Typography variant="h4" fontWeight="bold" color="error.main">
                {stats.cancelled}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Cancelled
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Search and Filter Bar */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <TextField
          placeholder="Search by customer name, phone, or service..."
          size="small"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ flexGrow: 1, minWidth: 250, maxWidth: 450 }}
        />
        <FormControl size="small" sx={{ minWidth: 170 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={statusFilter}
            label="Status"
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <MenuItem value="all">All Statuses</MenuItem>
            <MenuItem value="scheduled">Scheduled</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="cancelled">Cancelled</MenuItem>
            <MenuItem value="no_show">No Show</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Appointments Table */}
      <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
        <Table>
          <TableHead sx={{ bgcolor: '#f8fafc' }}>
            <TableRow>
              <TableCell>Customer</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell>Service</TableCell>
              <TableCell>Date &amp; Time</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredAppointments.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
                    <EventIcon sx={{ fontSize: 48, color: 'text.disabled' }} />
                    <Typography color="text.secondary">
                      {appointments.length === 0
                        ? 'No appointments yet. Create your first one!'
                        : 'No appointments match your filters.'}
                    </Typography>
                  </Box>
                </TableCell>
              </TableRow>
            ) : (
              filteredAppointments.map((apt) => (
                <TableRow key={apt.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <PersonIcon fontSize="small" color="action" />
                      <Typography variant="body2" fontWeight={500}>
                        {apt.customer_name}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{apt.customer_phone}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{apt.service_type}</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{formatAppointmentTime(apt.appointment_time)}</Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={formatStatusLabel(apt.status)}
                      color={getStatusChipColor(apt.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title="Edit Appointment">
                      <IconButton size="small" color="primary" onClick={() => openEditDialog(apt)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    {apt.status.toLowerCase() !== 'cancelled' && (
                      <Tooltip title="Cancel Appointment">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleCancel(apt)}
                          disabled={submitting}
                        >
                          <CancelIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>New Appointment</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, pt: 1 }}>
            <TextField
              label="Customer Name"
              fullWidth
              required
              value={formData.customer_name}
              onChange={handleTextFieldChange('customer_name')}
              placeholder="John Doe"
            />
            <TextField
              label="Customer Phone"
              fullWidth
              required
              value={formData.customer_phone}
              onChange={handleTextFieldChange('customer_phone')}
              placeholder="+1 (555) 123-4567"
            />
            <TextField
              label="Service Type"
              fullWidth
              required
              value={formData.service_type}
              onChange={handleTextFieldChange('service_type')}
              placeholder="e.g. Haircut, Consultation, Checkup"
            />
            <TextField
              label="Appointment Time"
              type="datetime-local"
              fullWidth
              required
              value={formData.appointment_time}
              onChange={handleTextFieldChange('appointment_time')}
              InputLabelProps={{ shrink: true }}
            />
            <FormControl fullWidth required>
              <InputLabel>Status</InputLabel>
              <Select
                value={formData.status}
                label="Status"
                onChange={handleSelectChange('status')}
              >
                {STATUS_OPTIONS.map((opt) => (
                  <MenuItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setCreateOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            variant="contained"
            disabled={submitting || !isFormValid()}
          >
            {submitting ? 'Creating...' : 'Create Appointment'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editOpen} onClose={() => setEditOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Appointment</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, pt: 1 }}>
            <TextField
              label="Customer Name"
              fullWidth
              required
              value={formData.customer_name}
              onChange={handleTextFieldChange('customer_name')}
            />
            <TextField
              label="Customer Phone"
              fullWidth
              required
              value={formData.customer_phone}
              onChange={handleTextFieldChange('customer_phone')}
            />
            <TextField
              label="Service Type"
              fullWidth
              required
              value={formData.service_type}
              onChange={handleTextFieldChange('service_type')}
            />
            <TextField
              label="Appointment Time"
              type="datetime-local"
              fullWidth
              required
              value={formData.appointment_time}
              onChange={handleTextFieldChange('appointment_time')}
              InputLabelProps={{ shrink: true }}
            />
            <FormControl fullWidth required>
              <InputLabel>Status</InputLabel>
              <Select
                value={formData.status}
                label="Status"
                onChange={handleSelectChange('status')}
              >
                {STATUS_OPTIONS.map((opt) => (
                  <MenuItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setEditOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button
            onClick={handleEdit}
            variant="contained"
            disabled={submitting || !isFormValid()}
          >
            {submitting ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar Feedback */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
          severity={snackbar.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}
