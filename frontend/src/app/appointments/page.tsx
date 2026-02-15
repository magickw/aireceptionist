'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { Container, Typography, Box, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, LinearProgress, Chip } from '@mui/material';
import api from '@/services/api';
import { format } from 'date-fns';

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const businessRes = await api.get('/businesses');
        if (businessRes.data.length > 0) {
          const appointmentsRes = await api.get(`/appointments/business/${businessRes.data[0].id}`);
          setAppointments(appointmentsRes.data);
        }
      } catch (error) {
        console.error('Failed to fetch appointments', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const getStatusChipColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'scheduled': return 'primary';
      case 'completed': return 'success';
      case 'cancelled': return 'error';
      case 'no_show': return 'warning';
      default: return 'default';
    }
  };

  if (loading) return <Container sx={{p:4}}><LinearProgress /></Container>;

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>Appointments</Typography>
      <TableContainer component={Paper}><Table><TableHead><TableRow><TableCell>Customer</TableCell><TableCell>Service</TableCell><TableCell>Date</TableCell><TableCell>Status</TableCell></TableRow></TableHead>
      <TableBody>
        {appointments.map((apt) => (
          <TableRow key={apt.id}>
            <TableCell>{apt.customer_name}</TableCell>
            <TableCell>{apt.service_type}</TableCell>
            <TableCell>{format(new Date(apt.appointment_time), 'MMM d, yyyy h:mm a')}</TableCell>
            <TableCell>
              <Chip label={apt.status} color={getStatusChipColor(apt.status)} size="small" />
            </TableCell>
          </TableRow>
        ))}
      </TableBody></Table></TableContainer>
    </Container>
  );
}
