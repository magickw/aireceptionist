'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import {
  Container, Typography, Box, Grid, Card, CardContent, 
  TextField, Button, CircularProgress, Alert, Divider,
  Paper, List, ListItem, ListItemText, Chip, Avatar
} from '@mui/material';
import EventIcon from '@mui/icons-material/Event';
import ShoppingBagIcon from '@mui/icons-material/ShoppingBag';
import PhoneIcon from '@mui/icons-material/Phone';
import api from '@/services/api';

export default function CustomerPortal() {
  const params = useParams();
  const businessId = params.id;
  
  const [business, setBusiness] = useState<any>(null);
  const [phone, setPhone] = useState('');
  const [isVerified, setIsVerified] = useState(false);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [data, setData] = useState({ appointments: [], orders: [] });
  const [error, setError] = useState('');

  useEffect(() => {
    fetchBusiness();
  }, [businessId]);

  const fetchBusiness = async () => {
    try {
      const res = await api.get(`/portal/business/${businessId}/profile`);
      setBusiness(res.data);
    } catch (err) {
      setError('Business not found.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    try {
      setVerifying(true);
      setError('');
      const res = await api.post('/portal/verify', { business_id: businessId, phone });
      
      // Fetch customer data
      const [appts, orders] = await Promise.all([
        api.get(`/portal/appointments?phone=${phone}&business_id=${businessId}`),
        api.get(`/portal/orders?phone=${phone}&business_id=${businessId}`)
      ]);
      
      setData({ appointments: appts.data, orders: orders.data });
      setIsVerified(true);
    } catch (err) {
      setError('Verification failed. Please check your phone number.');
    } finally {
      setVerifying(false);
    }
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}><CircularProgress /></Box>;
  if (!business) return <Container sx={{ mt: 4 }}><Alert severity="error">Business not found</Alert></Container>;

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f5f7fa', pb: 8 }}>
      {/* Brand Header */}
      <Paper sx={{ py: 4, px: 2, borderRadius: 0, bgcolor: 'primary.main', color: 'white', mb: 4 }}>
        <Container maxWidth="md">
          <Typography variant="h4" fontWeight="bold">{business.name}</Typography>
          <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>Customer Service Portal</Typography>
        </Container>
      </Paper>

      <Container maxWidth="md">
        {!isVerified ? (
          <Card variant="outlined" sx={{ maxWidth: 400, mx: 'auto', mt: 4 }}>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h6" gutterBottom align="center">Welcome back!</Typography>
              <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 4 }}>
                Enter your phone number to view your appointments and orders.
              </Typography>
              
              {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
              
              <TextField
                fullWidth
                label="Phone Number"
                placeholder="+15551234567"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                sx={{ mb: 3 }}
              />
              
              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handleVerify}
                disabled={verifying || !phone}
              >
                {verifying ? <CircularProgress size={24} color="inherit" /> : 'Access My Portal'}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <Grid container spacing={4}>
            {/* Appointments */}
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <EventIcon color="primary" /> My Appointments
              </Typography>
              <Card variant="outlined">
                <CardContent sx={{ p: 0 }}>
                  <List>
                    {data.appointments.length === 0 ? (
                      <ListItem><ListItemText secondary="No appointments found" /></ListItem>
                    ) : (
                      data.appointments.map((apt: any) => (
                        <React.Fragment key={apt.id}>
                          <ListItem>
                            <ListItemText 
                              primary={apt.service_type || 'Service'} 
                              secondary={new Date(apt.appointment_time).toLocaleString()}
                            />
                            <Chip label={apt.status} color="primary" size="small" variant="outlined" />
                          </ListItem>
                          <Divider />
                        </React.Fragment>
                      ))
                    )}
                  </List>
                </CardContent>
              </Card>
            </Grid>

            {/* Orders */}
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ShoppingBagIcon color="primary" /> My Recent Orders
              </Typography>
              <Card variant="outlined">
                <CardContent sx={{ p: 0 }}>
                  <List>
                    {data.orders.length === 0 ? (
                      <ListItem><ListItemText secondary="No orders found" /></ListItem>
                    ) : (
                      data.orders.map((order: any) => (
                        <React.Fragment key={order.id}>
                          <ListItem>
                            <ListItemText 
                              primary={`Order #${order.id.slice(0, 8)}`} 
                              secondary={`Total: $${order.total_amount} • ${new Date(order.created_at).toLocaleDateString()}`}
                            />
                            <Chip label={order.status} color="success" size="small" variant="outlined" />
                          </ListItem>
                          <Divider />
                        </React.Fragment>
                      ))
                    )}
                  </List>
                </CardContent>
              </Card>
            </Grid>

            {/* Business Info */}
            <Grid item xs={12}>
              <Card variant="outlined" sx={{ bgcolor: 'white' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Business Information</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="overline" color="text.secondary">Address</Typography>
                      <Typography variant="body2">{business.address || 'Online only'}</Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="overline" color="text.secondary">Contact</Typography>
                      <Typography variant="body2">{business.phone}</Typography>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Typography variant="overline" color="text.secondary">Hours</Typography>
                      <Typography variant="body2">{business.operating_hours || 'Contact business for hours'}</Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </Container>
    </Box>
  );
}
