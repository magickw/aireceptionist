'use client';
import * as React from 'react';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Grid from '@mui/material/Grid';
import Chip from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';
import Avatar from '@mui/material/Avatar';
import CalendarMonth from '@mui/icons-material/CalendarMonth';
import CheckCircle from '@mui/icons-material/CheckCircle';
import Error from '@mui/icons-material/Error';
import Refresh from '@mui/icons-material/Refresh';
import Link from '@mui/icons-material/Link';
import Delete from '@mui/icons-material/Delete';
import api, { calendlyApi } from '@/services/api';

interface CalendlyIntegration {
  id: number;
  provider: string;
  status: 'active' | 'inactive' | 'expired';
  calendar_id: string | null;
  token_expires_at: string | null;
  token_expiring_soon: boolean;
  last_sync_at: string | null;
}

interface CalendlyEventType {
  uri: string;
  name: string;
  description: string | null;
  duration_minutes: number;
  active: boolean;
}

interface CalendlyEvent {
  uri: string;
  event_type: string;
  start_time: string;
  end_time: string;
  invitee_name: string;
  invitee_email: string;
  status: string;
}

export default function CalendlyPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [integration, setIntegration] = useState<CalendlyIntegration | null>(null);
  const [eventTypes, setEventTypes] = useState<CalendlyEventType[]>([]);
  const [events, setEvents] = useState<CalendlyEvent[]>([]);
  const [selectedDateRange, setSelectedDateRange] = useState({
    start: new Date().toISOString(),
    end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() // Next 30 days
  });

  useEffect(() => {
    checkIntegrationStatus();
  }, []);

  const checkIntegrationStatus = async () => {
    setLoading(true);
    setError('');
    
    try {
      // Get calendar integrations
      const response = await api.get('/calendar');
      const integrations = response.data.integrations || [];
      
      const calendlyIntegration = integrations.find((i: any) => i.provider === 'calendly');
      
      if (calendlyIntegration) {
        setIntegration(calendlyIntegration);
        
        // If active, fetch event types and events
        if (calendlyIntegration.status === 'active') {
          await fetchEventTypes(calendlyIntegration.id);
          await fetchEvents(calendlyIntegration.id);
        }
      } else {
        setIntegration(null);
      }
    } catch (err: any) {
      console.error('Error checking Calendly status:', err);
      setError('Failed to load Calendly integration status');
    } finally {
      setLoading(false);
    }
  };

  const fetchEventTypes = async (integrationId: number) => {
    try {
      const response = await calendlyApi.getEventTypes(integrationId);
      setEventTypes(response.data.event_types || []);
    } catch (err: any) {
      console.error('Error fetching event types:', err);
    }
  };

  const fetchEvents = async (integrationId: number) => {
    try {
      const response = await calendlyApi.getEvents(integrationId, selectedDateRange.start, selectedDateRange.end);
      setEvents(response.data.events || []);
    } catch (err: any) {
      console.error('Error fetching events:', err);
    }
  };

  const handleConnect = async () => {
    setConnecting(true);
    setError('');
    try {
      const response = await calendlyApi.connect();
      window.location.href = response.data.auth_url;
    } catch (err: any) {
      setError('Failed to initiate Calendly connection: ' + (err.response?.data?.detail || err.message));
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!integration) return;
    if (!confirm('Are you sure you want to disconnect Calendly? This will stop all Calendly integrations.')) return;
    try {
      await api.delete(`/calendar/${integration.id}`);
      setSuccess('Calendly disconnected successfully');
      setIntegration(null);
      setEventTypes([]);
      setEvents([]);
      setTimeout(() => setSuccess(''), 5000);
    } catch (err: any) {
      setError('Failed to disconnect Calendly: ' + (err.response?.data?.detail || err.message));
      setTimeout(() => setError(''), 5000);
    }
  };

  const handleRefresh = async () => {
    if (!integration) return;
    
    try {
      await checkIntegrationStatus();
      setSuccess('Calendly data refreshed successfully');
      setTimeout(() => setSuccess(''), 5000);
    } catch (err: any) {
      setError('Failed to refresh Calendly data: ' + (err.response?.data?.detail || err.message));
      setTimeout(() => setError(''), 5000);
    }
  };

  const getStatusChip = () => {
    if (!integration) {
      return <Chip label="Not Connected" color="default" />;
    }
    
    switch (integration.status) {
      case 'active':
        if (integration.token_expiring_soon) {
          return <Chip label="Token Expiring Soon" color="warning" icon={<Refresh />} />;
        }
        return <Chip label="Connected" color="success" icon={<CheckCircle />} />;
      case 'expired':
        return <Chip label="Expired" color="error" icon={<Error />} />;
      case 'inactive':
        return <Chip label="Inactive" color="default" />;
      default:
        return <Chip label="Unknown" color="default" />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <LinearProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Calendly Integration
      </Typography>
      
      <Typography variant="body1" color="text.secondary" paragraph>
        Connect your Calendly account to automatically sync appointments and manage bookings through the AI receptionist.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {/* Connection Status Card */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} sm={6}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{ bgcolor: '#006BFF', width: 56, height: 56 }}>
                  <CalendarMonth />
                </Avatar>
                <Box>
                  <Typography variant="h6">Calendly</Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                    {getStatusChip()}
                  </Box>
                </Box>
              </Box>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                {!integration || integration.status !== 'active' ? (
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={handleConnect}
                    disabled={connecting}
                    startIcon={<Link />}
                  >
                    {connecting ? 'Connecting...' : 'Connect Calendly'}
                  </Button>
                ) : (
                  <>
                    <Button
                      variant="outlined"
                      color="primary"
                      onClick={handleRefresh}
                      startIcon={<Refresh />}
                    >
                      Refresh
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      onClick={handleDisconnect}
                      startIcon={<Delete />}
                    >
                      Disconnect
                    </Button>
                  </>
                )}
              </Box>
            </Grid>
          </Grid>

          {integration && integration.status === 'active' && (
            <Box sx={{ mt: 3 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Calendar ID
                  </Typography>
                  <Typography variant="body1" fontFamily="monospace">
                    {integration.calendar_id || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Token Expires
                  </Typography>
                  <Typography variant="body1">
                    {integration.token_expires_at ? formatDate(integration.token_expires_at) : 'N/A'}
                    {integration.token_expiring_soon && (
                      <Chip label="Expiring Soon" size="small" color="warning" sx={{ ml: 1 }} />
                    )}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Last Sync
                  </Typography>
                  <Typography variant="body1">
                    {integration.last_sync_at ? formatDate(integration.last_sync_at) : 'Never'}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Event Types Section */}
      {integration && integration.status === 'active' && eventTypes.length > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Available Event Types
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              These are the booking types available in your Calendly account
            </Typography>
            
            <Grid container spacing={2}>
              {eventTypes.map((eventType) => (
                <Grid item xs={12} sm={6} md={4} key={eventType.uri}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {eventType.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {eventType.duration_minutes} minutes
                      </Typography>
                      {eventType.description && (
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          {eventType.description}
                        </Typography>
                      )}
                      <Chip
                        label={eventType.active ? 'Active' : 'Inactive'}
                        size="small"
                        color={eventType.active ? 'success' : 'default'}
                        sx={{ mt: 1 }}
                      />
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Upcoming Events Section */}
      {integration && integration.status === 'active' && events.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Upcoming Events (Next 30 Days)
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Bookings synced from your Calendly account
            </Typography>
            
            <Grid container spacing={2}>
              {events.map((event) => (
                <Grid item xs={12} key={event.uri}>
                  <Card variant="outlined">
                    <CardContent>
                      <Grid container spacing={2} alignItems="center">
                        <Grid item xs={12} sm={4}>
                          <Typography variant="subtitle1" fontWeight="bold">
                            {event.event_type}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {event.invitee_name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {event.invitee_email}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={4}>
                          <Typography variant="body2" color="text.secondary">
                            Start Time
                          </Typography>
                          <Typography variant="body1">
                            {formatDate(event.start_time)}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={4}>
                          <Typography variant="body2" color="text.secondary">
                            End Time
                          </Typography>
                          <Typography variant="body1">
                            {formatDate(event.end_time)}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={12}>
                          <Chip
                            label={event.status}
                            size="small"
                            color={event.status === 'confirmed' ? 'success' : 'default'}
                          />
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {integration && integration.status === 'active' && events.length === 0 && (
        <Card>
          <CardContent>
            <Typography variant="body1" color="text.secondary" align="center">
              No upcoming events scheduled in the next 30 days
            </Typography>
          </CardContent>
        </Card>
      )}
    </Container>
  );
}
