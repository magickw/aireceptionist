'use client';
import * as React from 'react';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import { useState, useEffect } from 'react';
import axios from 'axios';

interface Appointment {
  id: number;
  business_id: number;
  customer_name: string;
  customer_phone: string;
  appointment_time: string;
  service_type: string;
  status: string;
  created_at: string;
}

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [businessId, setBusinessId] = useState<number | null>(null);

  useEffect(() => {
    const fetchBusinessAndAppointments = async () => {
      try {
        // Fetch the first business (assuming for now, will be dynamic later)
        const businessResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/businesses`);
        if (businessResponse.data.length > 0) {
          const fetchedBusinessId = businessResponse.data[0].id;
          setBusinessId(fetchedBusinessId);

          // Fetch appointments for that business
          const appointmentsResponse = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/appointments/business/${fetchedBusinessId}`);
          setAppointments(appointmentsResponse.data);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };
    fetchBusinessAndAppointments();
  }, []);

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Appointments
        </Typography>
        {appointments.length === 0 ? (
          <Typography>No appointments found.</Typography>
        ) : (
          <List>
            {appointments.map((appointment) => (
              <ListItem key={appointment.id} divider>
                <ListItemText
                  primary={`Service: ${appointment.service_type} with ${appointment.customer_name} (${appointment.customer_phone})`}
                  secondary={`Time: ${new Date(appointment.appointment_time).toLocaleString()} - Status: ${appointment.status}`}
                />
              </ListItem>
            ))}
          </List>
        )}
      </Box>
    </Container>
  );
}
